import unittest

import helpers
import agent
import mwc
import protocols

class FakeTransport:
    def __init__(self):
        self.rqueue = []
        self.squeue = []
    def push(self, msg):
        self.rqueue.append(msg)
    def pop(self):
        if self.rqueue:
            return self.rqueue.pop(0)
    def send(self, payload, destination):
        self.squeue.append((payload, destination))
    def receive(self):
        return self.pop()

t = FakeTransport()
a = agent.Agent(transport=t)

class AgentTest(unittest.TestCase):

    def setUp(self):
        t.rqueue = []
        t.squeue = []

    def test_fetch_with_empty_inbox(self):
        self.assertFalse(a.fetch_message())

    def test_fetch_one_message(self):
        t.push('hello')
        self.assertTrue(a.fetch_message())

    def test_process_one_message(self):
        wc = mwc.MessageWithContext('{"@type": "ping"}')
        a.process_message(wc)
        self.assertTrue(t.squeue)

if __name__ == '__main__':
    unittest.main()
