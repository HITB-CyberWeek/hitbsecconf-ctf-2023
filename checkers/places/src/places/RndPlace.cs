using System;
using checker.rnd;

namespace checker.places;

public static class RndPlace
{
	public static (double Lat, double Long) Coords()
		=> (Math.Round(RndUtil.Choice(1.0, -1.0) * RndUtil.GetDouble() * 90.0, 6), Math.Round(RndUtil.Choice(1.0, -1.0) * RndUtil.GetDouble() * 180.0, 6));

	public static string RandomPlaceField()
		=> RndUtil.Bool() ? RndText.RandomWord(RndUtil.GetInt(5, 16)) : RndText.RandomText(RndUtil.GetInt(20, 64));

	public static Place Place()
	{
		var (lat, lon) = Coords();
		return new Place
		{
			Lat = lat,
			Long = lon,
			Public = RandomPlaceField(),
			Secret = RandomPlaceField()
		};
	}
}
