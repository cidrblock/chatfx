"""Example using zmq with asyncio coroutines"""
# Copyright (c) PyZMQ Developers.
# This example is in the public domain (CC-0)

import asyncio
import time

import zmq
from zmq.asyncio import Context, Poller

url = 'tcp://127.0.0.1:5555'

ctx = Context.instance()

async def receiver():
    # MARK
    context = zmq.asyncio.Context()
    sub = context.socket(zmq.SUB)
    sub.connect(url)
    sub.setsockopt_string(zmq.SUBSCRIBE, '')

    while True:
        print('> before recv_multipart')
        a, b = await sub.recv_multipart()
        print('> after recv_multipart:', a, b)
        await asyncio.sleep(1)


async def main():
    asyncio.create_task(receiver())
    while True:
        await asyncio.sleep(1)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

loop.run_until_complete(main())
