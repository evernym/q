import os
import sys

from . import filesys_match

EXAMPLES = 'stdout|~/myfile.dat'


def match(uri):
    return filesys_match.match_uri_to_filesys(uri, os.path.isfile, 'stdout')


class Sender:

    def __init__(self, uri):
        # uri is passed to each Sender so it can extract authentication details or
        # similar. In our case, we don't need it, because we will create the
        # file if it doesn't exist.
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    async def send(self, payload, fname, *ignored):
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        if fname.lower() == 'stdout':
            sys.stdout.write(fname)
            sys.stdout.flush()
        else:
            with open(fname, 'ab') as f:
                f.write(payload)
                f.flush()
