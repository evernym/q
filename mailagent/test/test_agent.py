import unittest

import helpers
import agent
import mwc
import protocols.trust_ping.handler as h

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

    def test_ping_response(self):
        wc = mwc.MessageWithContext('{"@type": "%s", "@id": "x"}' % h.PING_MSG_TYPE)
        self.assertTrue(a.process_message(wc))
        self.assertTrue(t.squeue)
        to_send = t.squeue.pop(0)[0]
        for item in ['@thread', '@timing', 'in_time', 'out_time', 'thid']:
            self.assertTrue(to_send.index(item) > -1)

    def test_ping_no_response(self):
        wc = mwc.MessageWithContext('{"@type": "%s", "response_requested": false}' % h.PING_MSG_TYPE)
        # We should claim message is handled
        self.assertTrue(a.process_message(wc))
        # We shouldn't have anything to send, since we were asked not to respond.
        self.assertFalse(t.squeue)

if __name__ == '__main__':
    unittest.main()
