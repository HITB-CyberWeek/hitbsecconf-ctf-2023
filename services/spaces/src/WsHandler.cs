using System.Buffers;
using System.Collections.Concurrent;
using System.Net.WebSockets;
using System.Text.Json;
using CommunityToolkit.HighPerformance.Buffers;

namespace spaces;

internal static class WsHandler
{
    public static void CloseConnections() => Task.WhenAll(Connections.Select(async conn =>
    {
        try { await conn.Key.CloseAsync(WebSocketCloseStatus.NormalClosure, null, CancellationToken.None); }
        catch { /* ignored */ }
    })).Wait(TimeSpan.FromSeconds(3));

    public static async Task MessageLoopAsync(WebSocket ws, Guid userId, CancellationToken cancel)
    {
        var conn = new Connection(ws, userId);

        var state = await Storage.TryLoadStateAsync(userId, cancel);
        if(state?.User == null)
        {
            state = new State(null, conn.GenUser());
            await conn.SendProfileGeneratedAsync(state.User, cancel);
        }

        conn.State = state;
        Connections[ws] = conn;

        await conn.JoinAsync(state, true, cancel);

        while(!cancel.IsCancellationRequested && ws.State == WebSocketState.Open)
        {
            bool continuation = false;
            ValueWebSocketReceiveResult rcv;
            var buffer = MemoryPool<byte>.Shared.Rent(MaxInputMessageSize);
            try
            {
                rcv = await ws.ReceiveAsync(buffer.Memory, cancel);
                if(rcv.MessageType == WebSocketMessageType.Close)
                    break;
                if(!conn.ProfileLimit.TryIncrement(Connection.TotalLimitRpm, out var crossed))
                {
                    if(crossed) await conn.TrySendErrorAsync("Limit exceeded, wait 1 min", cancel);
                    continue;
                }
                continuation = true;
            }
            catch { break; }
            finally { if(!continuation) buffer.Dispose(); }

            _ = Task.Run(async () =>
            {
                try
                {
                    var cmd = JsonSerializer.Deserialize<Command>(buffer.Memory.Span.Slice(0, rcv.Count), JsonHelper.SerializerOptions);
                    if(cmd == default)
                        return;
                    if(conn.TryIncrement(cmd.Type, out var crossed) == false)
                    {
                        if(crossed) await conn.TrySendErrorAsync("Limit exceeded, wait 1 min", cancel);
                        return;
                    }
                    await conn.ExecuteCommandAsync(cmd, cancel);
                }
                catch { await conn.TrySendErrorAsync("Failed to process command", cancel); }
                finally { buffer.Dispose(); }
            }, cancel);
        }

        Connections.TryRemove(ws, out _);

        try { await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, string.Empty, cancel); }
        catch { /* ignored */ }
    }

    private static Task ExecuteCommandAsync(this Connection conn, Command cmd, CancellationToken cancel) => cmd.Type switch
    {
        MsgType.Close => conn.CloseSpace(cancel),
        MsgType.Join => conn.JoinAsync(cmd.Data, cancel),
        MsgType.Room => conn.JoinRoomAsync(cmd.Data, cancel),
        MsgType.Msg => conn.SendMessage(cmd.Data, cancel),
        MsgType.Generate => conn.GenProfile(cancel),
        _ => throw new Exception()
    };

    private static async Task CloseSpace(this Connection conn, CancellationToken cancel)
    {
        var state = conn.State;

        var space = state?.Context?.Space ?? 0UL;
        if(space == 0UL)
            return;

        await Storage.CloseSpace(space.ToBase58());

        await GetSpaceConnections(space).BroadcastAsync(state!, MsgType.Close, $"Closed space '{space.ToBase58()}', new members can no longer join", cancel);
    }

    private static User GenUser(this Connection conn)
    {
        var humanoid = Names.Humanoids[conn.Random.Value.Next(Names.Humanoids.Length)];
        var avatar = conn.Random.Value.CreateAvatar(out var color);
        return new($"{color} {humanoid}", avatar);
    }

    private static async Task GenProfile(this Connection conn, CancellationToken cancel)
    {
        var state = conn.State;
        if(state?.Context != null)
            return;

        var user = conn.GenUser();
        conn.State = new State(null, user);

        await conn.SendProfileGeneratedAsync(user, cancel);
    }

    private static async Task SendProfileGeneratedAsync(this Connection conn, User user, CancellationToken cancel)
    {
        await conn.TrySendMessageAsync(new Message
        {
            Type = MsgType.Generate,
            Text = "Generated new anonymous profile",
            Author = user.Name,
            Avatar = user.Avatar
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

        await Storage.SaveMessageAsync(ctx.Space.ToBase58(), ctx.Room, msg, cancel);
        await GetSpaceConnections(ctx).BroadcastAsync(msg, cancel);
    }

    private static async Task JoinAsync(this Connection conn, string? value, CancellationToken cancel)
    {
        value = value?.Trim().NullIfEmpty();

        ulong space;
        if(value == null)
            Storage.CreateSpace((space = conn.RndSpace()).ToBase58());
        else if(!ContextHelper.TryParseSpace(value, out space) || !Storage.IsSpaceExists(value) || !Storage.HasAccess(value, conn.UserId))
        {
            await conn.TrySendErrorAsync("Space not exists or invalid or closed", cancel);
            return;
        }

        var user = await Storage.FindUserAsync(conn.UserId, space.ToBase58(), cancel);
        if(user == null)
            await Storage.AddUserToSpaceAsync(space.ToBase58(), conn.UserId, user = conn.State?.User ?? throw new InvalidOperationException(), cancel);

        var state = new State(new Context(space, null), user);
        await conn.JoinAsync(state, false, cancel);
    }

    private static async Task JoinAsync(this Connection conn, State state, bool init, CancellationToken cancel)
    {
        var ctx = state.Context;
        if(ctx == null)
            return;

        var old = conn.State?.Context;
        if(old != ctx)
            await Storage.SaveContextAsync(conn.UserId, ctx, cancel);

        conn.State = state;

        var space = ctx.Space.ToBase58();
        if(ctx.Room != null)
            Storage.CreateRoom(space, ctx.Room);

        await foreach(var msg in Storage.TryReadMessages(space, ctx.Room, cancel))
            await conn.TrySendMessageAsync(msg, cancel);

        await GetSpaceConnections(ctx.Space).Where(c => c == conn && init || old?.Space != ctx.Space).BroadcastAsync(state, MsgType.Join, $"Joined space '{space}'", cancel);
        await GetSpaceConnections(ctx.Space).Where(c => c == conn && init && ctx.Room != null || old?.Room != ctx.Room).BroadcastAsync(state, MsgType.Room, string.IsNullOrEmpty(ctx.Room) ? "Returned back to space root" : $"Entered room '{ctx.Room}'", cancel);
    }

    private static async Task JoinRoomAsync(this Connection conn, string? room, CancellationToken cancel)
    {
        var state = conn.State;
        if(state?.Context == null)
            return;

        room = room?.Trim().ToLower().NullIfEmpty();
        if(!ContextHelper.IsRoomValid(room))
        {
            await conn.TrySendErrorAsync("Invalid room, only ascii letters allowed", cancel);
            return;
        }

        state = state with { Context = state.Context with { Room = room } };
        await conn.JoinAsync(state, false, cancel);
    }

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
    private static IEnumerable<Connection> GetSpaceConnections(ulong? space)
        => space > 0UL ? Connections.Select(pair => pair.Value).Where(c => c.State?.Context?.Space == space) : Enumerable.Empty<Connection>();

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
        using var buffer = MemoryPool<byte>.Shared.Rent(MaxOutputMessageSize);
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
    private const int MaxOutputMessageSize = 4096;
    private const int MaxInputMessageSize = 256;
}

internal class Connection
{
    public Connection(WebSocket ws, Guid userId)
    {
        Ws = ws;
        UserId = userId;
    }

    public bool TryIncrement(MsgType type, out bool crossed)
    {
        crossed = false;
        var (limit, max) = type switch
        {
            MsgType.Msg => (MsgLimit, MsgLimitRpm),
            MsgType.Join or MsgType.Room or MsgType.Close => (CtxLimit, CtxLimitRpm),
            _ => (null, int.MaxValue)
        };
        return limit == null || limit.TryIncrement(max, out crossed);
    }

    public readonly WebSocket Ws;
    public readonly Guid UserId;

    public volatile State? State;

    public readonly SemaphoreSlim WsSendSync = new(1, 1);
    public readonly Lazy<Random> Random = new(() => new Random(Guid.NewGuid().GetHashCode()));

    public readonly RequestLimit CtxLimit = new();
    public readonly RequestLimit MsgLimit = new();
    public readonly RequestLimit ProfileLimit = new();

    public const int CtxLimitRpm = 6;
    public const int MsgLimitRpm = 60;
    public const int TotalLimitRpm = 600;
}
