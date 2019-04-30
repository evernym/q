import os
import pytest
import random
import tempfile

import indy

from .. import *
from ....agents.base import norm_recipient_keys
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

        async def pack(self, msg, sender_key, to):
            if isinstance(msg, dict):
                msg = json.dumps(msg)
            elif isinstance(msg, bytes):
                msg = msg.decode('utf-8')
            if not isinstance(to, list):
                to = [to]
            i = len(to) - 1
            while i >= 0:
                # Always anon-crypt to mediator
                if i == 0 and len(to) > 1:
                    sender = None
                else:
                    sender = sender_key
                recipients = norm_recipient_keys(to[i])
                msg = await indy.crypto.pack_message(self.wallet_handle, msg, recipients, sender)
                msg = msg.decode('utf-8')
                i -= 1
            return msg

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
async def test_connection_request(invitation_with_key_and_did_endpoint, fake_agent):
    wc = invitation_with_key_and_did_endpoint
