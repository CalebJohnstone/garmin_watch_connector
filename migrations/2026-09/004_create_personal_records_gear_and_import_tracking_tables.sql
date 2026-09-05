-- Garmin Connect data export import: personal records, gear, and the
-- file-level import tracking table that makes re-running the pipeline
-- against a refreshed export cheap and safe. Historical/reviewable record;
-- actual DDL runs from backend/ingest/db.py IngestDatabaseManager.create_tables().

CREATE TABLE IF NOT EXISTS personal_records (
    id SERIAL PRIMARY KEY,
    personal_record_id BIGINT UNIQUE NOT NULL,
    activity_id BIGINT,
    value FLOAT,
    pr_start_time_gmt TIMESTAMP,
    personal_record_type VARCHAR(100),
    created_date DATE,
    current BOOLEAN,
    confirmed BOOLEAN,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gear (
    id SERIAL PRIMARY KEY,
    gear_pk BIGINT UNIQUE NOT NULL,
    uuid VARCHAR(64),
    user_profile_pk BIGINT,
    gear_type_name VARCHAR(100),
    gear_status_name VARCHAR(50),
    custom_make_model VARCHAR(255),
    date_begin DATE,
    maximum_meters FLOAT,
    gear_version INTEGER,
    create_date DATE,
    update_date DATE,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gear_activity_links (
    id SERIAL PRIMARY KEY,
    gear_pk BIGINT NOT NULL REFERENCES gear(gear_pk) ON DELETE CASCADE,
    activity_id BIGINT NOT NULL,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(gear_pk, activity_id)
);

-- File-level idempotency tracking: lets the CLI skip files that haven't
-- changed since the last run instead of re-parsing the whole export every time.
CREATE TABLE IF NOT EXISTS import_files (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    file_path TEXT UNIQUE NOT NULL,
    file_mtime DOUBLE PRECISION,
    file_size BIGINT,
    file_sha256 VARCHAR(64),
    row_count INTEGER,
    status VARCHAR(20),
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
