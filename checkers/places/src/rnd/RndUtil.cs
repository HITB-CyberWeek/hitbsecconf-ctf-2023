using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

namespace checker.rnd;

internal static class RndUtil
{
	public static bool DebugZeroDelays = false;

	[MethodImpl(MethodImplOptions.AggressiveInlining)]
	public static T Choice<T>(params T[] array) => array[Random.Shared.Next(array.Length)];

	public static T OrDefaultWithProbability<T>(this T item, double probability) => GetDouble() > probability ? item : default;

	[MethodImpl(MethodImplOptions.AggressiveInlining)]
	public static char Choice(string str) => str[Random.Shared.Next(str.Length)];

	[MethodImpl(MethodImplOptions.AggressiveInlining)]
	public static int GetInt(int inclusiveMinValue, int exclusiveMaxValue) => Random.Shared.Next(inclusiveMinValue, exclusiveMaxValue);

	[MethodImpl(MethodImplOptions.AggressiveInlining)]
	public static double GetDouble() => Random.Shared.NextDouble();

	[MethodImpl(MethodImplOptions.AggressiveInlining)]
	public static DateTime GetDateTime() => new(Random.Shared.NextInt64(0L, DateTime.MaxValue.Ticks));

	public static bool Bool() => Random.Shared.Next(2) == 0;

	public static Task RndDelay(int max) => DebugZeroDelays ? Task.CompletedTask : Task.Delay(Random.Shared.Next(max));
	public static Task RndDelay(int max, ref int total)
	{
		if(DebugZeroDelays)
			return Task.CompletedTask;

		var delay = Random.Shared.Next(max);
		total += delay;

		return Task.Delay(delay);
	}

	public static IEnumerable<T> RandomOrder<T>(this IEnumerable<T> enumerable)
		=> enumerable.OrderBy(_ => Random.Shared.Next()).Select(item => item);
}
