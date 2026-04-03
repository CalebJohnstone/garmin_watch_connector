from garminconnect import Garmin
import logging
from datetime import datetime, timedelta
import os
from DatabaseManager import DatabaseManager
import argparse

class GarminConnectSync:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.client = None
        self.logged_in = False
        self.db = DatabaseManager()
        if self.db.connect():
            self.db.create_tables()
        else:
            raise ConnectionError("Failed to connect to database")

    def login(self):
        """Login to Garmin Connect"""
        try:
            self.client = Garmin(self.email, self.password)
            self.client.login()
            self.logged_in = True
            logging.info("Successfully logged into Garmin Connect")
            return True
        except Exception as e:
            logging.error(f"Login failed: {e}")
            self.logged_in = False
            return False

    def format_activity_data(self, detailed_activity, summary_activity):
        """Format activity data for database storage"""
        try:
            start_time_str = summary_activity.get('startTimeLocal', '')
            if start_time_str:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', ''))
            else:
                start_time = datetime.now()

            duration_seconds = summary_activity.get('duration', 0)
            end_time = start_time + timedelta(seconds=duration_seconds) if duration_seconds else None

            distance_meters = summary_activity.get('distance', 0)
            avg_pace = self.calculate_pace(distance_meters, duration_seconds)

            formatted_data = {
                'activity_id': str(summary_activity.get('activityId')),
                'start_time': start_time,
                'end_time': end_time,
                'distance_meters': distance_meters,
                'duration_seconds': duration_seconds,
                'avg_pace_seconds_per_km': avg_pace,
                'calories': summary_activity.get('calories', 0),
                'avg_heart_rate': summary_activity.get('averageHR'),
                'max_heart_rate': summary_activity.get('maxHR'),
            }

            gps_points = self.get_gps_data(summary_activity.get('activityId'))
            formatted_data['gps_points'] = gps_points

            logging.info(f"Formatted activity data for run: {round(formatted_data['distance_meters'] / 1000, 2)} km in {round(formatted_data['duration_seconds'] / 60, 2)} mins")

            return formatted_data

        except Exception as e:
            logging.error(f"Error formatting activity data: {e}")
            return None

    def calculate_pace(self, distance_meters, duration_seconds):
        """Calculate pace in seconds per kilometer"""
        if distance_meters and duration_seconds and distance_meters > 0:
            distance_km = distance_meters / 1000
            pace_seconds_per_km = duration_seconds / distance_km
            return round(pace_seconds_per_km, 2)
        return None

    def get_gps_data(self, activity_id):
        """Get GPS track data for an activity"""
        try:
            gpx_data = self.client.download_activity(activity_id, dl_fmt=self.client.ActivityDownloadFormat.GPX)
            gps_points = self.parse_gpx_simple(gpx_data)
            logging.info(f"Retrieved {len(gps_points)} GPS points")
            return gps_points
        except Exception as e:
            logging.warning(f"Could not retrieve GPS data: {e}")
            return []

    def parse_gpx_simple(self, gpx_data):
        """Simple GPX parser to extract GPS points"""
        import xml.etree.ElementTree as ET

        gps_points = []
        try:
            root = ET.fromstring(gpx_data)

            for trkpt in root.iter():
                if 'trkpt' in trkpt.tag:
                    lat = trkpt.get('lat')
                    lon = trkpt.get('lon')

                    if lat and lon:
                        point = {
                            'latitude': float(lat),
                            'longitude': float(lon),
                            'elevation_meters': None,
                            'speed_mps': None,
                            'timestamp': datetime.now()
                        }

                        for child in trkpt:
                            if 'ele' in child.tag:
                                point['elevation_meters'] = float(child.text) if child.text else None
                            elif 'time' in child.tag and child.text:
                                try:
                                    point['timestamp'] = datetime.fromisoformat(child.text.replace('Z', '+00:00'))
                                except:
                                    pass

                        gps_points.append(point)

        except Exception as e:
            logging.warning(f"Error parsing GPX data: {e}")

        return gps_points

    def get_run_on_exact_date(self, target_date):
        """Get a run that occurred on the exact target date"""
        if not self.logged_in:
            logging.error("Not logged into Garmin Connect")
            return None

        try:
            activity = self.client.get_activities_by_date(target_date, target_date, activitytype='running')[0]

            if not activity:
                logging.info("No run found on target date")
                return None

            detailed_activity = self.client.get_activity(activity.get('activityId'))
            return self.format_activity_data(detailed_activity, activity)
        except Exception as e:
            logging.error(f"Error getting run on exact date: {e}")
            return None

    def get_all_recent_running_activities(self, days_back=30):
        """Get all running activities from the last N days and save new ones to database"""
        if not self.logged_in:
            logging.error("Not logged into Garmin Connect")
            return []

        try:
            activities = self.client.get_activities(0, days_back, activitytype='running')
            logging.info(f"Found {len(activities)} total activities")

            if not activities:
                logging.info("No activities found")
                return []

            saved_count = 0
            skipped_count = 0

            for current_activity in activities:
                activity_id = str(current_activity['activityId'])

                # Check if activity already exists using DatabaseManager
                if self.db.get_activity_by_id(activity_id):
                    logging.info(f"Activity {activity_id} already exists in database, skipping")
                    skipped_count += 1
                    continue

                try:
                    logging.info(f"Getting detailed data for new activity {activity_id}")

                    detailed_activity = self.client.get_activity(activity_id)
                    logging.info(f"xx {detailed_activity.values()}")
                    formatted_data = self.format_activity_data(detailed_activity, current_activity)

                    if not formatted_data:
                        logging.error(f"Failed to format activity {activity_id}")
                        continue

                    # Insert run using DatabaseManager
                    run_id = self.db.insert_run(formatted_data)

                    if run_id:
                        # Insert GPS points if any using DatabaseManager
                        if formatted_data['gps_points']:
                            self.db.insert_gps_points(run_id, formatted_data['gps_points'])

                        saved_count += 1
                        distance_km = round(formatted_data['distance_meters'] / 1000, 2)
                        duration_min = round(formatted_data['duration_seconds'] / 60, 2)
                        logging.info(f"Saved new run: {distance_km} km in {duration_min} mins")
                    else:
                        logging.error(f"Failed to save activity {activity_id}")

                except Exception as e:
                    logging.error(f"Error processing activity {activity_id}: {e}")
                    continue

            logging.info(f"Summary: {saved_count} new activities saved, {skipped_count} already existed")
            return activities

        except Exception as e:
            logging.error(f"Error getting running activities: {e}")
            return []

