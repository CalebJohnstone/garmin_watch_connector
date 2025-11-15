import psycopg
from psycopg.rows import dict_row
import logging
from config import DB_CONFIG

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor(row_factory=dict_row)
            logging.info("Database connection established")
            return True
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            return False

    def create_tables(self):
        """Create necessary tables for storing running data"""
        create_runs_table = """
        CREATE TABLE IF NOT EXISTS runs (
            id SERIAL PRIMARY KEY,
            activity_id VARCHAR(50) UNIQUE,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            distance_meters FLOAT,
            duration_seconds INTEGER,
            avg_pace_seconds_per_km FLOAT,
            calories INTEGER,
            avg_heart_rate INTEGER,
            max_heart_rate INTEGER,
            sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        create_gps_points_table = """
        CREATE TABLE IF NOT EXISTS gps_points (
            id SERIAL PRIMARY KEY,
            run_id INTEGER REFERENCES runs(id),
            timestamp TIMESTAMP,
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            elevation_meters FLOAT,
            speed_mps FLOAT
        );
        """

        try:
            self.cursor.execute(create_runs_table)
            self.cursor.execute(create_gps_points_table)
            self.connection.commit()
            logging.info("Database tables created/verified")
        except Exception as e:
            logging.error(f"Error creating tables: {e}")
            self.connection.rollback()

    def insert_run(self, run_data):
        """Insert a new run record"""
        insert_query = """
        INSERT INTO runs (activity_id, start_time, end_time, distance_meters,
                         duration_seconds, avg_pace_seconds_per_km, calories,
                         avg_heart_rate, max_heart_rate)
        VALUES (%(activity_id)s, %(start_time)s, %(end_time)s, %(distance_meters)s,
                %(duration_seconds)s, %(avg_pace_seconds_per_km)s, %(calories)s,
                %(avg_heart_rate)s, %(max_heart_rate)s)
        RETURNING id;
        """

        try:
            self.cursor.execute(insert_query, run_data)
            run_id = self.cursor.fetchone()['id']
            self.connection.commit()
            logging.info(f"Run inserted with ID: {run_id}")
            return run_id
        except Exception as e:
            logging.error(f"Error inserting run: {e}")
            self.connection.rollback()
            return None

    def insert_gps_points(self, run_id, gps_points):
        """Insert GPS points for a run"""
        insert_query = """
        INSERT INTO gps_points (run_id, timestamp, latitude, longitude,
                               elevation_meters, speed_mps)
        VALUES (%(run_id)s, %(timestamp)s, %(latitude)s, %(longitude)s,
                %(elevation_meters)s, %(speed_mps)s);
        """

        try:
            for point in gps_points:
                point['run_id'] = run_id
                self.cursor.execute(insert_query, point)
            self.connection.commit()
            logging.info(f"Inserted {len(gps_points)} GPS points for run {run_id}")
        except Exception as e:
            logging.error(f"Error inserting GPS points: {e}")
            self.connection.rollback()

    def get_activity_by_id(self, activity_id):
        """Check if an activity already exists in the database"""
        query = "SELECT id FROM runs WHERE activity_id = %s"

        try:
            self.cursor.execute(query, (activity_id,))
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            logging.error(f"Error checking for existing activity: {e}")
            return None

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logging.info("Database connection closed")
