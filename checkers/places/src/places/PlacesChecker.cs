using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using checker.net;
using checker.rnd;
using checker.utils;

namespace checker.places;

internal class PlacesChecker : IChecker
{
	public Task<string> Info()
		=> Task.FromResult("vulns: 1\npublic_flag_description: Flag ID is space ID, flag is inside message text in this space\n");

	public async Task Check(string host)
	{
		var baseUri = GetBaseUri(host);

		int slept = 0;
		await RndUtil.RndDelay(MaxOneTimeDelay, ref slept).ConfigureAwait(false);

		var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
		await Console.Error.WriteLineAsync($"random headers '{JsonSerializer.Serialize(new FakeDictionary<string, string>(randomDefaultHeaders))}'").ConfigureAwait(false);
		var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: false);

		var result = await client.DoRequestAsync(HttpMethod.Get, "/", null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
		if(result.StatusCode != HttpStatusCode.OK)
			throw new CheckerException(result.StatusCode.ToExitCode(), $"get / failed: {result.StatusCode.ToReadableCode()}");

		var html = result.BodyAsString.TrimStart();
		if(!(html.StartsWith("<!doctype html", StringComparison.OrdinalIgnoreCase) || html.StartsWith("<html", StringComparison.OrdinalIgnoreCase)))
			throw new CheckerException(ExitCode.MUMBLE, "invalid / response: html expected");

		await Console.Error.WriteLineAsync($"total sleep: {slept} msec").ConfigureAwait(false);
	}

	public async Task<PutResult> Put(string host, string flagId, string flag, int vuln)
	{
		var baseUri = GetBaseUri(host);

		int slept = 0;
		await RndUtil.RndDelay(MaxOneTimeDelay, ref slept).ConfigureAwait(false);

		var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
		await Console.Error.WriteLineAsync($"random headers '{JsonSerializer.Serialize(new FakeDictionary<string, string>(randomDefaultHeaders))}'").ConfigureAwait(false);
		var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);

		var (lat, lon) = RndUtil.Bool() ? (0.0, 0.0) : RndPlace.Coords();

		{
			var result = await client.DoRequestAsync(HttpMethod.Get, ApiAuth + $"?lat={lat.ToString(NumberFormatInfo.InvariantInfo)}&long={lon.ToString(NumberFormatInfo.InvariantInfo)}", null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiAuth} failed: {result.StatusCode.ToReadableCode()}");

			var id = result.BodyAsString;
			if(string.IsNullOrEmpty(id) || !PlaceIdRegex.IsMatch(id))
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiAuth} response: expected /[0-9a-fA-F]{{64}}/ place ID");

			await Console.Error.WriteLineAsync($"auth place id '{id}' (lat={lat.ToString(NumberFormatInfo.InvariantInfo)}, long={lon.ToString(NumberFormatInfo.InvariantInfo)})").ConfigureAwait(false);
			await RndUtil.RndDelay(MaxOneTimeDelay, ref slept).ConfigureAwait(false);

			if(RndUtil.Bool())
			{
				result = await client.DoRequestAsync(HttpMethod.Get, string.Format(ApiPlaceById, id), null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
				if(result.StatusCode != HttpStatusCode.OK)
					throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiPlaceById} failed: {result.StatusCode.ToReadableCode()}");

				var place = DoIt.TryOrDefault(() => JsonSerializer.Deserialize<Place>(result.BodyAsString, JsonOptions));
				if(place == null || Math.Abs(place.Lat - lat) > FloatingPointTolerance || Math.Abs(place.Long - lon) > FloatingPointTolerance)
					throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiPlaceById} response: invalid place returned");

