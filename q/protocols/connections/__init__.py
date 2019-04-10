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
            return False
        elif compare_identifiers(parsed_type.msg_type_name, REQUEST_MSG_TYPE):
            return False
        elif compare_identifiers(parsed_type.msg_type_name, RESPONSE_MSG_TYPE):
            return False
    except Exception as e:
        await agent.trans.send(problem_report(wc, str(e)))
