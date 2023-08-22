using System;
using System.Text.Json.Serialization;

namespace checker.spaces;

public class Command
{
	public MsgType Type { get; set; }
	public string Data { get; set; }
}

internal class Message
{
	[JsonInclude] public MsgType Type { get; set; }
	[JsonInclude] public string? Context { get; set; }
	[JsonInclude] public string? Author { get; set; }
	[JsonInclude] public string? Avatar { get; set; }
	[JsonInclude] public string? Text { get; set; }
	[JsonInclude] public DateTime Time { get; set; }
}

public enum MsgType
{
	Error = 1,
	Generate,
	Close,
	Join,
	Room,
	Msg
}