				await RndUtil.RndDelay(MaxOneTimeDelay, ref slept).ConfigureAwait(false);
			}
		}

		if(RndUtil.Bool())
		{
			var result = await client.DoRequestAsync(HttpMethod.Get, ApiList, null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiList} failed: {result.StatusCode.ToReadableCode()}");

			var places = DoIt.TryOrDefault(() => result.BodyAsString.Split('\r', '\n').Where(line => line != string.Empty).Select(line => JsonSerializer.Deserialize<Place>(line, JsonOptions)).ToArray());
			if(places == null)
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiList} response: invalid places stream returned");

			await RndUtil.RndDelay(MaxOneTimeDelay, ref slept).ConfigureAwait(false);
		}

		string publicFlagId;

		{
			var place = RndPlace.Place();
			place.Secret = flag;

			var data = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(place));

			var result = await client.DoRequestAsync(HttpMethod.Put, ApiPlace, JsonContentTypeHeaders, data, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"put {ApiPlace} failed: {result.StatusCode.ToReadableCode()}");

			var id = result.BodyAsString;
			if(string.IsNullOrEmpty(id) || !PlaceIdRegex.IsMatch(id))
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiPlace} response: expected /[0-9a-fA-F]{{64}}/ place ID");

			publicFlagId = id;
		}

		var cookie = string.Join("; ", client.Cookies?.GetAllCookies().Select(c => $"{c.Name}={c.Value}") ?? Enumerable.Empty<string>());
		await Console.Error.WriteLineAsync($"cookie '{cookie.ShortenLog(MaxCookieSize)}' with length '{cookie?.Length ?? 0}'").ConfigureAwait(false);

		if(string.IsNullOrEmpty(cookie) || cookie.Length > MaxCookieSize)
			throw new CheckerException(ExitCode.MUMBLE, "too large or invalid cookies");

		var bytes = DoIt.TryOrDefault(() => Encoding.UTF8.GetBytes(cookie));
		if(bytes == null || bytes.Length > MaxCookieSize)
			throw new CheckerException(ExitCode.MUMBLE, "too large or invalid cookies");

		await Console.Error.WriteLineAsync($"total sleep: {slept} msec").ConfigureAwait(false);

		return new PutResult
		{
			Cookie = Convert.ToBase64String(bytes),
			PublicFlagId = publicFlagId
		};
	}

	public async Task Get(string host, PutResult put, string flag, int vuln)
	{
		var baseUri = GetBaseUri(host);

		var flagId = put.PublicFlagId;
		var cookie = Encoding.UTF8.GetString(Convert.FromBase64String(put.Cookie));

		int slept = 0;
		await RndUtil.RndDelay(MaxOneTimeDelay, ref slept).ConfigureAwait(false);

		var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
		await Console.Error.WriteLineAsync($"random headers '{JsonSerializer.Serialize(new FakeDictionary<string, string>(randomDefaultHeaders))}'").ConfigureAwait(false);
		var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);

		await Console.Error.WriteLineAsync($"use saved cookie '{cookie}'").ConfigureAwait(false);
		client.Cookies.SetCookies(baseUri, cookie);

		if(RndUtil.Bool())
		{
			var (lat, lon) = RndUtil.Bool() ? (0.0, 0.0) : RndPlace.Coords();

			var result = await client.DoRequestAsync(HttpMethod.Get, ApiAuth + $"?lat={lat.ToString(NumberFormatInfo.InvariantInfo)}&long={lon.ToString(NumberFormatInfo.InvariantInfo)}", null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiAuth} failed: {result.StatusCode.ToReadableCode()}");

			var id = result.BodyAsString;
			if(string.IsNullOrEmpty(id) || !PlaceIdRegex.IsMatch(id))
				throw new CheckerException(ExitCode.MUMBLE, $"invalid {ApiAuth} response: expected /[0-9a-fA-F]{{64}}/ place ID");

			await Console.Error.WriteLineAsync($"auth place id '{id}' (lat={lat.ToString(NumberFormatInfo.InvariantInfo)}, long={lon.ToString(NumberFormatInfo.InvariantInfo)})").ConfigureAwait(false);
			await RndUtil.RndDelay(MaxOneTimeDelay, ref slept).ConfigureAwait(false);
		}

		if(RndUtil.Bool())
		{
			var result = await client.DoRequestAsync(HttpMethod.Get, string.Format(ApiPlaceById, flagId), null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"get {ApiPlaceById} failed: {result.StatusCode.ToReadableCode()}");

			var place = DoIt.TryOrDefault(() => JsonSerializer.Deserialize<Place>(result.BodyAsString, JsonOptions));
			if(place?.Secret != flag)
				throw new CheckerException(ExitCode.CORRUPT, $"invalid {ApiPlaceById} response: flag not found");
		}
		else
		{
			var data = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new[] { flagId }));

			var result = await client.DoRequestAsync(HttpMethod.Post, ApiRoute, JsonContentTypeHeaders, data, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
			if(result.StatusCode != HttpStatusCode.OK)
				throw new CheckerException(result.StatusCode.ToExitCode(), $"post {ApiRoute} failed: {result.StatusCode.ToReadableCode()}");

			var places = DoIt.TryOrDefault(() => result.BodyAsString.Split('\r', '\n').Where(line => line != string.Empty).Select(line => JsonSerializer.Deserialize<Place>(line, JsonOptions)).ToArray());
			if(places == null || !places.Any(place => place.Secret.Contains(flag)))
				throw new CheckerException(ExitCode.CORRUPT, $"invalid {ApiRoute} response: invalid places stream returned");
		}

		await Console.Error.WriteLineAsync($"total sleep: {slept} msec").ConfigureAwait(false);
	}

	private const int Port = 8080;

	private const int MaxHttpBodySize = 16 * 1024;
	private const int MaxCookieSize = 256;

	private const int MaxOneTimeDelay = 5000;
	private const int NetworkOpTimeout = 12000;

	private const double FloatingPointTolerance = 0.000001;

	private static Uri GetBaseUri(string host) => new($"http://{host}:{Port}/");

	private const string ApiAuth = "/api/auth";
	private const string ApiList = "/api/list";
	private const string ApiPlace = "/api/place";
	private const string ApiPlaceById = "/api/place/{0}";
	private const string ApiRoute = "/api/route";

	private static readonly Regex PlaceIdRegex = new("^[0-9a-fA-F]{64}$", RegexOptions.Compiled | RegexOptions.CultureInvariant);
	private static readonly Dictionary<string, string> JsonContentTypeHeaders = new() { { "Content-Type", "application/json" } };

	private static readonly JsonSerializerOptions JsonOptions = new()
	{
		IncludeFields = true,
		DefaultBufferSize = 1024,
		PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
		DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingDefault
	};
}
