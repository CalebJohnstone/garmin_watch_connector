"""Parses the DI-Connect-Wellness bio-metrics/config files. Each function
here handles one distinct file shape (see paths.SOURCES `subtype` values).
"""

import json
import logging

from .. import normalize as norm


def _load(file_path):
    with open(file_path) as f:
        return json.load(f)


def parse_heart_rate_zones(file_path):
    for zone in _load(file_path):
        try:
            yield {
                "sport": zone.get("sport"),
                "training_method": zone.get("trainingMethod"),
                "resting_heart_rate_used": zone.get("restingHeartRateUsed"),
                "lactate_threshold_heart_rate_used": zone.get("lactateThresholdHeartRateUsed"),
                "zone1_floor": zone.get("zone1Floor"),
                "zone2_floor": zone.get("zone2Floor"),
                "zone3_floor": zone.get("zone3Floor"),
                "zone4_floor": zone.get("zone4Floor"),
                "zone5_floor": zone.get("zone5Floor"),
                "max_heart_rate_used": zone.get("maxHeartRateUsed"),
                "resting_hr_auto_update_used": zone.get("restingHrAutoUpdateUsed"),
                "change_state": zone.get("changeState"),
                "source_file": file_path,
            }
        except Exception as exc:
            logging.error(f"biometrics parser (heart_rate_zones): failed: {exc}")


def parse_power_zones(file_path):
    for zone in _load(file_path):
        try:
            yield {
                "sport": zone.get("sport"),
                "functional_threshold_power": zone.get("functionalThresholdPower"),
                "zone1_floor": zone.get("zone1Floor"),
                "zone2_floor": zone.get("zone2Floor"),
                "zone3_floor": zone.get("zone3Floor"),
                "zone4_floor": zone.get("zone4Floor"),
                "zone5_floor": zone.get("zone5Floor"),
                "zone6_floor": zone.get("zone6Floor"),
                "zone7_floor": zone.get("zone7Floor"),
                "source_file": file_path,
            }
        except Exception as exc:
            logging.error(f"biometrics parser (power_zones): failed: {exc}")


def parse_user_bio_metric_profile_data(file_path):
    data = _load(file_path)
    if not data:
        return
    profile = data[0]
    yield {
        "id": 1,
        "height": profile.get("height"),
        "weight": profile.get("weight"),
        "activity_class": profile.get("activityClass"),
        "vo2_max": profile.get("vo2Max"),
        "lactate_threshold_heart_rate": profile.get("lactateThresholdHeartRate"),
        "functional_threshold_power": profile.get("functionalThresholdPower"),
        "source_file": file_path,
    }


def parse_bio_metrics_latest(file_path):
    data = _load(file_path)
    if not data:
        return
    latest = data[0]
    yield {
        "id": 1,
        "lactate_threshold_speed": latest.get("lactateThresholdSpeed"),
        "lactate_threshold_heart_rate": latest.get("lactateThresholdHeartRate"),
        "source_file": file_path,
    }


def _scalar_weight(weight):
    # A handful of events carry weight as {"weight": ..., "sourceType": ..., "timestampGMT": ...}
    # instead of a plain number - unwrap to the numeric value either way.
    if isinstance(weight, dict):
        return weight.get("weight")
    return weight


def parse_user_bio_metrics_history(file_path):
    for event in _load(file_path):
        try:
            meta = event.get("metaData") or {}
            yield {
                "version": event["version"],
                "metadata_calendar_date": norm.parse_iso_datetime(meta.get("calendarDate")),
                "metadata_sequence": meta.get("sequence"),
                "height": event.get("height"),
                "weight": _scalar_weight(event.get("weight")),
                "activity_class": event.get("activityClass"),
                "sport_id": event.get("sportId"),
                "vo2_max_running": event.get("vo2MaxRunning"),
                "vo2_max_cycling": event.get("vo2MaxCycling"),
                "lactate_threshold_speed": event.get("lactateThresholdSpeed"),
                # Note: Garmin's own key is misspelled "lactateThresholdHearRate" (missing 't').
                "lactate_threshold_heart_rate": event.get("lactateThresholdHearRate"),
                "lactate_threshold_rowing_pace": event.get("lactateThresholdRowingPace"),
                "lactate_threshold_rowing_heart_rate": event.get("lactateThresholdRowingHR"),
                "functional_threshold_power": event.get("functionalThresholdPower"),
                "ftp_auto_detected": event.get("ftpAutoDetected"),
                "threshold_heart_rate_auto_detected": event.get("thresholdHeartRateAutoDetected"),
                "firstbeat_running_lt_timestamp": event.get("firstbeatRunningLtTimestamp"),
                "source_file": file_path,
            }
        except Exception as exc:
            logging.error(f"biometrics parser (user_bio_metrics_history): failed on version={event.get('version')}: {exc}")


def parse_fitness_age_data(file_path):
    for entry in _load(file_path):
        try:
            yield {
                "as_of_date_gmt": norm.parse_iso_date((entry.get("asOfDateGmt") or "").split("T")[0] or None),
                "create_timestamp": norm.parse_iso_datetime(entry.get("createTimestamp")),
                "chronological_age": entry.get("chronologicalAge"),
                "bmi": entry.get("bmi"),
                "rhr": entry.get("rhr"),
                "total_vigorous_days": entry.get("totalVigorousDays"),
                "total_vigorous_ims": entry.get("totalVigorousIMs"),
                "num_of_weeks_for_im": entry.get("numOfWeeksForIM"),
                "healthy_bmi": entry.get("healthyBmi"),
                "healthy_fat": entry.get("healthyFat"),
                "vo2_max_for_healthy_bmi_fat": entry.get("vo2MaxForHealthyBmiFat"),
                "vo2_max_for_healthy_rhr": entry.get("vo2MaxForHealthyRhr"),
                "vo2_max_for_healthy_active": entry.get("vo2MaxForHealthyActive"),
                "biometric_vo2_max": entry.get("biometricVo2Max"),
                "current_bio_age": entry.get("currentBioAge"),
                "healthy_all_bio_age": entry.get("healthyAllBioAge"),
                "healthy_bmi_fat_bio_age": entry.get("healthyBmiFatBioAge"),
                "healthy_rhr_bio_age": entry.get("healthyRhrBioAge"),
                "healthy_active_bio_age": entry.get("healthyActiveBioAge"),
                "weight_data_last_entry_date": norm.parse_iso_date(entry.get("weightDataLastEntryDate")),
                "rhr_last_entry_date": norm.parse_iso_date(entry.get("rhrLastEntryDate")),
                "source_file": file_path,
            }
        except Exception as exc:
            logging.error(f"biometrics parser (fitness_age_data): failed on {entry.get('asOfDateGmt')}: {exc}")
