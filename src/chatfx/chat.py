"""The chat client and server."""

from __future__ import annotations

import asyncio
import os
import sys

from datetime import datetime
from datetime import timezone
from typing import TYPE_CHECKING

from aioax25.frame import AX25RawFrame
from aioax25.interface import AX25Interface
from aioax25.kiss import KISSDeviceState
from aioax25.kiss import TCPKISSDevice
from aioax25.kiss import make_device
from prompt_toolkit import HTML
from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout

from .definitions import CompressionType
from .definitions import Config
from .definitions import InfoByte
from .definitions import Message
from .definitions import MessageType
from .definitions import MsgId
from .utils import get_color


if TYPE_CHECKING:
    from .output import Output

class Chat:
    """Chat client for AX.25 packet radio networks."""

    def __init__(
        self: Chat,
        config: Config,
        output: Output,
    ) -> None:
        """Initialize the chat client.

        Args:
            callsign: The callsign to use for the chat client.
        """
        self.busy: bool = False
        self.config: Config = config
        self.counter: int = 0
        self.device: TCPKISSDevice
        self.exit: bool = False
        self.interface: AX25Interface
        self.last_comm: datetime = datetime.now(timezone.utc)
        self.out_queue: list[AX25RawFrame] = []
        self.output = output
        self.pending_ack: dict[int, tuple[str, int, str, str, str]] = {}

    async def build_device(self: Chat) -> TCPKISSDevice:
        """Build the TCPKISSDevice."""
        self.device = make_device(
            type="tcp",
            host=self.config.host,
            port=self.config.port,
            kiss_commands=[],
        )
        self.device.open()
        await asyncio.sleep(0.1)
        i = 1
        max_attempts = 4
        while self.device.state != KISSDeviceState.OPEN:
            msg = f"Waiting for direwolf connection... attempt {i}/{max_attempts}"
            print(msg, end="\r")  # noqa: T201
            if i > max_attempts:
                msg = "Cannot connect to direwolf. Is it running?"
                self.output.critical(msg)
                sys.exit(1)

            await asyncio.sleep(1)
            i += 1
        msg = f"Device: {self.device} opened"
        self.output.info(msg)

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
            scolor = get_color(self.config.colors, source)
            dcolor = get_color(self.config.colors, dest)
            mycolor = get_color(self.config.colors, self.config.callsign)
            mcolor = mycolor if source == self.config.callsign else scolor

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
        self.output.debug(msg)
        info_byte = InfoByte.from_int(frame.frame_payload[0])
        msg_id = MsgId.from_bytes(frame.frame_payload[1:3])
        r_message = Message.from_bytes(frame.frame_payload[3:], info_byte.compression_type)
        source = str(frame.header.source).strip().replace("*", "")
        ts = self.now()

        msg = f"Received: {ts} {source}: '{r_message.string}'"
        self.output.info(msg)
        if info_byte.message_type == MessageType.MSG:
            self.line_print(ts, "R", source, self.config.callsign, r_message.string)
            payload = (
                InfoByte(MessageType.ACK, CompressionType.SMAZ).to_byte()
                + MsgId(msg_id.id).to_bytes()
                + Message(string="").to_bytes()
            )

            raw_frame = AX25RawFrame(
                destination=source,
                source=self.config.callsign,
                control=0,
                payload=payload,
            )
            self.out_queue.append(raw_frame)
            return
        if info_byte.message_type == MessageType.ACK:
            try:
                ts, _counter, source, dest, s_message = self.pending_ack[msg_id.id]
            except KeyError:
                msg = f"Received ACK for unknown message ID: {msg_id.id}"
                self.output.error(msg)
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
                self.output.error("Invalid message format.")
                self.output.hint("Try: <destination callsign> <message>")
                continue

            msg = f"Sending: {ts} {dest}: {message}"
            self.output.info(msg)
            payload = (
                InfoByte(MessageType.MSG, CompressionType.SMAZ).to_byte()
                + MsgId(self.counter).to_bytes()
                + Message(string=message, compress=CompressionType.SMAZ).to_bytes()
            )

            raw_frame = AX25RawFrame(
                destination=dest,
                source=self.config.callsign,
                control=0,
                payload=payload,
            )
            self.out_queue.append(raw_frame)

            msg = f"Sent AX25: {ts} {dest}: {message}"
            self.output.info(msg)
            self.pending_ack[self.counter] = (
                ts,
                self.counter,
                self.config.callsign,
                dest,
                message,
            )
            self.line_print(ts, "S", self.config.callsign, dest, message)
            self.counter += 1

    def tx_complete(self: Chat, interface: AX25Interface, frame: AX25RawFrame) -> None:
        """Transmit complete callback.

        Args:
            interface: The interface.
            frame: The frame.
        """
        msg = f"Transmit complete: {frame} on {interface}"
        self.output.debug(msg)
        self.last_comm = datetime.now(timezone.utc)
        self.busy = False

    async def process(self: Chat) -> None:
        """Process the interface."""
        interface = AX25Interface(
            kissport=self.device[0],
            log=self.output.logger,
        )
        interface.bind(
            callback=self.rx_frame,
            callsign=self.config.callsign,
            ssid=0,
            regex=False,
        )

        while True:
            if self.exit:
                return
            if len(self.out_queue) == 0:
                await asyncio.sleep(0.1)
                continue
            if self.busy:
                await asyncio.sleep(0.1)
                continue
            if (datetime.now(timezone.utc) - self.last_comm).seconds < self.config.time_delay:
                await asyncio.sleep(0.1)
                continue
            frame = self.out_queue.pop(0)
            interface.transmit(frame, callback=self.tx_complete)

    async def run(self: Chat) -> None:
        """Run the chat client."""
        async with asyncio.TaskGroup() as tg:
            _task2 = tg.create_task(self.send())
            _task3 = tg.create_task(self.process())
