import json
import os
import pytest

from .. import *
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
def fake_agent():
    class FakeAgent:
        def __init__(self):
            self.trans = ram_transport.RamTransport("test")
    return FakeAgent()

@pytest.mark.asyncio
async def test_invitation_handled(load_json, fake_agent):
    wc = load_json('invitation-with-key-and-did-endpoint')
    parsed_type = parse_msg_type("did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/invitation")
    assert await handle(wc, parsed_type, fake_agent)
