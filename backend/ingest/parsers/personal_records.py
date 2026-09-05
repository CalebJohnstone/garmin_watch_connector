"""Parses DI-Connect-Fitness/*_personalRecord.json. Wrapped in a single-element
list: `[{"personalRecords": [...]}]`."""

import json
import logging

from .. import normalize as norm


def _load(file_path):
    with open(file_path) as f:
        data = json.load(f)
    data = data[0] if isinstance(data, list) else data
    return data["personalRecords"]


def parse(file_path):
    for pr in _load(file_path):
        try:
            yield {
                "personal_record_id": pr["personalRecordId"],
                # Sentinel 0 means "no associated activity" (e.g. step-count/streak PRs).
                "activity_id": norm.none_if_zero(pr.get("activityId")),
                "value": pr.get("value"),
                "pr_start_time_gmt": norm.parse_java_date_tostring(pr.get("prStartTimeGMT")),
                "personal_record_type": pr.get("personalRecordType"),
                "created_date": norm.parse_iso_date(pr.get("createdDate")),
                "current": pr.get("current"),
                "confirmed": pr.get("confirmed"),
                "source_file": file_path,
            }
        except Exception as exc:
            logging.error(f"personal_records parser: failed on personalRecordId={pr.get('personalRecordId')}: {exc}")
