"""Implements the trust ping protocol as defined at http://bit.ly/2GfTaEX."""

import json

from ..common import start_msg, finish_msg

PING_MSG_TYPE = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/trust_ping/1.0/ping'
PING_RESPONSE_MSG_TYPE = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/trust_ping/1.0/ping_response'

TYPES = [
    PING_MSG_TYPE,
    PING_RESPONSE_MSG_TYPE,
]


async def handle(wc, agent):
    t = wc.obj.get('@type')
    if t == PING_MSG_TYPE:
        # Don't respond to a message that says "response_requested": false.
        rr = wc.obj.get('response_requested', None)
        if rr is not None:
            if not rr:
                return True
        # Okay, build response and return to sender.
        msg = start_msg(PING_RESPONSE_MSG_TYPE, thid=wc.obj.get('@id'), in_time=wc.in_time)
        msg = finish_msg(msg)
        if wc.sender:
            msg = await agent.pack(msg, wc.unpacked.get('recipient_verkey'), wc.sender)
        await agent.trans.send(msg)
        return True
    elif t == PING_RESPONSE_MSG_TYPE:
        return True
    return False