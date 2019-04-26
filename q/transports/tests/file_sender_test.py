import os
import pytest
import tempfile

from .. import file_sender

@pytest.fixture()
def scratch_space():
    x = tempfile.TemporaryDirectory()
    yield x
    x.cleanup()

@pytest.mark.asyncio
async def test_file_sender(scratch_space):

    fname = os.path.join(scratch_space.name, 'x')
    with file_sender.Sender(fname) as fs:
        with open(fname, 'rt') as f:
            assert not bool(f.read())
            await fs.send('hello', fname)
            assert f.read() == 'hello'
            assert not bool(f.read())
            await fs.send('world', fname)
            assert f.read() == 'world'
