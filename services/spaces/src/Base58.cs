namespace spaces;

internal static class Base58
{
    static Base58()
    {
        Array.Fill(Values, ulong.MaxValue);
        foreach(var (idx, value) in Digits.Select((digit, idx) => ((int)digit, (ulong)idx)))
            Values[idx] = value;
    }

    public static string ToBase58(this ulong value)
    {
        Span<char> buffer = stackalloc char[11];

        int index = 0;
        while(value > 0)
        {
            buffer[index++] = Digits[(int)(value % Base)];
            value /= Base;
        }

        return buffer.Slice(0, index).ToString();
    }

    public static bool TryDecodeUInt64(string value, out ulong result)
    {
        result = 0UL;
        if(string.IsNullOrEmpty(value))
            return false;

        ulong tmp = 0UL, mul = 1UL;
        for(int i = 0; i < value.Length; i++)
        {
            var c = value[i];

            var digit = c >= Values.Length ? ulong.MaxValue : Values[c];
            if(digit == ulong.MaxValue)
                return false;

            tmp += digit * mul;
            mul *= Base;
        }

        result = tmp;
        return true;
    }

    public static bool IsBase58Alphabet(this string value)
        => value.All(Alphabet.Contains);

    private static readonly char[] Digits = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".ToCharArray();
    private static readonly HashSet<char> Alphabet = new(Digits);
    private static readonly ulong[] Values = new ulong[Digits.Max() + 1];
    private static readonly ulong Base = (ulong)Digits.Length;
}
