using System.Text.Json;
using System.Text.Json.Serialization;

namespace spaces;

internal static class ContextHelper
{
    public static string ToStringValue(this Context ctx)
        => string.IsNullOrWhiteSpace(ctx.Room) ? ctx.Space.ToBase58() : string.Join("/", ctx.Space.ToBase58(), ctx.Room);

    public static bool IsSpaceValid(string? space)
        => string.IsNullOrEmpty(space) || space.IsBase58Alphabet();

    public static bool IsRoomValid(string? room)
        => string.IsNullOrEmpty(room) || room.All(char.IsAsciiLetter);

    public static bool TryParseSpace(string? value, out ulong space)
    {
        space = 0UL;

        if((value = value?.Trim().NullIfEmpty()) == null)
            return false;

        if(!Base58.TryDecodeUInt64(value, out space) && space == 0UL)
            return false;

        return true;
    }
}

internal static class JsonHelper
{
    internal static readonly JsonSerializerOptions SerializerOptions = new()
    {
        Converters = { new JsonStringEnumConverter(JsonNamingPolicy.CamelCase) },
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingDefault,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultBufferSize = 4096
    };
}

internal static class EnumerableHelper
{
    public static IEnumerable<T> Yield<T>(T item)
    {
        yield return item;
    }

    public static async IAsyncEnumerable<T> TakeHeadAndTail<T>(this IAsyncEnumerable<T> enumerable, int first, int last, Func<int, IEnumerable<T>> replace)
    {
        int count = 0, skipped = 0;
        var queue = new Queue<T>(last);
        await foreach(var item in enumerable)
        {
            if(++count <= first)
                yield return item;
            else
            {
                if(queue.Count == last)
                {
                    queue.Dequeue();
                    skipped++;
                }
                queue.Enqueue(item);
            }
        }

        if(skipped > 0)
        {
            foreach(var item in replace(skipped))
                yield return item;
        }

        foreach(var item in queue)
            yield return item;
    }
}

internal static class StringHelper
{
    public static string? NullIfEmpty(this string? value)
        => value == string.Empty ? null : value;
}
