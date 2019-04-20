import os
import pytest
import tempfile
import aiofiles

from ..file_channel import Channel


@pytest.fixture()
def scratch_space():
    x = tempfile.TemporaryDirectory()
    yield x
    x.cleanup()


@pytest.mark.asyncio
async def test_receive_from_empty(scratch_space):
    x = Channel(scratch_space.name)
    assert not bool(await x.receive())


@pytest.mark.asyncio
async def test_receive_from_full(scratch_space):
    x = Channel(scratch_space.name)
    # Write something to the folder I'm about to read from.
    fpath = os.path.join(x.folder, 'x.in')
    async with aiofiles.open(fpath, 'wt') as f:
        await f.write('hello')
    # First attempt to read shouldn't yield what I just wrote,
    # because this object's perspective on the channel wants
    # a different file extension for receiving vs. sending.
    assert not await x.receive()
    y = Channel(scratch_space.name, is_destward=False)
    assert await y.receive()
    # Next fetch should yield None.
    assert not await y.receive()


@pytest.mark.asyncio
async def test_request_response(scratch_space):
    requester = Channel(scratch_space.name)
    responder = Channel(scratch_space.name, is_destward=False)
    id = await requester.sender.send('ping', responder.folder)
    # The requester should not see a response yet.
    assert not (await requester.peek(id))
    # If the responder sends a response to an unrelated id,
    # the requester should still not see a response.
    await responder.send('unrelated')
    assert not (await requester.peek(id))
    await responder.send('pong', id)
    assert await requester.peek(id)
    wc = await requester.receive(id)
    assert 'pong' == wc.plaintext


@pytest.mark.asyncio
async def test_send(scratch_space):
    requester = Channel(scratch_space.name)
    await requester.send('hello')
    assert not (await requester.receive())
    responder = Channel(scratch_space.name, is_destward=False)
    wc = await responder.receive()
    assert 'hello' == wc.plaintext


if __name__ == '__main__':
    import asyncio
    asyncio.get_event_loop().set_debug(True)
    pytest.main([__file__])