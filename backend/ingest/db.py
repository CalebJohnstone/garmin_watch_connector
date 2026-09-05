"""Postgres access layer for the Garmin export import pipeline.

Kept separate from the root `DatabaseManager` (which is a lazy-reconnect
wrapper built for a long-lived Flask process) - a batch CLI run is simpler
as a single connection opened at start and closed at end, committing once
per source file. Reuses `config.DB_CONFIG` and mirrors DatabaseManager's
psycopg/dict_row/snake_case conventions.
"""

import logging
import os
import sys

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import DB_CONFIG  # noqa: E402

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MIGRATIONS_DIR = os.path.join(_REPO_ROOT, "migrations", "2026-09")


def _split_sql_statements(sql_text):
    """Splits a migration file into individual statements. Only safe because
    these files contain plain CREATE TABLE/INDEX DDL with no embedded
    semicolons (no functions, no string literals containing ';')."""
    kept_lines = [line for line in sql_text.splitlines() if not line.strip().startswith("--")]
    cleaned = "\n".join(kept_lines)
    return [stmt.strip() for stmt in cleaned.split(";") if stmt.strip()]


class IngestDatabaseManager:
    def __init__(self):
        self._conn = psycopg.connect(**DB_CONFIG, row_factory=dict_row)
        self._conn.autocommit = False
        self._activity_type_cache = {}

    # -----------------------------------------------------------------
    # Connection lifecycle
    # -----------------------------------------------------------------
    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    # -----------------------------------------------------------------
    # Schema
    # -----------------------------------------------------------------
    def create_tables(self):
        """Applies every migrations/2026-09/*.sql file (idempotent
        CREATE TABLE/INDEX IF NOT EXISTS statements) - the migration files
        are the single source of truth for the schema, executed here rather
        than duplicated as inline strings so the two can't drift apart."""
        for filename in sorted(os.listdir(_MIGRATIONS_DIR)):
            if not filename.endswith(".sql"):
                continue
            path = os.path.join(_MIGRATIONS_DIR, filename)
            with open(path) as f:
                sql_text = f.read()
            cur = self._conn.cursor()
            try:
                for statement in _split_sql_statements(sql_text):
                    cur.execute(statement)
                self._conn.commit()
                logging.info(f"Applied schema from {filename}")
            except Exception:
                self._conn.rollback()
                raise

    # -----------------------------------------------------------------
    # Generic upsert helper
    # -----------------------------------------------------------------
    def _upsert(self, table, row, conflict_cols, do_nothing=False):
        """INSERT ... ON CONFLICT upsert built from `row`'s own keys.

        `table`/`conflict_cols` are always internal fixed strings supplied by
        this module's own methods, never user input, so building the SQL
        text with them is safe; only `row`'s values are passed as query
        parameters.
        """
        columns = list(row.keys())
        col_list = ", ".join(columns)
        placeholders = ", ".join(f"%({c})s" for c in columns)
        if do_nothing:
            conflict_clause = f"ON CONFLICT ({', '.join(conflict_cols)}) DO NOTHING"
        else:
            update_cols = [c for c in columns if c not in conflict_cols]
            set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
            conflict_clause = f"ON CONFLICT ({', '.join(conflict_cols)}) DO UPDATE SET {set_clause}"
        sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) {conflict_clause}"
        cur = self._conn.cursor()
        cur.execute(sql, row)

    # -----------------------------------------------------------------
    # import_files tracking
    # -----------------------------------------------------------------
    def get_import_file(self, file_path):
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM import_files WHERE file_path = %s", (file_path,))
        return cur.fetchone()

    def upsert_import_file(self, row):
        self._upsert("import_files", row, conflict_cols=["file_path"])

    # -----------------------------------------------------------------
    # Activities
    # -----------------------------------------------------------------
    def get_or_create_activity_type_id(self, type_key):
        if type_key in self._activity_type_cache:
            return self._activity_type_cache[type_key]
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO activity_types (type_key) VALUES (%s)
            ON CONFLICT (type_key) DO UPDATE SET type_key = EXCLUDED.type_key
            RETURNING id
            """,
            (type_key,),
        )
        type_id = cur.fetchone()["id"]
        self._activity_type_cache[type_key] = type_id
        return type_id

    def upsert_activity(self, row):
        self._upsert("activities", row, conflict_cols=["activity_id"])

    def upsert_activity_hr_zone(self, row):
        self._upsert("activity_hr_zones", row, conflict_cols=["activity_id", "zone_number"])

    def upsert_activity_power_zone(self, row):
        self._upsert("activity_power_zones", row, conflict_cols=["activity_id", "zone_number"])

    def upsert_activity_split(self, row):
        self._upsert("activity_splits", row, conflict_cols=["activity_id", "message_index"])

    def upsert_activity_split_summary(self, row):
        self._upsert("activity_split_summaries", row, conflict_cols=["activity_id", "split_type"])

    def upsert_activity_exercise_set(self, row):
        self._upsert("activity_exercise_sets", row, conflict_cols=["activity_id", "set_index"])

    def upsert_activity_dive_info(self, row):
        self._upsert("activity_dive_info", row, conflict_cols=["activity_id"])

    # -----------------------------------------------------------------
    # Daily summary / hydration / sleep
    # -----------------------------------------------------------------
    def upsert_daily_summary(self, row):
        self._upsert("daily_summary", row, conflict_cols=["calendar_date"])

    def upsert_hydration_log(self, row):
        self._upsert("hydration_logs", row, conflict_cols=["uuid"])

    def upsert_sleep_session(self, row):
        self._upsert("sleep_sessions", row, conflict_cols=["calendar_date"])

    # -----------------------------------------------------------------
    # Bio-metrics / wellness
    # -----------------------------------------------------------------
    def upsert_heart_rate_zone(self, row):
        self._upsert("heart_rate_zones", row, conflict_cols=["sport", "training_method"])

    def upsert_power_zone(self, row):
        self._upsert("power_zones", row, conflict_cols=["sport"])

    def upsert_user_bio_metric_profile_data(self, row):
        self._upsert("user_bio_metric_profile_data", row, conflict_cols=["id"])

    def upsert_bio_metrics_latest(self, row):
        self._upsert("bio_metrics_latest", row, conflict_cols=["id"])

    def upsert_user_bio_metrics_history(self, row):
        self._upsert("user_bio_metrics_history", row, conflict_cols=["version"], do_nothing=True)

    def upsert_fitness_age_data(self, row):
        self._upsert("fitness_age_data", row, conflict_cols=["as_of_date_gmt"])

    # -----------------------------------------------------------------
    # Training metrics
    # -----------------------------------------------------------------
    def upsert_activity_vo2_max(self, row):
        self._upsert("activity_vo2_max", row, conflict_cols=["activity_id"])

    def upsert_acute_training_load(self, row):
        self._upsert("acute_training_load", row, conflict_cols=["calendar_date", "reading_timestamp"])

    def upsert_max_met_data(self, row):
        self._upsert("max_met_data", row, conflict_cols=["calendar_date", "update_timestamp"])

    def upsert_race_predictions(self, row):
        self._upsert("race_predictions", row, conflict_cols=["calendar_date", "reading_timestamp"])

    def upsert_training_status_history(self, row):
        self._upsert("training_status_history", row, conflict_cols=["calendar_date", "reading_timestamp"])

    # -----------------------------------------------------------------
    # Personal records / gear
    # -----------------------------------------------------------------
    def upsert_personal_record(self, row):
        self._upsert("personal_records", row, conflict_cols=["personal_record_id"])

    def upsert_gear(self, row):
        self._upsert("gear", row, conflict_cols=["gear_pk"])

    def upsert_gear_activity_link(self, row):
        self._upsert("gear_activity_links", row, conflict_cols=["gear_pk", "activity_id"])
