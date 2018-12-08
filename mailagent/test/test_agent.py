import unittest, sys

# Tell python that code in the parent folder should be searched
# when processing import statementss
sys.path.append('..')
from agent import *

class AgentTestCase(unittest.TestCase):

    def setUp(self):
        self.agent = Agent()
    def tearDown(self):
        self.agent = None

    def test_fetch_message_with_empty_inbox_yields_None(self):
        self.assertTrue(self.agent.fetch_message() is None)

if __name__ == '__main__':
    unittest.main()
