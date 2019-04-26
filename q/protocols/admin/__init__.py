"""Implements a non-interoperable protocol to control the agent itself."""

from ..common import start_msg, finish_msg

INTERRUPT_MSG_TYPE = 'interrupt'
SEND_MSG_TYPE = 'send'

SUPPORTED = [
    ('./admin/1.0', [INTERRUPT_MSG_TYPE, SEND_MSG_TYPE], [])
]

async def handle(wc, parsed_type, agent):
    typ = parsed_type.msg_type_name
    if typ == INTERRUPT_MSG_TYPE:
        await agent.interrupt()
        return True
    elif typ == SEND_MSG_TYPE:
        plaintext = wc.obj

