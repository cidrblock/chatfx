"""Example using zmq with asyncio coroutines"""
# Copyright (c) PyZMQ Developers.
# This example is in the public domain (CC-0)

import asyncio
import time

import zmq
from zmq.asyncio import Context, Poller

url = 'tcp://127.0.0.1:5555'

ctx = Context.instance()


async def ping() -> None:
    """print dots to indicate idleness"""
    while True:
        await asyncio.sleep(0.5)
        print('.')

async def sender():
    # MARK
    context = zmq.asyncio.Context()
    pub = context.socket(zmq.PUB)
    pub.bind(url)

    while True:
        print('> before send_multipart')
        await pub.send_multipart([
            b'test',
            b'test'
        ])
        print('> after send_multipart')
        await asyncio.sleep(1)


async def main():
    asyncio.create_task(ping())
    asyncio.create_task(sender())

    while True:
        await asyncio.sleep(1)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

loop.run_until_complete(main())
