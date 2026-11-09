# suntimes

Sunrise, sunset and day length for a place and date — no network, no
dependencies, just the NOAA solar algorithm in the standard library.

It was written for planning days on a South America trip: knowing when
the sun rises over Machu Picchu or sets over the Salar de Uyuni is
worth more than another generic weather widget. Presets cover the
stops of that trip, and any latitude/longitude works too.

## Install

```bash
pip install .
```

Requires Python 3.10+. No dependencies (standard library only).

## Usage

```bash
suntimes 2026-06-21 --place cusco
# cusco  2026-06-21  (lat -13.5319, lon -71.9675, UTC-5)
#   sunrise    06:10
#   solar noon 11:50
#   sunset     17:29
#   day length 11h 20m
```

Compare several stops on the same day:

```bash
suntimes 2026-06-21 --place lima --place uyuni --place sao-paulo
```

Arbitrary coordinates, with a UTC offset for local time:

```bash
suntimes 2026-06-21 --lat 35.6762 --lon 139.6503 --utc-offset 9
```

Add `--utc` to show times in UTC instead of local time. `suntimes places`
lists the built-in presets (Lima, Cusco, Machu Picchu, Uyuni, Iguazú,
São Paulo, Tokyo).

Polar day and night are reported instead of sunrise/sunset:

```bash
suntimes 2026-06-21 --lat 78 --lon 15 --utc-offset 2
#   polar day: the sun does not set
```

Exit status: 0 on success, 2 on invalid input.

## Tests

```bash
PYTHONPATH=src python -m pytest tests/ -q
```

## License

MIT. See [LICENSE](LICENSE).
