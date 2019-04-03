import os
import pytest
import tempfile
import aiofiles

from ..transports.file_transport import FileTransport as FT


@pytest.fixture()
def scratch_space():
    x = tempfile.TemporaryDirectory()
    yield x
    x.cleanup()


@pytest.mark.asyncio
async def test_receive_from_empty(scratch_space):
    x = FT(scratch_space.name)
    assert not bool(await x.receive())


@pytest.mark.asyncio
async def test_receive_from_full(scratch_space):
    x = FT(scratch_space.name)
    # Write something to the folder I'm about to read from.
    fpath = os.path.join(x.read_dir, 'x.msg')
    async with aiofiles.open(fpath, 'wt') as f:
        await f.write('hello')
    # First attempt to read should yield what I just wrote.
    assert await x.receive()
    # Next fetch should yield None.
    assert not await x.receive()


@pytest.mark.asyncio
async def test_request_response(scratch_space):
    requester = FT(scratch_space.name)
    responder = FT(scratch_space.name, folder_is_destward=False)
    id = await requester.send('ping')
    # The requester should not see a response yet.
    assert not (await requester.peek(id))
    # If the responder sends a response to an unrelated id,
    # the requester should still not see a response.
    await responder.send('unrelated')
    assert not (await requester.peek(id))
    await responder.send('pong', id)
    assert await requester.peek(id)
    mwc = await requester.receive(id)
    assert 'pong' == mwc.msg.decode('utf-8')


@pytest.mark.asyncio
async def test_send(scratch_space):
    requester = FT(scratch_space.name)
    await requester.send('hello')
    assert not (await requester.receive())
    responder = FT(scratch_space.name, folder_is_destward=False)
    mwc = await responder.receive()
    assert 'hello' == mwc.msg.decode('utf-8')


if __name__ == '__main__':
    import asyncio
    asyncio.get_event_loop().set_debug(True)
    pytest.main([__file__])