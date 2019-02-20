import os
import unittest
import tempfile

import helpers
from file_transport import FileTransport as FT

class TransportTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_receive_from_empty(self):
        x = FT(self.tempdir.name)
        self.assertFalse(x.receive())

    def test_receive_from_full(self):
        x = FT(self.tempdir.name)
        # Write something to the folder I'm about to read from.
        fpath = os.path.join(x.read_dir, 'x.msg')
        with open(fpath, 'wt') as f:
            f.write('hello')
        # First attempt to read should yield what I just wrote.
        self.assertTrue(x.receive())
        # Next fetch should yield None.
        self.assertFalse(x.receive())

    def test_request_response(self):
        requester = FT(self.tempdir.name)
        responder = FT(self.tempdir.name, folder_is_destward=False)
        id = requester.send('ping')
        # The requester should not see a response yet.
        self.assertFalse(requester.peek(id))
        # If the responder sends a response to an unrelated id,
        # the requester should still not see a response.
        responder.send('unrelated')
        self.assertFalse(requester.peek(id))
        responder.send('pong', id)
        self.assertTrue(requester.peek(id))
        mwc = requester.receive(id)
        self.assertEqual('pong', mwc.msg.decode('utf-8'))

    def test_send(self):
        requester = FT(self.tempdir.name)
        requester.send('hello')
        self.assertFalse(requester.receive())
        responder = FT(self.tempdir.name, folder_is_destward=False)
        mwc = responder.receive()
        self.assertEqual('hello', mwc.msg.decode('utf-8'))

if __name__ == '__main__':
    unittest.main()
