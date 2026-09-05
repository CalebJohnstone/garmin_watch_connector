"""Format-specific date/unit normalization helpers for the Garmin export parsers.

The export mixes several distinct date representations depending on which
Garmin export component produced the file, so each gets its own named parser
rather than one universal date parser that would have to guess the format.
"""

from datetime import date, datetime, timezone

# Epoch-ms values in this export fall roughly between 2000-01-01 and
# 2100-01-01. Used to catch a file format silently reverting to string dates
# (e.g. MetricsAcuteTrainingLoad) instead of silently producing a wrong date.
_EPOCH_MS_MIN = 946684800000
_EPOCH_MS_MAX = 4102444800000


def parse_iso_date(value):
    """'2023-04-01' -> date(2023, 4, 1)"""
    if value in (None, ""):
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_iso_datetime(value):
    """'2024-02-19T22:00:00.0' or '2023-04-01T13:03:39.300' -> datetime (naive, GMT/local as given)"""
    if value in (None, ""):
        return None
    if "." in value:
        base, frac = value.split(".", 1)
        frac = (frac + "000000")[:6]
        value = f"{base}.{frac}"
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")


def parse_epoch_ms(value):
    """Epoch milliseconds (int/float) -> naive UTC datetime."""
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc).replace(tzinfo=None)


def parse_epoch_ms_date(value):
    """Epoch milliseconds -> date. Raises if `value` isn't a plausible epoch-ms
    int, so a future format change (e.g. Garmin reverting to a date string)
    fails loudly instead of silently corrupting dates."""
    if value is None:
        return None
    if not isinstance(value, int):
        raise TypeError(f"expected epoch-ms int, got {type(value).__name__}: {value!r}")
    if not (_EPOCH_MS_MIN <= value <= _EPOCH_MS_MAX):
        raise ValueError(f"epoch-ms value out of plausible range: {value!r}")
    return parse_epoch_ms(value).date()


_JAVA_DATE_FORMAT = "%a %b %d %H:%M:%S %Y"


def parse_java_date_tostring(value):
    """Java Date.toString() format, e.g. 'Thu Aug 06 22:00:00 GMT 2026' -> datetime.

    Strips the literal "GMT" token and parses the rest as UTC rather than
    relying on %Z matching, which is locale/platform-fragile.
    """
    if value in (None, ""):
        return None
    cleaned = value.replace(" GMT ", " ")
    return datetime.strptime(cleaned, _JAVA_DATE_FORMAT)


def cm_to_m(value):
    """Centimeters -> meters."""
    return None if value is None else value / 100.0


def ms_to_s(value):
    """Milliseconds -> seconds."""
    return None if value is None else value / 1000.0


def cmms_to_mps(value):
    """Centimeters-per-millisecond -> meters-per-second (x10)."""
    return None if value is None else value * 10.0


def none_if_zero(value):
    """Maps Garmin's `0` sentinel (meaning "no associated activity") to NULL."""
    return None if value in (0, 0.0) else value
