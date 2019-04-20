import aiofiles
from asyncio.coroutines import os
import re

from .file_direction import Direction
from .. import mwc
from .. import log_helpers

PAT = re.compile('.*')
EXAMPLE = '~/myfolder'
_MSG_EXT = '.in'


def _next_item_name(folder, ext, filter=None):
    for root, folders, files in os.walk(folder):
        folders.clear()
        for fname in files:
            # Ignore files that are not messages.
            if fname.endswith(ext):
                if (filter is None) or (fname.startswith(filter)):
                    yield fname


async def _pop_item(fpath):
    async with aiofiles.open(fpath, 'rb') as f:
        data = await f.read()
    os.remove(fpath)
    return data


async def _item_content(folder, ext, filter=None):
    """Return next as mwc.MessageWithContext, or None if nothing is found."""
    try:
        data = None
        for fname in _next_item_name(folder, ext, filter):
            data = await _pop_item(os.path.join(folder, fname))
            return mwc.MessageWithContext(data)
    except KeyboardInterrupt:
        raise
    except:
        log_helpers.log_exception()


class Receiver(Direction):
    def __init__(self, folder, is_destward):
        Direction.__init__(self, is_destward)
        self._folder = os.path.normpath(folder)

    @property
    def endpoint(self):
        return self._folder

    @property
    def folder(self):
        return self._folder

    async def peek(self, filter=None):
        for x in _next_item_name(self._folder, self.read_ext, filter):
            return True

    async def receive(self, filter=None):
        return await _item_content(self._folder, self.read_ext, filter)
