using System;
using System.Buffers;
using System.Net;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace checker.net;

public class WsClient<TInMsg, TOutMsg> where TInMsg : class
{
	public WsClient(Serialize serialize, DeserializeAsync deserialize, CookieContainer cookies = null, int maxMsgSize = 8192)
	{
		this.serialize = serialize;
		this.deserialize = deserialize;
		this.maxMsgSize = maxMsgSize;
		ws = new ClientWebSocket { Options =
		{
			KeepAliveInterval = TimeSpan.FromSeconds(30),
			Cookies = cookies
		}};
	}

	public delegate Task<TInMsg> DeserializeAsync(ReadOnlyMemory<byte> buffer);
	public delegate ReadOnlyMemory<byte> Serialize(TOutMsg msg, Memory<byte> buffer);

	public async Task<WsClient<TInMsg, TOutMsg>> ConnectAsync(Uri uri, int timeout = 10000)
	{
		using var cts = new CancellationTokenSource(timeout);
		await ws.ConnectAsync(uri, cts.Token).ConfigureAwait(false);
		return this;
	}

	public async Task<WsResult> SendAsync(TOutMsg msg, int timeout = 10000)
	{
		using var cts = new CancellationTokenSource(timeout);
		using var buffer = MemoryPool<byte>.Shared.Rent(maxMsgSize);
		var serialized = serialize(msg, buffer.Memory);
		try
		{
			await ws.SendAsync(serialized, WebSocketMessageType.Text, true, cts.Token).ConfigureAwait(false);
			await Console.Error.WriteLineAsync($"ws sent {WebSocketMessageType.Text} msg, {serialized.Length} bytes: {Encoding.UTF8.GetString(serialized.Span)}").ConfigureAwait(false);
			return WsResult.Ok;
		}
		catch(WebSocketException e)
		{
			await Console.Error.WriteLineAsync($"ws send failed with status {e.WebSocketErrorCode}").ConfigureAwait(false);
			return e.WebSocketErrorCode == WebSocketError.ConnectionClosedPrematurely ? WsResult.ConnectionClosed : WsResult.UnknownError;
		}
		catch(Exception e) when (e is OperationCanceledException) { return WsResult.TimedOut; }
		catch(Exception e)
		{
			await Console.Error.WriteLineAsync($"ws send failed -> {e}").ConfigureAwait(false);
			return WsResult.UnknownError;
		}
	}

	public async Task<(WsResult Result, TInMsg Msg)> ReceiveLoopAsync(Func<(WsResult Result, TInMsg Msg), bool> process, int timeout)
	{
		var end = DateTime.UtcNow.AddMilliseconds(timeout);
		while(true)
		{
			var left = end - DateTime.UtcNow;
			if(left < TimeSpan.Zero)
				return (WsResult.TimedOut, null);
			var result = await ReceiveAsync((int)left.TotalMilliseconds).ConfigureAwait(false);
			if(result.Result == WsResult.TimedOut || process(result))
				return result;
		}
	}

	public async Task<(WsResult Result, TInMsg Msg)> ReceiveAsync(int timeout = 10000)
	{
		using var cts = new CancellationTokenSource(timeout);
		using var buffer = MemoryPool<byte>.Shared.Rent(maxMsgSize);
		try
		{
			var result = await ws.ReceiveAsync(buffer.Memory, cts.Token).ConfigureAwait(false);
			if(result.MessageType == WebSocketMessageType.Close)
				return (WsResult.ConnectionClosed, null);
			await Console.Error.WriteLineAsync($"ws recv {result.MessageType} msg, eom flag '{result.EndOfMessage}', {result.Count} bytes").ConfigureAwait(false);
			try
			{
				var msg = await deserialize(buffer.Memory.Slice(0, result.Count));
				return msg == null ? (WsResult.InvalidMessage, null) : (WsResult.Ok, msg);
			}
			catch { return (WsResult.InvalidMessage, null); }
		}
		catch(WebSocketException e)
		{
			await Console.Error.WriteLineAsync($"ws receive failed with status {e.WebSocketErrorCode}").ConfigureAwait(false);
			return (e.WebSocketErrorCode == WebSocketError.ConnectionClosedPrematurely ? WsResult.ConnectionClosed : WsResult.UnknownError, default);
		}
		catch(Exception e) when (e is OperationCanceledException) { return (WsResult.TimedOut, null); }
		catch(Exception e)
		{
			await Console.Error.WriteLineAsync($"ws receive failed -> {e}").ConfigureAwait(false);
			return (WsResult.UnknownError, null);
		}
	}

	private readonly ClientWebSocket ws;
	private readonly Serialize serialize;
	private readonly DeserializeAsync deserialize;
	private readonly int maxMsgSize;
}

public enum WsResult
{
	Ok = 1,
	TimedOut = 2,
	ConnectionClosed = 3,
	InvalidMessage = 4,
	UnknownError = 5
}

public static class WsResultHelper
{
	public static ExitCode ToExitCode(this WsResult result)
	{
		if(result == WsResult.Ok)
			return ExitCode.OK;
		if(result == WsResult.ConnectionClosed || result == WsResult.TimedOut)
			return ExitCode.DOWN;
		return ExitCode.MUMBLE;
	}

	public static string ToReadableCode(this WsResult result)
		=> result.ToString("G");
}
