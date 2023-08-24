using System.Numerics;

public static class Base58
{
    static Base58()
    {
        Array.Fill(Values, ulong.MaxValue);
        foreach(var (idx, value) in Digits.Select((digit, idx) => ((int)digit, (ulong)idx)))
            Values[idx] = value;
    }

    public static string ToBase58(this BigInteger value)
    {
        int index = 0;
        Span<char> buffer = stackalloc char[1024];
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

    public static bool TryDecodeBigInt(string value, out BigInteger result)
    {
        result = 0UL;
        if(string.IsNullOrEmpty(value))
            return false;

        BigInteger tmp = 0UL, mul = 1UL;
        for(int i = 0; i < value.Length; i++)
        {
            var c = value[i];

            var digit = c >= Values.Length ? ulong.MaxValue : Values[c];
            if(digit == ulong.MaxValue)
                return false;

            tmp += new BigInteger(digit) * mul;
            mul *= new BigInteger(Base);
        }

        result = tmp;
        return true;
    }

    private static readonly char[] Digits = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".ToCharArray();
    private static readonly ulong[] Values = new ulong[Digits.Max() + 1];
    private static readonly ulong Base = (ulong)Digits.Length;
}
