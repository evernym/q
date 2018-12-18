import unittest
import json
import re

import helpers
import agent
import mwc
import handlers
import tp_handler
import ttt_handler
import handler_common

class FakeTransport:
    def __init__(self):
        self.rqueue = []
        self.squeue = []
    def push(self, msg):
        self.rqueue.append(msg)
    def pop(self):
        if self.rqueue:
            return self.rqueue.pop(0)
    def send(self, payload, destination, in_reply_to_id = None, in_reply_to_subj = None):
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

    def get_game_response(self, ill_be, moves=None):
        msg = {}
        msg['@id'] = 'fakeid'
        msg['@type'] = ttt_handler.MOVE_MSG_TYPE
        msg['ill_be'] = ill_be
        if moves is not None:
            msg['moves'] = moves
        return self.check_req_resp(json.dumps(msg))

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

    def test_their_initial_ttt_move(self):
        response = self.get_game_response('O', ['O:A1']) # They are O and make a first move; do I respond as X?
        self.check_json(response, ttt_handler.MOVE_MSG_TYPE, '@thread', 'thid', '"X:B2"')

    def test_my_initial_ttt_move(self):
        response = self.get_game_response('X') # They are X but invite me to go first; do I respond as O?
        self.check_json(response, ttt_handler.MOVE_MSG_TYPE, '@thread', 'thid', '"O:B2"')

    def test_win_ttt_move(self):
        response = self.get_game_response('X', ['X:A1', 'O:B1', 'X:A2', 'O:B2', 'X:A3'])
        self.check_json(response, ttt_handler.OUTCOME_MSG_TYPE, r'"winner"\s*:\s*"X"')

    def test_lose_ttt_move(self):
        response = self.get_game_response('O', ['X:A1', 'O:B1', 'X:A2', 'O:B2', 'X:A3'])
        self.check_json(response, ttt_handler.OUTCOME_MSG_TYPE, r'"winner"\s*:\s*"X"')

    def test_draw_ttt_move(self):
        response = self.get_game_response('O', ['X:A1', 'O:B1', 'X:A2', 'O:B2', 'X:B3', 'O:A3', 'X:C1', 'O:C2', 'X:C3'])
        self.check_json(response, ttt_handler.OUTCOME_MSG_TYPE, r'"winner"\s*:\s*"none"')

    def test_ttt_bad_move(self):
        response = self.get_game_response('O', ['X:A4'])
        self.check_json(response, handler_common.PROBLEM_REPORT_MSG_TYPE, 'Bad key')

    def test_ttt_bad_ill_be(self):
        response = self.get_game_response('Fred', ['X:A1'])
        self.check_json(response, handler_common.PROBLEM_REPORT_MSG_TYPE, 'Bad player')

if __name__ == '__main__':
    unittest.main()