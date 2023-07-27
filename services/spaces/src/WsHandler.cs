using System.Buffers;
using System.Collections.Concurrent;
using System.Net.WebSockets;
using System.Text.Json;
using CommunityToolkit.HighPerformance.Buffers;

namespace spaces;

internal static class WebSocketHandler
{
    public static async Task MessageLoopAsync(WebSocket ws, Guid userId, CancellationToken cancel)
    {
        var conn = new Connection(ws, userId);

        var state = await Storage.TryLoadStateAsync(userId, cancel);
        state = state?.User != null ? state : new State(null, conn.GenUser());
        conn.State = state;

        Connections[ws] = conn;

        await conn.JoinAsync(state, cancel);

        while(!cancel.IsCancellationRequested && ws.State == WebSocketState.Open)
        {
            bool continuation = false;
            ValueWebSocketReceiveResult rcv;
            var buffer = MemoryPool<byte>.Shared.Rent(MaxMessageSize);
            try
            {
                rcv = await ws.ReceiveAsync(buffer.Memory, cancel);
                if(rcv.MessageType == WebSocketMessageType.Close)
                    break;
                if(!rcv.EndOfMessage) // Too large fragmented message, skip all fragments except the last one
                    continue;
                continuation = true;
            }
            catch
            {
                break;
            }
            finally
            {
                if(!continuation)
                    buffer.Dispose();
            }

            _ = Task.Run(async () =>
            {
                try
                {
                    var cmd = JsonSerializer.Deserialize<Command>(buffer.Memory.Span.Slice(0, rcv.Count), JsonHelper.SerializerOptions);
                    if(cmd == default)
                        return;
                    await conn.ExecuteCommandAsync(cmd, cancel);
                }
                catch
                {
                    await conn.TrySendErrorAsync("Failed to process command", cancel);
                }
                finally
                {
                    buffer.Dispose();
                }
            }, cancel);
        }

        Connections.TryRemove(ws, out var removed);

        try { await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, string.Empty, cancel); }
        catch { /* ignored */ }

        if(removed?.State?.Context == null)
            return;

