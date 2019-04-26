import os
import sys

from . import filesys_match

EXAMPLES = 'stdout|~/myfile.dat'


def match(uri):
    return filesys_match.match_uri_to_filesys(uri, os.path.isfile, 'stdout')


class Sender:

    def __init__(self, fname=None):
        # If given a filename, make sure file exists.
        if fname:
            with open(fname, 'at') as f:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    async def send(self, payload, fname, *ignored):
        if fname == 'stdout':
            sys.stdout.write(fname)
            sys.stdout.flush()
        else:
            with open(fname, 'at') as f:
                f.write(payload)
                f.flush()
