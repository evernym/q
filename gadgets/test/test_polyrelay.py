import os
import unittest
import tempfile
import threading
import time
import random

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

if __name__ == '__main__':
    unittest.main()
