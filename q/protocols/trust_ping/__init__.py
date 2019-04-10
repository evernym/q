"""Implements the trust ping protocol as defined at http://bit.ly/2GfTaEX."""

import json

from ..common import start_msg, finish_msg, problem_report
from ...protocols import compare_identifiers

PING_MSG_TYPE = 'ping'
PING_RESPONSE_MSG_TYPE = 'ping_response'

SUPPORTED = [
    ('did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/trust_ping/1.0', [PING_MSG_TYPE, PING_RESPONSE_MSG_TYPE], ['requester', 'responder'])
]

async def handle(wc, parsed_type, agent):
    try:
        if compare_identifiers(parsed_type.msg_type_name, PING_MSG_TYPE) == 0:
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
        elif compare_identifiers(parsed_type.msg_type_name, PING_RESPONSE_MSG_TYPE):
            return True
    except Exception as e:
        await agent.trans.send(problem_report(wc, str(e)))
