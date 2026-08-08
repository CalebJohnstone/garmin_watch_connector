import sys
import os
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, jsonify, request
from DatabaseManager import DatabaseManager
from GarminConnectSync import GarminConnectSync
from config import GARMIN_EMAIL, GARMIN_PASSWORD

steps_bp = Blueprint("steps", __name__)


@steps_bp.route("/", methods=["GET"])
def get_steps():
    """Return step data from the database"""
    days_back = request.args.get("days_back", 30, type=int)

    db = DatabaseManager()
    try:
        cutoff = (datetime.now() - timedelta(days=days_back)).date()
        rows = db.get_daily_steps_since(cutoff)

        steps = [{"date": str(row["date"]), "step_count": row["step_count"]} for row in rows]
        return jsonify(steps)
    except Exception as e:
        logging.error("Error fetching steps: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@steps_bp.route("/statistics", methods=["GET"])
def get_statistics():
    """Return the most recent step statistics from the database"""
    db = DatabaseManager()
    try:
        row = db.get_most_recent_step_statistics()
        if not row:
            return jsonify({"error": "No statistics found"}), 404

        stat = dict(row)
        # strings
        for key in ("start_date", "end_date"):
            if stat.get(key):
                stat[key] = str(stat[key])
        # datetimes
        for key in ("analysis_date_time",):
            if stat.get(key) is not None:
                stat[key] = stat[key].isoformat()

        for key in ("average_steps", "standard_deviation"):
            if stat.get(key) is not None:
                stat[key] = float(stat[key])

        return jsonify(stat)
    except Exception as e:
        logging.error("Error fetching statistics: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@steps_bp.route("/sync", methods=["POST"])
def sync_steps():
    """Sync step data from Garmin Connect"""
    days_back = request.json.get("days_back", 30) if request.is_json else 30

    client, error = GarminConnectSync.get_instance(GARMIN_EMAIL, GARMIN_PASSWORD)
    if error:
        msg, status = error
        return jsonify({"error": msg}), status

    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        step_data = client.client.get_daily_steps(start_str, end_str)

        # Reuse existing save logic
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from visualize_steps import save_step_data_to_db, save_statistics_to_db
        save_step_data_to_db(step_data)
        save_statistics_to_db(
            [day.get("calendarDate", "") for day in step_data],
            [int(day.get("totalSteps", 0) or 0) for day in step_data],
            start_str,
            end_str
        )

        return jsonify({
            "message": f"Synced {len(step_data)} days of step data.",
            "count": len(step_data)
        })
    except Exception as e:
        logging.error("Error syncing steps: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        client.db.close()
