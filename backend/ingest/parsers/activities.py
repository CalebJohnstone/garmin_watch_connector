"""Parses DI-Connect-Fitness/*summarizedActivities.json.

Unit conversions below were verified by cross-checking a real activity's
top-level fields against its own `splitSummaries` (which are already in
display/SI units): distance/elevation/stride length are in centimeters,
duration is in milliseconds, and avg/max speed are reported at 1/10th of
the true m/s value. Fields marked "(inferred)" follow the same pattern as
a verified sibling field but weren't independently cross-checked.
"""

import json
import logging

from .. import normalize as norm

# fieldEnum -> (column_name, converter). Verified against the full export:
# exactly 52 distinct fieldEnum values across all splits, each with one
# consistent unitEnum. 3 of them (see _REDUNDANT_MEASUREMENT_FIELDS) duplicate
# fields already present on the split's envelope and are not stored again.
MEASUREMENT_FIELD_MAP = {
    "AVG_STEP_LENGTH": ("avg_step_length_meters", norm.cm_to_m),
    "BEGIN_ELEVATION": ("begin_elevation_meters", norm.cm_to_m),
    "GAIN_ELEVATION": ("gain_elevation_meters", norm.cm_to_m),
    "GAIN_UNCORRECTED_ELEVATION": ("gain_uncorrected_elevation_meters", norm.cm_to_m),
    "LOSS_ELEVATION": ("loss_elevation_meters", norm.cm_to_m),
    "LOSS_UNCORRECTED_ELEVATION": ("loss_uncorrected_elevation_meters", norm.cm_to_m),
    "MAX_AIRTEMPERATURE": ("max_air_temperature_celsius", None),
    "MAX_CORRECTED_ELEVATION": ("max_corrected_elevation_meters", norm.cm_to_m),
    "MAX_DOUBLE_CADENCE": ("max_double_cadence", None),
    "MAX_ELEVATION": ("max_elevation_meters", norm.cm_to_m),
    "MAX_FRACTIONAL_CADENCE": ("max_fractional_cadence", None),
    "MAX_HEARTRATE": ("max_heart_rate", None),
    "MAX_POWER": ("max_power_watts", None),
    "MAX_RUNCADENCE": ("max_run_cadence", None),
    "MAX_SPEED": ("max_speed_mps", norm.cmms_to_mps),
    "MAX_UNCORRECTED_ELEVATION": ("max_uncorrected_elevation_meters", norm.cm_to_m),
    "MAX_VERTICAL_SPEED": ("max_vertical_speed_mps", norm.cmms_to_mps),
    "MIN_ACTIVITY_LAP_DURATION": ("min_activity_lap_duration_seconds", norm.ms_to_s),
    "MIN_AIRTEMPERATURE": ("min_air_temperature_celsius", None),
    "MIN_CORRECTED_ELEVATION": ("min_corrected_elevation_meters", norm.cm_to_m),
    "MIN_ELEVATION": ("min_elevation_meters", norm.cm_to_m),
    "MIN_POWER": ("min_power_watts", None),
    "MIN_RUNCADENCE": ("min_run_cadence", None),
    "MIN_SPEED": ("min_speed_mps", norm.cmms_to_mps),
    "MIN_UNCORRECTED_ELEVATION": ("min_uncorrected_elevation_meters", norm.cm_to_m),
    "SUM_BMR_ENERGY": ("sum_bmr_energy_kj", None),
    "SUM_DISTANCE": ("sum_distance_meters", norm.cm_to_m),
    "SUM_DURATION": ("sum_duration_seconds", norm.ms_to_s),
    "SUM_ELAPSEDDURATION": ("sum_elapsed_duration_seconds", norm.ms_to_s),
    "SUM_ENERGY": ("sum_energy_kj", None),
    "SUM_MOVINGDURATION": ("sum_moving_duration_seconds", norm.ms_to_s),
    "SUM_STEP": ("sum_steps", None),
    "SUM_TOTALWORK": ("sum_total_work_kj", None),
    "WEIGHTED_MEAN_AIRTEMPERATURE": ("weighted_mean_air_temperature_celsius", None),
    "WEIGHTED_MEAN_DOUBLE_CADENCE": ("weighted_mean_double_cadence", None),
    "WEIGHTED_MEAN_ELAPSED_DURATION_VERTICAL_SPEED": (
        "weighted_mean_elapsed_duration_vertical_speed_mps",
        norm.cmms_to_mps,
    ),
    "WEIGHTED_MEAN_FRACTIONAL_CADENCE": ("weighted_mean_fractional_cadence", None),
    "WEIGHTED_MEAN_GRADE_ADJUSTED_SPEED": ("weighted_mean_grade_adjusted_speed_mps", norm.cmms_to_mps),
    # Garmin tags this fieldEnum's unit as BPM, which looks like a mislabel
    # (ground contact time is a duration, not a cadence) - stored as-is
    # under a name that doesn't imply a unit, pending clarification.
    "WEIGHTED_MEAN_GROUND_CONTACT_TIME": ("weighted_mean_ground_contact_time_raw", None),
    "WEIGHTED_MEAN_HEARTRATE": ("weighted_mean_heart_rate", None),
    "WEIGHTED_MEAN_MOVINGSPEED": ("weighted_mean_moving_speed_mps", norm.cmms_to_mps),
    "WEIGHTED_MEAN_NORMALIZEDPOWER": ("weighted_mean_normalized_power_watts", None),
    "WEIGHTED_MEAN_POWER": ("weighted_mean_power_watts", None),
    "WEIGHTED_MEAN_RUNCADENCE": ("weighted_mean_run_cadence", None),
    "WEIGHTED_MEAN_SPEED": ("weighted_mean_speed_mps", norm.cmms_to_mps),
    "WEIGHTED_MEAN_STRIDE_LENGTH": ("weighted_mean_stride_length_meters", norm.cm_to_m),
    "WEIGHTED_MEAN_VERTICAL_OSCILLATION": ("weighted_mean_vertical_oscillation_meters", norm.cm_to_m),
    "WEIGHTED_MEAN_VERTICAL_RATIO": ("weighted_mean_vertical_ratio", None),
    "WEIGHTED_MEAN_VERTICAL_SPEED": ("weighted_mean_vertical_speed_mps", norm.cmms_to_mps),
}

