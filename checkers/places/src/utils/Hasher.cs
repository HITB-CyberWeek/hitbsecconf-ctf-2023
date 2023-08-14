using System;
using System.Buffers;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;

namespace checker.utils;

public static class Hasher
{
	public static byte[] ComputeSha256(this IEnumerable<string> values)
	{
		using var sha = SHA256.Create();
		var encoder = Encoding.UTF8.GetEncoder();
		var buffer = ArrayPool<byte>.Shared.Rent(8192);
		try
		{
			foreach(var value in values)
			{
				var chars = value.AsSpan();
				do
				{
					encoder.Convert(chars, buffer, false, out var charsUsed, out var bytesUsed, out _);
					sha.TransformBlock(buffer, 0, bytesUsed, null, 0);
					chars = chars.Slice(charsUsed);
				} while(!chars.IsEmpty);
			}

			encoder.Convert(string.Empty, buffer, true, out _, out var bytes, out _);
			sha.TransformBlock(buffer, 0, bytes, null, 0);
			sha.TransformFinalBlock(buffer, 0, 0);

			return sha.Hash;
		}
		finally
		{
			ArrayPool<byte>.Shared.Return(buffer);
		}
	}
}
