using System.Buffers;

namespace spaces;

internal static class AvatarGen
{
    private static readonly byte[,] Mask8 =
    {
        { 0, 0, 0, 0 },
        { 0, 1, 1, 1 },
        { 0, 2, 2, 1 },
        { 0, 2, 4, 1 },
        { 0, 1, 1, 3 },
        { 0, 1, 1, 1 },
        { 0, 0, 1, 5 },
        { 0, 0, 0, 0 },
    };

    private static readonly Dictionary<char, string> ColorNames = new()
    {
        {'0', "White"},
        {'A', "Amethyst"},
        {'B', "Blue"},
        {'C', "Caramel"},
        {'D', "Damson"},
        {'E', "Ebony"},
        {'F', "Forest"},
        {'G', "Green"},
        {'H', "Honeydew"},
        {'I', "Iron"},
        {'J', "Jade"},
        {'K', "Khaki"},
        {'L', "Lime"},
        {'M', "Mallow"},
        {'N', "Navy"},
        {'O', "Orpiment"},
        {'P', "Pink"},
        {'Q', "Quagmire"},
        {'R', "Red"},
        {'S', "Sky"},
        {'T', "Turquoise"},
        {'U', "Uranium"},
        {'V', "Violet"},
        {'W', "Wine"},
        {'X', "Xanthin"},
        {'Y', "Yellow"},
        {'Z', "Zinnia"},
    };

    private static readonly byte[,] Mask = Mask8;
    private static readonly int MaskHeight = Mask.GetLength(0);
    private static readonly int MaskWidth = Mask.GetLength(1);

    private static readonly int Size = MaskHeight;
    private static readonly int SizeLog2 = (int)Math.Log2(Size);
    private static readonly int SizeMinusOne = Size - 1;

    private const char Black = 'E';
    private const char White = '0';
    private static readonly char[] Colors = Enumerable.Range(0, 26).Select(c => (char)(c + 'A')).Where(c => c != Black).ToArray();

    public const string SystemName = "System";
    public static readonly string SystemAvatar = new Random(31337).CreateAvatar(out _);

    public static string CreateAvatar(this Random rnd, out string color)
    {
        var buffer = ArrayPool<char>.Shared.Rent(Size * Size);
        try
        {
            rnd.FillAvatar(buffer, out color);
            return new string(buffer);
        }
        finally
        {
            ArrayPool<char>.Shared.Return(buffer);
        }
    }

    private static void FillAvatar(this Random rnd, char[] array, out string baseColor)
    {
        var palette = rnd.GetItems(Colors, 6);
        baseColor = ColorNames[palette[1]];
        palette[0] = White;

        for(int y = 0; y < MaskHeight; y++)
        {
            var flag = false;
            var row = y << SizeLog2;
            for(int x = 0; x < MaskWidth; x++)
            {
                var i = Mask[y, x] switch
                {
                    0 => 0,
                    1 => flag ? 1 : rnd.Next(2),
                    var v and >= 2 => rnd.Next(2) == 0 ? rnd.Next(2) : v
                };

                flag |= i > 0;

                var color = palette[i];

                array[row + x] = color;
                array[row - x + SizeMinusOne] = color;
            }
        }

        for(int y = 0; y < MaskHeight; y++)
        {
            var row = y << SizeLog2;
            for(int x = 0; x < MaskWidth; x++)
            {
                var idx = row + x;
                if(array[idx] != White)
                    continue;

                if(x > 0 && array[idx - 1] is not (White or Black) || x < MaskWidth - 1 && array[idx + 1] is not (White or Black) || y > 0 && array[((y - 1) << SizeLog2) + x] is not (White or Black) || y < MaskHeight - 1 && array[((y + 1) << SizeLog2) + x] is not (White or Black))
                {
                    array[idx] = Black;
                    array[row - x + SizeMinusOne] = Black;
                }
            }
        }
    }
}