_REDUNDANT_MEASUREMENT_FIELDS = {"END_LATITUDE", "END_LONGITUDE", "END_TIMESTAMP"}


def _load(file_path):
    with open(file_path) as f:
        data = json.load(f)
    data = data[0] if isinstance(data, list) else data
    return data["summarizedActivitiesExport"]


def _build_activity_row(a):
    return {
        "activity_id": a["activityId"],
        "sport_type": a.get("sportType"),
        "name": a.get("name"),
        "uuid_msb": a.get("uuidMsb"),
        "uuid_lsb": a.get("uuidLsb"),
        "device_id": a.get("deviceId"),
        "manufacturer": a.get("manufacturer"),
        "event_type_id": a.get("eventTypeId"),
        "begin_timestamp": norm.parse_epoch_ms(a.get("beginTimestamp")),
        "start_time_gmt": norm.parse_epoch_ms(a.get("startTimeGmt")),
        "start_time_local": norm.parse_epoch_ms(a.get("startTimeLocal")),
        "time_zone_id": a.get("timeZoneId"),
        "duration_seconds": norm.ms_to_s(a.get("duration")),
        "elapsed_duration_seconds": norm.ms_to_s(a.get("elapsedDuration")),  # (inferred)
        "moving_duration_seconds": norm.ms_to_s(a.get("movingDuration")),  # (inferred)
        "distance_meters": norm.cm_to_m(a.get("distance")),
        "elevation_gain_meters": norm.cm_to_m(a.get("elevationGain")),
        "elevation_loss_meters": norm.cm_to_m(a.get("elevationLoss")),
        "elevation_corrected": a.get("elevationCorrected"),
        "min_elevation_meters": norm.cm_to_m(a.get("minElevation")),
        "max_elevation_meters": norm.cm_to_m(a.get("maxElevation")),
        "avg_speed_mps": norm.cmms_to_mps(a.get("avgSpeed")),
        "max_speed_mps": norm.cmms_to_mps(a.get("maxSpeed")),  # (inferred, same field class as avgSpeed)
        "avg_grade_adjusted_speed_mps": norm.cmms_to_mps(a.get("avgGradeAdjustedSpeed")),  # (inferred)
        "avg_hr": a.get("avgHr"),
        "max_hr": a.get("maxHr"),
        "min_hr": a.get("minHr"),
        "avg_power": a.get("avgPower"),
        "max_power": a.get("maxPower"),
        "norm_power": a.get("normPower"),
        "avg_run_cadence": a.get("avgRunCadence"),
        "max_run_cadence": a.get("maxRunCadence"),
        "avg_double_cadence": a.get("avgDoubleCadence"),
        "max_double_cadence": a.get("maxDoubleCadence"),
        "avg_fractional_cadence": a.get("avgFractionalCadence"),
        "max_fractional_cadence": a.get("maxFractionalCadence"),
        # Verified: matches splitSummaries.avgGroundContactTime 1:1 (already ms, no scaling).
        "avg_ground_contact_time_ms": a.get("avgGroundContactTime"),
        "avg_stride_length_meters": norm.cm_to_m(a.get("avgStrideLength")),
        "avg_vertical_oscillation_meters": norm.cm_to_m(a.get("avgVerticalOscillation")),
        # Verified: matches splitSummaries.verticalRatio 1:1, dimensionless.
        "avg_vertical_ratio": a.get("avgVerticalRatio"),
        "steps": a.get("steps"),
        "calories": a.get("calories"),
        "bmr_calories": a.get("bmrCalories"),
        "auto_calc_calories": a.get("autoCalcCalories"),
        "start_latitude": a.get("startLatitude"),
        "start_longitude": a.get("startLongitude"),
        "end_latitude": a.get("endLatitude"),
        "end_longitude": a.get("endLongitude"),
        "min_latitude": a.get("minLatitude"),
        "max_latitude": a.get("maxLatitude"),
        "min_longitude": a.get("minLongitude"),
        "max_longitude": a.get("maxLongitude"),
        "max_temperature": a.get("maxTemperature"),
        "min_temperature": a.get("minTemperature"),
        "max_vertical_speed": norm.cmms_to_mps(a.get("maxVerticalSpeed")),  # (inferred)
        "vo2_max_value": a.get("vO2MaxValue"),
        "aerobic_training_effect": a.get("aerobicTrainingEffect"),
        "aerobic_training_effect_message": a.get("aerobicTrainingEffectMessage"),
        "anaerobic_training_effect": a.get("anaerobicTrainingEffect"),
        "anaerobic_training_effect_message": a.get("anaerobicTrainingEffectMessage"),
        "activity_training_load": a.get("activityTrainingLoad"),
        "training_effect_label": a.get("trainingEffectLabel"),
        "moderate_intensity_minutes": a.get("moderateIntensityMinutes"),
        "vigorous_intensity_minutes": a.get("vigorousIntensityMinutes"),
        "lap_count": a.get("lapCount"),
        "favorite": a.get("favorite"),
        "pr": a.get("pr"),
        "purposeful": a.get("purposeful"),
        "location_name": a.get("locationName"),
        "workout_id": a.get("workoutId"),
        "workout_feel": a.get("workoutFeel"),
        "workout_rpe": a.get("workoutRpe"),
        "workout_compliance_score": a.get("workoutComplianceScore"),
        "total_sets": a.get("totalSets"),
        "active_sets": a.get("activeSets"),
        "total_reps": a.get("totalReps"),
        "difference_body_battery": a.get("differenceBodyBattery"),
        "is_run_power_wind_data_enabled": a.get("isRunPowerWindDataEnabled"),
        "run_power_wind_data_enabled": a.get("runPowerWindDataEnabled"),
        "deco_dive": a.get("decoDive"),
        "water_estimated": a.get("waterEstimated"),
    }


