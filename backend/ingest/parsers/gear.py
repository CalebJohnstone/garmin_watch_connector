"""Parses DI-Connect-Fitness/*_gear.json. Wrapped in a single-element list:
`[{"gearDTOS": [...], "gearActivityDTOs": {...}}]`. `gearActivityDTOs` is a
dict keyed by stringified gearPk -> list of {gearPk, activityId} links, not
a uniform array - asserted here so a future format change is caught loudly.
"""

import json
import logging

from .. import normalize as norm


def _load(file_path):
    with open(file_path) as f:
        data = json.load(f)
    return data[0] if isinstance(data, list) else data


def parse_gear(file_path):
    data = _load(file_path)
    for item in data.get("gearDTOS") or []:
        try:
            yield {
                "gear_pk": item["gearPk"],
                "uuid": item.get("uuid"),
                "user_profile_pk": item.get("userProfilePk"),
                "gear_type_name": item.get("gearTypeName"),
                "gear_status_name": item.get("gearStatusName"),
                "custom_make_model": item.get("customMakeModel"),
                "date_begin": norm.parse_iso_date(item.get("dateBegin")),
                "maximum_meters": item.get("maximumMeters"),
                "gear_version": item.get("gearVersion"),
                "create_date": norm.parse_iso_date(item.get("createDate")),
                "update_date": norm.parse_iso_date(item.get("updateDate")),
                "source_file": file_path,
            }
        except Exception as exc:
            logging.error(f"gear parser (gear): failed on gearPk={item.get('gearPk')}: {exc}")


def parse_gear_activity_links(file_path):
    data = _load(file_path)
    gear_activity_dtos = data.get("gearActivityDTOs") or {}
    if not isinstance(gear_activity_dtos, dict):
        raise TypeError(
            f"gear parser: expected gearActivityDTOs to be a dict, got {type(gear_activity_dtos).__name__}"
        )
    for links in gear_activity_dtos.values():
        for link in links:
            try:
                yield {
                    "gear_pk": link["gearPk"],
                    "activity_id": link["activityId"],
                    "source_file": file_path,
                }
            except Exception as exc:
                logging.error(f"gear parser (gear_activity_links): failed on {link}: {exc}")
