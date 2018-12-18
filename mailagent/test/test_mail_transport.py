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

def _get_sample_email(which):
    fname = os.path.join(data_files_folder, which + '.email')
    with open(fname, 'rb') as f:
        return f.read()

def _get_sample_email_tweaked(which, search_for, replace_with):
    return _get_sample_email(which).decode('utf-8').replace(search_for, replace_with).encode('utf-8')

def _get_a2a_from_sample_email(which):
    raw = _get_sample_email(which)
    return mail_transport.MailTransport.bytes_to_a2a_message(raw)

class TransportTest(unittest.TestCase):

    def test_bytes_to_a2a_ap_body(self):
        wc =_get_a2a_from_sample_email('ap_body')
        self.assertTrue(wc.msg)
        self.assertEqual('fred@flintstones.org', wc.sender)
        self.assertFalse(wc.tc)

    def test_bytes_to_a2a_jwt_attached(self):
        raw = _get_sample_email_tweaked('aw_attached', 'tiny.aw', 'tiny.jwt')
        wc = mail_transport.MailTransport.bytes_to_a2a_message(raw)
        self.assertTrue(wc.msg)
        self.assertTrue('confidentiality, integrity' in str(wc.tc))

    def test_bytes_to_a2a_aw_attached(self):
        wc =_get_a2a_from_sample_email('aw_attached')
        self.assertTrue(wc.msg)
        self.assertTrue('confidentiality, integrity' in str(wc.tc))

    def test_bytes_to_a2a_ap_attached(self):
        wc =_get_a2a_from_sample_email('ap_attached')
        self.assertTrue(wc.msg)
        self.assertFalse(wc.tc)

    def test_bytes_to_a2a_json_attached(self):
        raw = _get_sample_email_tweaked('ap_attached', 'sample.ap', 'sample.json')
        wc =mail_transport.MailTransport.bytes_to_a2a_message(raw)
        self.assertTrue(wc.msg)
        self.assertFalse(wc.tc)

    def test_receive_from_local_queue(self):
        t.queue.push(_get_sample_email('ap_body'))
        self.assertTrue(t.receive())

    def test_receive_over_imap(self):
        # Right now, this only passes if the inbox isn't empty.
        pass #self.assertTrue(t.receive())

    def test_send(self):
        # Right now, this only passes if we have an internet connection.
        pass #t.send('this is a test', 'daniel.hardman@gmail.com')

if __name__ == '__main__':
    unittest.main()
