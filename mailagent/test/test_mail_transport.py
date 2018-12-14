import unittest
import sys
import os

# Tell python that code in the parent folder should be searched
# when processing import statementss
sys.path.append('..')
from mailagent.mail_transport import *

class TransportTestCase(unittest.TestCase):

    def setUp(self):
        self.t = MailTransport()
    def tearDown(self):
        self.t = None

    def test_receive(self):
        # Right now, this only passes if the inbox isn't empty.
        self.assertTrue(self.t.receive())

if __name__ == '__main__':
    import logging
    logging.basicConfig(
        filename=os.path.basename(__file__) + '.log',
        format='%(asctime)s\t%(funcName)s@%(filename)s#%(lineno)s\t%(levelname)s\t%(message)s',
        level=logging.DEBUG)
    unittest.main()
