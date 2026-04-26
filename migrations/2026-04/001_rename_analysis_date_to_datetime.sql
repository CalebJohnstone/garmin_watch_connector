-- Active: 1763192014745@@127.0.0.1@5432@garmin_data
-- Migration 001: Rename analysis_date to analysis_date_time and change type to TIMESTAMP
-- Table: step_statistics

BEGIN;

-- Step 1: Add the new column as TIMESTAMP
ALTER TABLE step_statistics
    ADD COLUMN analysis_date_time TIMESTAMP;

-- Step 2: Populate it from the existing DATE column (midnight on that date)
UPDATE step_statistics
    SET analysis_date_time = analysis_date::TIMESTAMP;

-- Step 3: Make it NOT NULL now that it's populated
ALTER TABLE step_statistics
    ALTER COLUMN analysis_date_time SET NOT NULL;

-- Step 4: Drop the old column
ALTER TABLE step_statistics
    DROP COLUMN analysis_date;

COMMIT;
