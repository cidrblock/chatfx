import asyncio
import json
import logging
import os
import sys
import time

from asyncio import sleep
from datetime import datetime
from pathlib import Path

from aioax25.frame import AX25RawFrame
from aioax25.interface import AX25Interface
from aioax25.kiss import make_device
from prompt_toolkit import HTML
from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout

from definitions import CompressionType
from definitions import InfoByte
from definitions import Message
from definitions import MessageType
from definitions import MsgId


LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.ERROR)


class Chat:
    def __init__(self, callsign: str):
        self.device = None
        self.interface = None
        self.callsign = callsign
        self.exit = False
        self.counter = 0
        self.pending_ack = {}
        self.colors = {}
        self._load_colors()

    def _load_colors(self):
        file = Path(__file__).parent / "colors.json"
        with open(file) as f:
            self.colors = json.load(f)

    def build_device(self):
        self.device = make_device(
            type="tcp",
            host="localhost",
            port=8001,
            kiss_commands=[],
            log=LOGGER,
        )
        self.device.open()
        LOGGER.info(f"Device: {self.device} opened")

    def build_interface(self):
        self.interface = AX25Interface(kissport=self.device[0], log=LOGGER)
        LOGGER.info(f"Interface: {self.interface} created")

    def now(self):
        return datetime.now().strftime("%m/%d/%y %H:%M:%S")

    def line_print(self, ts, indicator, source, dest, message):
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

            if source == self.callsign:
                mcolor = mycolor
            else:
                mcolor = scolor

        pre = f"<grey>{ts} {indicator}\u2502</grey>"
        source = f"<{scolor}>{source}</{scolor}>"
        dest = f"<{dcolor}>{dest}</{dcolor}>"
        message = f"<{mcolor}>{message}</{mcolor}>"
        print_formatted_text(HTML(f"{pre}{source}>{dest} {message}"))

    def rx_frame(self, interface, frame):  # pylint: disable=unused-argument
        info_byte = InfoByte.from_int(frame.frame_payload[0])
        msg_id = MsgId.from_bytes(frame.frame_payload[1:3])
        message = Message.from_bytes(frame.frame_payload[3:], info_byte.compression_type)
        message = message.string
        source = str(frame.header.source).strip().replace("*", "")
        ts = self.now()

        LOGGER.info(f"Received: {ts} {source}: '{message}'")
        if info_byte.message_type == MessageType.MSG:
            self.line_print(ts, "R", source, self.callsign, message)
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
            time.sleep(5.0)
            self.interface.transmit(raw_frame, self.xmit_cb)
            LOGGER.info(f"Sent AX25 ACK: {raw_frame}")
            return
        if info_byte.message_type == MessageType.ACK:
            try:
                ts, counter, source, dest, message = self.pending_ack[msg_id.id]
            except KeyError:
                print("Invalid ACK received.")
                return
            self.line_print(ts, "A", source, dest, message)
            return

    def xmit_cb(self, *args, **kwargs):
        pass

    async def send(self):
        session = PromptSession()
        while True:
            with patch_stdout():
                line = await session.prompt_async("> ")
            print("\033[1A", end="\r")
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
                print("Invalid message format.")
                continue
            LOGGER.info(f"Sending: {ts} {dest}: {message}")
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
            self.interface.transmit(raw_frame, self.xmit_cb)
            LOGGER.info(f"Sent AX25: {raw_frame}")
            self.pending_ack[self.counter] = (
                ts,
                self.counter,
                self.callsign,
                dest,
                message,
            )
            self.line_print(ts, "S", self.callsign, dest, message)
            self.counter += 1

    async def receive(self):
        self.interface.bind(callback=self.rx_frame, callsign=self.callsign, ssid=0, regex=False)
        LOGGER.info(f"Interface: {self.interface} bound to callback")
        while True:
            if self.exit:
                return
            await sleep(1)

    async def run(self):
        self.build_device()
        self.build_interface()
        async with asyncio.TaskGroup() as tg:
            _task1 = tg.create_task(self.receive())
            _task2 = tg.create_task(self.send())


def main(callsign: str):
    os.system("clear")  # noqa: ASYNC102, S607, S605
    chat = Chat(callsign=callsign)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(chat.run())
    loop.close()


if __name__ == "__main__":
    callsign = sys.argv[1]
    main(callsign=callsign)
