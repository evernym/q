from . import game
from . import ai
from ..common import start_msg, finish_msg, problem_report, get_thread_id

MOVE_MSG_TYPE = 'did:sov:SLfEi9esrjzybysFxQZbfq;spec/tictactoe/1.0/move'
OUTCOME_MSG_TYPE = 'did:sov:SLfEi9esrjzybysFxQZbfq;spec/tictactoe/1.0/outcome'

TYPES = [
    MOVE_MSG_TYPE,
    OUTCOME_MSG_TYPE
]


async def handle(wc, agent):
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
                resp = start_msg(OUTCOME_MSG_TYPE, thid, in_time=wc.in_time)
                resp['winner'] = w
            else:
                them = wc.obj.get('me', '')
                if them:
                    me = game.other_player(them)
                else:
                    me = g.whose_turn()
                choice = ai.next_move(g, me)
                g[choice] = me
                resp = start_msg(MOVE_MSG_TYPE, thid, in_time=wc.in_time)
                resp['me'] = me
                resp['moves'] = g.dump()

            # Okay, build response and return to sender.
            msg = finish_msg(resp)
            if wc.sender:
                msg = await agent.pack(msg, wc.unpacked.get('recipient_verkey'), wc.sender)
            await agent.trans.send(msg)
            return True

        elif t == OUTCOME_MSG_TYPE:
            return True
        else:
            return False
    except Exception as e:
        await agent.trans.send(problem_report(wc, str(e)))
