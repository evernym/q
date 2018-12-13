import unittest
import json
import re

import helpers
import agent
import mwc
import handlers
import tp_handler
import ttt_handler

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

    def check_json(self, json_txt, *regexes):
        # Prove it is valid json.
        obj = json.loads(json_txt)
        # Prove that it contains the specified strings.
        missing = []
        for item in regexes:
            pat = re.compile(item)
            if not pat.search(json_txt):
                missing.append(pat.pattern)
        if missing:
            self.fail('Could not find the following patterns in the JSON text: %s' % '/'.join(missing))

    def test_fetch_with_empty_inbox(self):
        self.assertFalse(a.fetch_msg())

    def test_fetch_one_message(self):
        t.push('hello')
        self.assertTrue(a.fetch_msg())

    def test_ping_response(self):
        response = self.check_req_resp('{"@type": "%s", "@id": "x"}' % tp_handler.PING_MSG_TYPE)
        self.check_json(response, '@thread', '@timing', 'in_time', 'out_time', 'thid')

    def test_ping_no_response(self):
        wc = mwc.MessageWithContext('{"@type": "%s", "response_requested": false}' % tp_handler.PING_MSG_TYPE)
        # We should claim message is handled
        self.assertTrue(a.handle_msg(wc))
        # We shouldn't have anything to send, since we were asked not to respond.
        self.assertFalse(t.squeue)

    def test_initial_ttt_move(self):
        msg = {}
        msg['@id'] = 'fakeid'
        msg['@type'] = ttt_handler.MOVE_MSG_TYPE
        msg['ill_be'] = 'X'
        response = self.check_req_resp(json.dumps(msg))
        self.check_json(response, ttt_handler.MOVE_MSG_TYPE, '@thread', 'thid')

if __name__ == '__main__':
    unittest.main()
