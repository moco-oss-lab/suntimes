"""Sunrise / sunset / day-length calculations (NOAA solar algorithm).

Pure standard library. All angles in degrees unless noted.
Times are returned as minutes after 00:00 UTC on the given date.
"""

import math
from datetime import date

__all__ = ["SunTimes", "sun_times", "PLACES"]


def _julian_day(d: date) -> float:
    """Julian day number at 00:00 UTC on the given date."""
    return d.toordinal() + 1721424.5


class SunTimes:
    """Result of :func:`sun_times` for one date and location."""

    def __init__(self, sunrise, solar_noon, sunset):
        self.sunrise = sunrise          # minutes after 00:00 UTC, or None
        self.solar_noon = solar_noon    # minutes after 00:00 UTC
        self.sunset = sunset            # minutes after 00:00 UTC, or None
        self._sun_up = True             # set by sun_times() for polar cases

    @property
    def polar_day(self):
        """True when the sun never sets on this date at this location."""
        return self.sunrise is None and self.sunset is None and self._sun_up

    @property
    def polar_night(self):
        """True when the sun never rises on this date at this location."""
        return self.sunrise is None and self.sunset is None and not self._sun_up

    @property
    def day_length_minutes(self):
        """Minutes between sunrise and sunset, or None for polar day/night."""
        if self.sunrise is None or self.sunset is None:
            return None
        return self.sunset - self.sunrise


def sun_times(d: date, latitude: float, longitude: float) -> SunTimes:
    """Return sunrise, solar noon and sunset (UTC minutes) for a date/place.

    ``latitude`` is degrees north (negative = south), ``longitude`` is
    degrees east (negative = west). Raises ValueError for out-of-range
    coordinates or a non-date input. When the sun never rises or never
    sets (polar day/night), sunrise and sunset are None and the
    ``polar_day`` / ``polar_night`` properties say which one it is.
    """
    if not isinstance(d, date):
        raise ValueError("date must be a datetime.date")
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("latitude must be between -90 and 90")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError("longitude must be between -180 and 180")

    julian_day = _julian_day(d)
    julian_century = (julian_day - 2451545.0) / 36525.0
    t = julian_century

    geom_mean_long_sun = (
        280.46646 + t * (36000.76983 + t * 0.0003032)
    ) % 360.0
    geom_mean_anom_sun = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    eccent_earth_orbit = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)

    m_rad = math.radians(geom_mean_anom_sun)
    sun_eq_of_ctr = (
        math.sin(m_rad) * (1.914602 - t * (0.004817 + 0.000014 * t))
        + math.sin(2 * m_rad) * (0.019993 - 0.000101 * t)
        + math.sin(3 * m_rad) * 0.000289
    )
    sun_true_long = geom_mean_long_sun + sun_eq_of_ctr
    sun_app_long = sun_true_long - 0.00569 - 0.00478 * math.sin(
        math.radians(125.04 - 1934.136 * t)
    )

    mean_obliq_ecliptic = 23.0 + (
        26.0 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60.0
    ) / 60.0
    obliq_corr = mean_obliq_ecliptic + 0.00256 * math.cos(
        math.radians(125.04 - 1934.136 * t)
    )

    sun_declin = math.degrees(
        math.asin(
            math.sin(math.radians(obliq_corr))
            * math.sin(math.radians(sun_app_long))
        )
    )
    var_y = math.tan(math.radians(obliq_corr / 2.0)) ** 2
    eq_of_time = 4.0 * math.degrees(
        var_y * math.sin(2 * math.radians(geom_mean_long_sun))
        - 2.0 * eccent_earth_orbit * math.sin(m_rad)
        + 4.0 * eccent_earth_orbit * var_y * math.sin(m_rad)
        * math.cos(2 * math.radians(geom_mean_long_sun))
        - 0.5 * var_y * var_y * math.sin(4 * math.radians(geom_mean_long_sun))
        - 1.25 * eccent_earth_orbit * eccent_earth_orbit
        * math.sin(2 * m_rad)
    )

    lat_rad = math.radians(latitude)
    declin_rad = math.radians(sun_declin)
    cos_ha = math.cos(math.radians(90.833)) / (
        math.cos(lat_rad) * math.cos(declin_rad)
    ) - math.tan(lat_rad) * math.tan(declin_rad)

    solar_noon = (720.0 - 4.0 * longitude - eq_of_time) % 1440.0

    result = SunTimes(None, solar_noon, None)
    if cos_ha > 1.0:
        # Sun below the horizon all day.
        result._sun_up = False
        return result
    if cos_ha < -1.0:
        # Sun above the horizon all day.
        result._sun_up = True
        return result
    result._sun_up = True
    hour_angle = math.degrees(math.acos(cos_ha))
    result.sunrise = (solar_noon - hour_angle * 4.0) % 1440.0
    result.sunset = (solar_noon + hour_angle * 4.0) % 1440.0
    return result


# Presets for the South America trip (lat, lon, UTC offset in hours).
PLACES = {
    "lima": (-12.0464, -77.0428, -5),
    "cusco": (-13.5319, -71.9675, -5),
    "machu-picchu": (-13.1631, -72.5450, -5),
    "uyuni": (-20.4604, -66.8269, -4),
    "iguazu": (-25.6953, -54.4367, -3),
    "sao-paulo": (-23.5505, -46.6333, -3),
    "tokyo": (35.6762, 139.6503, 9),
}
