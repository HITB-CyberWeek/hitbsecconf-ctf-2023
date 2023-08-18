using System;
using System.Collections.Concurrent;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using checker.net;
using checker.rnd;
using checker.utils;
using CommunityToolkit.HighPerformance.Buffers;

namespace checker.spaces;

internal class SpacesChecker : IChecker
{
	public Task<string> Info()
		=> Task.FromResult("vulns: 1\npublic_flag_description: Flag ID is space ID, flag is inside message text in this space\n");

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

		wsClient = await DoIt.TryOrDefaultAsync(() => wsClient.ConnectAsync(wsUri)).ConfigureAwait(false);
		if(wsClient == null)
			throw new CheckerException(ExitCode.DOWN, "ws connection failed");

		WsResult wsSendResult;
		var messagesCount = RndUtil.GetInt(1, 20);
		for(int i = 0; i < messagesCount; i++)
		{
			wsSendResult = await wsClient.SendAsync(new Command { Type = MsgType.Generate }).ConfigureAwait(false);
			if(wsSendResult != WsResult.Ok)
				throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

			await RndUtil.RndDelay(MaxWsOneTimeDelay, ref slept).ConfigureAwait(false);
		}

		int count = 0;
		var avatars = new ConcurrentDictionary<string, bool>();
		var awaited = await AwaitReceiveMessagesAsync(wsClient, msg => msg.Type == MsgType.Generate && avatars.TryAdd(msg.Avatar ?? string.Empty, true) && Interlocked.Increment(ref count) >= messagesCount).ConfigureAwait(false);

		if(awaited == null)
			throw new CheckerException(ExitCode.MUMBLE, "failed to await profile generation messages with random anonymous profile");

		wsSendResult = await wsClient.SendAsync(new Command { Type = MsgType.Join }).ConfigureAwait(false);
		if(wsSendResult != WsResult.Ok)
			throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

		var joinMsg = await AwaitReceiveMessagesAsync(wsClient, msg => msg.Type == MsgType.Join).ConfigureAwait(false);

		string author = joinMsg.Author, space = joinMsg.Context?.Split('/')[0];
		if(string.IsNullOrEmpty(author) || string.IsNullOrEmpty(space))
			throw new CheckerException(ExitCode.MUMBLE, "invalid join msg format");

		wsSendResult = await wsClient.SendAsync(new Command { Type = MsgType.Close }).ConfigureAwait(false);
		if(wsSendResult != WsResult.Ok)
			throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

		var msgs = Enumerable.Range(0, RndUtil.GetInt(1, 4))
			.Select(_ => RndUtil.Bool() ? RndText.RandomWord(RndUtil.GetInt(2, 16)) : RndText.RandomText(RndUtil.GetInt(16, 128)))
			.Prepend(flag)
			.ToHashSet();

		foreach(var cmd in msgs.Select(msg => new Command { Type = MsgType.Msg, Data = msg }).RandomOrder())
		{
			wsSendResult = await wsClient.SendAsync(cmd).ConfigureAwait(false);
			if(wsSendResult != WsResult.Ok)
				throw new CheckerException(wsSendResult.ToExitCode(), $"ws send failed: {wsSendResult.ToReadableCode()}");

			await RndUtil.RndDelay(MaxWsOneTimeDelay, ref slept).ConfigureAwait(false);
		}

		count = 0;
		awaited = await AwaitReceiveMessagesAsync(wsClient, msg => msg.Author == author && msg.Type == MsgType.Msg && msgs.Contains(msg.Text ?? string.Empty) && Interlocked.Increment(ref count) >= msgs.Count).ConfigureAwait(false);

		if(awaited == null)
			throw new CheckerException(ExitCode.MUMBLE, "failed to await all messages");

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
			Space = space,
			Cookie = Convert.ToBase64String(bytes),

			PublicFlagId = space
		};
	}

	public async Task Get(string host, PutResult put, string flag, int vuln)
	{
		var baseUri = GetBaseUri(host);

		var space = put.Space;
		var cookie = Encoding.UTF8.GetString(Convert.FromBase64String(put.Cookie));

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

		var awaited = await AwaitReceiveMessagesAsync(wsClient, msg => msg.Text?.Contains(flag) ?? false).ConfigureAwait(false);
		if(awaited == null)
			throw new CheckerException(ExitCode.CORRUPT, "flag not found");

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
		await Console.Error.WriteLineAsync($"deserialized '{JsonSerializer.Serialize(msg, JsonOptions)}'").ConfigureAwait(false);
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
	private const int MaxCookieSize = 512;

	private const int MaxOneTimeDelay = 5000;
	private const int MaxWsOneTimeDelay = 200;
	private const int NetworkOpTimeout = 12000;

	private static Uri GetBaseUri(string host) => new($"https://{host}:{Port}/");
	private static Uri GetWsUri(string host) => new($"wss://{host}:{Port}/ws");

	private static readonly JsonSerializerOptions JsonOptions = new()
	{
		IncludeFields = true,
		DefaultBufferSize = 1024,
		PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
		DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingDefault,
		Converters = { new JsonStringEnumConverter(JsonNamingPolicy.CamelCase) }
	};
}