def _build_zone_rows(activity_id, activity, prefix, count):
    rows = []
    for zone_number in range(count):
        seconds = activity.get(f"{prefix}TimeInZone_{zone_number}")
        if seconds is not None:
            rows.append({"activity_id": activity_id, "zone_number": zone_number, "seconds": seconds})
    return rows


def _build_split_row(activity_id, split):
    row = {
        "activity_id": activity_id,
        "message_index": split.get("messageIndex"),
        "split_type": split.get("type"),
        "start_index": split.get("startIndex"),
        "end_index": split.get("endIndex"),
        "start_time_gmt": norm.parse_epoch_ms(split.get("startTimeGMT")),
        "end_time_gmt": norm.parse_epoch_ms(split.get("endTimeGMT")),
        "start_time_source": split.get("startTimeSource"),
        "end_time_source": split.get("endTimeSource"),
        "start_latitude": split.get("startLatitude"),
        "start_longitude": split.get("startLongitude"),
        "end_latitude": split.get("endLatitude"),
        "end_longitude": split.get("endLongitude"),
        "total_exercise_reps": split.get("totalExerciseReps"),
        "lap_indexes": split.get("lapIndexes"),
    }
    for measurement in split.get("measurements") or []:
        field_enum = measurement.get("fieldEnum")
        if field_enum in _REDUNDANT_MEASUREMENT_FIELDS:
            continue
        mapping = MEASUREMENT_FIELD_MAP.get(field_enum)
        if mapping is None:
            logging.warning(f"activities parser: unknown split measurement fieldEnum {field_enum!r}, skipping")
            continue
        column, converter = mapping
        value = measurement.get("value")
        row[column] = converter(value) if converter else value
    return row


