import pytest

from ..ram_transport import RamTransport

@pytest.fixture
def t():
    return RamTransport("x")

@pytest.mark.asyncio
async def test_ram_send(t):
    assert await t.send("payload")
    assert t.queue.items

@pytest.mark.asyncio
async def test_ram_receive(t):
    t.queue.items.append('hi')
    msg = await t.receive()
    assert msg == 'hi'

@pytest.mark.asyncio
async def test_ram_peek(t):
    assert not t.queue.items
    assert not await t.peek()
    t.queue.items.append('hi')
    assert await t.peek()
