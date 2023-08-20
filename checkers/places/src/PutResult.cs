using System.Text.Json.Serialization;

namespace checker;

internal class PutResult
{
	[JsonPropertyName("public_flag_id")] public string PublicFlagId { get; set; }

	[JsonPropertyName("p")] public string PublicHash { get; set; }
	[JsonPropertyName("s")] public string SecretHash { get; set; }
	[JsonPropertyName("r")] public string[] Route { get; set; }
	[JsonPropertyName("cf")] public string CookieWithFlag { get; set; }
	[JsonPropertyName("cn")] public string CookieWithoutFlag { get; set; }
}
