PING_MSG_TYPE = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/trust_ping/1.0/ping'
PONG_MSG_TYPE = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/trust_ping/1.0/ping_response'

TYPES = [
    PING_MSG_TYPE,
    PONG_MSG_TYPE,
]

def handle(wc, agent):
    t = wc.obj['@type']
    if t == PING_MSG_TYPE:
        agent.trans.send('{"@type": "%s"}' % PONG_MSG_TYPE, wc.sender)
    return False