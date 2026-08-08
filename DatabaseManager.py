import logging
import psycopg
from psycopg.rows import dict_row
from datetime import date
from pydantic import BaseModel

# -------------------------------------------------------------
# 1. Load DB credentials (adjust as your project uses)
# -------------------------------------------------------------
from config import DB_CONFIG  # { "host": "...", "port": 5432, ... }

# -------------------------------------------------------------
# 2. Helper: Connection wrapper
# -------------------------------------------------------------
class _PsycopgConnection:
    """Thin wrapper that guarantees a live psycopg Connection."""
    def __init__(self, dsn: dict):
        self.dsn = dsn
        self._conn: psycopg.Connection | None = None

    def _open(self):
        """Open the underlying connection (idempotent)."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(**self.dsn, row_factory=dict_row)
            self._conn.autocommit = False  # we commit manually
            logging.info("PostgreSQL connection opened")

    def cursor(self) -> psycopg.Cursor:
        """Return a fresh cursor on a live connection."""
        self._open()
        return self._conn.cursor()

    def commit(self):
        self._open()
        self._conn.commit()

    def rollback(self):
        self._open()
        self._conn.rollback()

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
            logging.info("PostgreSQL connection closed")
        self._conn = None


# -------------------------------------------------------------
# 3. Main manager
# -------------------------------------------------------------
class DatabaseManager:
    def __init__(self):
        # The wrapper does lazy‑open and auto‑reconnect
        self._conn = _PsycopgConnection(DB_CONFIG)

    # -----------------------------------------------------------------
    # Public API – all methods automatically ensure a live connection
    # -----------------------------------------------------------------
    def create_tables(self):
        """Create the tables if they do not yet exist."""
        create_runs_table = """
            CREATE TABLE IF NOT EXISTS runs (
                id              SERIAL PRIMARY KEY,
                activity_id     VARCHAR(50) UNIQUE,
                start_time      TIMESTAMP,
                end_time        TIMESTAMP,
                distance_meters FLOAT,
                duration_seconds INTEGER,
                avg_pace_seconds_per_km FLOAT,
                calories        INTEGER,
                avg_heart_rate  INTEGER,
                max_heart_rate  INTEGER,
                sync_timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """

        create_gps_points_table = """
            CREATE TABLE IF NOT EXISTS gps_points (
                id                SERIAL PRIMARY KEY,
                run_id            INTEGER REFERENCES runs(id),
                timestamp         TIMESTAMP,
                latitude          DECIMAL(10,8),
                longitude         DECIMAL(11,8),
                elevation_meters  FLOAT,
                speed_mps         FLOAT
            );
        """

        cur = self._conn.cursor()
        try:
            cur.execute(create_runs_table)
            cur.execute(create_gps_points_table)
            self._conn.commit()
            logging.info("Database tables created/verified")
        except Exception as exc:
            self._conn.rollback()
            logging.error(f"Error creating tables: {exc}")

    def insert_run(self, run_data: dict) -> int | None:
        """Insert a new run and return its ID."""
        sql = """
            INSERT INTO runs (
                activity_id, start_time, end_time,
                distance_meters, duration_seconds,
                avg_pace_seconds_per_km, calories,
                avg_heart_rate, max_heart_rate
            )
            VALUES (%(activity_id)s, %(start_time)s, %(end_time)s,
                    %(distance_meters)s, %(duration_seconds)s,
                    %(avg_pace_seconds_per_km)s, %(calories)s,
                    %(avg_heart_rate)s, %(max_heart_rate)s)
            RETURNING id;
        """

        cur = self._conn.cursor()
        try:
            cur.execute(sql, run_data)
            run_id = cur.fetchone()["id"]
            self._conn.commit()
            logging.info(f"Run inserted, id={run_id}")
            return run_id
        except Exception as exc:
            self._conn.rollback()
            logging.error(f"Error inserting run: {exc}")
            return None

    def insert_gps_points(self, run_id: int, gps_points: list[dict]):
        """Insert a batch of GPS points."""
        sql = """
            INSERT INTO gps_points (
                run_id, timestamp, latitude, longitude,
                elevation_meters, speed_mps
            )
            VALUES (%(run_id)s, %(timestamp)s, %(latitude)s, %(longitude)s,
                    %(elevation_meters)s, %(speed_mps)s);
        """

        cur = self._conn.cursor()
        try:
            for pt in gps_points:
                pt["run_id"] = run_id
                cur.execute(sql, pt)
            self._conn.commit()
            logging.info(f"Inserted {len(gps_points)} GPS points for run {run_id}")
        except Exception as exc:
            self._conn.rollback()
            logging.error(f"Error inserting GPS points: {exc}")

    def get_activity_by_id(self, activity_id: str) -> dict | None:
        """Return the internal run id if the activity exists."""
        cur = self._conn.cursor()
        try:
            cur.execute("SELECT id FROM runs WHERE activity_id = %s", (activity_id,))
            return cur.fetchone()
        except Exception as exc:
            logging.error(f"Error checking for existing activity: {exc}")
            return None

    def get_daily_steps_since(self, start_date: date) -> list[dict] | None:
        cur = self._conn.cursor()
        try:
            cur.execute("""
                SELECT date, step_count
                FROM daily_steps
                WHERE date >= %s
                ORDER BY date ASC
            """, (start_date,))
            return cur.fetchall()
        except Exception as ex:
            logging.error(f"Error getting the daily steps since: {start_date}. {ex}")
            return None

    def get_most_recent_step_statistics(self) -> list[dict] | None:
        cur = self._conn.cursor()
        try:
            cur.execute("""
                SELECT analysis_date_time, start_date, end_date, days_analyzed,
                    average_steps, max_steps, min_steps, standard_deviation
                FROM step_statistics
                ORDER BY analysis_date_time DESC
                LIMIT 1
            """)
            return cur.fetchone()
        except Exception as ex:
            logging.error(f"Error getting the most recent step stats: {ex}")
            return None

    def get_runs(self, days_back: int) -> list[dict] | None:
        cur = self._conn.cursor()
        try:
            cur.execute("""
                SELECT id, activity_id, start_time, end_time, distance_meters,
                    duration_seconds, avg_pace_seconds_per_km, calories,
                    avg_heart_rate, max_heart_rate, sync_timestamp
                FROM runs
                ORDER BY start_time DESC
                LIMIT %s
            """, (days_back,))
            return cur.fetchall()
        except Exception as ex:
            logging.error(f"Error getting the most recent runs: {ex}")
            return None

    # -------------------------------------------------
    # Clean‑up helpers
    # -------------------------------------------------
    def close(self):
        self._conn.close()
