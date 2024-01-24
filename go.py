
import logging

from asyncio import get_event_loop, sleep

from aioax25 import kiss

from aioax25.kiss import make_device
from aioax25.interface import AX25Interface
from aioax25.frame import AX25RawFrame


LOGGER = logging.basicConfig(level=logging.DEBUG)


def xmit_cb(*args, **kwargs):
    print('xmit_cb', args, kwargs)


def rx_frame(interface, frame):
    print(frame.frame_payload)

async def test_open_connection():
    try:
        device = make_device(
            type='tcp', host='localhost', port=8001, kiss_commands=[],
            log=LOGGER
        )
        device.open()


        raw_frame = AX25RawFrame(
            destination='ABCDEF',
            source='ABCDEF',
            control=0,
            payload=b'This is a test'
        )


        ax25int = AX25Interface(
            kissport=device[0],     # or whatever port number you need
            log=LOGGER   
        )
        ax25int.bind(callback=rx_frame, callsign='ABCDEF', ssid=0, regex=False)
        ax25int.transmit(raw_frame, xmit_cb)

        while True:
            await sleep(1)

    finally:
        pass
        # Restore mock

def main():
    loop = get_event_loop()
    loop.run_until_complete(test_open_connection())
    loop.close()

main()
