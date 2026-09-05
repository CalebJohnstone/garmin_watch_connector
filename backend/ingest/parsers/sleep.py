"""Parses DI-Connect-Wellness/*_sleepData.json. Bare top-level array.

Known export gap: only the earliest chunk has real fields; every later
chunk is just `{"retro": false}` placeholders. Placeholder records (no
`calendarDate`) are counted separately by the caller via the None yielded
here, rather than silently dropped or inserted as null rows.
"""

import json
import logging

from .. import normalize as norm


def _load(file_path):
    with open(file_path) as f:
        return json.load(f)


def parse(file_path):
    """Yields a row dict per real sleep record, or None for each placeholder
    record encountered (so the orchestrator can count them separately)."""
    for entry in _load(file_path):
        if "calendarDate" not in entry:
            yield None
            continue
        try:
            yield {
                "calendar_date": norm.parse_iso_date(entry["calendarDate"]),
                "sleep_start_gmt": norm.parse_iso_datetime(entry.get("sleepStartTimestampGMT")),
                "sleep_end_gmt": norm.parse_iso_datetime(entry.get("sleepEndTimestampGMT")),
                "sleep_window_confirmation_type": entry.get("sleepWindowConfirmationType"),
                "retro": entry.get("retro"),
                "source_file": file_path,
            }
        except Exception as exc:
            logging.error(f"sleep parser: failed on {entry.get('calendarDate')}: {exc}")
