"""Chat client for AX.25 packet radio networks."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys

from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from enum import Enum
from pathlib import Path

import smaz

from aioax25.frame import AX25RawFrame
from aioax25.interface import AX25Interface
from aioax25.kiss import KISSDeviceState
from aioax25.kiss import TCPKISSDevice
from aioax25.kiss import make_device
from prompt_toolkit import HTML
from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout


TIME_BETWEEN_COMM = 5.0
LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.CRITICAL)


class MessageType(Enum):
    """Message type enumeration."""

    MSG = 0
    ACK = 1

    def to_bits(self: MessageType) -> str:
        """Return the message type as a 2-bit string."""
        return bin(self.value)[2:].zfill(2)


class CompressionType(Enum):
    """Compression type enumeration."""

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


class Chat:
    """Chat client for AX.25 packet radio networks."""

    def __init__(self: Chat, callsign: str) -> None:
        """Initialize the chat client.

        Args:
            callsign: The callsign to use for the chat client.
        """
        self.callsign: str = callsign
        self.colors: dict[str, str] = {}
        self.counter: int = 0
        self.exit: bool = False
        self.interface: AX25Interface
        self.pending_ack: dict[int, tuple[str, int, str, str, str]] = {}
        self.out_queue: list[AX25RawFrame] = []
        self.last_comm: datetime = datetime.now(timezone.utc)
        self.busy: bool = False
        self._load_colors()

    def _load_colors(self: Chat) -> None:
        """Load the colors from the colors.json file."""
        file = Path(__file__).parent / "colors.json"
        with file.open(encoding="utf-8") as f:
            self.colors = json.load(f)

    async def build_device(self: Chat) -> TCPKISSDevice:
        """Build the TCPKISSDevice."""
        device = make_device(
            type="tcp",
            host="localhost",
            port=8001,
            kiss_commands=[],
            log=LOGGER,
        )
        device.open()
        i = 1
        max_attempts = 4
        while device.state != KISSDeviceState.OPEN:
            msg = f"Waiting for direwolf connection... attempt {i}/{max_attempts}"
            print(msg, end="\r")  # noqa: T201
            if i > max_attempts:
                msg = "Cannot connect to direwolf. Is it running?"
                LOGGER.critical(msg)
                sys.exit(1)

            await asyncio.sleep(1)
            i += 1
        msg = f"Device: {device} opened"
        LOGGER.info(msg)
        return device

    def now(self: Chat) -> str:
        """Return the current time in the format: MM/DD/YY HH:MM:SS."""
        return datetime.now(timezone.utc).astimezone().strftime("%m/%d/%y %H:%M:%S")

    def line_print(  # noqa: PLR0913
        self: Chat,
        ts: str,
        indicator: str,
        source: str,
        dest: str,
        message: str,
    ) -> None:
        """Print a line to the terminal.

        Args:
            ts: The timestamp.
            indicator: The indicator.
            source: The source callsign.
            dest: The destination callsign.
            message: The message.
        """
        if indicator == "S":
            scolor = "grey"
            dcolor = "grey"
            mcolor = "grey"
        else:
            try:
                scolor = self.colors[source]
            except KeyError:
                scolor = "white"
            try:
                dcolor = self.colors[dest]
            except KeyError:
                dcolor = "white"

            try:
                mycolor = self.colors[self.callsign]
            except KeyError:
                mycolor = "white"

            mcolor = mycolor if source == self.callsign else scolor

        pre = f"<grey>{ts} {indicator}\u2502</grey>"
        source = f"<{scolor}>{source}</{scolor}>"
        dest = f"<{dcolor}>{dest}</{dcolor}>"
        message = f"<{mcolor}>{message}</{mcolor}>"
        print_formatted_text(HTML(f"{pre}{source}>{dest} {message}"))

    def rx_frame(self: Chat, interface: AX25Interface, frame: AX25RawFrame) -> None:
        """Receive a frame.

        Args:
            interface: The interface.
            frame: The frame.
        """
        self.last_comm = datetime.now(timezone.utc)
        msg = f"Received frame: {frame} on {interface}"
        LOGGER.debug(msg)
        info_byte = InfoByte.from_int(frame.frame_payload[0])
        msg_id = MsgId.from_bytes(frame.frame_payload[1:3])
        r_message = Message.from_bytes(frame.frame_payload[3:], info_byte.compression_type)
        source = str(frame.header.source).strip().replace("*", "")
        ts = self.now()

        msg = f"Received: {ts} {source}: '{r_message.string}'"
        LOGGER.info(msg)
        if info_byte.message_type == MessageType.MSG:
            self.line_print(ts, "R", source, self.callsign, r_message.string)
            payload = (
                InfoByte(MessageType.ACK, CompressionType.SMAZ).to_byte()
                + MsgId(msg_id.id).to_bytes()
                + Message(string="").to_bytes()
            )

            raw_frame = AX25RawFrame(
                destination=source,
                source=self.callsign,
                control=0,
                payload=payload,
            )
            self.out_queue.append(raw_frame)
            return
        if info_byte.message_type == MessageType.ACK:
            try:
                ts, counter, source, dest, s_message = self.pending_ack[msg_id.id]
            except KeyError:
                msg = f"Received ACK for unknown message ID: {msg_id.id}"
                LOGGER.error(msg)  # noqa: TRY400
                return
            self.line_print(ts, "A", source, dest, s_message)
            return

    async def send(self: Chat) -> None:
        """Send a message."""
        session: PromptSession = PromptSession()  # type: ignore[type-arg]
        while True:
            with patch_stdout():
                try:
                    line = await session.prompt_async("> ")
                except KeyboardInterrupt:
                    line = "/quit"
            print("\033[1A", end="\r")  # noqa: T201
            if line == "/quit":
                self.exit = True
                return
            if line == "/clear":
                os.system("clear")  # noqa: ASYNC102, S607, S605
                continue

            ts = self.now()
            try:
                dest, message = line.split(" ", 1)
            except ValueError:
                LOGGER.error("Invalid message format.")  # noqa: TRY400
                continue

            msg = f"Sending: {ts} {dest}: {message}"
            LOGGER.info(msg)
            payload = (
                InfoByte(MessageType.MSG, CompressionType.SMAZ).to_byte()
                + MsgId(self.counter).to_bytes()
                + Message(string=message, compress=CompressionType.SMAZ).to_bytes()
            )

            raw_frame = AX25RawFrame(
                destination=dest,
                source=self.callsign,
                control=0,
                payload=payload,
            )
            self.out_queue.append(raw_frame)

            msg = f"Sent AX25: {ts} {dest}: {message}"
            LOGGER.info(msg)
            self.pending_ack[self.counter] = (
                ts,
                self.counter,
                self.callsign,
                dest,
                message,
            )
            self.line_print(ts, "S", self.callsign, dest, message)
            self.counter += 1

    def tx_complete(self: Chat, interface: AX25Interface, frame: AX25RawFrame) -> None:
        """Transmit complete callback.

        Args:
            interface: The interface.
            frame: The frame.
        """
        msg = f"Transmit complete: {frame} on {interface}"
        LOGGER.debug(msg)
        self.last_comm = datetime.now(timezone.utc)
        self.busy = False

    async def process(self: Chat) -> None:
        """Process the interface."""
        device = await self.build_device()
        interface = AX25Interface(kissport=device[0], log=LOGGER)
        interface.bind(callback=self.rx_frame, callsign=self.callsign, ssid=0, regex=False)

        while True:
            if self.exit:
                return
            if len(self.out_queue) == 0:
                await asyncio.sleep(0.1)
                continue
            if self.busy:
                await asyncio.sleep(0.1)
                continue
            if (datetime.now(timezone.utc) - self.last_comm).seconds < TIME_BETWEEN_COMM:
                await asyncio.sleep(0.1)
                continue
            frame = self.out_queue.pop(0)
            interface.transmit(frame, callback=self.tx_complete)

    async def run(self: Chat) -> None:
        """Run the chat client."""
        async with asyncio.TaskGroup() as tg:
            _task2 = tg.create_task(self.send())
            _task3 = tg.create_task(self.process())


def main(callsign: str) -> None:
    """Run the chat client.

    Args:
        callsign: The callsign to use for the chat client.
    """
    os.system("clear")  # noqa: S607, S605
    chat = Chat(callsign=callsign)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(chat.run())
    loop.close()


if __name__ == "__main__":
    callsign = sys.argv[1]
    main(callsign=callsign)
