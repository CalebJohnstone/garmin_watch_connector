"""Parses DI-Connect-Aggregator/HydrationLogFile_*.json. Bare top-level array."""

import json
import logging

from .. import normalize as norm


def _load(file_path):
    with open(file_path) as f:
        return json.load(f)


def _build_row(entry, source_file):
    return {
        "uuid": entry["uuid"]["uuid"],
        "user_profile_pk": entry.get("userProfilePK"),
        "calendar_date": norm.parse_iso_date(entry.get("calendarDate")),
        "timestamp_local": norm.parse_iso_datetime(entry.get("timestampLocal")),
        "persisted_timestamp_gmt": norm.parse_iso_datetime(entry.get("persistedTimestampGMT")),
        "hydration_source": entry.get("hydrationSource"),
        "value_in_ml": entry.get("valueInML"),
        "activity_id": norm.none_if_zero(entry.get("activityId")),
        "estimated_sweat_loss_in_ml": entry.get("estimatedSweatLossInML"),
        "duration_seconds": entry.get("duration"),
        "source_file": source_file,
    }


def parse(file_path):
    for entry in _load(file_path):
        if not isinstance(entry.get("uuid"), dict):
            # A handful of the earliest entries (account-creation era) have no
            # uuid at all - there's no other genuinely stable natural key for
            # this table, so these are skipped rather than guessed at.
            logging.warning(
                f"hydration parser: entry with no uuid in {file_path} (calendarDate={entry.get('calendarDate')}), skipping"
            )
            continue
        try:
            yield _build_row(entry, file_path)
        except Exception as exc:
            logging.error(f"hydration parser: failed on entry {entry.get('uuid')}: {exc}")
