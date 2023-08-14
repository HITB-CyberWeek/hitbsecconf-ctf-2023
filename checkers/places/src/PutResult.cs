using System.Text.Json.Serialization;

namespace checker;

internal class PutResult
{
	[JsonPropertyName("public_flag_id")] public string PublicFlagId { get; set; }

	[JsonPropertyName("cookie")] public string Cookie { get; set; }
}
