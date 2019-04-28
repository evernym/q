import aiofiles
import os
import uuid

from .folder_direction import Direction
from . import filesys_match
from ..dbc import precondition

EXAMPLES = '~/myfolder'


def match(uri):
    return filesys_match.match_uri_to_filesys(uri, os.path.isdir)


class Sender(Direction):
    def __init__(self, uri, is_destward: bool = True):
        # uri is passed to each Sender so it can extract authentication details or
        # similar. All we're going to do is make sure it's a folder that exists.
        folder = os.path.expanduser(uri)
        precondition(os.path.isdir(folder), "Folder %s must exist." % folder)
        Direction.__init__(self, is_destward)

    async def send(self, payload, folder, id=None, *args):
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        if id is None:
            id = str(uuid.uuid4())
        # Because writing is not an atomic operation, create the file with
        # a temp name, then rename it once the file has been written and
        # closed. This prevents code from peeking/reading the file before
        # we are done writing it.
        temp_fname = os.path.join(folder, '.' + id + '.tmp')
        perm_fname = os.path.join(folder, id + self.write_ext)
        async with aiofiles.open(temp_fname, 'wb') as f:
            await f.write(payload)
        os.rename(temp_fname, perm_fname)
        return id
