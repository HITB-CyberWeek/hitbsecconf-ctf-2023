using System.Text.Json.Serialization;

namespace checker;

internal class PutResult
{
	[JsonPropertyName("public_flag_id")] public string PublicFlagId { get; set; }

	[JsonPropertyName("public")] public string PublicHash { get; set; }
	[JsonPropertyName("secret")] public string SecretHash { get; set; }
	[JsonPropertyName("route")] public string[] Route { get; set; }
	[JsonPropertyName("cookie_with_flag")] public string CookieWithFlag { get; set; }
	[JsonPropertyName("cookie_without_flag")] public string CookieWithoutFlag { get; set; }
}
