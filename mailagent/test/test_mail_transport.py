import unittest
import helpers
import tempfile
import shutil

import mail_transport

class MockQueue:
    def pop(self):
        pass
    def push(self, bytes):
        pass

t = mail_transport.MailTransport(queue=MockQueue())

class QueueTestCase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory().name
        self.q = mail_transport.MailQueue(self.folder)
    def tearDown(self):
        shutil.rmtree(self.folder)
    def test_pop_empty(self):
        self.assertFalse(self.q.pop())
    def test_push1(self):
        self.q.push('hi'.encode('utf-8'))
        self.assertTrue(self.q.pop())
        self.assertFalse(self.q.pop())

class TransportTestCase(unittest.TestCase):

    def test_receive(self):
        # Right now, this only passes if the inbox isn't empty.
        pass #self.assertTrue(self.t.receive())

if __name__ == '__main__':
    unittest.main()
