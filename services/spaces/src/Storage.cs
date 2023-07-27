using System.Text.Json;

namespace spaces;

internal static class Storage
{
    public static async Task<User?> TryJoinOrCreateAsync(Guid userId, Context ctx, User user, CancellationToken cancel)
    {
        var saved = await FindUser(userId, ctx.Space, cancel);
        if(saved == null && IsSpaceClosed(ctx.Space))
            return null;

        Directory.CreateDirectory(GetSpaceDirPath(ctx.Space, ctx.Room));

        await WriteAsync(ctx, null, userId, CtxFileExt, true, cancel);
        if(saved != null)
            return saved;

        await WriteAsync(user, ctx, userId, UsrFileExt, false, cancel);
        return user;
    }

    public static void CreateRoom(Context ctx)
        => Directory.CreateDirectory(GetSpaceDirPath(ctx.Space, ctx.Room));

    public static async Task<State?> TryLoadStateAsync(Guid userId, CancellationToken cancel)
    {
        var ctx = await TryReadAsync<Context>(GetContextFilePath(userId), cancel);
        return ctx == null ? null : new State(ctx, await FindUser(userId, ctx.Space, cancel) ?? throw new InvalidOperationException());
    }

    public static ValueTask CloseSpace(ulong space)
        => TouchFile(GetCloseFilePath(space));

    public static Task SaveMessage(Message message, Context ctx, CancellationToken cancel)
        => WriteAsync(message, ctx, Guid.NewGuid(), MsgFileExt, false, cancel);

    public static IAsyncEnumerable<Message> TryReadMessages(Context ctx, CancellationToken cancel)
    {
        try { return ReadMessages(ctx, cancel); }
        catch(DirectoryNotFoundException) { return AsyncEnumerable.Empty<Message>(); }
    }

    private static async Task<User?> FindUser(Guid userId, ulong space, CancellationToken cancel)
        => await TryReadAsync<User>(GetUserFilePath(space, userId), cancel);

    private static ValueTask TouchFile(string file)
        => File.Create(file).DisposeAsync();

    private static IAsyncEnumerable<Message> ReadMessages(Context ctx, CancellationToken cancel)
        => Directory.EnumerateFiles(Path.Combine(DataPath, ctx.Space.ToBase58(), ctx.Room ?? string.Empty), '*' + MsgFileExt, SearchOption.TopDirectoryOnly)
            .ToAsyncEnumerable()
            .SelectAwait(async file => await TryReadAsync<Message>(file, cancel))
            .Where(msg => msg != null)!;

    private static async Task<T?> WriteAsync<T>(T item, Context? ctx, Guid id, string ext, bool overwrite, CancellationToken cancel)
    {
        var path = Path.Combine(DataPath, ctx?.Space.ToBase58() ?? string.Empty, ctx?.Room ?? string.Empty, id.ToString("N") + ext);
        await using var stream = new FileStream(path, overwrite ? FileMode.Create : FileMode.CreateNew, FileAccess.Write, FileShare.None, BufferSize, FileOptions.Asynchronous);
        await JsonSerializer.SerializeAsync(stream, item, JsonHelper.SerializerOptions, cancel);
        return item;
    }

    private static Task<T?> TryReadAsync<T>(ulong space, string? room, Guid id, string ext, CancellationToken cancel)
        => TryReadAsync<T>(Path.Combine(DataPath, space.ToBase58(), room ?? string.Empty, id.ToString("N") + ext), cancel);

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

    public static bool IsSpaceExists(ulong space)
        => Directory.Exists(GetSpaceDirPath(space));

    private static bool IsSpaceClosed(ulong space)
        => File.Exists(GetCloseFilePath(space));

    private static string GetSpaceDirPath(ulong space, string? room = null)
        => Path.Combine(DataPath, space.ToBase58(), room ?? string.Empty);

    private static string GetCloseFilePath(ulong space)
        => Path.Combine(DataPath, space.ToBase58(), SpaceClosed);

    private static string GetUserFilePath(ulong space, Guid userId)
        => Path.Combine(DataPath, space.ToBase58(), userId.ToString("N") + UsrFileExt);

    private static string GetContextFilePath(Guid userId)
        => Path.Combine(DataPath, userId.ToString("N") + CtxFileExt);

    private const int BufferSize = 4096;

    private const string DataPath = "data/";
    private const string SpaceClosed = ".lck";
    private const string CtxFileExt = ".ctx";
    private const string MsgFileExt = ".msg";
    private const string UsrFileExt = ".usr";
}
