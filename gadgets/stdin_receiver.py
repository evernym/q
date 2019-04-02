import re
import sys

PAT = re.compile('^stdin$', re.I)
EXAMPLE = 'stdin'

class Receiver:
    def __init__(self, ignored):
        pass
    async def receive(self):
        return sys.stdin.read()