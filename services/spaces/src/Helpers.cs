using System.Text.Json;
using System.Text.Json.Serialization;

namespace spaces;

internal static class ContextHelper
{
    public static string ToStringValue(this Context ctx)
        => string.IsNullOrWhiteSpace(ctx.Room) ? ctx.Space.ToBase58() : string.Join("/", ctx.Space.ToBase58(), ctx.Room);

    public static bool IsRoomValid(string? room)
        => string.IsNullOrEmpty(room) || room.All(char.IsAsciiLetterOrDigit);

    public static bool TryParseContext(string? value, out Context? ctx)
    {
        ctx = null;
        if((value = value?.Trim().NullIfEmpty()) == null)
            return false;

        var parts = value.Split('/');
        if(parts.Length > 2)
            return false;

        if(!Base58.TryDecodeUInt64(parts[0], out var space) && space == 0UL)
            return false;

        var room = parts.Length > 1 ? parts[1] : null;
        if(!IsRoomValid(room))
            return false;

        ctx = new Context(space, room);
        return true;
    }
}

internal static class JsonHelper
{
    internal static readonly JsonSerializerOptions SerializerOptions = new()
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingDefault,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultBufferSize = 4096,
        Converters = { new JsonStringEnumConverter(JsonNamingPolicy.CamelCase) }
    };

    /*private sealed class CharArrayConverter : JsonConverter<char[]?>
    {
        public override void Write(Utf8JsonWriter writer, char[]? value, JsonSerializerOptions options)
            => writer.WriteStringValue(value);

        public override char[] Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            var result = new char[Encoding.UTF8.GetCharCount(reader.ValueSpan)];
            if(!Encoding.UTF8.TryGetChars(reader.ValueSpan, result, out var written) || written != result.Length)
                throw new InvalidOperationException("Invalid json string value");
            return result;
        }
    }*/

    /*internal sealed class ContextConverter : JsonConverter<Context?>
    {
        public override bool HandleNull => true;

        public override void Write(Utf8JsonWriter writer, Context? value, JsonSerializerOptions options)
        {
            if(value == null)
                writer.WriteNullValue();
            else if(string.IsNullOrEmpty(value.Room))
                writer.WriteStringValue(value.Space.ToBase58());
            else
                writer.WriteStringValue(string.Join("/", value.Space.ToBase58(), value.Room));
        }

        public override Context? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
            => throw new NotImplementedException();
    }*/
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
