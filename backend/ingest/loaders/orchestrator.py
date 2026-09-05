"""Walks the export directory per requested category, parses matching files,
and upserts rows via IngestDatabaseManager - or, in --dry-run mode, just
counts what it would have done with zero DB connection/writes at all.
"""

import glob
import logging
import os

from .. import paths
from ..db import IngestDatabaseManager
from ..file_tracker import file_sha256, file_stat, needs_processing
from ..parsers import activities, biometrics, daily_summary, gear, hydration, personal_records, sleep, training_metrics

# subtype -> (parse_fn, upsert_method_name) for the categories that are a
# straightforward one-parser-generator-to-one-table mapping. `activities`,
# `sleep`, and `gear` need bespoke handling below (multi-table fan-out,
# placeholder-row counting, and two parse functions respectively).
SIMPLE_HANDLERS = {
    "daily_summary": (daily_summary.parse, "upsert_daily_summary"),
    "hydration": (hydration.parse, "upsert_hydration_log"),
    "heart_rate_zones": (biometrics.parse_heart_rate_zones, "upsert_heart_rate_zone"),
    "power_zones": (biometrics.parse_power_zones, "upsert_power_zone"),
    "user_bio_metric_profile_data": (
        biometrics.parse_user_bio_metric_profile_data,
        "upsert_user_bio_metric_profile_data",
    ),
    "bio_metrics_latest": (biometrics.parse_bio_metrics_latest, "upsert_bio_metrics_latest"),
    "user_bio_metrics_history": (biometrics.parse_user_bio_metrics_history, "upsert_user_bio_metrics_history"),
    "fitness_age_data": (biometrics.parse_fitness_age_data, "upsert_fitness_age_data"),
    "activity_vo2_max": (training_metrics.parse_activity_vo2_max, "upsert_activity_vo2_max"),
    "acute_training_load": (training_metrics.parse_acute_training_load, "upsert_acute_training_load"),
    "max_met_data": (training_metrics.parse_max_met_data, "upsert_max_met_data"),
    "race_predictions": (training_metrics.parse_race_predictions, "upsert_race_predictions"),
    "training_status_history": (training_metrics.parse_training_status_history, "upsert_training_status_history"),
    "personal_records": (personal_records.parse, "upsert_personal_record"),
}


def _process_activity_file(db, file_path, dry_run):
    row_count = error_count = 0
    for record in activities.parse(file_path):
        try:
            if not dry_run:
                type_id = db.get_or_create_activity_type_id(record["activity_type_key"])
                activity_row = dict(record["activity"])
                activity_row["activity_type_id"] = type_id
                activity_row["source_file"] = file_path
                db.upsert_activity(activity_row)
                for zone in record["hr_zones"]:
                    db.upsert_activity_hr_zone(zone)
                for zone in record["power_zones"]:
                    db.upsert_activity_power_zone(zone)
                for split in record["splits"]:
                    db.upsert_activity_split(split)
                for summary in record["split_summaries"]:
                    db.upsert_activity_split_summary(summary)
                for exercise_set in record["exercise_sets"]:
                    db.upsert_activity_exercise_set(exercise_set)
                if record["dive_info"]:
                    db.upsert_activity_dive_info(record["dive_info"])
            row_count += 1
        except Exception as exc:
            logging.error(f"orchestrator: failed to load activity from {file_path}: {exc}")
            error_count += 1
    return row_count, error_count, 0


def _process_sleep_file(db, file_path, dry_run):
    row_count = error_count = placeholder_count = 0
    for row in sleep.parse(file_path):
        if row is None:
            placeholder_count += 1
            continue
        try:
            if not dry_run:
                db.upsert_sleep_session(row)
            row_count += 1
        except Exception as exc:
            logging.error(f"orchestrator: failed to load sleep row from {file_path}: {exc}")
            error_count += 1
    return row_count, error_count, placeholder_count


def _process_gear_file(db, file_path, dry_run):
    row_count = error_count = 0
    for row in gear.parse_gear(file_path):
        try:
            if not dry_run:
                db.upsert_gear(row)
            row_count += 1
        except Exception as exc:
            logging.error(f"orchestrator: failed to load gear row from {file_path}: {exc}")
            error_count += 1
    for row in gear.parse_gear_activity_links(file_path):
        try:
            if not dry_run:
                db.upsert_gear_activity_link(row)
            row_count += 1
        except Exception as exc:
            logging.error(f"orchestrator: failed to load gear_activity_link row from {file_path}: {exc}")
            error_count += 1
    return row_count, error_count, 0


def _process_simple_file(db, subtype, file_path, dry_run):
    parse_fn, upsert_method_name = SIMPLE_HANDLERS[subtype]
    row_count = error_count = 0
    for row in parse_fn(file_path):
        try:
            if not dry_run:
                getattr(db, upsert_method_name)(row)
            row_count += 1
        except Exception as exc:
            logging.error(f"orchestrator: failed to load {subtype} row from {file_path}: {exc}")
            error_count += 1
    return row_count, error_count, 0


def process_file(db, subtype, file_path, dry_run):
    """Returns (row_count, error_count, placeholder_count)."""
    if subtype == "activities":
        return _process_activity_file(db, file_path, dry_run)
    if subtype == "sleep":
        return _process_sleep_file(db, file_path, dry_run)
    if subtype == "gear":
        return _process_gear_file(db, file_path, dry_run)
    if subtype in SIMPLE_HANDLERS:
        return _process_simple_file(db, subtype, file_path, dry_run)
    raise ValueError(f"no handler registered for subtype {subtype!r}")


def run(export_dir, categories, dry_run=False, force=False, limit=None):
    db = None
    if not dry_run:
        db = IngestDatabaseManager()
        db.create_tables()

    summary = {}

    try:
        for source in paths.sources_for(categories):
            category = source["category"]
            pattern = os.path.join(export_dir, source["glob"])
            file_paths = sorted(glob.glob(pattern))
            if limit:
                file_paths = file_paths[:limit]
            cat_summary = summary.setdefault(
                category, {"files": 0, "skipped": 0, "rows": 0, "errors": 0, "placeholders": 0}
            )

            for file_path in file_paths:
                tracked = db.get_import_file(file_path) if db else None
                if not needs_processing(file_path, tracked, force):
                    cat_summary["skipped"] += 1
                    continue

                cat_summary["files"] += 1
                try:
                    row_count, error_count, placeholder_count = process_file(
                        db, source["subtype"], file_path, dry_run
                    )
                    cat_summary["rows"] += row_count
                    cat_summary["errors"] += error_count
                    cat_summary["placeholders"] += placeholder_count

                    if db:
                        mtime, size = file_stat(file_path)
                        db.upsert_import_file(
                            {
                                "category": category,
                                "file_path": file_path,
                                "file_mtime": mtime,
                                "file_size": size,
                                "file_sha256": file_sha256(file_path),
                                "row_count": row_count,
                                "status": "success" if error_count == 0 else "partial",
                            }
                        )
                        db.commit()
                except Exception as exc:
                    logging.error(f"orchestrator: aborting file {file_path}: {exc}")
                    cat_summary["errors"] += 1
                    if db:
                        db.rollback()
    finally:
        if db:
            db.close()

    return summary
