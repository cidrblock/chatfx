"""Utilities."""

from __future__ import annotations

import decimal

from datetime import datetime
from datetime import timezone


def now() -> str:
    """Return the current time."""
    return datetime.now(timezone.utc).astimezone()


def ts_full(time_stamp: datetime.datetime) -> str:
    """Return the current date."""
    return time_stamp.strftime("%m/%d/%y %H:%M:%S")


def ts_time(time_stamp: datetime.datetime) -> str:
    """Return the current time."""
    return time_stamp.strftime("%H:%M:%S")


def round_half_up(number: float) -> int:
    """Round a number to the nearest integer with ties going away from zero.

    This is different the round() where exact halfway cases are rounded to the nearest
    even result instead of away from zero. (e.g. round(2.5) = 2, round(3.5) = 4).

    This will always round based on distance from zero. (e.g round(2.5) = 3, round(3.5) = 4).

    :param number: The number to round
    :returns: The rounded number as an it
    """
    rounded = decimal.Decimal(number).quantize(
        decimal.Decimal("1"),
        rounding=decimal.ROUND_HALF_UP,
    )
    return int(rounded)


def scaled_width(width: int) -> int:
    """Get a sliding scale screen width.

    :returns: The console width
    """
    s_max = 2160
    p_at_max = 0.80

    r1 = s_max / width
    r2 = p_at_max / r1
    s = 1 - r2
    return round_half_up(width * s)


def scale_for_curses(rgb_value: int) -> int:
    """Scale a single RGB value for curses.

    :param rgb_value: One RGB value
    :returns: The value scaled for curses
    """
    curses_ceiling = 1000
    rgb_ceiling = 255
    return int(rgb_value * curses_ceiling / rgb_ceiling)
