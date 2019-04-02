import sys

class StdoutSender:

    def __init__(self):
        pass

    async def send(self, payload):
        sys.stdout.write(payload)
        sys.stdout.write('\n')
