import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, jsonify, request
from DatabaseManager import DatabaseManager
from GarminConnectSync import GarminConnectSync
from config import GARMIN_EMAIL, GARMIN_PASSWORD

activities_bp = Blueprint("activities", __name__)

def get_garmin_client():
    client = GarminConnectSync(GARMIN_EMAIL, GARMIN_PASSWORD)
    if not client.login():
        return None, "Failed to login to Garmin Connect"
    return client, None


@activities_bp.route("/", methods=["GET"])
def get_activities():
    """Return all runs stored in the database"""
    db = DatabaseManager()
    if not db.connect():
        return jsonify({"error": "Database connection failed"}), 500

    try:
        db.cursor.execute("""
            SELECT id, activity_id, start_time, end_time, distance_meters,
                   duration_seconds, avg_pace_seconds_per_km, calories,
                   avg_heart_rate, max_heart_rate, sync_timestamp
            FROM runs
            ORDER BY start_time DESC
        """)
        rows = db.cursor.fetchall()

        activities = []
        for row in rows:
            activity = dict(row)
            # Convert datetime objects to ISO strings for JSON serialization
            for key in ("start_time", "end_time", "sync_timestamp"):
                if activity.get(key):
                    activity[key] = activity[key].isoformat()
            activities.append(activity)

        return jsonify(activities)
    except Exception as e:
        logging.error("Error fetching activities: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@activities_bp.route("/<int:run_id>/gps", methods=["GET"])
def get_gps_points(run_id):
    """Return GPS points for a specific run"""
    db = DatabaseManager()
    if not db.connect():
        return jsonify({"error": "Database connection failed"}), 500

    try:
        db.cursor.execute("""
            SELECT id, run_id, timestamp, latitude, longitude,
                   elevation_meters, speed_mps
            FROM gps_points
            WHERE run_id = %s
            ORDER BY timestamp ASC
        """, (run_id,))
        rows = db.cursor.fetchall()

        points = []
        for row in rows:
            point = dict(row)
            if point.get("timestamp"):
                point["timestamp"] = point["timestamp"].isoformat()
            points.append(point)

        return jsonify(points)
    except Exception as e:
        logging.error("Error fetching GPS points: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@activities_bp.route("/sync", methods=["POST"])
def sync_activities():
    """Sync recent running activities from Garmin Connect"""
    days_back = request.json.get("days_back", 30) if request.is_json else 30

    client, error = get_garmin_client()
    if error:
        return jsonify({"error": error}), 500

    try:
        activities = client.get_all_recent_running_activities(days_back)
        return jsonify({
            "message": f"Sync complete. Processed {len(activities)} activities.",
            "count": len(activities)
        })
    except Exception as e:
        logging.error("Error syncing activities: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        client.db.close()
