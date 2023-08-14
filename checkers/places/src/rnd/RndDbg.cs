using System;
using System.Linq;

namespace checker.rnd;

internal static class RndDbg
{
	public static int RandomVuln(int[] vulns)
	{
		var rnd = Random.Shared.Next(vulns.Sum());
		for(int i = 0; i < vulns.Length; i++)
		{
			if((rnd -= vulns[i]) < 0)
				return i + 1;
		}
		throw new Exception();
	}

	public static string RandomFlag()
	{
		var flag = new char[FlagSuffixLength];
		for(int i = 0; i < FlagSuffixLength; i++)
			flag[i] = Alphabet[Random.Shared.Next(Alphabet.Length)];
		return $"TEAM{RndUtil.GetInt(1, 1000):000}_{new string(flag)}";
	}

	private const int FlagSuffixLength = 32;
	private static readonly char[] Alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789".ToCharArray();
}
