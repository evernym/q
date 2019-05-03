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
            sm = json.loads(wc.interaction.data.get('state_machine'))
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
            await handle_invitation(wc, agent)
            return True

        if not wc.tc.trust_for(CONFIDENTIALITY | INTEGRITY):
            msg = "%s message must have %s and %s for protocol to be secure." % (mt, LABELS[CONFIDENTIALITY], LABELS[INTEGRITY])
            raise ProtocolAnomaly(wc.state_machine.protocol, wc.state_machine.role, wc.state_machine.state, msg)
        if not wc.interaction:
            msg = "%s message received without previous message in protocol." % mt
            raise ProtocolAnomaly(wc.state_machine.protocol, wc.state_machine.role, wc.state_machine.state, msg)

        if compare_identifiers(mt, REQUEST_MSG_TYPE) == 0:
            await handle_request(wc, parsed_type)
            return True
        elif compare_identifiers(mt, RESPONSE_MSG_TYPE) == 0:
            await handle_response(wc, parsed_type)
            return True
        else:
            assert "Unhandled message type %s" % mt and False
    except Exception as e:
        await agent.trans.send(problem_report(wc, str(e)))


async def handle_request(wc, agent):
    if wc.interaction:
        data = wc.interaction.data
        # TODO: Handle already started interaction
    conn = wc.obj.get("connection")
    if conn:
        wc.state_machine.handle(RECEIVE_CONN_REQ_EVENT)
        r = await make_conn_resp(conn, agent, wc.id, wc.in_time)
        if r:
            # TODO: Send message to agent.trans
            wc.state_machine.handle(SEND_CONN_RESP_EVENT)
            did, verkey, _ = r
            data = {"my_did": did, "my_verkey": verkey, "state_machine": wc.state_machine.to_json()}
            wc.interaction.data = data


async def handle_response(wc, agent):
    data = wc.interaction.data
    conn = wc.obj.get("connection")
    if conn:
        did = conn.get('did')
        did_doc = DIDDoc.from_json(conn.get('did_doc', {}))
        verkey = get_first_verkey(did_doc)
        if verkey:
            await indy.did.store_their_did(agent.wallet_handle, json.dumps({"did": did, "verkey": verkey}))
            wc.state_machine.handle(RECEIVE_CONN_RESP_EVENT)
            wc.interaction.data["state_machine"] = wc.state_machine.to_json()
            wc.interaction.data = data


async def handle_invitation(wc, agent):
    # Did we get the form of invitation that uses keys+endpoint?
    event = SEND_CONN_REQ_EVENT
    keys = wc.obj.get('recipientKeys')
    endpoint = wc.obj.get('serviceEndpoint')
    if not keys and not endpoint:
        # Try another variation of the invitation
        keys = [wc.obj.get('key')]
        endpoint = wc.obj.get('endpoint')
    if keys and endpoint:
        did, verkey = await indy.did.create_and_store_my_did(agent.wallet_handle, '{}')
        data = {"my_did": did, "my_verkey": verkey, "state_machine": None}
        type_ = CONNECTIONS_PROTOCOL_NAME + '/' + REQUEST_MSG_TYPE
        msg = start_msg(type_, thid=wc.id, in_time=wc.in_time)
        msg["label"] = "q"
        msg["connection"] = {
            "did": did,
            "did_doc": str(DIDDoc.from_scratch(did, verkey, agent.endpoint))
        }
        msg = finish_msg(msg)
        msg = await agent.pack(msg, verkey, keys[0])
    else:
        did = wc.obj.get('did')
        msg = problem_report(wc, "Connecting with public DIDs isn't currently supported.")
        event = SEND_ERROR_EVENT
        data = {}
    await agent.trans.send(msg, endpoint)
    # Update state machine to reflect what we did as we handled this message.
    wc.state_machine.handle(event)
    data["state_machine"] = wc.state_machine.to_json()
    wc.interaction.data = data


def get_first_verkey(did_doc):
    authns = did_doc.obj.get('authentication')
    if authns:
        keys = did_doc.obj.get('publicKey')
        if keys:
            for au in authns:
                pubkey = au.get('publicKey')
                if pubkey:
                    for key in keys:
                        if key.get('id') == pubkey:
                            t = key.get("type")
                            if t == "Ed25519VerificationKey2018":
                                value = key.get('publicKeyBase58')
                                if value:
                                    return value


async def make_conn_resp(conn, agent, thread_id=None, in_time=None):
    did = conn.get('did')
    did_doc = DIDDoc.from_json(conn.get('did_doc', {}))
    their_verkey = get_first_verkey(did_doc)
    if their_verkey:
        await indy.did.store_their_did(agent.wallet_handle, json.dumps({"did": did, "verkey": their_verkey}))
        did, verkey = await indy.did.create_and_store_my_did(agent.wallet_handle, '{}')
        type_ = CONNECTIONS_PROTOCOL_NAME + '/' + RESPONSE_MSG_TYPE
        msg = start_msg(type_, thid=thread_id, in_time=in_time)
        msg["label"] = "q"
        msg["connection"] = {
            "did": did,
            "did_doc": str(DIDDoc.from_scratch(did, verkey, agent.endpoint))
        }
        msg = finish_msg(msg)
        packed = await agent.pack(msg, verkey, their_verkey)
        return did, verkey, packed
