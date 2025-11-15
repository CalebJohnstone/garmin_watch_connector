import logging
import sys
from DatabaseManager import DatabaseManager
from GarminConnectSync import GarminConnectSync
from config import DB_CONFIG, GARMIN_EMAIL, GARMIN_PASSWORD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('garmin_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """Main sync process using Garmin Connect API"""
    logging.info("Starting Garmin Connect sync process...")

    # Check credentials
    if not GARMIN_EMAIL or not GARMIN_PASSWORD:
        logging.error("Garmin Connect credentials not configured in .env file")
        return

    # Initialize database
    db = DatabaseManager()
    if not db.connect():
        logging.error("Failed to connect to database")
        return

    db.create_tables()

    # Initialize Garmin Connect client
    garmin = GarminConnectSync(GARMIN_EMAIL, GARMIN_PASSWORD)

    try:
        # Login to Garmin Connect
        if not garmin.login():
            logging.error("Failed to login to Garmin Connect")
            return

        # Get the latest running activity
        activity_data = garmin.get_latest_run()
        if not activity_data:
            logging.info("No new running activities found")
            return

        # Check if this activity is already in the database
        existing_activity = db.get_activity_by_id(activity_data['activity_id'])
        if existing_activity:
            logging.info(f"Activity with ID = {activity_data['activity_id']} already exists in database")
            return

        # Store run data
        gps_points = activity_data.pop('gps_points', [])
        run_id = db.insert_run(activity_data)

        if run_id and gps_points:
            db.insert_gps_points(run_id, gps_points)
            logging.info(f"Stored {len(gps_points)} GPS points")

        logging.info("Sync completed successfully")

    except Exception as e:
        logging.error(f"Sync failed: {e}")

    finally:
        # Cleanup
        db.close()

if __name__ == "__main__":
    main()
