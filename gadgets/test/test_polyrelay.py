import os
import unittest
import tempfile
import threading
import time
import random
import http.server
import socketserver
import requests
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

class PolyRelayTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tempdir.cleanup()

    def run_relay_from_file(self, dests):
        src = self.tempdir.name
        th = threading.Thread(target=polyrelay.main, args=([src] + dests,
                Interrupter()))
        th.start()
        # If the relay is working properly, it will have created a src FileTransport
        # with folder_is_destward=False. This means it will expect to *read* messages
        # from its /a subdir. To write something there easily, create a new FileTransport
        # that has folder_is_destward=True. It will *write* to the /a subdir.
        fsrc = file_transport.FileTransport(src)
        fsrc.send("hello")
        # Now wait for the relay to process the message, get interrupted, and exit
        # its main loop.
        th.join()

    def relay_to_and_from_files(self, dest_count):
        destdirs = []
        dests = []
        for i in range(dest_count):
            x = tempfile.TemporaryDirectory()
            destdirs.append(x)
            dests.append(x.name)
        try:
            self.run_relay_from_file(dests)
            # Now we want to check whether the message has been written to each dest.
            # The dest FileTransport will have been created with folder_is_destward
            # =True. This means it will have written its message to the /a subdir.
            # We want to read from /a, so we'll now create a FileTransport with the
            # opposite setting. It will *read* from dest's /a.
            for dest in dests:
                fdest = file_transport.FileTransport(dest, folder_is_destward=False)
                self.assertEqual(fdest.receive().msg, b"hello")
        finally:
            for dd in destdirs:
                dd.cleanup()

    def test_to_and_from_file(self):
        self.relay_to_and_from_files(1)

    def test_tee(self):
        self.relay_to_and_from_files(3)

    def test_to_email_with_mock(self):
        with patch('smtp_sender.smtplib.SMTP', autospec=True) as p:
            self.run_relay_from_file(['smtp://user:pass@mail.my.org:234?from=sender@x.com&to=recipient@y.com'])
            # Guarantee that we exited normally and that we did in fact call
            # the SMTP object's quit() method.
            p.assert_has_calls([call().quit()])

    def test_to_http(self):
        port, thread = start_web_server_for_one_request()
        self.run_relay_from_file(["http://localhost:%d" % port])
        # Wait for up to 2 secs for a post to be processed by our mini web server.
        with post_body_signal:
            post_body_signal.wait_for(lambda: post_body_ready, timeout=2)
        global post_body
        self.assertEqual(post_body, b"hello")

    def test_from_http(self):
        dests = [self.tempdir.name]
        port = random.randint(10000,65000)
        src = "http://localhost:%d" % port
        th = threading.Thread(target=polyrelay.main, args=([src, self.tempdir.name], Interrupter()))
        th.start()
        r = requests.post(src, headers={'content-length':'5'}, data="hello")
        # Now wait for the relay to process the message, get interrupted, and exit
        # its main loop.
        th.join()
        # If the relay worked properly, it will have received the http post, and will
        # have created a dest FileTransport with folder_is_destward=True. This means
        # it wrote messages to its /a subdir. To read something there easily,
        # we create a new FileTransport that has folder_is_destward=False. It will
        # *read* from the /a subdir.
        f = file_transport.FileTransport(self.tempdir.name, folder_is_destward=False)
        f.receive("hello")
        self.assertEqual(f.receive().msg, b'hello')

if __name__ == '__main__':
    unittest.main()
