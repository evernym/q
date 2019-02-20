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

    def __init__(self, folder:str, folder_is_destward:bool=True):
        '''
        Claim a folder in the file system as the locus of message
        sending and receiving.

        :param folder: Container for subdirs where messages should be
          read from and and written to. It will be created, along
          with subdirs named req and resp, if folder structure does
          not exist.
        :param folder_is_destward: Tells whether to treat the folder as
          destward or srcward, relative to the owner of this transport
          object. This parameter exists so the same folder can be used
          in complimentary ways by a producer and consumer of messages. If
          you are using a FileTransport on the back side of a relay (emitting
          to the file system as you get closer to the destination), then
          folder_is_destward is true. This means that when the transport's
          send() method is called, files are written to the /in folder,
          and when the receive() method is called, files are read from the
          /out folder. If you are writing an agent that uses a FileTransport
          as its intake mechanism, then folder_is_destward is false. In this
          case, when the transport's send() method is called, files are
          written to the /out folder, and when the receive() method is called,
          files are read from the /in folder:
          
               FileTransport is destward of the relay
                    |
          http -> relay -> FileTransport -> agent
                                              |
                    FileTransport that is srcward of the agent                                 
        '''
        folder = os.path.normpath(os.path.abspath(folder))
        self.in_dir = os.path.join(folder, 'in')
        self.out_dir = os.path.join(folder, 'out')
        self.folder_is_destward = folder_is_destward
        os.makedirs(self.in_dir, exist_ok=True)
        os.makedirs(self.out_dir, exist_ok=True)

    @property
    def read_dir(self):
        '''Which folder do I read from?'''
        return self.out_dir if self.folder_is_destward else self.in_dir

    @property
    def write_dir(self):
        '''Which folder do I write to?'''
        return self.in_dir if self.folder_is_destward else self.out_dir

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
