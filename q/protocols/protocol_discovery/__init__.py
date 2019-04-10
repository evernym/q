"""Implements the trust ping protocol as defined at http://bit.ly/2GfTaEX."""

import re
import random

from ..common import start_msg, finish_msg, problem_report
from ...protocols import compare_identifiers, HANDLERS

QUERY_MSG_TYPE = 'query'
DISCLOSE_MSG_TYPE = 'disclose'

SUPPORTED = [
    ('did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/protocol_discovery/1.0', [QUERY_MSG_TYPE, DISCLOSE_MSG_TYPE], ['requester', 'responder'])
]

async def handle(wc, parsed_type, agent):
    try:
        if compare_identifiers(parsed_type.msg_type_name, QUERY_MSG_TYPE) == 0:
            q = wc.obj.get('query')
            if q:
                matches = []
                pat = re.compile(q.replace('*', '.*'))
                for handler in HANDLERS:
                    handler_piuri = handler.doc_uri + handler.protocol_name + '/' + str(handler.semver)
                    if pat.match(handler_piuri):
                        matches.append(handler_piuri)
                random.shuffle(matches)
                msg = start_msg(DISCLOSE_MSG_TYPE, thid=wc.obj.get('@id'), in_time=wc.in_time)
                msg = finish_msg(msg)
                if wc.sender:
                    msg = await agent.pack(msg, wc.unpacked.get('recipient_verkey'), wc.sender)
                await agent.trans.send(msg)
            return True
        elif compare_identifiers(parsed_type.msg_type_name, DISCLOSE_MSG_TYPE):
            return True
    except Exception as e:
        await agent.trans.send(problem_report(wc, str(e)))
