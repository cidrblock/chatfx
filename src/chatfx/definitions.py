"""Some common definitions for the chatfx package."""

from __future__ import annotations

import textwrap

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
from typing import NamedTuple
from typing import NewType
from typing import Union

import smaz

from chatfx.colors import color_by_name
from chatfx.utils import scaled_width
from chatfx.utils import ts_full


if TYPE_CHECKING:
    from datetime import datetime


JSONVal = Union[None, bool, str, float, int, list["JSONVal"], dict[str, "JSONVal"]]


@dataclass
class TermFeatures:
    """Terminal features."""

    color: bool
    links: bool

    def any_enabled(self: TermFeatures) -> bool:
        """Return True if any features are enabled."""
        return any((self.color, self.links))


@dataclass
class FormattedText:
    """A formatted log message."""

    #: The message
    message: str
    #: The log level
    indicator: int
    #: The time the message was logged
    time_stamp: datetime.datetime
    #: color
    color: str

    def lines(
        self: FormattedText,
        width: int,
    ) -> CursesLines:
        """Output exit message to the console.

        :param width: Constrain message to width
        :returns: The message as a string
        """
        width = scaled_width(width)
        c_lines = []
        message_lines = self.message.splitlines()

        ts = ts_full(self.time_stamp)

        s_indent = " " * (len(ts) + len(" X|"))

        indent_str = f"{ts} {self.indicator}|"

        lines = textwrap.fill(
            message_lines[0],
            width=width,
            break_on_hyphens=False,
            initial_indent=indent_str,
            subsequent_indent=s_indent,
        ).splitlines()
        c_lines.extend(
            [
                CursesLine(
                    (CursesLinePart(line, self.color, 0),),
                )
                for line in lines
            ],
        )
        if len(message_lines) > 1:
            for line in message_lines[1:]:
                lines = textwrap.fill(
                    line,
                    width=width,
                    break_on_hyphens=False,
                    initial_indent=" " * len(indent_str),
                    subsequent_indent=" " * len(indent_str),
                ).splitlines()
                c_lines.extend(
                    [
                        CursesLine(
                            (CursesLinePart(line, self.color, 0),),
                        )
                        for line in lines
                    ],
                )
        return CursesLines(tuple(c_lines))


@dataclass
class FormattedMsg:
    """A formatted message class."""

    counter: int
    source: str
    destination: str
    message: str
    timestamp: datetime
    indicator: str
    colors: dict[str, str]

    def lines(self: FormattedMsg, width: int) -> CursesLines:
        """Render the message."""
        tcolor = icolor = pcolor = color_by_name("dimgray")
        if self.indicator == "S":
            scolor = dcolor = mcolor = acolor = color_by_name("dimgray")
        if self.indicator in ("R", "A"):
            scolor = color_by_name(self.colors.get(self.source, "white"))
            dcolor = color_by_name(self.colors.get(self.destination, "white"))
            mcolor = acolor = scolor

        prefix = [
            CursesLinePart(self.timestamp.strftime("%m/%d/%y %H:%M:%S"), tcolor, 0),
            CursesLinePart(" ", 0, 0),
            CursesLinePart(self.indicator, icolor, 0),
            CursesLinePart("|", pcolor, 0),
            CursesLinePart(self.source, scolor, 0),
            CursesLinePart(">", acolor, 0),
            CursesLinePart(self.destination, dcolor, 0),
            CursesLinePart(" ", 0, 0),
        ]

        prefix_length = sum(len(part.string) for part in prefix)

        message_lines = self.message.splitlines()

        first_lines = textwrap.fill(
            message_lines[0],
            width=width - prefix_length,
            break_on_hyphens=False,
            initial_indent=" " * prefix_length,
            subsequent_indent=" " * prefix_length,
        ).splitlines()

        first_line = [*prefix, CursesLinePart(first_lines[0].lstrip(), mcolor, 0)]

        c_lines = [CursesLine(tuple(first_line))]
        c_lines.extend(CursesLine((CursesLinePart(line, mcolor, 0),)) for line in first_lines[1:])

        if len(message_lines) > 1:
            for line in message_lines[1:]:
                lines = textwrap.fill(
                    line,
                    width=width - prefix_length,
                    break_on_hyphens=False,
                    initial_indent=" " * prefix_length,
                    subsequent_indent=" " * prefix_length,
                ).splitlines()
                c_lines.extend(CursesLine((CursesLinePart(line, mcolor, 0),)) for line in lines)

        return CursesLines(tuple(c_lines))


