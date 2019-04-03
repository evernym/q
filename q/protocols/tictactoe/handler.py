from . import game
from . import ai
from ...handler_common import start_msg, finish_msg, problem_report, get_thread_id

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
            moves = wc.obj.get('moves', [])
            if not isinstance(moves, list) or len(moves) > 9:
                raise Exception('Expected "moves" to be a list of at most 9 items.')
            g = game.Game()
            g.load(moves)
            thid = get_thread_id(wc)
            w = g.winner()
            if w:
                resp = start_msg(OUTCOME_MSG_TYPE, thid)
                resp['winner'] = w
            else:
                # TTT protocol was updated to rename field ill_be --> me.
                # Look for 'me' by preference, but still allow ill_be for
                # the time being.
                them = wc.obj.get('me', '')
                if not them:
                    them = wc.obj.get('ill_be')
                if them:
                    me = game.other_player(them)
                else:
                    me = g.whose_turn()
                    them = game.other_player(me)
                choice = ai.next_move(g, me)
                g[choice] = me
                resp = start_msg(MOVE_MSG_TYPE, thid)
                resp['me'] = me
                resp['moves'] = g.dump()
    except Exception as e:
        agent.trans.send(problem_report(wc, str(e)), wc.sender, wc.in_reply_to, wc.subject)
    return resp