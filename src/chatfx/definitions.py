"""Some common definitions for the chatfx package."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Union

import smaz


JSONVal = Union[None, bool, str, float, int, list["JSONVal"], dict[str, "JSONVal"]]


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
