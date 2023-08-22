using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using checker.net;
using checker.rnd;
using checker.utils;
using CommunityToolkit.HighPerformance;
using CommunityToolkit.HighPerformance.Buffers;

namespace checker.spaces;

internal class SpacesChecker : IChecker
{
	public Task<string> Info()
		=> Task.FromResult("vulns: 1\npublic_flag_description: Flag ID is space ID and optional room name, flag is inside message text in this space/room\n");

	public Task Check(string host)
		=> Console.Error.WriteLineAsync("empty check");

	public async Task<PutResult> Put(string host, string flagId, string flag, int vuln)
	{
		var baseUri = GetBaseUri(host);

		int slept = 0;
		await RndUtil.RndDelay(MaxOneTimeDelay, ref slept).ConfigureAwait(false);

		var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
		await Console.Error.WriteLineAsync($"random headers '{JsonSerializer.Serialize(new FakeDictionary<string, string>(randomDefaultHeaders))}'").ConfigureAwait(false);
		var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);

		var result = await client.DoRequestAsync(HttpMethod.Get, "/", null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
		if(result.StatusCode != HttpStatusCode.OK)
			throw new CheckerException(result.StatusCode.ToExitCode(), $"get / failed: {result.StatusCode.ToReadableCode()}");

		var wsUri = GetWsUri(host);
		var wsClient = new WsClient<Message, Command>(SerializeMessage, DeserializeMessageAsync<Message>, client.Cookies, MaxMessageSize);
		var wsClient2 = new WsClient<Message, Command>(SerializeMessage, DeserializeMessageAsync<Message>, null, MaxMessageSize);

		wsClient = await DoIt.TryOrDefaultAsync(() => wsClient.ConnectAsync(wsUri)).ConfigureAwait(false);
		if(wsClient == null)
			throw new CheckerException(ExitCode.DOWN, "ws connection failed");

		var avatars = new HashSet<string>(StringComparer.Ordinal);

		var genMsg = await AwaitReceiveMessagesAsync(wsClient, msg => msg.Type == MsgType.Generate && !string.IsNullOrEmpty(msg.Avatar) && avatars.Add(msg.Avatar)).ConfigureAwait(false);
		if(genMsg == null)
			throw new CheckerException(ExitCode.MUMBLE, "failed to await random anonymous profile generation");

		WsResult wsSendResult;
		var messagesCount = RndUtil.GetDouble() <= 0.8 ? RndUtil.GetInt(1, 5) : RndUtil.GetDouble() <= 0.75 ? RndUtil.GetInt(10, 20) : RndUtil.GetInt(20, 30);
		for(int i = 0; i < messagesCount; i++)
		{
			wsSendResult = await wsClient.SendAsync(new Command { Type = MsgType.Generate }).ConfigureAwait(false);
			if(wsSendResult != WsResult.Ok)
				throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

			var wsRecvResult = await wsClient.ReceiveAsync(NetworkOpTimeout).ConfigureAwait(false);
			if(wsRecvResult.Result != WsResult.Ok)
				throw new CheckerException(wsRecvResult.Result.ToExitCode(), $"ws recv failed: {wsRecvResult.Result.ToReadableCode()}");
			if(wsRecvResult.Msg.Type != MsgType.Generate || string.IsNullOrEmpty(wsRecvResult.Msg.Avatar) || !avatars.Add(wsRecvResult.Msg.Avatar))
				throw new CheckerException(ExitCode.MUMBLE, "failed to await random anonymous profile generation");

			await RndUtil.RndDelay(MaxWsOneTimeDelay, ref slept).ConfigureAwait(false);
		}

		wsSendResult = await wsClient.SendAsync(new Command { Type = MsgType.Join }).ConfigureAwait(false);
		if(wsSendResult != WsResult.Ok)
			throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

		var joinMsg = await AwaitReceiveMessagesAsync(wsClient, msg => msg.Type == MsgType.Join).ConfigureAwait(false);
		if(joinMsg == null)
			throw new CheckerException(ExitCode.MUMBLE, "failed to await join msg");

		string author = joinMsg.Author, context = joinMsg.Context, space = context?.Split('/')[0];
		if(string.IsNullOrEmpty(author) || string.IsNullOrEmpty(space))
			throw new CheckerException(ExitCode.MUMBLE, "invalid join msg format");

		wsClient2 = await DoIt.TryOrDefaultAsync(() => wsClient2.ConnectAsync(wsUri)).ConfigureAwait(false);
		if(wsClient2 == null)
			throw new CheckerException(ExitCode.DOWN, "ws connection failed");

		genMsg = await AwaitReceiveMessagesAsync(wsClient2, msg => msg.Type == MsgType.Generate && !string.IsNullOrEmpty(msg.Avatar) && avatars.Add(msg.Avatar)).ConfigureAwait(false);
		if(genMsg == null)
			throw new CheckerException(ExitCode.MUMBLE, "failed to await random anonymous profile generation");

		wsSendResult = await wsClient2.SendAsync(new Command { Type = MsgType.Join, Data = space }).ConfigureAwait(false);
		if(wsSendResult != WsResult.Ok)
			throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

		joinMsg = await AwaitReceiveMessagesAsync(wsClient2, msg => msg.Type == MsgType.Join).ConfigureAwait(false);
		if(joinMsg == null)
			throw new CheckerException(ExitCode.MUMBLE, "failed to await join msg");

		author = joinMsg.Author;
		space = joinMsg.Context?.Split('/')[0];
		if(string.IsNullOrEmpty(author) || string.IsNullOrEmpty(space))
			throw new CheckerException(ExitCode.MUMBLE, "invalid join msg format");

		if(RndUtil.Bool())
		{
			var room = RndText.RandomWord(RndUtil.GetInt(1, 32));
			wsSendResult = await wsClient.SendAsync(new Command { Type = MsgType.Room, Data = room }).ConfigureAwait(false);
			if(wsSendResult != WsResult.Ok)
				throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

			var roomMsg = await AwaitReceiveMessagesAsync(wsClient, msg => msg.Type == MsgType.Room).ConfigureAwait(false);
			if(roomMsg == null)
				throw new CheckerException(ExitCode.MUMBLE, "failed to await room msg");
			roomMsg = await AwaitReceiveMessagesAsync(wsClient2, msg => msg.Type == MsgType.Room).ConfigureAwait(false);
			if(roomMsg == null)
				throw new CheckerException(ExitCode.MUMBLE, "failed to await room msg");

			await RndUtil.RndDelay(MaxWsOneTimeDelay, ref slept).ConfigureAwait(false);

			wsSendResult = await wsClient2.SendAsync(new Command { Type = MsgType.Room, Data = room }).ConfigureAwait(false);
			if(wsSendResult != WsResult.Ok)
				throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

			roomMsg = await AwaitReceiveMessagesAsync(wsClient, msg => msg.Type == MsgType.Room).ConfigureAwait(false);
			if(roomMsg == null)
				throw new CheckerException(ExitCode.MUMBLE, "failed to await room msg");
			roomMsg = await AwaitReceiveMessagesAsync(wsClient2, msg => msg.Type == MsgType.Room).ConfigureAwait(false);
			if(roomMsg == null)
				throw new CheckerException(ExitCode.MUMBLE, "failed to await room msg");

			if(string.IsNullOrEmpty(roomMsg.Context) || roomMsg.Context != $"{space}/{room}")
				throw new CheckerException(ExitCode.MUMBLE, "room msg has invalid context");

			await RndUtil.RndDelay(MaxWsOneTimeDelay, ref slept).ConfigureAwait(false);

			context = roomMsg.Context;
		}

		wsSendResult = await (RndUtil.Bool() ? wsClient : wsClient2).SendAsync(new Command { Type = MsgType.Close }).ConfigureAwait(false);
		if(wsSendResult != WsResult.Ok)
			throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

		var msgs = Enumerable.Range(0, RndUtil.GetInt(1, 4))
			.Select(_ => RndUtil.Bool() ? RndText.RandomWord(RndUtil.GetInt(2, 16)) : RndText.RandomText(RndUtil.GetInt(16, 64)))
			.Prepend(flag)
			.ToHashSet();

		foreach(var cmd in msgs.Select(msg => new Command { Type = MsgType.Msg, Data = msg }).RandomOrder())
		{
			wsSendResult = await (RndUtil.Bool() ? wsClient : wsClient2).SendAsync(cmd).ConfigureAwait(false);
			if(wsSendResult != WsResult.Ok)
				throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

			await RndUtil.RndDelay(MaxWsOneTimeDelay, ref slept).ConfigureAwait(false);
		}

		var received = new HashSet<string>();
		var awaited = await AwaitReceiveMessagesAsync(RndUtil.Bool() ? wsClient : wsClient2, msg => msg.Type == MsgType.Msg && received.Add(msg.Text ?? string.Empty) && msgs.IsSubsetOf(received)).ConfigureAwait(false);
		if(awaited == null)
			throw new CheckerException(ExitCode.MUMBLE, "failed to await all sent msgs");

		bool roomChanged = false;
		if(RndUtil.Bool() && context.Contains('/'))
		{
			var another = RndUtil.Bool() ? string.Empty : RndText.RandomWord(RndUtil.GetInt(1, 32));

			wsSendResult = await wsClient.SendAsync(new Command { Type = MsgType.Room, Data = another }).ConfigureAwait(false);
			if(wsSendResult != WsResult.Ok)
				throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

			var roomMsg = await AwaitReceiveMessagesAsync(wsClient, msg => msg.Type == MsgType.Room).ConfigureAwait(false);
			if(roomMsg == null)
				throw new CheckerException(ExitCode.MUMBLE, "failed to await room msg");

			roomChanged = true;
		}

		var cookie = client.Cookies?.GetAllCookies().FirstOrDefault(c => c.Name == AuthCookieName)?.Value;
		await Console.Error.WriteLineAsync($"cookie '{cookie.ShortenLog(MaxCookieSize)}' with length '{cookie?.Length}'").ConfigureAwait(false);

		if(string.IsNullOrEmpty(cookie) || cookie.Length > MaxCookieSize || !AuthCookieRegex.IsMatch(cookie))
			throw new CheckerException(ExitCode.MUMBLE, "cookie 'auth' not found or too large or contains invalid chars");

		await Console.Error.WriteLineAsync($"total sleep: {slept} msec").ConfigureAwait(false);

		return new PutResult
		{
			Cookie = cookie,
			RoomChanged = roomChanged,

			PublicFlagId = context
		};
	}

