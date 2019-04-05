"""Implements the trust ping protocol as defined at http://bit.ly/2GfTaEX."""

import re
import random

from ..common import start_msg, finish_msg
from ...protocols import HANDLERS_BY_MSG_TYPE
PAT = re.compile('FOOBAR')
TYPES = []

SUPPORTED = {
    'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/protocol_discovery/1.0': {
        'messages': ['query', 'disclose'],
        'roles': ['requester', 'responder']
    }
}

async def handle(wc, agent):
    t = wc.obj.get('@type')
    if t == QUERY_MSG_TYPE:
        q = wc.obj.get('query')
        if q:
            matches = []
            pat = re.compile(q.replace('*', '.*'))
            for handler in HANDLERS_BY_MSG_TYPE:
                for typ in handler.TYPES:
                    typ = typ[:typ.rfind('/')]
                    if typ not in matches:
                        if pat.match(typ):
                            matches.append(typ)
            random.shuffle(matches)
            msg = start_msg(DISCLOSE_MSG_TYPE, thid=wc.obj.get('@id'), in_time=wc.in_time)
            msg = finish_msg(msg)
            if wc.sender:
                msg = await agent.pack(msg, wc.unpacked.get('recipient_verkey'), wc.sender)
            await agent.trans.send(msg)
        return True
    elif t == DISCLOSE_MSG_TYPE:
        return True
    return False