import re
import uuid

import ttt_game as game
import ttt_ai as ai
from handler_common import start_msg, finish_msg, problem_report, get_thread_id

MOVE_MSG_TYPE = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/tictactoe/1.0/move'
OUTCOME_MSG_TYPE = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/tictactoe/1.0/outcome'

TYPES = [
    MOVE_MSG_TYPE,
    OUTCOME_MSG_TYPE
]

def handle(wc, agent):
    try:
        t = wc.obj['@type']
        if t == MOVE_MSG_TYPE:
            them = wc.obj.get('ill_be', '')
            if them and isinstance(them, str) and len(them) == 1 and them in 'XO':
                them = them.strip().upper()
            else:
                raise Exception('Expected "ill_be" to contain either "X" or "O".')
            moves = wc.obj.get('moves', [])
            if not isinstance(moves, list) or len(moves) > 9:
                raise Exception('Expected "moves" to be a list of at most 9 items.')
            thid = get_thread_id(wc)
            g = game.Game()
            g.load(moves)
            w = g.winner()
            if w:
                resp = start_msg(OUTCOME_MSG_TYPE, thid)
                resp['winner'] = w
            else:
                me = game.other_player(them)
                choice = ai.next_move(g, me)
                g[choice] = me
                resp = start_msg(MOVE_MSG_TYPE, thid)
                resp['moves'] = g.dump()
            agent.trans.send(finish_msg(resp), wc.sender)
    except Exception as e:
        agent.trans.send(problem_report(wc, str(e)), wc.sender)
    return True