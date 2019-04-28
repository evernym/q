import os
import pytest
import tempfile

from ..file_receiver import Receiver

@pytest.fixture()
def scratch_space():
    x = tempfile.TemporaryDirectory()
    yield x
    x.cleanup()

@pytest.mark.asyncio
async def test_file_receiver(scratch_space):

    fname = os.path.join(scratch_space.name, 'x')
    with open(fname, 'wt') as f:
        with Receiver(fname) as fr:
            assert not bool(await fr.receive())
            f.write('hello')
            f.flush()
            assert (await fr.receive()) == b'hello'
            assert not bool(await fr.receive())
            f.write('world')
            f.flush()
            assert (await fr.receive()) == b'world'