def _build_split_summary_row(activity_id, summary):
    # Verified: splitSummaries fields are already in display/SI units
    # (meters, seconds, m/s) - no conversion applied here.
    return {
        "activity_id": activity_id,
        "split_type": summary.get("type"),
        "no_of_splits": summary.get("noOfSplits"),
        "duration_seconds": summary.get("duration"),
        "distance_meters": summary.get("distance"),
        "average_speed_mps": summary.get("averageSpeed"),
        "max_speed_mps": summary.get("maxSpeed"),
        "average_elevation_gain_meters": summary.get("averageElevationGain"),
        "elevation_loss_meters": summary.get("elevationLoss"),
        "max_elevation_gain_meters": summary.get("maxElevationGain"),
        "total_ascent_meters": summary.get("totalAscent"),
        "avg_ground_contact_time": summary.get("avgGroundContactTime"),
        "avg_step_frequency": summary.get("avgStepFrequency"),
        "avg_step_length_meters": summary.get("avgStepLength"),
        "vertical_oscillation": summary.get("verticalOscillation"),
        "vertical_ratio": summary.get("verticalRatio"),
        "max_distance_meters": summary.get("maxDistance"),
        "max_distance_with_precision": summary.get("maxDistanceWithPrecision"),
        "num_climb_sends": summary.get("numClimbSends"),
        "num_climbs_attempted": summary.get("numClimbsAttempted"),
        "num_climbs_completed": summary.get("numClimbsCompleted"),
        "num_falls": summary.get("numFalls"),
    }


def _build_exercise_set_row(activity_id, set_index, exercise_set):
    return {
        "activity_id": activity_id,
        "set_index": set_index,
        "category": exercise_set.get("category"),
        "sub_category": exercise_set.get("subCategory"),
        "reps": exercise_set.get("reps"),
        "sets": exercise_set.get("sets"),
        "volume": exercise_set.get("volume"),
        "max_weight": exercise_set.get("maxWeight"),
        "duration_seconds": norm.ms_to_s(exercise_set.get("duration")),
    }


def _build_dive_info_row(activity_id, dive_info):
    return {
        "activity_id": activity_id,
        "total_surface_time_seconds": dive_info.get("totalSurfaceTime"),
    }


def parse(file_path):
    """Yields one dict per activity:
    {"activity_type_key", "activity", "hr_zones", "power_zones", "splits",
     "split_summaries", "exercise_sets", "dive_info"}
    """
    for a in _load(file_path):
        try:
            activity_id = a["activityId"]
            record = {
                "activity_type_key": a.get("activityType"),
                "activity": _build_activity_row(a),
                "hr_zones": _build_zone_rows(activity_id, a, "hr", 7),
                "power_zones": _build_zone_rows(activity_id, a, "power", 6),
                "splits": [_build_split_row(activity_id, s) for s in (a.get("splits") or [])],
                "split_summaries": [
                    _build_split_summary_row(activity_id, s) for s in (a.get("splitSummaries") or [])
                ],
                "exercise_sets": [
                    _build_exercise_set_row(activity_id, i, s)
                    for i, s in enumerate(a.get("summarizedExerciseSets") or [])
                ],
                "dive_info": (
                    _build_dive_info_row(activity_id, a["summarizedDiveInfo"])
                    if a.get("summarizedDiveInfo")
                    else None
                ),
            }
            yield record
        except Exception as exc:
            logging.error(f"activities parser: failed on activityId={a.get('activityId')}: {exc}")
