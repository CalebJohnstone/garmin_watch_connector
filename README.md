# garmin_watch_connector
Sync my Garmin Forerunner 255 Music data to perform data analytics and visualization

## Features

### Step Count Visualization

**Usage:**
```bash
python visualize_steps.py
```

This will:
- Fetch your step count data from Garmin Connect for the last 30 days
- Create a bar chart with a bar for each day
- Export the visualization as a PDF file (`step_count_chart.pdf`)
- Display statistics including average, maximum, and minimum steps

**Requirements:**
- Garmin Connect credentials configured in `.env` file
- See configuration section below

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your Garmin Connect credentials in a `.env` file:
```
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password
```

3. (Optional) Configure database settings for activity sync:
```
DB_HOST=localhost
DB_NAME=garmin_data
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_PORT=5432
```

### Data Export Import

Import a full Garmin Connect data export (the "Export Your Data" download,
extracted to a folder) into Postgres — activities, daily wellness, sleep,
training metrics, personal records, and gear. See
[backend/ingest/README.md](backend/ingest/README.md) for setup and usage.

```bash
python -m backend.ingest.cli --export-dir /path/to/garmin_export --dry-run
```

## Scripts

- `main.py` - Sync running activities to PostgreSQL database
- `visualize_steps.py` - Generate step count visualization for the last month
- `backend/ingest/cli.py` - Import a Garmin Connect data export into PostgreSQL (see above)
