using System.Text.Json.Serialization;

namespace checker;

internal class PutResult
{
	[JsonPropertyName("public_flag_id")] public string PublicFlagId { get; set; }

	[JsonPropertyName("c")] public string Cookie { get; set; }
	[JsonPropertyName("rc")] public bool RoomChanged { get; set; }
}
