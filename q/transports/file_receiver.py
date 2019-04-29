import os
import sys

from ..dbc import precondition
from . import filesys_match

EXAMPLES = 'stdin|~/myfile.dat'


def match(uri):
    return filesys_match.match_uri_to_filesys(uri, os.path.isfile, 'stdin')


class Receiver:
    def __init__(self, uri):
        fname = os.path.expanduser(uri)
        if not os.path.isfile(fname) and fname.lower() != 'stdin':
            precondition(False, "File %s must exist" % uri)
        self._fname = os.path.normpath(fname)
        self._handle = None

    @property
    def fname(self):
        return self._fname

    @property
    def handle(self):
        if self._handle is None:
            if self._fname == 'stdin':
                self._handle = sys.stdin
            else:
                self._handle = open(self._fname, 'rb')
        return self._handle

    def __del__(self):
        if self._handle:
            self._handle.close()

    def __enter__(self):
        _ = self.handle # force file to be opened
        return self

    def __exit__(self, *args):
        if self._handle:
            self._handle.close()
            self._handle = None

    async def receive(self):
        return self.handle.read()