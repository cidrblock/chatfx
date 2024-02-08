"""Output functionality."""

from __future__ import annotations

import logging
import sys

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Callable

from chatfx.colors import color_by_name
from chatfx.definitions import FormattedText
from chatfx.utils import now


if TYPE_CHECKING:
    from chatfx.definitions import FormattedMsg

    from .utils import TermFeatures


class Level(Enum):
    """An exit message prefix."""

    CRITICAL = "Critical"
    DEBUG = "Debug"
    ERROR = "Error"
    HINT = "Hint"
    INFO = "Info"
    NOTE = "Note"
    WARNING = "Warning"

    @property
    def log_level(self: Level) -> int:
        """Return a log level.

        :returns: The log level
        """
        mapping = {
            Level.CRITICAL: logging.CRITICAL,
            Level.DEBUG: logging.DEBUG,
            Level.ERROR: logging.ERROR,
            Level.HINT: logging.INFO,
            Level.INFO: logging.INFO,
            Level.NOTE: logging.INFO,
            Level.WARNING: logging.WARNING,
        }
        return mapping[self]


COLOR_MAPPING = {
    Level.CRITICAL: color_by_name("red"),
    Level.DEBUG: color_by_name("dimgrey"),
    Level.ERROR: color_by_name("crimson"),
    Level.HINT: color_by_name("limegreen"),
    Level.INFO: color_by_name("lightskyblue"),
    Level.NOTE: color_by_name("green"),
    Level.WARNING: color_by_name("yellow"),
}


class Output:
    """Output functionality."""

    def __init__(  # noqa: PLR0913
        self: Output,
        log_file: str,
        log_level: str,
        log_append: str,
        term_features: TermFeatures,
        verbosity: int,
        ui_refresh: Callable[[], None],
        ui_output: list[FormattedText | FormattedMsg],
    ) -> None:
        """Initialize the output object.

        Args:
            log_file: The path to the los.get_terminal_size()og file
            log_level: The log level
            log_append: Whether to append to the log file
            term_features: Terminal features
            verbosity: The verbosity level
        """
        self._verbosity = verbosity
        self.call_count: dict[str, int] = {
            "critical": 0,
            "debug": 0,
            "error": 0,
            "hint": 0,
            "info": 0,
            "note": 0,
            "warning": 0,
        }
        self.ui_refresh = ui_refresh
        self.ui_output = ui_output
        self.term_features = term_features
        self.logger = logging.getLogger("chatfx")
        if log_level != "notset":
            self.logger.setLevel(log_level.upper())
            self.log_to_file = bool(log_file)
            log_file_path = Path(log_file)
            if log_file_path.exists() and log_append == "false":
                log_file_path.unlink()
            formatter = logging.Formatter(
                fmt="%(asctime)s %(levelname)s '%(name)s.%(module)s.%(funcName)s' %(message)s",
            )
            handler = logging.FileHandler(log_file)
            handler.setFormatter(formatter)
            handler.setLevel(log_level.upper())
            self.logger.addHandler(handler)
            self.log_to_file = True
        else:
            self.log_to_file = False

    def critical(self: Output, msg: str) -> None:
        """Print a critical message to the console.

        :param msg: The message to print
        """
        self.call_count["critical"] += 1
        self.log(msg, level=Level.CRITICAL)
        sys.exit(1)

    def debug(self: Output, msg: str) -> None:
        """Print a debug message to the console.

        :param msg: The message to print
        """
        self.call_count["debug"] += 1
        self.log(msg, level=Level.DEBUG)

    def error(self: Output, msg: str) -> None:
        """Print an error message to the console.

        :param msg: The message to print
        """
        self.call_count["error"] += 1
        self.log(msg, level=Level.ERROR)

    def hint(self: Output, msg: str) -> None:
        """Print a hint message to the console.

        :param msg: The message to print
        """
        self.call_count["hint"] += 1
        self.log(msg, level=Level.HINT)

    def info(self: Output, msg: str) -> None:
        """Print a hint message to the console.

        :param msg: The message to print
        """
        self.call_count["info"] += 1
        self.log(msg, level=Level.INFO)

    def note(self: Output, msg: str) -> None:
        """Print a note message to the console.

        :param msg: The message to print
        """
        self.call_count["note"] += 1
        self.log(msg, level=Level.NOTE)

    def warning(self: Output, msg: str) -> None:
        """Print a warning message to the console.

        :param msg: The message to print
        """
        self.call_count["warning"] += 1
        self.log(msg, level=Level.WARNING)

    def log(self: Output, msg: str, level: Level = Level.ERROR) -> None:
        """Print a message to the console.

        :param msg: The message to print
        :param prefix: The prefix for the message
        """
        if self.log_to_file:
            self.logger.log(level.log_level, msg, stacklevel=3)

        debug = 2
        info = 1
        if (self._verbosity < debug and level == Level.DEBUG) or (
            self._verbosity < info and level == Level.INFO
        ):
            return

        self.ui_output.append(
            FormattedText(
                message=msg,
                indicator=logging.getLevelName(level.log_level)[0],
                time_stamp=now(),
                color=COLOR_MAPPING[level],
            ),
        )
        self.ui_refresh()
