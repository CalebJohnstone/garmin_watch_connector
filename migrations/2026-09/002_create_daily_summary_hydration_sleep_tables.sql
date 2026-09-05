-- Garmin Connect data export import: daily wellness summary, hydration, sleep.
-- Historical/reviewable record; actual DDL runs from
-- backend/ingest/db.py IngestDatabaseManager.create_tables().

CREATE TABLE IF NOT EXISTS daily_summary (
    id SERIAL PRIMARY KEY,
    calendar_date DATE UNIQUE NOT NULL,
    user_profile_pk BIGINT,
    uuid VARCHAR(64),
    total_steps INTEGER,
    daily_step_goal INTEGER,
    total_distance_meters FLOAT,
    total_kilocalories FLOAT,
    active_kilocalories FLOAT,
    bmr_kilocalories FLOAT,
    resting_heart_rate INTEGER,
    min_heart_rate INTEGER,
    max_heart_rate INTEGER,
    floors_ascended_meters FLOAT,
    floors_descended_meters FLOAT,
    moderate_intensity_minutes INTEGER,
    vigorous_intensity_minutes INTEGER,
    highly_active_seconds INTEGER,
    active_seconds INTEGER,
    wellness_start_time_gmt TIMESTAMP,
    wellness_end_time_gmt TIMESTAMP,
    wellness_start_time_local TIMESTAMP,
    wellness_end_time_local TIMESTAMP,
    avg_waking_respiration_value FLOAT,
    highest_respiration_value FLOAT,
    lowest_respiration_value FLOAT,
    latest_respiration_value FLOAT,
    latest_respiration_time_gmt TIMESTAMP,
    avg_stress_level INTEGER,
    avg_stress_level_intensity INTEGER,
    stress_off_wrist_count INTEGER,
    total_stress_count INTEGER,
    uncategorized_stress_seconds INTEGER,
    total_stress_duration_seconds INTEGER,
    stress_breakdown_json JSONB,
    body_battery_json JSONB,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hydration_logs (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(64) UNIQUE NOT NULL,
    user_profile_pk BIGINT,
    calendar_date DATE,
    timestamp_local TIMESTAMP,
    persisted_timestamp_gmt TIMESTAMP,
    hydration_source VARCHAR(50),
    value_in_ml FLOAT,
    activity_id BIGINT,
    estimated_sweat_loss_in_ml FLOAT,
    duration_seconds FLOAT,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Real sleep detail is largely absent from this export (only the earliest
-- chunk has populated fields; later chunks are `{"retro": false}`
-- placeholders) - table/parser built to be ready when real data exists.
CREATE TABLE IF NOT EXISTS sleep_sessions (
    id SERIAL PRIMARY KEY,
    calendar_date DATE UNIQUE NOT NULL,
    sleep_start_gmt TIMESTAMP,
    sleep_end_gmt TIMESTAMP,
    sleep_window_confirmation_type VARCHAR(50),
    retro BOOLEAN,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
