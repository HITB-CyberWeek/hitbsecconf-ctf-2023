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
        DefaultBufferSize = 1024
    };
}

internal static class EnumerableHelper
{
    public static IEnumerable<T> Yield<T>(T item)
    {
        yield return item;
    }
}

internal static class StringHelper
{
    public static string? NullIfEmpty(this string? value)
        => value == string.Empty ? null : value;
}
