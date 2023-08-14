using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

namespace checker.utils;

internal static class CollectionUtils
{
	[MethodImpl(MethodImplOptions.AggressiveInlining)]
	public static TValue GetOrDefault<TKey, TValue>(this Dictionary<TKey, TValue> dict, TKey key)
		=> dict.TryGetValue(key, out var value) ? value : default;

	public static void ForEach<T>(this IEnumerable<T> enumerable, Action<T> action)
	{
		foreach(var item in enumerable)
			action(item);
	}
}

// Used for {K:V} JSON serialization
internal class FakeDictionary<TK, TV> : IDictionary<TK, TV>
{
	private readonly IEnumerable<KeyValuePair<TK, TV>> enumerable;

	public FakeDictionary(IEnumerable<KeyValuePair<TK, TV>> enumerable) => this.enumerable = enumerable;

	public IEnumerator<KeyValuePair<TK, TV>> GetEnumerator() => enumerable.GetEnumerator();
	IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();

	public void Add(KeyValuePair<TK, TV> item) => throw new NotImplementedException();
	public void Clear() => throw new NotImplementedException();
	public bool Contains(KeyValuePair<TK, TV> item) => throw new NotImplementedException();
	public void CopyTo(KeyValuePair<TK, TV>[] array, int arrayIndex) => throw new NotImplementedException();
	public bool Remove(KeyValuePair<TK, TV> item) => throw new NotImplementedException();

	public int Count => throw new NotImplementedException();
	public bool IsReadOnly => true;
	public void Add(TK key, TV value) => throw new NotImplementedException();
	public bool ContainsKey(TK key) => throw new NotImplementedException();
	public bool Remove(TK key) => throw new NotImplementedException();
	public bool TryGetValue(TK key, out TV value) => throw new NotImplementedException();

	public TV this[TK key]
	{
		get => throw new NotImplementedException();
		set => throw new NotImplementedException();
	}

	public ICollection<TK> Keys => throw new NotImplementedException();
	public ICollection<TV> Values => throw new NotImplementedException();
}