	public async Task Get(string host, PutResult put, string flag, int vuln)
	{
		var baseUri = GetBaseUri(host);

		var cookie = $"{AuthCookieName}={put.Cookie}";

		int slept = 0;
		await RndUtil.RndDelay(MaxOneTimeDelay, ref slept).ConfigureAwait(false);

		var randomDefaultHeaders = RndHttp.RndDefaultHeaders(baseUri);
		await Console.Error.WriteLineAsync($"random headers '{JsonSerializer.Serialize(new FakeDictionary<string, string>(randomDefaultHeaders))}'").ConfigureAwait(false);
		var client = new AsyncHttpClient(baseUri, randomDefaultHeaders, cookies: true);

		await Console.Error.WriteLineAsync($"use saved cookie '{cookie}'").ConfigureAwait(false);
		client.Cookies.SetCookies(baseUri, cookie);

		var result = await client.DoRequestAsync(HttpMethod.Get, "/", null, null, NetworkOpTimeout, MaxHttpBodySize).ConfigureAwait(false);
		if(result.StatusCode != HttpStatusCode.OK)
			throw new CheckerException(result.StatusCode.ToExitCode(), $"get / failed: {result.StatusCode.ToReadableCode()}");

		var wsUri = GetWsUri(host);
		var wsClient = new WsClient<Message, Command>(SerializeMessage, DeserializeMessageAsync<Message>, client.Cookies, MaxMessageSize);

		wsClient = await DoIt.TryOrDefaultAsync(() => wsClient.ConnectAsync(wsUri)).ConfigureAwait(false);
		if(wsClient == null)
			throw new CheckerException(ExitCode.DOWN, "ws connection failed");

		var room = put.PublicFlagId.Contains('/') ? put.PublicFlagId.Split('/').Last() : null;

		if(!put.RoomChanged)
		{
			var awaited = await AwaitReceiveMessagesAsync(wsClient, msg => msg.Type == MsgType.Msg && msg.Text != null && msg.Text.Contains(flag)).ConfigureAwait(false);
			if(awaited == null)
				throw new CheckerException(ExitCode.CORRUPT, "flag not found");
		}
		else
		{
			var wsSendResult = await wsClient.SendAsync(new Command { Type = MsgType.Room, Data = room }).ConfigureAwait(false);
			if(wsSendResult != WsResult.Ok)
				throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

			var awaited = await AwaitReceiveMessagesAsync(wsClient, msg => msg.Type == MsgType.Msg && msg.Text != null && msg.Text.Contains(flag)).ConfigureAwait(false);
			if(awaited == null)
				throw new CheckerException(ExitCode.CORRUPT, "flag not found");
		}

		await Console.Error.WriteLineAsync($"total sleep: {slept} msec").ConfigureAwait(false);
	}

