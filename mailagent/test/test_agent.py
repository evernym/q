import unittest
import helpers
import agent
import fake_transport

t = fake_transport.FakeTransport()
a = agent.Agent(transport=t)

class AgentTestCase(unittest.TestCase):

    def setUp(self):
        t.queue = []

    def test_fetch_with_empty_inbox(self):
        self.assertFalse(a.fetch_message())

    def test_fetch_one_message(self):
        t.push('hello')
        self.assertTrue(a.fetch_message())

if __name__ == '__main__':
    unittest.main()
