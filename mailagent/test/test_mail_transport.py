import os
import unittest
import tempfile

import helpers
import mail_transport

class MockQueue:
    def __init__(self):
        self.q = []
    def pop(self):
        if self.q:
            return self.q.pop(0)
    def push(self, bytes):
        self.q.append(bytes)

t = mail_transport.MailTransport(queue=MockQueue())
data_files_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_files')

class QueueTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.q = mail_transport.MailQueue(self.tempdir.name)
    def tearDown(self):
        self.tempdir.cleanup()
    def test_pop_empty(self):
        self.assertFalse(self.q.pop())
    def test_push1(self):
        self.q.push('hi'.encode('utf-8'))
        self.assertTrue(self.q.pop())
        self.assertFalse(self.q.pop())

class TransportTest(unittest.TestCase):

    def test_bytes_to_a2a_ap_body(self):
        fname = os.path.join(data_files_folder, 'ap_body.email')
        with open(fname, 'rb') as f:
            raw = f.read()
        mwet = mail_transport.MailTransport.bytes_to_a2a_message(raw)
        self.assertTrue(mwet.msg)
        self.assertFalse(mwet.tc)

    def test_receive_from_local_queue(self):
        fname = os.path.join(data_files_folder, 'ap_body.email')
        with open(fname, 'rb') as f:
            t.queue.push(f.read())
        self.assertTrue(t.receive())

    def test_receive_over_imap(self):
        # Right now, this only passes if the inbox isn't empty.
        pass #self.assertTrue(t.receive())

if __name__ == '__main__':
    unittest.main()
