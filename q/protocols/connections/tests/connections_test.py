import os
import pytest
import random
import tempfile
import json

import indy

from .. import *
from ....agents.base import norm_recipient_keys, Agent
from ....transports import ram_transport
from ....protocols import parse_msg_type
from ....mwc import MessageWithContext

_DATA_FILES_FOLDER = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   '../../../../messages/connections'))


@pytest.fixture
def load_json():
    def _load_json(which):
        with open(os.path.join(_DATA_FILES_FOLDER, which + '.json'), 'rb') as f:
            data = f.read()
        wc = MessageWithContext(data)
        return wc
    return _load_json


@pytest.fixture
def scratch_space():
    x = tempfile.TemporaryDirectory()
    yield x
    x.cleanup()


@pytest.fixture
async def fake_agent(scratch_space):
    class FakeAgent:
        def __init__(self):
            self.trans = ram_transport.RamTransport("test")
            wallet_id = 'wallet' + str(random.randint(100000,999999))
            self.wallet_config = '{"id": "' + wallet_id + '", "storage_config": {"path": "%s"}}' % scratch_space.name
            self.wallet_credentials = '{"key": "pickle"}'
            self.endpoint = "ram://test"

        async def prep(self):
            await indy.wallet.create_wallet(self.wallet_config, self.wallet_credentials)
            self.wallet_handle = await indy.wallet.open_wallet(self.wallet_config, self.wallet_credentials)
            # Following seed is used to create key in invitation file
            await indy.crypto.create_key(self.wallet_handle, '{"seed": "11111111111111111111111111111111"}')

        async def pack(self, msg, sender_key, to):
            return await Agent._pack(self.wallet_handle, msg, sender_key, to)

        async def unpack(self, msg):
            if isinstance(msg, str):
                msg = msg.encode()
            return json.loads(await indy.crypto.unpack_message(self.wallet_handle, msg))

    fa = FakeAgent()
    await fa.prep()
    yield fa
    await indy.wallet.close_wallet(fa.wallet_handle)


@pytest.mark.asyncio
@pytest.fixture
async def invitation_with_key_and_did_endpoint(load_json, fake_agent):
    wc = load_json('invitation-with-key-and-did-endpoint')
    parsed_type = parse_msg_type("did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/invitation")
    assert await handle(wc, parsed_type, fake_agent)
    return wc


@pytest.mark.asyncio
@pytest.fixture
async def invitation_with_key_and_url_endpoint(load_json, fake_agent):
    wc = load_json('invitation-with-key-and-url-endpoint')
    parsed_type = parse_msg_type("did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/invitation")
    assert await handle(wc, parsed_type, fake_agent)
    return wc


@pytest.mark.asyncio
async def test_invitation_with_key_and_did_endpoint_handled(invitation_with_key_and_did_endpoint):
    wc = invitation_with_key_and_did_endpoint
    assert wc.state_machine.state == REQUESTED_STATE


@pytest.mark.asyncio
async def test_invitation_with_key_and_url_endpoint_handled(invitation_with_key_and_url_endpoint):
    wc = invitation_with_key_and_url_endpoint
    assert wc.state_machine.state == REQUESTED_STATE


@pytest.mark.asyncio
@pytest.fixture
async def conn_request_with_key_and_did_endpoint(invitation_with_key_and_did_endpoint, fake_agent):
    request = await fake_agent.trans.receive()
    unpacked = await fake_agent.unpack(request)
    return unpacked


@pytest.mark.asyncio
async def test_connection_request(conn_request_with_key_and_did_endpoint, fake_agent):
    # Check that the agent did send a connection request
    unpacked = conn_request_with_key_and_did_endpoint
    wc1 = MessageWithContext(unpacked['message'])
    assert parse_msg_type(wc1.type).msg_type_name == REQUEST_MSG_TYPE
