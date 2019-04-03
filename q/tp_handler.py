'''Implements the trust ping protocol as defined at http://bit.ly/2GfTaEX.'''

from handler_common import start_msg, finish_msg

PING_MSG_TYPE = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/trust_ping/1.0/ping'
PING_RESPONSE_MSG_TYPE = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/trust_ping/1.0/ping_response'

TYPES = [
    PING_MSG_TYPE,
    PING_RESPONSE_MSG_TYPE,
]

def handle(wc, agent):
    t = wc.obj['@type']
    if t == PING_MSG_TYPE:
        rr = wc.obj.get('response_requested', None)
        if rr is not None:
            if not rr:
                return True
        msg = start_msg(PING_RESPONSE_MSG_TYPE, thid=wc.obj.get('@id'), in_time=wc.in_time)
        msg['comment_ltxt'] = 'Hi from indyagent1@gmail.com.'
        agent.trans.send(finish_msg(msg), wc.sender, wc.in_reply_to, wc.subject)
        return True
    elif t == PING_RESPONSE_MSG_TYPE:
        return True
    return False