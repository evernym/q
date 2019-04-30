import pytest

from ..ram_transport import RamTransport


@pytest.fixture
def t():
    return RamTransport("x")


@pytest.mark.asyncio
async def test_ram_send(t):
    assert not t.queue.items
    assert await t.send("payload", 'x')
    assert t.queue.items


@pytest.mark.asyncio
async def test_ram_receive(t):
    assert not t.queue.items
    t.queue.items.append('hi')
    msg = await t.receive()
    assert msg == 'hi'
    assert not t.queue.items


@pytest.mark.asyncio
async def test_ram_peek(t):
    assert not t.queue.items
    assert not await t.peek()
    t.queue.items.append('hi')
    assert await t.peek()


@pytest.mark.asyncio
async def test_ram_send_receive_order(t):
    assert not await t.peek()
    assert await t.send('1', 'x')
    assert await t.send('2', 'x')
    assert await t.send('3', 'x')
    assert await t.receive() == '1'
    assert await t.receive() == '2'
    assert await t.receive() == '3'