def main():
    """Main method to sync Garmin Connect running activities"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('garmin_sync.log'),
            logging.StreamHandler()
        ]
    )

    parser = argparse.ArgumentParser(description='Sync Garmin Connect running activities')
    parser.add_argument('--days-back', type=int, default=30, help='Number of days back to sync (default: 30)')
    parser.add_argument('--exact-date', type=str, help='Get run on exact date (format: YYYY-MM-DD)')
    args = parser.parse_args()

    garmin_sync = GarminConnectSync(os.getenv('GARMIN_EMAIL'), os.getenv('GARMIN_PASSWORD'))

    try:
        if not garmin_sync.login():
            logging.error("Failed to login to Garmin Connect")
            return

        if args.exact_date:
            try:
                run_data = garmin_sync.get_run_on_exact_date(args.exact_date)

                if run_data:
                    logging.info(f"Successfully retrieved run on {args.exact_date}")
                else:
                    logging.info(f"No run found on {args.exact_date}")

            except ValueError:
                logging.error("Invalid date format for --exact-date. Use YYYY-MM-DD.")

            return

        activities = garmin_sync.get_all_recent_running_activities(args.days_back or 30)

        if activities:
            logging.info(f"Successfully processed {len(activities)} running activities")
        else:
            logging.info("No running activities found to process")

    except Exception as e:
        logging.error(f"Error in main execution: {e}")

    finally:
        garmin_sync.db.close()
        logging.info("Garmin Connect sync completed")

if __name__ == "__main__":
    main()
