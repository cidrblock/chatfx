"""Utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .definitions import JSONVal


@dataclass
class TermFeatures:
    """Terminal features."""

    color: bool
    links: bool

    def any_enabled(self: TermFeatures) -> bool:
        """Return True if any features are enabled."""
        return any((self.color, self.links))


def ci_get(
    dictionary: dict[str, str],
    key: str,
    default: None = None,
) -> JSONVal:
    """Get a value from a dictionary with case-insensitive keys."""
    for k, v in dictionary.items():
        if k.lower() == key.lower():
            return v
    return default


def get_color(
    dictionary: dict[str, str],
    key: str,
    default: str = "white",
) -> str:
    """Get a color from a dictionary."""
    value = ci_get(dictionary, key)
    if value is None:
        return default
    if not isinstance(value, str):
        msg = f"Expected string for color, got {value!r}"
        raise TypeError(msg)
    return value
