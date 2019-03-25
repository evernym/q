import os
import pytest
import tempfile
import threading
import time
import random
import http.server
import socketserver
import requests
import asyncio
from unittest.mock import MagicMock, patch, call

import helpers
import polyrelay
import file_transport

class Interrupter:
    def __init__(self, count=1, timeout=5):
        self.count = count
        self.expires = time.time() + timeout
    def __call__(self, msg):
        if msg:
            self.count -= 1
            if self.count < 1:
                return True
        if time.time() >= self.expires:
            return True

post_body_lock = threading.Lock()
post_body_signal = threading.Condition(post_body_lock)
post_body_ready = False
post_body = None

class TrivialWebHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        global post_body
        global post_body_signal
        clen = int(self.headers.get('Content-Length', 0))
        with post_body_signal:
            if clen:
                post_body = self.rfile.read(clen)
            else:
                post_body = ''
            self.send_response(202)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write("202 OK".encode("utf-8"))
            post_body_signal.notify_all()

def start_web_server_for_one_request():
    global post_body_lock
    global post_body_ready
    global post_body
    with post_body_lock:
        post_body = None
        post_body_ready = False
    port = random.randint(10000, 65000)
    def run_web_server():
        with socketserver.TCPServer(("", port), TrivialWebHandler) as httpd:
            try:
                httpd.timeout = 3 #seconds
                httpd.handle_request()
            finally:
                httpd.socket.close()
    thread = threading.Thread(target=run_web_server)
    thread.start()
    return (port, thread)

@pytest.fixture()
def scratch_space():
    x = tempfile.TemporaryDirectory()
    yield x
    x.cleanup()

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
            assert x.msg == b"hello"
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
    with patch('smtp_sender.smtplib.SMTP', autospec=True) as p:
        await run_relay_from_file(scratch_space,
            ['smtp://user:pass@mail.my.org:234?from=sender@x.com&to=recipient@y.com'])
        # Guarantee that we exited normally and that we did in fact call
        # the SMTP object's quit() method.
        p.assert_has_calls([call().quit()])

#@pytest.mark.asyncio
async def txest_to_http(scratch_space):
    port, thread = start_web_server_for_one_request()
    await run_relay_from_file(scratch_space, ["http://localhost:%d" % port])
    # Wait for up to 2 secs for a post to be processed by our mini web server.
    with post_body_signal:
        post_body_signal.wait_for(lambda: post_body_ready, timeout=2)
    global post_body
    assert post_body == b"hello"

#@pytest.mark.asyncio
async def txest_from_http(scratch_space):
    dests = [scratch_space.name]
    port = random.randint(10000,65000)
    src = "http://localhost:%d" % port
    main = asyncio.create_task(polyrelay.main([src, scratch_space.name], Interrupter()))
    r = requests.post(src, headers={'content-length':'5'}, data="hello")
    # Now wait for the relay to process the message, get interrupted, and exit
    # its main loop.
    await main
    # If the relay worked properly, it will have received the http post, and will
    # have created a dest FileTransport with folder_is_destward=True. This means
    # it wrote messages to its /a subdir. To read something there easily,
    # we create a new FileTransport that has folder_is_destward=False. It will
    # *read* from the /a subdir.
    f = file_transport.FileTransport(scratch_space.name, folder_is_destward=False)
    x = await f.receive("hello")
    assert x.msg == b'hello'
