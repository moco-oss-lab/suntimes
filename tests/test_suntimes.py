"""Tests for suntimes."""

import os
import subprocess
import sys
from datetime import date

import pytest

from suntimes.core import PLACES, sun_times


def test_equinox_at_equator_is_about_twelve_hours():
    # On the March equinox the day is ~12h everywhere; at the equator the
    # sun rises close to 06:00 UTC and sets close to 18:00 UTC.
    result = sun_times(date(2026, 3, 20), 0.0, 0.0)
    assert result.sunrise is not None and result.sunset is not None
    assert 710 <= result.day_length_minutes <= 740
    assert 350 <= result.sunrise <= 370
    assert 1070 <= result.sunset <= 1100


def test_southern_winter_day_shorter_than_summer():
    winter = sun_times(date(2026, 6, 21), -20.4604, -66.8269)  # Uyuni
    summer = sun_times(date(2026, 12, 21), -20.4604, -66.8269)
    assert winter.day_length_minutes < summer.day_length_minutes - 120


def test_northern_summer_day_longer_than_winter():
    summer = sun_times(date(2026, 6, 21), 35.6762, 139.6503)  # Tokyo
    winter = sun_times(date(2026, 12, 21), 35.6762, 139.6503)
    assert summer.day_length_minutes > winter.day_length_minutes + 240


def test_sunrise_before_noon_before_sunset():
    result = sun_times(date(2026, 6, 21), -13.5319, -71.9675)  # Cusco
    assert result.sunrise < result.solar_noon < result.sunset


def test_polar_day_and_night():
    # 78N: the sun never sets in June and never rises in December.
    june = sun_times(date(2026, 6, 21), 78.0, 15.0)
    assert june.sunrise is None and june.sunset is None
    assert june.polar_day and not june.polar_night
    assert june.day_length_minutes is None
    december = sun_times(date(2026, 12, 21), 78.0, 15.0)
    assert december.sunrise is None and december.sunset is None
    assert december.polar_night and not december.polar_day


def test_invalid_coordinates_rejected():
    with pytest.raises(ValueError):
        sun_times(date(2026, 6, 21), 91.0, 0.0)
    with pytest.raises(ValueError):
        sun_times(date(2026, 6, 21), 0.0, 181.0)


def test_lima_june_sunrise_is_morning_local_time():
    # Lima in June: sunrise around 06:25 local (UTC-5), sunset ~17:50.
    result = sun_times(date(2026, 6, 21), -12.0464, -77.0428)
    sunrise_local = (result.sunrise - 5 * 60) % 1440
    sunset_local = (result.sunset - 5 * 60) % 1440
    assert 360 <= sunrise_local <= 400
    assert 1050 <= sunset_local <= 1090


def test_places_cover_the_trip():
    for name in ("lima", "cusco", "machu-picchu", "uyuni", "iguazu",
                 "sao-paulo"):
        lat, lon, offset = PLACES[name]
        assert -90 <= lat <= 90 and -180 <= lon <= 180
        result = sun_times(date(2026, 6, 21), lat, lon)
        assert result.solar_noon is not None


def _run_cli(*args):
    env = dict(os.environ, PYTHONPATH="src")
    return subprocess.run(
        [sys.executable, "-m", "suntimes.cli", *args],
        capture_output=True, text=True, env=env,
    )


def test_cli_place_output():
    proc = _run_cli("2026-06-21", "--place", "cusco")
    assert proc.returncode == 0
    assert "sunrise" in proc.stdout
    assert "sunset" in proc.stdout
    assert "day length" in proc.stdout


def test_cli_places_lists_presets():
    proc = _run_cli("places")
    assert proc.returncode == 0
    for name in ("lima", "uyuni", "sao-paulo"):
        assert name in proc.stdout


def test_cli_multiple_places():
    proc = _run_cli("2026-06-21", "--place", "lima", "--place", "uyuni")
    assert proc.returncode == 0
    assert "lima" in proc.stdout and "uyuni" in proc.stdout


def test_cli_custom_coordinates():
    proc = _run_cli("2026-06-21", "--lat", "35.6762", "--lon", "139.6503",
                    "--utc-offset", "9")
    assert proc.returncode == 0
    assert "sunrise" in proc.stdout


def test_cli_bad_date_and_place_fail():
    assert _run_cli("2026-13-40", "--place", "lima").returncode == 2
    assert _run_cli("2026-06-21", "--place", "nowhere").returncode == 2
    assert _run_cli("2026-06-21").returncode == 2
    assert _run_cli("2026-06-21", "--lat", "10").returncode == 2
