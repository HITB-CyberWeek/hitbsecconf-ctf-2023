using System.Text.Json;

namespace spaces;

internal static class Storage
{
    public static async Task<State?> TryLoadStateAsync(Guid userId, CancellationToken cancel)
    {
        try
        {
            var ctx = await TryReadAsync<Context>(GetContextFilePath(userId), cancel);
            return ctx == null ? null : new State(ctx, await FindUserAsync(userId, ctx.Space.ToBase58(), cancel) ?? throw new InvalidOperationException());
        }
        catch { return default; }
    }

    public static async Task SaveContextAsync(Guid userId, Context ctx, CancellationToken cancel)
        => await WriteAsync(ctx, GetContextFilePath(userId), true, cancel);

    public static Task AddUserToSpaceAsync(string space, Guid userId, User user, CancellationToken cancel)
        => WriteAsync(user, GetUserFilePath(space, userId), false, cancel);
    public static async Task<User?> FindUserAsync(Guid userId, string space, CancellationToken cancel)
        => await TryReadAsync<User>(GetUserFilePath(space, userId), cancel);

    public static void CreateSpace(string space)
        => Directory.CreateDirectory(GetSpaceDirPath(space));
    public static void CreateRoom(string space, string room)
        => Directory.CreateDirectory(GetRoomDirPath(space, room));
    public static ValueTask CloseSpace(string space)
        => TouchFile(GetCloseFilePath(space));

    private static long writtenCount;
    public static Task SaveMessageAsync(string space, string? room, Message message, CancellationToken cancel)
        => WriteAsync(message, GetMessageFilePath(space, room, message.Time.Ticks.ToString("x16") + Interlocked.Increment(ref writtenCount).ToString("x16")), false, cancel);

    public static IAsyncEnumerable<Message> TryReadMessages(string space, string? room, CancellationToken cancel)
    {
        try { return ReadMessages(space, room, cancel); }
        catch(DirectoryNotFoundException) { return AsyncEnumerable.Empty<Message>(); }
    }

    private static IAsyncEnumerable<Message> ReadMessages(string space, string? room, CancellationToken cancel)
        => Directory.EnumerateFiles(GetRoomDirPath(space, room), '*' + MsgFileExt, SearchOption.TopDirectoryOnly)
            .ToAsyncEnumerable()
            .OrderBy(file => file, StringComparer.OrdinalIgnoreCase)
            .SelectAwait(async file => await TryReadAsync<Message>(file, cancel))
            .Where(msg => msg != null)!
            .TakeHeadAndTail<Message>(3, 3, skipped => EnumerableHelper.Yield(new Message { Type = MsgType.Error, Author = AvatarGen.SystemName, Avatar = AvatarGen.SystemAvatar, Text = $"... {skipped} messages skipped ..." }));

    private static async Task<T?> TryReadAsync<T>(string filepath, CancellationToken cancel)
    {
        try
        {
            await using var stream = new FileStream(filepath, FileMode.Open, FileAccess.Read, FileShare.Read, BufferSize, FileOptions.Asynchronous);
            return await JsonSerializer.DeserializeAsync<T>(stream, JsonHelper.SerializerOptions, cancel);
        }
        catch(DirectoryNotFoundException) { return default; }
        catch(FileNotFoundException) { return default; }
    }

    private static async Task<T?> WriteAsync<T>(T item, string filepath, bool overwrite, CancellationToken cancel)
    {
        await using var stream = new FileStream(filepath, overwrite ? FileMode.Create : FileMode.CreateNew, FileAccess.Write, FileShare.None, BufferSize, FileOptions.Asynchronous);
        await JsonSerializer.SerializeAsync(stream, item, JsonHelper.SerializerOptions, cancel);
        return item;
    }

    private static ValueTask TouchFile(string file)
        => File.Create(file).DisposeAsync();

    public static bool IsSpaceExists(string space)
        => Directory.Exists(GetSpaceDirPath(space));
    private static bool IsSpaceClosed(string space)
        => File.Exists(GetCloseFilePath(space));
    public static bool HasAccess(string space, Guid userId)
        => !IsSpaceClosed(space) || File.Exists(GetUserFilePath(space, userId));

    private static string GetContextFilePath(Guid userId)
        => Path.Combine(DataPath, userId.ToString("N") + CtxFileExt);
    private static string GetSpaceDirPath(string space)
        => Path.Combine(DataPath, space);
    private static string GetRoomDirPath(string space, string? room)
        => Path.Combine(DataPath, space, room ?? string.Empty);
    private static string GetCloseFilePath(string space)
        => Path.Combine(DataPath, space, SpaceClosed);
    private static string GetUserFilePath(string space, Guid userId)
        => Path.Combine(DataPath, space, userId.ToString("N") + UsrFileExt);
    private static string GetMessageFilePath(string space, string? room, string msgId)
        => Path.Combine(DataPath, space, room ?? string.Empty, msgId + MsgFileExt);

    private const int BufferSize = 4096;

    private const string DataPath = "data/";
    private const string SpaceClosed = ".lock";
    private const string CtxFileExt = ".ctx";
    private const string MsgFileExt = ".msg";
    private const string UsrFileExt = ".usr";
}
