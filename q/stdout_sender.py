import re
import sys

PAT = re.compile('^stdout$', re.I)
EXAMPLE = 'stdout'


class Sender:

    def __init__(self, ignored):
        pass

    async def send(self, payload):
        sys.stdout.write(payload)
        sys.stdout.write('\n')
