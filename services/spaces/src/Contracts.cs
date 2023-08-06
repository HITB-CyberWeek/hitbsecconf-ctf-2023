using System.Text.Json.Serialization;

namespace spaces;

internal enum MsgType
{
    Error = 1,
    Generate,
    Close,
    Join,
    Room,
    Msg
}

internal record struct Command(MsgType Type, string? Data);

internal class Message
{
    [JsonInclude] public MsgType Type { get; set; }
    [JsonInclude] public string? Context { get; set; }
    [JsonInclude] public string? Author { get; set; }
    [JsonInclude] public string? Avatar { get; set; }
    [JsonInclude] public string? Text { get; set; }
    [JsonInclude] public DateTime Time { get; private set; } = DateTime.UtcNow;
}

internal record State(Context? Context, User User);
internal record Context(ulong Space, string? Room);
internal record User(string Name, string Avatar);
