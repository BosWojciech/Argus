# Architecture

```
src/argus/
  identifiers.py  checksum rules: make_* generators + is_valid_* validators
  data.py         weighted draws of names, addresses, bank branches (SQLite or fallback); VIN/plate tables
  fallback.py     small built-in lists used when the database is missing
  records.py      one builder per tab -> ordered dict {label: value}; age/date parsing
  app.py          CustomTkinter window (App) and GeneratorTab
  __main__.py     `python -m argus`
db/
  argus.db        built by `make data` from open data (see data.md)
Makefile          install / run / data / test / clean, with uv, Python and Tk checks
make.cmd          the same targets for Windows without GNU make
scripts/
  build_data.py   downloads open data and writes db/argus.db
tests/
  conftest.py          runs every test against the database and against the fallback lists
  test_identifiers.py  validators on known values, generators over many seeded draws
  test_records.py      labels per tab, options, age ranges and age/date input
  test_app.py          window smoke test (skipped without a display)
  test_data.py         data layer: formats, determinism, frequency weighting
  test_build_data.py   build helpers + full offline build from tiny sample files
```

## Flow

1. `App` creates one `GeneratorTab` per tab with a `make_record` callable.
   Tabs with options get a `build_options` function that fills a frame and
   binds widgets to `StringVar`s held on `App`.
2. `GeneratorTab.generate()` calls `make_record()`. A `ValueError` (bad age
   input) goes to the status line and the old record stays.
3. Record builders in `records.py` combine identifiers (`identifiers.py`) with
   names, addresses and bank branches drawn by `data.py`.
4. Results are rendered as label + button rows; a button click calls
   `App.copy()`, which uses Tk's clipboard.

## Design choices

- The app makes no network requests and stores nothing, only `make data` downloads.
- Real-world data is prepared once into SQLite instead of fetched at runtime:
  fast startup, works offline, repeatable with a seed.
- The app keeps working without the database (fallback lists), so a failed
  download never blocks it.
- Every function that draws randomness takes `rng` (default: the `random`
  module) so tests can use a seeded `random.Random`.
- `today` is injectable in `records` so age logic is testable on a fixed date.
- Records are plain dicts, label order is the display order.
- The Makefile prefers uv's managed Python builds (`UV_PYTHON_PREFERENCE=managed`)
  and checks for Tk, because some Python builds (e.g. Homebrew's) lack it.
