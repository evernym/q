import pytest
import tempfile
import time
import random
import asyncio

import aiohttp
from aiohttp import web
from unittest.mock import patch, call

from .. import polyrelay
from ...transports import file_transport
from ...transports import smtp_sender


class Interrupter:
    def __init__(self, count=1, timeout=3):
        self.count = count
        self.expires = time.time() + timeout
    def __call__(self, msg):
        if msg:
            self.count -= 1
            if self.count < 1:
                return True
        if time.time() >= self.expires:
            return True


post_body_signal = asyncio.Event()
post_body = None


async def accept_post(request):
    global post_body
    global post_body_signal
    data = await request.content.read()
    post_body = data
    resp = web.Response(text="202 OK", headers={"Content-Type": "text/plain"})
    resp.set_status(202)
    post_body_signal.set()
    return resp


@pytest.fixture
def scratch_space():
    x = tempfile.TemporaryDirectory()
    yield x
    x.cleanup()


@pytest.fixture
async def web_server_port():
    post_body = None
    post_body_signal.clear()
    app = web.Application()
    app.add_routes([web.post('/', accept_post)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = random.randint(10000, 65000)
    site = web.TCPSite(runner, 'localhost', port)
    await site.start()
    yield port
    await runner.cleanup()


async def run_relay_from_file(scratch_space, dests):
    src = scratch_space.name
    main = asyncio.create_task(polyrelay.main([src] + dests, Interrupter()))
    # If the relay is working properly, it will have created a src FileTransport
    # with folder_is_destward=False. This means it will expect to *read* messages
    # from its /a subdir. To write something there easily, create a new FileTransport
    # that has folder_is_destward=True. It will *write* to the /a subdir.
    fsrc = file_transport.FileTransport(src)
    await fsrc.send("hello")
    # Now wait for the relay to process the message, get interrupted, and exit
    # its main loop.
    await main


async def relay_to_and_from_files(scratch_space, dest_count):
    destdirs = []
    dests = []
    for i in range(dest_count):
        x = tempfile.TemporaryDirectory()
        destdirs.append(x)
        dests.append(x.name)
    try:
        await run_relay_from_file(scratch_space, dests)
        # Now we want to check whether the message has been written to each dest.
        # The dest FileTransport will have been created with folder_is_destward
        # =True. This means it will have written its message to the /a subdir.
        # We want to read from /a, so we'll now create a FileTransport with the
        # opposite setting. It will *read* from dest's /a.
        for dest in dests:
            fdest = file_transport.FileTransport(dest, folder_is_destward=False)
            x = await fdest.receive()
            assert x is not None
            assert x.raw == "hello"
    finally:
        for dd in destdirs:
            dd.cleanup()


@pytest.mark.asyncio
async def test_to_and_from_file(scratch_space):
    await relay_to_and_from_files(scratch_space, 1)


@pytest.mark.asyncio
async def test_tee(scratch_space):
    await relay_to_and_from_files(scratch_space, 3)


@pytest.mark.asyncio
async def test_to_email_with_mock(scratch_space):
    with patch(__name__ + '.smtp_sender.smtplib.SMTP', autospec=True) as p:
        await run_relay_from_file(scratch_space,
            ['smtp://user:pass@mail.my.org:234?from=sender@x.com&to=recipient@y.com'])
        # Guarantee that we exited normally and that we did in fact call
        # the SMTP object's quit() method.
        p.assert_has_calls([call().quit()])


@pytest.mark.asyncio
async def test_to_http(scratch_space, web_server_port):
    await run_relay_from_file(scratch_space, ["http://localhost:%d" % web_server_port])
    global post_body
    assert post_body == b"hello"


@pytest.mark.asyncio
async def test_from_http(scratch_space):
    dests = [scratch_space.name]
    # Start an inbound http relay
    port = random.randint(10000,65000)
    src = "http://localhost:%d" % port
    main = asyncio.create_task(polyrelay.main([src, scratch_space.name], Interrupter()))
    # Give web server a chance to start up. (This isn't strictly
    # necessary, but it makes the order of logged events a little
    # easier to understand.)
    await asyncio.sleep(0.25)
    # POST to the relay
    async with aiohttp.ClientSession() as session:
        async with session.post(src, data="hello") as resp:
            x = await resp.text()
    # Now wait for the relay to process the message, get interrupted, and exit
    # its main loop.
    await main
    # If the relay worked properly, it will have received the http post, and will
    # have created a dest FileTransport with folder_is_destward=True. This means
    # it wrote messages to its /a subdir. To read something there easily,
    # we create a new FileTransport that has folder_is_destward=False. It will
    # *read* from the /a subdir.
    f = file_transport.FileTransport(scratch_space.name, folder_is_destward=False)
    x = await f.receive()
    assert x.raw == 'hello'


if __name__ == '__main__':
    asyncio.get_event_loop().set_debug(True)
    pytest.main([__file__])