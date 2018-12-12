import unittest

import helpers
import agent
import mwc
import plugins
from protocols.trust_ping import tp_handler
from protocols.tictactoe import ttt_handler

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

    def check_req_resp(self, req_msg):
        wc = mwc.MessageWithContext(req_msg)
        self.assertTrue(a.handle_msg(wc))
        self.assertTrue(t.squeue)
        return t.squeue.pop(0)[0]

    def test_fetch_with_empty_inbox(self):
        self.assertFalse(a.fetch_msg())

    def test_fetch_one_message(self):
        t.push('hello')
        self.assertTrue(a.fetch_msg())

    def test_ping_response(self):
        response = self.check_req_resp('{"@type": "%s", "@id": "x"}' % tp_handler.PING_MSG_TYPE)
        for item in ['@thread', '@timing', 'in_time', 'out_time', 'thid']:
            self.assertTrue(response.index(item) > -1)

    def test_ping_no_response(self):
        wc = mwc.MessageWithContext('{"@type": "%s", "response_requested": false}' % tp_handler.PING_MSG_TYPE)
        # We should claim message is handled
        self.assertTrue(a.handle_msg(wc))
        # We shouldn't have anything to send, since we were asked not to respond.
        self.assertFalse(t.squeue)

    def test_initial_ttt_move(self):
        response = self.check_req_resp(ttt_handler.MOVE_MSG_TEMPLATE % "fakeid")


if __name__ == '__main__':
    unittest.main()
