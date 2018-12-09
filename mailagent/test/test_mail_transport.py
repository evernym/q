import unittest
import helpers
import mail_transport

t = mail_transport.MailTransport()

class TransportTestCase(unittest.TestCase):

    def test_receive(self):
        # Right now, this only passes if the inbox isn't empty.
        pass #self.assertTrue(self.t.receive())

if __name__ == '__main__':
    unittest.main()
