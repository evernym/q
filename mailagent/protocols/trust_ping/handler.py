'''Implements the trust ping protocol as defined at http://bit.ly/2GfTaEX.'''

import json
import datetime

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
        in_time = datetime.datetime.utcnow()
        msg = {}
        thid = wc.obj.get('@id')
        if thid:
            thread = {}
            msg['@thread'] = thread
            thread['thid'] = thid
            thread['seqnum'] = 0
        msg['comment_ltxt'] = 'Hi from indyagent1@gmail.com.'
        timing = {}
        msg['@timing'] = timing
        timing['in_time'] = in_time.isoformat()
        timing['out_time'] = datetime.datetime.utcnow().isoformat()
        agent.trans.send(json.dumps(msg), wc.sender)
        return True
    elif t == PING_RESPONSE_MSG_TYPE:
        return True
    return False