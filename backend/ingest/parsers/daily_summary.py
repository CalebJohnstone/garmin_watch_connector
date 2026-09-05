"""Parses DI-Connect-Aggregator/UDSFile_*.json (User Daily Summary).

Bare top-level array, one object per day. `respiration` and the `allDayStress`
TOTAL bucket are small, fixed-shape sub-objects collapsed onto the row as
flat columns; `allDayStress`'s AWAKE/ASLEEP breakdown and `bodyBattery`'s
stat list are kept as JSONB since they're genuinely list-shaped/nested and
not part of this pipeline's query scope.
"""

import json
import logging

from .. import normalize as norm


def _load(file_path):
    with open(file_path) as f:
        return json.load(f)


def _stress_total(day):
    stress = day.get("allDayStress") or {}
    for entry in stress.get("aggregatorList") or []:
        if entry.get("type") == "TOTAL":
            return entry
    return {}


def _build_row(day, source_file):
    respiration = day.get("respiration") or {}
    stress_total = _stress_total(day)
    return {
        "calendar_date": norm.parse_iso_date(day["calendarDate"]),
        "user_profile_pk": day.get("userProfilePK"),
        "uuid": day.get("uuid"),
        "total_steps": day.get("totalSteps"),
        "daily_step_goal": day.get("dailyStepGoal"),
        "total_distance_meters": day.get("totalDistanceMeters"),
        "total_kilocalories": day.get("totalKilocalories"),
        "active_kilocalories": day.get("activeKilocalories"),
        "bmr_kilocalories": day.get("bmrKilocalories"),
        "resting_heart_rate": day.get("restingHeartRate"),
        "min_heart_rate": day.get("minHeartRate"),
        "max_heart_rate": day.get("maxHeartRate"),
        "floors_ascended_meters": day.get("floorsAscendedInMeters"),
        "floors_descended_meters": day.get("floorsDescendedInMeters"),
        "moderate_intensity_minutes": day.get("moderateIntensityMinutes"),
        "vigorous_intensity_minutes": day.get("vigorousIntensityMinutes"),
        "highly_active_seconds": day.get("highlyActiveSeconds"),
        "active_seconds": day.get("activeSeconds"),
        "wellness_start_time_gmt": norm.parse_iso_datetime(day.get("wellnessStartTimeGmt")),
        "wellness_end_time_gmt": norm.parse_iso_datetime(day.get("wellnessEndTimeGmt")),
        "wellness_start_time_local": norm.parse_iso_datetime(day.get("wellnessStartTimeLocal")),
        "wellness_end_time_local": norm.parse_iso_datetime(day.get("wellnessEndTimeLocal")),
        "avg_waking_respiration_value": respiration.get("avgWakingRespirationValue"),
        "highest_respiration_value": respiration.get("highestRespirationValue"),
        "lowest_respiration_value": respiration.get("lowestRespirationValue"),
        "latest_respiration_value": respiration.get("latestRespirationValue"),
        "latest_respiration_time_gmt": norm.parse_iso_datetime(respiration.get("latestRespirationTimeGMT")),
        "avg_stress_level": stress_total.get("averageStressLevel"),
        "avg_stress_level_intensity": stress_total.get("averageStressLevelIntensity"),
        "stress_off_wrist_count": stress_total.get("stressOffWristCount"),
        "total_stress_count": stress_total.get("totalStressCount"),
        "uncategorized_stress_seconds": stress_total.get("uncategorizedDuration"),
        "total_stress_duration_seconds": stress_total.get("totalDuration"),
        "stress_breakdown_json": json.dumps(day.get("allDayStress")) if day.get("allDayStress") else None,
        "body_battery_json": json.dumps(day.get("bodyBattery")) if day.get("bodyBattery") else None,
        "source_file": source_file,
    }


def parse(file_path):
    for day in _load(file_path):
        try:
            if "calendarDate" not in day:
                logging.warning(f"daily_summary parser: record with no calendarDate in {file_path}, skipping")
                continue
            yield _build_row(day, file_path)
        except Exception as exc:
            logging.error(f"daily_summary parser: failed on {day.get('calendarDate')}: {exc}")
