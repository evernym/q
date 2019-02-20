import os
import unittest
import tempfile
import threading
import time
import random
import http.server
import socketserver

import helpers
import polyrelay
import file_transport

class MessageCountdown:
    def __init__(self, count=1):
        self.count = count
    def __call__(self, msg):
        if msg:
            self.count -= 1
            if self.count < 1:
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

    def relay_to_and_from_files(self, dest_count):
        src = self.tempdir.name
        destdirs = []
        dests = []
        for i in range(dest_count):
            x = tempfile.TemporaryDirectory()
            destdirs.append(x)
            dests.append(x.name)
        try:
            interrupt_after_one_message = MessageCountdown()
            th = threading.Thread(target=polyrelay.main, args=([src] + dests, interrupt_after_one_message))
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

    def test_to_http(self):
        port, thread = start_web_server_for_one_request()
        src = self.tempdir.name
        interrupt_after_one_message = MessageCountdown()
        relay_thread = threading.Thread(target=polyrelay.main,
                                        args=([src, "http://localhost:%d" % port], interrupt_after_one_message))
        relay_thread.start()
        # Send a message to the relay.
        fsrc = file_transport.FileTransport(src)
        fsrc.send("hello")
        # Now wait for the relay to process the message, get interrupted, and exit
        # its main loop.
        relay_thread.join()
        # Wait for up to 2 secs for a post to be processed by our mini web server.
        with post_body_signal:
            post_body_signal.wait_for(lambda: post_body_ready, timeout=2)
        global post_body
        self.assertEqual(post_body, b"hello")

if __name__ == '__main__':
    unittest.main()
