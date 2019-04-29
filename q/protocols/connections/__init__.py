"""Implements the connection protocol as defined at http://bit.ly/2GfTaEX."""

import indy

from ..common import start_msg, finish_msg, problem_report
from ...protocols import compare_identifiers
from ..exceptions import ProtocolAnomaly
from ...interaction import *
from ...did_doc import DIDDoc
from ...mtc import CONFIDENTIALITY, INTEGRITY, LABELS
from .state_machine import *

INVITATION_MSG_TYPE = 'invitation'
REQUEST_MSG_TYPE = 'request'
RESPONSE_MSG_TYPE = 'response'
CONNECTIONS_PROTOCOL_NAME = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0'

SUPPORTED = [
    (CONNECTIONS_PROTOCOL_NAME, [INVITATION_MSG_TYPE, REQUEST_MSG_TYPE, RESPONSE_MSG_TYPE], ['inviter', 'invitee'])
]


def message_type_to_event(mt):
    if compare_identifiers(mt, INVITATION_MSG_TYPE) == 0:
        return RECEIVE_INVITATION_EVENT
    if compare_identifiers(mt, REQUEST_MSG_TYPE) == 0:
        return RECEIVE_CONN_REQ_EVENT
    if compare_identifiers(mt, RESPONSE_MSG_TYPE) == 0:
        return RECEIVE_CONN_RESP_EVENT
    if compare_identifiers(mt, "ack") == 0:
        return RECEIVE_ACK_EVENT
    if compare_identifiers(mt, "problem_report") == 0:
        return RECEIVE_ERROR_EVENT


async def handle(wc, parsed_type, agent):
    try:
        # Do we have a pre-existing thread with cumulative state?
        if wc.interaction:
            sm = wc.interaction.data.get('state_machine')
            role = sm.get('role')
            if role == 'inviter':
                wc.state_machine = Inviter()
            else:
                wc.state_machine = Invitee()
            wc.state_machine.set_state_by_short_circuit(sm.get('state', NULL_STATE))
        else:
            wc.interaction = Interaction(wc.thid, wc.in_time)
            wc.state_machine = Invitee()

        mt = parsed_type.msg_type_name

        # Make sure state thinks this is a valid event to be handling in our current
        # state. This will raise a ProtocolAnomaly exception if not.
        received_event = message_type_to_event(mt)
        wc.state_machine.handle(received_event)

        if compare_identifiers(mt, INVITATION_MSG_TYPE) == 0:
            await handle_invitation(wc, parsed_type, agent)
            return True

        if not wc.tc.trust_for(CONFIDENTIALITY | INTEGRITY):
            raise ProtocolAnomaly("%s message must have %s and %s for protocol to be secure." % (
                mt, LABELS[CONFIDENTIALITY], LABELS[INTEGRITY]))
        if not wc.interaction:
            raise ProtocolAnomaly("%s message received without previous message in protocol." % mt)

        if compare_identifiers(mt, REQUEST_MSG_TYPE):
            return False
        elif compare_identifiers(mt, RESPONSE_MSG_TYPE):
            return False
        else:
            assert "Unhandled message type %s" % mt and False
    except Exception as e:
        await agent.trans.send(problem_report(wc, str(e)))


async def handle_request(wc, parsed_type, agent):
    pass


async def handle_invitation(wc, parsed_type, agent):
    # Did we get the form of invitation that uses keys+endpoint?
    keys = wc.obj.get('recipientKeys')
    endpoint = wc.obj.get('serviceEndpoint')
    event = SEND_CONN_REQ_EVENT
    if keys and endpoint:
        did, verkey = await indy.did.create_and_store_my_did(agent.wallet_handle, '{}')
        data = {"my_did": did, "my_verkey": verkey, "state_machine": None}
        msg = start_msg(REQUEST_MSG_TYPE, thid=wc.id, in_time=wc.in_time)
        msg["label"] = "q"
        msg["connection"] = {
            # TODO: change key names to lower case (HIPE was updated after Feb 2019 connectathon)
            "DID": did,
            "DIDDoc": str(DIDDoc.from_scratch(did, verkey, agent.endpoint))
        }
        msg = finish_msg(msg)
        msg = await agent.pack(msg, verkey, keys[0])
    else:
        did = wc.obj.get('did')
        msg = problem_report(wc, "Connecting with public DIDs isn't currently supported.")
        event = SEND_ERROR_EVENT
    await agent.trans.send(msg, endpoint)
    # Update state machine to reflect what we did as we handled this message.
    wc.state_machine.handle(event)
    data["state_machine"] = wc.state_machine.to_json()
    wc.interaction.data = data

