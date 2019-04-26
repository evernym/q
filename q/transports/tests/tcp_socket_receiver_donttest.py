import asyncio
import pytest

from ..tcp_socket_receiver import Receiver

@pytest.mark.asyncio
async def test_tcp_socket_receiver():

    async with Receiver() as r:
        print("Listening on port %d" % r.port)
        while True:
            data = await r.receive()
            if data:
                print(data)
            await asyncio.sleep(1)
