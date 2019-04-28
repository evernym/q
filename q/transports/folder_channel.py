from asyncio.coroutines import os

from .folder_sender import Sender
from .folder_receiver import Receiver
from .folder_direction import Direction


class Channel(Direction):
    """
    Provide a duplex channel that works by manipulating files in a folder.
    """

    def __init__(self, folder: str, is_destward: bool = True):
        """
        Claim a folder in the file system as the locus of message
        sending and receiving.

        :param folder: Container for message files. It must exist.
        :param is_destward: Tells whether to treat the folder as
          destward or srcward, relative to the owner of this channel
          object. This parameter exists so the same folder can be used
          in complimentary ways by a producer and consumer of messages. If
          you are using a Channel on the back side of a relay (emitting
          to the file system as you get closer to the destination), then
          is_destward is true. This means that when a send() method is called,
          *.in files are written, and when the receive() method is called,
          *.out files are read. If you are writing an agent that uses a
          Channel as its intake mechanism, then is_destward is false. In
          this case, when a send() method is called, *.out files are
          written, and when a receive() method is called, *.in files
          are read:
          
               Channel is destward of the relay (write *.in; read *.out)
                    |
          http -> relay -> FolderChannel -> agent
                                              |
               Channel is srcward of the agent (read from *.in; write to *.out)
        """
        Direction.__init__(self, is_destward)
        folder = os.path.normpath(os.path.abspath(folder))
        self.receiver = Receiver(folder, is_destward)
        self.sender = Sender(is_destward)

    @property
    def folder(self):
        return self.receiver.folder

    async def send(self, payload, id=None, *args):
        return await self.sender.send(payload, self.folder, id)

    async def peek(self, filter=None):
        return await self.receiver.peek(filter)

    async def receive(self, filter=None):
        return await self.receiver.receive(filter)

    def __str__(self):
        return self.direction + '=' + self.folder