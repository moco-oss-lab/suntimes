"""Command line interface for suntimes.

Usage:
    suntimes 2026-06-21 --place cusco
    suntimes 2026-06-21 --lat -13.5319 --lon -71.9675 --utc-offset -5
    suntimes 2026-06-21 --place uyuni --place lima
    suntimes places
"""

import argparse
import sys
from datetime import date

from .core import PLACES, sun_times


def _fmt(minutes, utc_offset):
    """Format UTC minutes as HH:MM local time for the given UTC offset."""
    local = (minutes + utc_offset * 60.0) % 1440.0
    hours = int(local // 60)
    mins = int(round(local % 60))
    if mins == 60:
        hours = (hours + 1) % 24
        mins = 0
    return f"{hours:02d}:{mins:02d}"


def _fmt_duration(minutes):
    hours = int(minutes // 60)
    mins = int(round(minutes % 60))
    if mins == 60:
        hours += 1
        mins = 0
    return f"{hours}h {mins:02d}m"


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="suntimes",
        description="Sunrise, sunset and day length for a place and date.",
    )
    parser.add_argument("date", nargs="?", help="date as YYYY-MM-DD")
    parser.add_argument("--place", action="append", dest="places",
                        help="preset place (repeatable); see `suntimes places`")
    parser.add_argument("--lat", type=float, help="latitude in degrees")
    parser.add_argument("--lon", type=float, help="longitude in degrees")
    parser.add_argument("--utc-offset", type=float, default=0.0,
                        help="hours to add to UTC for local time (default 0)")
    parser.add_argument("--utc", action="store_true",
                        help="show times in UTC instead of local time")
    return parser.parse_args(argv)


def _show(d, name, lat, lon, utc_offset, show_utc):
    result = sun_times(d, lat, lon)
    offset = 0.0 if show_utc else utc_offset
    label = "UTC" if show_utc else f"UTC{utc_offset:+.0f}"
    print(f"{name}  {d.isoformat()}  (lat {lat}, lon {lon}, {label})")
    if result.polar_day:
        print("  polar day: the sun does not set")
    elif result.polar_night:
        print("  polar night: the sun does not rise")
    else:
        print(f"  sunrise    {_fmt(result.sunrise, offset)}")
        print(f"  solar noon {_fmt(result.solar_noon, offset)}")
        print(f"  sunset     {_fmt(result.sunset, offset)}")
        print(f"  day length {_fmt_duration(result.day_length_minutes)}")


def main(argv=None):
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    if args.date == "places":
        for name in sorted(PLACES):
            lat, lon, offset = PLACES[name]
            print(f"{name:<12} lat {lat:>8}  lon {lon:>9}  UTC{offset:+.0f}")
        return 0

    if args.date is None:
        print("error: a date (YYYY-MM-DD) or 'places' is required",
              file=sys.stderr)
        return 2
    try:
        d = date.fromisoformat(args.date)
    except ValueError:
        print(f"error: invalid date {args.date!r} (use YYYY-MM-DD)",
              file=sys.stderr)
        return 2

    targets = []
    if args.places:
        for name in args.places:
            key = name.lower()
            if key not in PLACES:
                print(f"error: unknown place {name!r} "
                      f"(see `suntimes places`)", file=sys.stderr)
                return 2
            lat, lon, offset = PLACES[key]
            targets.append((name, lat, lon, offset))
    if args.lat is not None or args.lon is not None:
        if args.lat is None or args.lon is None:
            print("error: --lat and --lon must be given together",
                  file=sys.stderr)
            return 2
        targets.append(("custom", args.lat, args.lon, args.utc_offset))
    if not targets:
        print("error: give --place and/or --lat/--lon", file=sys.stderr)
        return 2

    try:
        for name, lat, lon, offset in targets:
            _show(d, name, lat, lon, offset, args.utc)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
