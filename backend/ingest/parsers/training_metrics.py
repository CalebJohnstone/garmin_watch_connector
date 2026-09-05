"""Parses the DI-Connect-Metrics training metric feeds. Each function here
handles one distinct file family (see paths.SOURCES `subtype` values). All
are bare top-level arrays, one record per day (occasionally more than one
per day at chunk boundaries - hence the (calendar_date, reading_timestamp)
composite natural keys used by the DB layer).
"""

import json
import logging

from .. import normalize as norm


def _load(file_path):
    with open(file_path) as f:
        return json.load(f)


def parse_activity_vo2_max(file_path):
    for entry in _load(file_path):
        try:
            uuid = (entry.get("activityUuid") or {}).get("uuid")
            yield {
                "activity_id": entry["activityId"],
                "user_profile_pk": entry.get("userProfilePK"),
                "calendar_date": norm.parse_iso_date(entry.get("calendarDate")),
                "device_id": entry.get("deviceId"),
                "timestamp_gmt": norm.parse_iso_datetime(entry.get("timestampGmt")),
                "sport": entry.get("sport"),
                "sub_sport": entry.get("subSport"),
                "activity_uuid": uuid,
                "vo2_max_value": entry.get("vo2MaxValue"),
                "source_file": file_path,
            }
        except Exception as exc:
            logging.error(f"training_metrics parser (activity_vo2_max): failed on activityId={entry.get('activityId')}: {exc}")


def parse_acute_training_load(file_path):
    for entry in _load(file_path):
        try:
            yield {
                "calendar_date": norm.parse_epoch_ms_date(entry["calendarDate"]),
                "reading_timestamp": norm.parse_epoch_ms(entry.get("timestamp")),
                "user_profile_pk": entry.get("userProfilePK"),
                "device_id": entry.get("deviceId"),
                "acwr_percent": entry.get("acwrPercent"),
                "acwr_status": entry.get("acwrStatus"),
                "acwr_status_feedback": entry.get("acwrStatusFeedback"),
                "daily_training_load_acute": entry.get("dailyTrainingLoadAcute"),
                "daily_training_load_chronic": entry.get("dailyTrainingLoadChronic"),
                "daily_acute_chronic_workload_ratio": entry.get("dailyAcuteChronicWorkloadRatio"),
                "source_file": file_path,
            }
        except Exception as exc:
            logging.error(f"training_metrics parser (acute_training_load): failed on calendarDate={entry.get('calendarDate')}: {exc}")


def parse_max_met_data(file_path):
    for entry in _load(file_path):
        try:
            yield {
                "calendar_date": norm.parse_iso_date(entry.get("calendarDate")),
                "update_timestamp": norm.parse_iso_datetime(entry.get("updateTimestamp")),
                "user_profile_pk": entry.get("userProfilePK"),
                "device_id": entry.get("deviceId"),
                "sport": entry.get("sport"),
                "sub_sport": entry.get("subSport"),
                "vo2_max_value": entry.get("vo2MaxValue"),
                "max_met": entry.get("maxMet"),
                "max_met_category": entry.get("maxMetCategory"),
                "calibrated_data": entry.get("calibratedData"),
                "source_file": file_path,
            }
        except Exception as exc:
            logging.error(f"training_metrics parser (max_met_data): failed on calendarDate={entry.get('calendarDate')}: {exc}")


def parse_race_predictions(file_path):
    for entry in _load(file_path):
        try:
            yield {
                "calendar_date": norm.parse_iso_date(entry.get("calendarDate")),
                "reading_timestamp": norm.parse_iso_datetime(entry.get("timestamp")),
                "user_profile_pk": entry.get("userProfilePK"),
                "device_id": entry.get("deviceId"),
                "race_time_5k_seconds": entry.get("raceTime5K"),
                "race_time_10k_seconds": entry.get("raceTime10K"),
                "race_time_half_seconds": entry.get("raceTimeHalf"),
                "race_time_marathon_seconds": entry.get("raceTimeMarathon"),
                "source_file": file_path,
            }
        except Exception as exc:
            logging.error(f"training_metrics parser (race_predictions): failed on calendarDate={entry.get('calendarDate')}: {exc}")


def parse_training_status_history(file_path):
    for entry in _load(file_path):
        try:
            yield {
                "calendar_date": norm.parse_iso_date(entry.get("calendarDate")),
                "reading_timestamp": norm.parse_iso_datetime(entry.get("timestamp")),
                "user_profile_pk": entry.get("userProfilePK"),
                "device_id": entry.get("deviceId"),
                "training_status": entry.get("trainingStatus"),
                "fitness_level_trend": entry.get("fitnessLevelTrend"),
                "training_status_feedback_phrase": entry.get("trainingStatus2FeedbackPhrase"),
                "source_file": file_path,
            }
        except Exception as exc:
            logging.error(f"training_metrics parser (training_status_history): failed on calendarDate={entry.get('calendarDate')}: {exc}")
