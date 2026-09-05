# activity_graph

A C++ command-line tool that renders line graphs and bar charts of the
`activities` table directly in the terminal — a one-shot "print a chart and
exit" tool (like `htop`'s snapshot mode), not an interactive dashboard.

Separate subsystem from `backend/`/`frontend/`, with its own CMake build
root. Reads from the same Postgres database as the rest of the app, via the
same root `.env` file.

## Setup

```bash
brew install libpqxx ftxui cli11
```

## Build

```bash
cmake -S cli/activity_graph -B cli/activity_graph/build \
  -DCMAKE_PREFIX_PATH="$(brew --prefix libpqxx);$(brew --prefix ftxui);$(brew --prefix cli11);$(brew --prefix libpq)"
cmake --build cli/activity_graph/build -j
```

The explicit `CMAKE_PREFIX_PATH` is needed because Homebrew's `libpqxx`,
`ftxui`, `cli11`, and `libpq` are keg-only / not symlinked into a default
CMake search path.

## Run

```bash
./cli/activity_graph/build/activity_graph --list-metrics
./cli/activity_graph/build/activity_graph --type line --metric distance --activity-type running --limit 50
./cli/activity_graph/build/activity_graph --type bar --metric calories --group-by type --agg sum
./cli/activity_graph/build/activity_graph --type bar --metric distance --group-by month --agg sum --since 2024-01-01
```

Run from the repo root (or anywhere under it) so the `.env` file is found by
walking up from the current directory; or export `DB_HOST`/`DB_NAME`/
`DB_USER`/`DB_PASSWORD`/`DB_PORT` directly to override.

### Flags

| Flag | Purpose |
| --- | --- |
| `-t, --type <line\|bar>` | Chart type. Required unless `--list-metrics`. |
| `-m, --metric <key>` | Metric to plot — see `--list-metrics` for the full list. |
| `--activity-type <type_key>` | Filter to one activity type (e.g. `running`). Omit for all types. |
| `--since <YYYY-MM-DD>` | Only include activities on/after this date. |
| `--limit <N>` | Max number of most-recent activities to plot (line chart only, default 200). |
| `--group-by <type\|month>` | Bar chart grouping (default `type`). |
| `--agg <count\|sum\|avg>` | Bar chart aggregation (default `count`). |
| `--width <N>` / `--height <N>` | Chart size in terminal columns/rows (default: detected terminal size). |
| `--list-metrics` | Print available `--metric` values and exit. |

### Metrics

`distance`, `duration`, `speed`, `heart-rate`, `calories`, `steps`,
`elevation-gain`, `vo2max` — a curated subset of the `activities` table's
~85 columns (see `src/metrics.hpp` to add more).

## Notes

- Rows with a NULL value for the selected metric are excluded (e.g. most
  non-running activity types have no `avg_run_cadence`), rather than being
  coerced to 0.
- The bar chart is a horizontal gauge-bar chart (one row per group) rather
  than vertical bars, since category labels (e.g. `strength_training`) don't
  fit well under a narrow vertical bar in a terminal.
- Output is plain ANSI-colored text; piping to a file captures the same
  escape codes a real terminal would render.