@dataclass
class Config:
    """The application configuration."""

    callsign: str
    colors: dict[str, str]
    host: str
    log_file: str
    log_level: str
    log_append: str
    port: int
    time_delay: float
    verbose: int

    def __str__(self: Config) -> str:
        """Return the configuration as a string."""
        return (
            "\n"
            f"\tcallsign: {self.callsign}\n"
            f"\thost: {self.host}\n"
            f"\tlog_file: {self.log_file}\n"
            f"\tlog_level: {self.log_level}\n"
            f"\tlog_append: {self.log_append}\n"
            f"\tport: {self.port}\n"
            f"\ttime_delay: {self.time_delay}\n"
            f"\tverbosity: {self.verbose}"
        )


class MessageType(Enum):
    """Message type enumeration. (0-3)."""

    MSG = 0
    ACK = 1

    def to_bits(self: MessageType) -> str:
        """Return the message type as a 2-bit string."""
        return bin(self.value)[2:].zfill(2)


class CompressionType(Enum):
    """Compression type enumeration. (0-3)."""

    NONE = 0
    SMAZ = 1

    def to_bits(self: CompressionType) -> str:
        """Return the compression type as a 2-bit string."""
        return bin(self.value)[2:].zfill(2)


@dataclass
class MsgId:
    """Message ID dataclass."""

    id: int

    def __post_init__(self: MsgId) -> None:
        """Validate the message ID.

        Raises:
            ValueError: If the message ID is greater than 65535.
        """
        max_val = 65535
        if self.id > max_val:
            msg = f"id must be less than {max_val}"
            raise ValueError(msg)

    def to_bytes(self: MsgId) -> bytes:
        """Return the message ID as a 2-byte array."""
        return self.id.to_bytes(2)

    @classmethod
    def from_bytes(cls: type[MsgId], bytes_array: bytearray) -> MsgId:
        """Return the message ID from a 2-byte array.

        Args:
            bytes_array: The 2-byte array.
        """
        return MsgId(int.from_bytes(bytes_array))


@dataclass
class InfoByte:
    """Info byte dataclass."""

    message_type: MessageType
    compression_type: CompressionType

    def to_byte(self: InfoByte) -> bytes:
        """Return the info byte as a byte."""
        bits = ""
        bits += str(self.message_type.to_bits())
        bits += str(self.compression_type.to_bits())
        bits = bits.ljust(8, "0")
        return bytes([int(bits, 2)])

    @classmethod
    def from_int(cls: type[InfoByte], integer: int) -> InfoByte:
        """Return the info byte from an integer.

        Args:
            integer: The integer.
        Returns:
            The info byte.
        """
        byte_value = integer.to_bytes(1)
        bits = "".join([bit for byte in byte_value for bit in f"{byte:08b}"])
        message_type = MessageType(int(bits[0:2]))
        compression_type = CompressionType(int(bits[2:4]))
        return InfoByte(message_type, compression_type)


@dataclass
class Message:
    """Message dataclass."""

    string: str
    compress: CompressionType = CompressionType.NONE

    def to_bytes(self: Message) -> bytes:
        """Return the message as a byte array.

        Raises:
            ValueError: If the compression type is not supported.
        """
        if self.compress == CompressionType.SMAZ:
            compressed: bytes = smaz.compress(self.string)
            return compressed
        return self.string.encode()

    @classmethod
    def from_bytes(
        cls: type[Message],
        byte_array: bytearray,
        compression_type: CompressionType,
    ) -> Message:
        """Return the message from a byte array.

        Args:
            byte_array: The byte array.
            compression_type: The compression type.
        Returns:
            The message.
        """
        if compression_type == CompressionType.SMAZ:
            return Message(smaz.decompress(bytes(byte_array)))
        return Message(byte_array.decode())


class CursesLinePart(NamedTuple):
    """One chunk of a line of text.

    :param string: the text to be displayed
    :param color: An integer representing a color, not a curses.color_pair(n)
    :param decoration: A curses decoration
    """

    string: str
    color: int
    decoration: int


CursesLine = NewType("CursesLine", tuple[CursesLinePart, ...])
"""One line of text ready for curses."""

CursesLines = NewType("CursesLines", tuple[CursesLine, ...])
"""One or more lines of text ready for curses."""
