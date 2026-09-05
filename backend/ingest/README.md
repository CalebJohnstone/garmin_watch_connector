# Garmin Connect data export import

Parses a Garmin Connect account data export (the "Export Your Data" ZIP from
Garmin Connect, extracted to a folder) and loads it into Postgres. This is
separate from the live sync (`GarminConnectSync.py` / `visualize_steps.py`),
which pulls recent activities directly from the Garmin Connect API — this
pipeline is for importing your full historical export instead.

## Requirements

- The export already extracted to a folder (it should contain a `DI_CONNECT/`
  subfolder).
- Postgres reachable via the same `.env` / `config.DB_CONFIG` used by the rest
  of the app (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`).
- No extra Python packages beyond what's already in `requirements.txt`
  (`psycopg[binary]`).

## Usage

Run all commands from the repo root.

**1. Dry run first** — parses everything and prints per-category counts with
zero DB writes (no DB connection needed at all, so this works even without
Postgres running):

```bash
python -m backend.ingest.cli --export-dir /path/to/garmin_export --dry-run
```

**2. Run for real** — creates the tables (if needed) and upserts everything:

```bash
python -m backend.ingest.cli --export-dir /path/to/garmin_export
```

Safe to re-run any time (e.g. after downloading a refreshed export): files
that haven't changed since the last run are skipped, and every row upserts on
its natural key, so re-running never creates duplicates.

### Options

| Flag | Purpose |
| --- | --- |
| `--export-dir PATH` | Required. Root of the extracted export (the folder containing `DI_CONNECT/`). |
| `--categories a,b,c` | Only import specific categories (default: all). See list below. |
| `--dry-run` | Parse and count only; makes no DB writes and opens no DB connection. |
| `--force` | Re-parse and re-upsert every file, even ones the pipeline has already imported (bypasses the file-level skip; the row-level upsert still makes this safe). |
| `--limit N` | Process at most N files per category — useful for quickly testing a change. |

### Categories

`activities`, `daily_summary`, `hydration`, `sleep`, `biometrics`,
`training_metrics`, `personal_records`, `gear`.

Out of scope (not imported by this pipeline): golf data, device backup
files, raw `.fit` files, and account-level data (customer record, orders,
support form submissions, login history, profile images).

### Example: re-import just activities after a parser fix

```bash
python -m backend.ingest.cli --export-dir /path/to/garmin_export --categories activities --force
```

## What it creates

Tables are created automatically on first run (`CREATE TABLE IF NOT EXISTS`),
matching the reviewable schema history in `migrations/2026-09/*.sql`:

- **Activities**: `activities`, `activity_types`, `activity_hr_zones`,
  `activity_power_zones`, `activity_splits`, `activity_split_summaries`,
  `activity_exercise_sets`, `activity_dive_info` — kept separate from the
  existing `runs`/`gps_points` tables (different units, much larger column set).
- **Daily wellness**: `daily_summary`, `hydration_logs`, `sleep_sessions`.
- **Bio-metrics / training load**: `heart_rate_zones`, `power_zones`,
  `user_bio_metric_profile_data`, `bio_metrics_latest`,
  `user_bio_metrics_history`, `fitness_age_data`, `activity_vo2_max`,
  `acute_training_load`, `max_met_data`, `race_predictions`,
  `training_status_history`.
- **Records / gear**: `personal_records`, `gear`, `gear_activity_links`.
- **Import tracking**: `import_files` — powers the "skip unchanged files"
  behavior described above.

## Known data gap

Sleep detail is mostly absent from Garmin's export: only the very earliest
export chunk has real sleep records, and every later chunk is a placeholder.
The CLI's summary reports these separately as "placeholders" rather than
importing them as empty rows — this is a limitation of the export itself,
not a pipeline bug.

## Logs

Runs log to `ingest.log` (repo root) and stdout.