        await BroadcastAsync(removed.State, MsgType.Leave, "Left", cancel);
    }

    private static Task ExecuteCommandAsync(this Connection conn, Command cmd, CancellationToken cancel) => cmd.Type switch
    {
        MsgType.Close => conn.CtxLimit.WithRpmLimit(conn.CloseSpace, () => conn.TrySendErrorAsync("Space ops limit exceeded, wait 1 min", cancel), 6),
        MsgType.Join => conn.CtxLimit.WithRpmLimit(() => conn.JoinAsync(cmd.Data, cancel), () => conn.TrySendErrorAsync("Space ops limit exceeded, wait 1 min", cancel), 6),
        MsgType.Room => conn.CtxLimit.WithRpmLimit(() => conn.JoinRoomAsync(cmd.Data, cancel), () => conn.TrySendErrorAsync("Space ops limit exceeded, wait 1 min", cancel), 6),
        MsgType.Msg => conn.MsgLimit.WithRpmLimit(() => conn.SendMessage(cmd.Data, cancel), () => conn.TrySendErrorAsync("Messages limit exceeded, wait 1 min", cancel), 60),
        MsgType.Generate => conn.ProfileLimit.WithRpmLimit(() => conn.GenProfile(cancel), () => conn.TrySendErrorAsync("Profile limit exceeded, wait 1 min", cancel), 600),
        _ => throw new Exception()
    };

    private static async Task CloseSpace(this Connection conn)
    {
        var space = conn.State?.Context?.Space ?? 0UL;
        if(space == 0UL)
            return;

        await Storage.CloseSpace(space);
    }

    private static User GenUser(this Connection conn)
        => new(Names.Humanoids[conn.Random.Value.Next(Names.Humanoids.Length)], conn.Random.Value.CreateAvatar());

    private static async Task GenProfile(this Connection conn, CancellationToken cancel)
    {
        var state = conn.State;
        if(state?.Context != null)
            return;

        conn.State = state = new State(null, conn.GenUser());
        await conn.TrySendMessageAsync(new Message
        {
            Type = MsgType.Generate,
            Author = state.User.Name,
            Avatar = state.User.Avatar
        }, cancel);
    }

    private static async Task SendMessage(this Connection conn, string? text, CancellationToken cancel)
    {
        if(string.IsNullOrEmpty(text))
            return;

        var state = conn.State;
        if(state == null)
            return;

        var (ctx, user) = state;
        if(ctx == null)
            return;

        var msg = new Message
        {
            Type = MsgType.Msg,
            Author = user.Name,
            Avatar = user.Avatar,
            Text = text
        };

        await Storage.SaveMessage(msg, ctx, cancel);
        await GetSpaceConnections(ctx).BroadcastAsync(msg, cancel);
    }

    private static async Task JoinAsync(this Connection conn, string? value, CancellationToken cancel)
    {
        if(ContextHelper.TryParseContext(value, out var ctx) && !Storage.IsSpaceExists(ctx!.Space))
        {
            await conn.TrySendErrorAsync("Space not exists", cancel);
            return;
        }

        ctx ??= new Context(conn.RndSpace(), null);

        var user = await Storage.TryJoinOrCreateAsync(conn.UserId, ctx, conn.State?.User ?? throw new InvalidOperationException(), cancel);
        if(user == null)
        {
            await conn.TrySendErrorAsync("Space is closed", cancel);
            return;
        }

        var state = new State(ctx, user);
        conn.State = state;

        await conn.JoinAsync(state, cancel);
    }

    private static async Task JoinAsync(this Connection conn, State state, CancellationToken cancel)
    {
        if(state.Context == null)
            return;

        await foreach(var msg in Storage.TryReadMessages(state.Context, cancel))
            await conn.TrySendMessageAsync(msg, cancel);

        await BroadcastAsync(state, MsgType.Join, "Joined", cancel);
    }

    private static async Task JoinRoomAsync(this Connection conn, string? room, CancellationToken cancel)
    {
        var state = conn.State;
        if(state?.Context == null)
            return;

        room = room?.Trim().NullIfEmpty();
        if(state.Context.Room == room)
            return;

        if(!ContextHelper.IsRoomValid(room))
            return;

        var ctx = state.Context with { Room = room };
        state = state with { Context = ctx };
        conn.State = state;

        Storage.CreateRoom(ctx);

        await foreach(var msg in Storage.TryReadMessages(ctx, cancel))
            await conn.TrySendMessageAsync(msg, cancel);

        await GetSpaceConnections(ctx.Space).BroadcastAsync(state, MsgType.Room, string.IsNullOrEmpty(room) ? "Returned back to space root" : $"Entered room '{room}'", cancel);
    }

    private static async Task BroadcastAsync(State state, MsgType type, string text, CancellationToken cancel)
        => await GetSpaceConnections(state.Context).BroadcastAsync(state, type, text, cancel);

    private static Task BroadcastAsync(this IEnumerable<Connection> connections, State state, MsgType type, string text, CancellationToken cancel) => connections.BroadcastAsync(new Message
    {
        Context = state.Context?.ToStringValue(),
        Type = type,
        Text = text,
        Author = state.User.Name,
        Avatar = state.User.Avatar
    }, cancel);

    private static IEnumerable<Connection> GetSpaceConnections(Context? ctx)
        => ctx == null ? Enumerable.Empty<Connection>() : Connections.Select(pair => pair.Value).Where(c => c.State?.Context == ctx);

    private static IEnumerable<Connection> GetSpaceConnections(ulong space)
        => Connections.Select(pair => pair.Value).Where(c => c.State?.Context?.Space == space);

    private static Task TrySendErrorAsync(this Connection conn, string text, CancellationToken cancel) => conn.TrySendMessageAsync(new Message
    {
        Type = MsgType.Error,
        Author = AvatarGen.SystemName,
        Avatar = AvatarGen.SystemAvatar,
        Text = text
    }, cancel);

    private static Task TrySendMessageAsync(this Connection conn, Message msg, CancellationToken cancel)
        => BroadcastAsync(EnumerableHelper.Yield(conn), msg, cancel);

    private static async Task BroadcastAsync(this IEnumerable<Connection> connections, Message msg, CancellationToken cancel)
    {
        using var buffer = MemoryPool<byte>.Shared.Rent(MaxMessageSize);
        var serialized = SerializeMessage(msg, buffer.Memory);
        await Task.WhenAll(connections.Select(conn => TrySendMessageAsync(conn, serialized, cancel)));
    }

    private static ReadOnlyMemory<byte> SerializeMessage(Message msg, Memory<byte> memory)
    {
        var writer = new MemoryBufferWriter<byte>(memory);
        using var jsonWriter = new Utf8JsonWriter(writer);
        JsonSerializer.Serialize(jsonWriter, msg, JsonHelper.SerializerOptions);
        return writer.WrittenMemory;
    }

    private static async Task TrySendMessageAsync(Connection conn, ReadOnlyMemory<byte> memory, CancellationToken cancel)
    {
        await conn.WsSendSync.WaitAsync(cancel);
        try { await conn.Ws.SendAsync(memory, WebSocketMessageType.Text, true, cancel); }
        catch { /* ignored */ }
        finally { conn.WsSendSync.Release(); }
    }

    private static ulong RndSpace(this Connection conn)
        => unchecked((ulong)conn.Random.Value.NextInt64());

    private static readonly ConcurrentDictionary<WebSocket, Connection> Connections = new();
    private const int MaxMessageSize = 4096;
}

internal class Connection
{
    public Connection(WebSocket ws, Guid userId)
    {
        Ws = ws;
        UserId = userId;
    }

    public readonly WebSocket Ws;
    public readonly Guid UserId;

    public volatile State? State;

    public readonly SemaphoreSlim WsSendSync = new(1, 1);
    public readonly Lazy<Random> Random = new(() => new Random(Guid.NewGuid().GetHashCode()));

    public readonly RequestLimit CtxLimit = new();
    public readonly RequestLimit MsgLimit = new();
    public readonly RequestLimit ProfileLimit = new();
}
