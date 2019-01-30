import os
import uuid

import mwc
import agent_common

_MSG_EXT = '.msg'

def _next_item_name(folder, filter=None):
    for root, folders, files in os.walk(folder):
        folders.clear()
        for fname in files:
            if (filter is None) or (fname.startswith(filter)):
                yield fname

def _pop_item(fpath):
    with open(fpath, 'rb') as f:
        data = f.read()
    os.remove(fpath)
    return data

def _item_content(folder, filter=None):
    '''Return next as mwc.MessageWithContext, or None if nothing is found.'''
    try:
        data = None
        for fname in _next_item_name(folder, filter):
            data = _pop_item(os.path.join(folder, fname))
            return mwc.MessageWithContext(data)

    except KeyboardInterrupt:
        raise
    except:
        agent_common.log_exception()

class FileTransport:
    '''
    Provide a transport that works by manipulating files in the file system.
    '''

    def __init__(self, folder:str, requester:bool=True):
        '''
        Claim a folder in the file system as the locus of message
        sending and receiving.

        :param folder: Container for subdirs where messages should be
          read from and to and written to. It will be created, along
          with subdirs named req and resp, if folder structure does
          not exist.
        :param requester: Tells whether to take the perspective of a
          requester or a responder when handling the send() and
          receive() functions. Requesters send() to the req folder
          and receive() from the resp folder; responders do the
          opposite. This allows a FileTransport to service either
          side of an interaction.
        '''
        folder = os.path.normpath(os.path.abspath(folder))
        self.req_dir = os.path.join(folder, 'req')
        self.resp_dir = os.path.join(folder, 'resp')
        self.requester = requester
        os.makedirs(self.req_dir, exist_ok=True)
        os.makedirs(self.resp_dir, exist_ok=True)

    @property
    def read_dir(self):
        '''Which folder do I read from?'''
        return self.resp_dir if self.requester else self.req_dir

    @property
    def write_dir(self):
        '''Which folder do I write to?'''
        return self.req_dir if self.requester else self.resp_dir

    def send(self, payload, id=None, *args):
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        if id is None:
            id = str(uuid.uuid4())
        fname = id + _MSG_EXT
        with open(os.path.join(self.write_dir, fname), 'wb') as f:
            f.write(payload)
        return id

    def peek(self, filter=None):
        for x in _next_item_name(self.read_dir, filter):
            return True

    def receive(self, filter=None):
        return _item_content(self.read_dir, filter)
