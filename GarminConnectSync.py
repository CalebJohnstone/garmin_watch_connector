from garminconnect import Garmin
import logging
from datetime import datetime, timedelta

class GarminConnectSync:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.client = None
        self.logged_in = False

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

    def get_latest_run(self):
        """Get the most recent running activity"""
        if not self.logged_in:
            logging.error("Not logged into Garmin Connect")
            return None

        try:
            # Get activities from last 30 days
            activities = self.client.get_activities(0, 100)
            logging.info(f"Found {len(activities)} total activities")

            # Filter for running activities
            running_activities = []
            for activity in activities:
                activity_type = activity.get('activityType', {})
                if activity_type and activity_type.get('typeKey') == 'running':
                    running_activities.append(activity)

            logging.info(f"Found {len(running_activities)} running activities")

            if not running_activities:
                logging.info("No running activities found")
                return None

            # Get the most recent one
            latest_run = running_activities[0]
            activity_id = latest_run['activityId']

            logging.info(f"Getting detailed data for activity {activity_id}")

            # Get detailed activity data
            detailed_activity = self.client.get_activity(activity_id)

            return self.format_activity_data(detailed_activity, latest_run)

        except Exception as e:
            logging.error(f"Error getting latest run: {e}")
            return None

    def format_activity_data(self, detailed_activity, summary_activity):
        """Format activity data for database storage"""
        try:
            start_time_str = summary_activity.get('startTimeLocal', '')
            if start_time_str:
                # Remove timezone info and parse
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

            # Try to get GPS points if available
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
            # Get GPX data
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

            # Find all trackpoints
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
                            'timestamp': datetime.now()  # You'd parse actual timestamp from GPX
                        }

                        # Try to get elevation
                        for child in trkpt:
                            if 'ele' in child.tag:
                                point['elevation_meters'] = float(child.text) if child.text else None
                            elif 'time' in child.tag and child.text:
                                # Parse timestamp
                                try:
                                    point['timestamp'] = datetime.fromisoformat(child.text.replace('Z', '+00:00'))
                                except:
                                    pass

                        gps_points.append(point)

        except Exception as e:
            logging.warning(f"Error parsing GPX data: {e}")

        return gps_points

    def get_activities_since(self, days_back=7):
        """Get all activities from the last N days"""
        if not self.logged_in:
            logging.error("Not logged into Garmin Connect")
            return []

        try:
            activities = self.client.get_activities(0, days_back * 10)  # Estimate activities per day

            # Filter by date
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_activities = []

            for activity in activities:
                start_time_str = activity.get('startTimeLocal', '')
                if start_time_str:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', ''))
                    if start_time > cutoff_date:
                        recent_activities.append(activity)

            return recent_activities

        except Exception as e:
            logging.error(f"Error getting recent activities: {e}")
            return []
