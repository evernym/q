"""Implements the connection protocol as defined at http://bit.ly/2GfTaEX."""

import re
import random

from ..common import start_msg, finish_msg, problem_report
from ...protocols import compare_identifiers, HANDLERS

INVITATION_MSG_TYPE = 'invitation'
REQUEST_MSG_TYPE = 'request'
RESPONSE_MSG_TYPE = 'response'

SUPPORTED = [
    ('did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0', [INVITATION_MSG_TYPE, REQUEST_MSG_TYPE, RESPONSE_MSG_TYPE], ['inviter', 'invitee'])
]

async def handle(wc, parsed_type, agent):
    try:
        if compare_identifiers(parsed_type.msg_type_name, INVITATION_MSG_TYPE) == 0:
            keys = wc.obj.get('recipientKeys')
            if keys:
                msg = start_msg(REQUEST_MSG_TYPE, thid=wc.obj.get('@id'), in_time=wc.in_time)
                msg = finish_msg(msg)
                if wc.sender:
                    msg = await agent.pack(msg, wc.obj.get('recipient_verkey'), wc.sender)
            else:
                did = wc.obj.get('did')
                msg = problem_report(wc, "Connecting with public DIDs isn't currently supported.")
            return await agent.trans.send(msg)
        elif compare_identifiers(parsed_type.msg_type_name, REQUEST_MSG_TYPE):
            return False
        elif compare_identifiers(parsed_type.msg_type_name, RESPONSE_MSG_TYPE):
            return False
    except Exception as e:
        await agent.trans.send(problem_report(wc, str(e)))
