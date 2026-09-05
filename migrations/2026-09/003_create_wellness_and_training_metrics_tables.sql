-- Garmin Connect data export import: bio-metrics/wellness config, and the
-- DI-Connect-Metrics training metric feeds (VO2max, training load, max MET,
-- race predictions, training status). Historical/reviewable record; actual
-- DDL runs from backend/ingest/db.py IngestDatabaseManager.create_tables().

CREATE TABLE IF NOT EXISTS heart_rate_zones (
    id SERIAL PRIMARY KEY,
    sport VARCHAR(50) NOT NULL,
    training_method VARCHAR(50) NOT NULL,
    resting_heart_rate_used INTEGER,
    lactate_threshold_heart_rate_used INTEGER,
    zone1_floor INTEGER,
    zone2_floor INTEGER,
    zone3_floor INTEGER,
    zone4_floor INTEGER,
    zone5_floor INTEGER,
    max_heart_rate_used INTEGER,
    resting_hr_auto_update_used BOOLEAN,
    change_state VARCHAR(50),
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sport, training_method)
);

CREATE TABLE IF NOT EXISTS power_zones (
    id SERIAL PRIMARY KEY,
    sport VARCHAR(50) UNIQUE NOT NULL,
    functional_threshold_power FLOAT,
    zone1_floor FLOAT,
    zone2_floor FLOAT,
    zone3_floor FLOAT,
    zone4_floor FLOAT,
    zone5_floor FLOAT,
    zone6_floor FLOAT,
    zone7_floor FLOAT,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Single-row current profile snapshots, refreshed in place on every run.
CREATE TABLE IF NOT EXISTS user_bio_metric_profile_data (
    id INTEGER PRIMARY KEY DEFAULT 1,
    height FLOAT,
    weight FLOAT,
    activity_class INTEGER,
    vo2_max FLOAT,
    lactate_threshold_heart_rate FLOAT,
    functional_threshold_power FLOAT,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (id = 1)
);

CREATE TABLE IF NOT EXISTS bio_metrics_latest (
    id INTEGER PRIMARY KEY DEFAULT 1,
    lactate_threshold_speed FLOAT,
    lactate_threshold_heart_rate FLOAT,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (id = 1)
);

-- Append-only/immutable event log of bio-metric changes (weight, height,
-- VO2max, lactate threshold, etc.) - `version` (epoch-ms) is Garmin's own
-- natural id for each event. All fields nullable since only the fields that
-- actually changed are populated on a given event.
CREATE TABLE IF NOT EXISTS user_bio_metrics_history (
    id SERIAL PRIMARY KEY,
    version BIGINT UNIQUE NOT NULL,
    metadata_calendar_date TIMESTAMP,
    metadata_sequence BIGINT,
    height FLOAT,
    weight FLOAT,
    activity_class INTEGER,
    sport_id INTEGER,
    vo2_max_running FLOAT,
    vo2_max_cycling FLOAT,
    lactate_threshold_speed FLOAT,
    lactate_threshold_heart_rate INTEGER,
    lactate_threshold_rowing_pace FLOAT,
    lactate_threshold_rowing_heart_rate INTEGER,
    functional_threshold_power INTEGER,
    ftp_auto_detected BOOLEAN,
    threshold_heart_rate_auto_detected BOOLEAN,
    firstbeat_running_lt_timestamp BIGINT,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fitness_age_data (
    id SERIAL PRIMARY KEY,
    as_of_date_gmt DATE UNIQUE NOT NULL,
    create_timestamp TIMESTAMP,
    chronological_age INTEGER,
    bmi FLOAT,
    rhr INTEGER,
    total_vigorous_days INTEGER,
    total_vigorous_ims INTEGER,
    num_of_weeks_for_im INTEGER,
    healthy_bmi FLOAT,
    healthy_fat FLOAT,
    vo2_max_for_healthy_bmi_fat FLOAT,
    vo2_max_for_healthy_rhr FLOAT,
    vo2_max_for_healthy_active FLOAT,
    biometric_vo2_max FLOAT,
    current_bio_age FLOAT,
    healthy_all_bio_age FLOAT,
    healthy_bmi_fat_bio_age FLOAT,
    healthy_rhr_bio_age FLOAT,
    healthy_active_bio_age FLOAT,
    weight_data_last_entry_date DATE,
    rhr_last_entry_date DATE,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_vo2_max (
    id SERIAL PRIMARY KEY,
    activity_id BIGINT UNIQUE NOT NULL,
    user_profile_pk BIGINT,
    calendar_date DATE,
    device_id BIGINT,
    timestamp_gmt TIMESTAMP,
    sport VARCHAR(50),
    sub_sport VARCHAR(50),
    activity_uuid VARCHAR(64),
    vo2_max_value FLOAT,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- `calendarDate` in this file is epoch-ms (unlike its sibling metrics files,
-- which use plain date strings) - parsed via normalize.parse_epoch_ms_date.
CREATE TABLE IF NOT EXISTS acute_training_load (
    id SERIAL PRIMARY KEY,
    calendar_date DATE NOT NULL,
    reading_timestamp TIMESTAMP NOT NULL,
    user_profile_pk BIGINT,
    device_id BIGINT,
    acwr_percent FLOAT,
    acwr_status VARCHAR(50),
    acwr_status_feedback VARCHAR(50),
    daily_training_load_acute FLOAT,
    daily_training_load_chronic FLOAT,
    daily_acute_chronic_workload_ratio FLOAT,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(calendar_date, reading_timestamp)
);

CREATE TABLE IF NOT EXISTS max_met_data (
    id SERIAL PRIMARY KEY,
    calendar_date DATE NOT NULL,
    update_timestamp TIMESTAMP NOT NULL,
    user_profile_pk BIGINT,
    device_id BIGINT,
    sport VARCHAR(50),
    sub_sport VARCHAR(50),
    vo2_max_value FLOAT,
    max_met FLOAT,
    max_met_category VARCHAR(50),
    calibrated_data INTEGER,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(calendar_date, update_timestamp)
);

CREATE TABLE IF NOT EXISTS race_predictions (
    id SERIAL PRIMARY KEY,
    calendar_date DATE NOT NULL,
    reading_timestamp TIMESTAMP NOT NULL,
    user_profile_pk BIGINT,
    device_id BIGINT,
    race_time_5k_seconds INTEGER,
    race_time_10k_seconds INTEGER,
    race_time_half_seconds INTEGER,
    race_time_marathon_seconds INTEGER,
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(calendar_date, reading_timestamp)
);

CREATE TABLE IF NOT EXISTS training_status_history (
    id SERIAL PRIMARY KEY,
    calendar_date DATE NOT NULL,
    reading_timestamp TIMESTAMP NOT NULL,
    user_profile_pk BIGINT,
    device_id BIGINT,
    training_status VARCHAR(50),
    fitness_level_trend VARCHAR(50),
    training_status_feedback_phrase VARCHAR(100),
    source_file TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(calendar_date, reading_timestamp)
);
