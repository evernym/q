import aiofiles
import asyncio
import json
import os
import pytest
import tempfile
import time

import indy

from ..folderagent import Agent
from ...transports import folder_sender
from ...protocols.common import start_msg, finish_msg

@pytest.fixture
def scratch_space():
    x = tempfile.TemporaryDirectory()
    yield x
    x.cleanup()

async def _get_agent(root, num):
    agent = Agent()
    folder = os.path.join(root, str(num))
    agent.configure(argv=['--folder', folder, '--phrase', 'pickle', '--wallet', 'wallet' + str(num)])
    await agent.open_wallet()
    task = asyncio.create_task(agent.run())
    return agent, task

@pytest.fixture
async def agent1(scratch_space):
    agent, task = await _get_agent(scratch_space.name, 1)
    yield agent
    agent.interrupt()
    await task

@pytest.fixture
async def agent2(scratch_space):
    agent, task = await _get_agent(scratch_space.name, 2)
    yield agent
    agent.interrupt()
    await task

async def send(msg, dest):
    sender = folder_sender.Sender(is_destward=True)
    await sender.send(msg, dest.queue_dir)

async def send_conn_invitation(src, dest):
    did, verkey = await indy.did.create_and_store_my_did(src.wallet_handle, '{}')
    msg = start_msg("did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/invitation")
    msg['label'] = "test"
    msg['recipientKeys'] = [verkey]
    msg['serviceEndpoint'] = src.queue_dir
    await send(json.dumps(msg, indent=2), dest)

@pytest.mark.asyncio
async def test_connection_flow(agent1, agent2):
    await send_conn_invitation(agent1, agent2)
