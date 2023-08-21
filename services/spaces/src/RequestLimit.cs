namespace spaces;

internal class RequestLimit
{
    public bool TryIncrement(long rpm, out bool crossed)
    {
        var value = Increment();
        crossed = value == rpm + 1;
        return value <= rpm;
    }

    private long Increment()
    {
        var value = Interlocked.Increment(ref count);
        var last = Interlocked.Read(ref minutes);

        var now = DateTime.UtcNow.Ticks / TicksInMinute;
        if(last != now && Interlocked.CompareExchange(ref minutes, now, last) == last)
            Interlocked.Exchange(ref count, value = 1);

        return value;
    }

    private const long TicksInMinute = 10000L * 1000L * 60L;
    private long minutes;
    private long count;
}
