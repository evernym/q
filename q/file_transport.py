import uuid
import aiofiles
from asyncio.coroutines import os

from . import mwc
from . import log_helpers

_MSG_EXT = '.msg'

def _next_item_name(folder, filter=None):
    for root, folders, files in os.walk(folder):
        folders.clear()
        for fname in files:
            # Ignore files that are not messages.
            if fname.endswith(_MSG_EXT):
                if (filter is None) or (fname.startswith(filter)):
                    yield fname

async def _pop_item(fpath):
    async with aiofiles.open(fpath, 'rb') as f:
        data = await f.read()
    os.remove(fpath)
    return data

async def _item_content(folder, filter=None):
    '''Return next as mwc.MessageWithContext, or None if nothing is found.'''
    try:
        data = None
        for fname in _next_item_name(folder, filter):
            data = await _pop_item(os.path.join(folder, fname))
            return mwc.MessageWithContext(data)
    except KeyboardInterrupt:
        raise
    except:
        log_helpers.log_exception()

class FileTransport:
    '''
    Provide a transport that works by manipulating files in the file system.
    '''

    def __init__(self, folder:str, folder_is_destward:bool=True):
        '''
        Claim a folder in the file system as the locus of message
        sending and receiving.

        :param folder: Container for subdirs where messages should be
          read from and and written to. It must exist, but its subdirs
          will be created automatically, if they do not exist.
        :param folder_is_destward: Tells whether to treat the folder as
          destward or srcward, relative to the owner of this transport
          object. This parameter exists so the same folder can be used
          in complimentary ways by a producer and consumer of messages. If
          you are using a FileTransport on the back side of a relay (emitting
          to the file system as you get closer to the destination), then
          folder_is_destward is true. This means that when the transport's
          send() method is called, files are written to the /a folder,
          and when the receive() method is called, files are read from the
          /b folder. If you are writing an agent that uses a FileTransport
          as its intake mechanism, then folder_is_destward is false. In this
          case, when the transport's send() method is called, files are
          written to the /b folder, and when the receive() method is called,
          files are read from the /a folder:
          
               FileTransport is destward of the relay (write to /a)
                    |
          http -> relay -> FileTransport -> agent
                                              |
               FileTransport is srcward of the agent (read from /a)
        '''
        folder = os.path.normpath(os.path.abspath(folder))
        if not os.path.isdir(folder):
            raise ValueError('Folder "%s" does not exist.' % folder)
        self.a_dir = os.path.join(folder, 'a')
        self.b_dir = os.path.join(folder, 'b')
        self.folder_is_destward = folder_is_destward
        os.makedirs(self.a_dir, exist_ok=True)
        os.makedirs(self.b_dir, exist_ok=True)

    @property
    def read_dir(self):
        '''Which folder do I read from?'''
        return self.b_dir if self.folder_is_destward else self.a_dir

    @property
    def write_dir(self):
        '''Which folder do I write to?'''
        return self.a_dir if self.folder_is_destward else self.b_dir

    async def send(self, payload, id=None, *args):
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        if id is None:
            id = str(uuid.uuid4())
        # Because writing is not an atomic operation, create the file with
        # a temp name, then rename it once the file has been written and
        # closed. This prevents code from peeking/reading the file before
        # we are done writing it.
        w = self.write_dir
        temp_fname = os.path.join(w, '.' + id + '.tmp')
        perm_fname = os.path.join(w, id + _MSG_EXT)
        async with aiofiles.open(temp_fname, 'wb') as f:
            await f.write(payload)
        os.rename(temp_fname, perm_fname)
        return id

    async def peek(self, filter=None):
        for x in _next_item_name(self.read_dir, filter):
            return True

    async def receive(self, filter=None):
        return await _item_content(self.read_dir, filter)
