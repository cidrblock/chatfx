"""The chat client and server."""

from __future__ import annotations

import asyncio
import sys

from datetime import datetime
from datetime import timezone
from typing import TYPE_CHECKING
from typing import Callable

from aioax25.frame import AX25UnnumberedInformationFrame
from aioax25.interface import AX25Interface
from aioax25.kiss import KISSDeviceState
from aioax25.kiss import TCPKISSDevice
from aioax25.kiss import make_device

from chatfx.definitions import CompressionType
from chatfx.definitions import Config
from chatfx.definitions import FormattedMsg
from chatfx.definitions import FormattedText
from chatfx.definitions import InfoByte
from chatfx.definitions import Message
from chatfx.definitions import MessageType
from chatfx.definitions import MsgId


if TYPE_CHECKING:
    from .output import Output


class Chat:
    """Chat client for AX.25 packet radio networks."""

    def __init__(
        self: Chat,
        config: Config,
        output: Output,
        ui_output: list[FormattedMsg | FormattedText],
        ui_refresh: Callable[[], None],
    ) -> None:
        """Initialize the chat client.

        Args:
            callsign: The callsign to use for the chat client.
        """
        self.config: Config = config
        self.counter: int = 0
        self.device: TCPKISSDevice
        self.exit: bool = False
        self.interface: AX25Interface
        self.out_queue: list[AX25UnnumberedInformationFrame] = []
        self.output = output
        self.ui_output = ui_output
        self.ui_refresh = ui_refresh

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
        return datetime.now(timezone.utc).astimezone()

    def rx_frame(
        self: Chat,
        interface: AX25Interface,
        frame: AX25UnnumberedInformationFrame,
    ) -> None:
        """Receive a frame.

        Args:
            interface: The interface.
            frame: The frame.
        """
        msg = f"Received frame: {frame} on {interface}"
        self.output.debug(msg)
        info_byte = InfoByte.from_int(frame.frame_payload[1])
        msg_id = MsgId.from_bytes(frame.frame_payload[2:4])
        r_message = Message.from_bytes(frame.frame_payload[4:], info_byte.compression_type)
        source = str(frame.header.source).strip().replace("*", "")
        ts = self.now()

        msg = f"Received: {ts} {source}: '{r_message.string}'"
        self.output.info(msg)
        if info_byte.message_type == MessageType.MSG:
            fmsg = FormattedMsg(
                colors=self.config.colors,
                counter=msg_id.id,
                timestamp=ts,
                indicator="R",
                source=source,
                destination=self.config.callsign,
                message=r_message.string,
            )
            self.ui_output.append(fmsg)
            self.ui_refresh()
            payload = (
                InfoByte(MessageType.ACK, CompressionType.SMAZ).to_byte()
                + MsgId(msg_id.id).to_bytes()
                + Message(string="").to_bytes()
            )

            raw_frame = AX25UnnumberedInformationFrame(
                destination=source,
                source=self.config.callsign,
                payload=payload,
                pid=0xF0,
            )
            self.output.debug(f"ACKing message ID: {msg_id.id} from {source}")
            self.out_queue.append(raw_frame)
            return
        if info_byte.message_type == MessageType.ACK:
            found = [
                idx
                for idx, x in enumerate(self.ui_output)
                if isinstance(x, FormattedMsg)
                and x.counter == msg_id.id
                and x.source == self.config.callsign
            ]
            if len(found) == 0:
                msg = f"Received ACK for unknown message ID: {msg_id.id}"
                self.output.error(msg)
                return
            if len(found) > 1:
                msg = f"Received ACK for message ID: {msg_id.id} multiple times"
                self.output.error(msg)
                return
            self.ui_output[found[0]].indicator = "A"
            self.ui_refresh()
            return

    async def send(self: Chat, line: str) -> None:
        """Send a message."""
        ts = self.now()
        try:
            dest, message = line.split(" ", 1)
        except ValueError:
            self.output.error("Invalid message format.")
            self.output.hint("Try: <destination callsign> <message>")
            return
        if not message:
            self.output.error("Message cannot be empty.")
            return

        msg = f"Sending: {ts} {dest}: {message}"
        self.output.info(msg)
        payload = (
            InfoByte(MessageType.MSG, CompressionType.SMAZ).to_byte()
            + MsgId(self.counter).to_bytes()
            + Message(string=message, compress=CompressionType.SMAZ).to_bytes()
        )
        self.output.debug(f"Payload length: {len(payload)} bytes")

        raw_frame = AX25UnnumberedInformationFrame(
            destination=dest,
            source=self.config.callsign,
            payload=payload,
            pid=0xF0,
        )
        self.out_queue.append(raw_frame)

        msg = f"Sent AX25: {ts} {dest}: {message}"
        self.output.info(msg)
        fmsg = FormattedMsg(
            colors=self.config.colors,
            counter=self.counter,
            timestamp=ts,
            indicator="S",
            source=self.config.callsign,
            destination=dest,
            message=message,
        )
        self.output.ui_output.append(fmsg)
        self.output.ui_refresh()
        self.counter += 1

    def tx_complete(
        self: Chat,
        interface: AX25Interface,
        frame: AX25UnnumberedInformationFrame,
    ) -> None:
        """Transmit complete callback.

        Args:
            interface: The interface.
            frame: The frame.
        """
        msg = f"Transmit complete: {frame} on {interface}"
        self.output.debug(msg)

    async def process(self: Chat) -> None:
        """Process the interface."""
        interface = AX25Interface(
            kissport=self.device[0],
            log=self.output.logger,
            cts_delay=self.config.time_delay,
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
            frame = self.out_queue.pop(0)
            interface.transmit(frame, callback=self.tx_complete)

    async def run(self: Chat) -> None:
        """Run the chat client."""
        await self.process()
