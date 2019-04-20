import aiofiles
import os
import re
import uuid

from .file_direction import Direction

PAT = re.compile('.*')
EXAMPLE = '~/myfolder'


class Sender(Direction):
    def __init__(self, is_destward):
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