	private static async Task<Message> AwaitReceiveMessagesAsync(WsClient<Message, Command> wsClient, Func<Message, bool> condition, int timeout = 10000) => (await wsClient.ReceiveLoopAsync(tuple =>
	{
		if(tuple.Result != WsResult.Ok)
			throw new CheckerException(tuple.Result.ToExitCode(), $"ws recv failed: {tuple.Result.ToReadableCode()}");

		if(tuple.Msg == null)
			return false;

		if(condition(tuple.Msg))
			return true;

		return false;
	}, timeout).ConfigureAwait(false)).Msg;

	private static async Task<T> DeserializeMessageAsync<T>(ReadOnlyMemory<byte> memory)
	{
		var msg = JsonSerializer.Deserialize<T>(memory.Span, JsonOptions);
		await Console.Error.WriteLineAsync($"deserialized '{AvatarRegex.Replace(JsonSerializer.Serialize(msg, JsonOptions), match => "zeroes:" + match.ValueSpan.Count('0'))}'").ConfigureAwait(false);
		return msg;
	}

	private static ReadOnlyMemory<byte> SerializeMessage<T>(T msg, Memory<byte> memory)
	{
		var writer = new MemoryBufferWriter<byte>(memory);
		using var jsonWriter = new Utf8JsonWriter(writer);
		JsonSerializer.Serialize(jsonWriter, msg, JsonOptions);
		return writer.WrittenMemory;
	}

	private const int Port = 443;

	private const int MaxMessageSize = 1024;

	private const int MaxHttpBodySize = 64 * 1024;
	private const int MaxCookieSize = 400;

	private const int MaxOneTimeDelay = 5000;
	private const int MaxWsOneTimeDelay = 200;
	private const int NetworkOpTimeout = 12000;

	private static Uri GetBaseUri(string host) => new($"https://{host}:{Port}/");
	private static Uri GetWsUri(string host) => new($"wss://{host}:{Port}/ws");

	private const string AuthCookieName = "usr";
	private static readonly Regex AuthCookieRegex = new(@"^[a-zA-Z0-9\.!$@:+\*=_-]+$", RegexOptions.Compiled | RegexOptions.CultureInvariant);
	private static readonly Regex AvatarRegex = new(@"\b[A-Z0]{256}\b", RegexOptions.Compiled | RegexOptions.CultureInvariant);

	private static readonly JsonSerializerOptions JsonOptions = new()
	{
		IncludeFields = true,
		DefaultBufferSize = 1024,
		PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
		DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingDefault,
		Converters = { new JsonStringEnumConverter(JsonNamingPolicy.CamelCase) }
	};
}
