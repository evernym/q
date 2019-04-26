import asyncio
import random
import re
import threading

_PAT = re.compile('^tcp://[1-9][0-9]{3,4}$')
_EXAMPLE = 'tcp://8080'

HOST = '127.0.0.1'

class _QueueReader:
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
    async def __call__(self, reader, writer):
        data = []
        while True:
            more = await reader.read(1000)  # Max number of bytes to read
            if not more:
                break
            data += more
            if len(data) < 1000:
                break
        if data:
            with self.lock:
                self.queue.append(data)

class Receiver:
    def __init__(self, port=0, *ignored):
        if port == 0:
            port = random.randint(1025, 65000)
        self._port = port
        self._server = None
        self._queue_reader = _QueueReader()

    @property
    def port(self):
        return self._port

    async def start(self):
        if self._server is None:
            self._server = await asyncio.start_server(self._queue_reader, HOST, self.port)

    def __del__(self):
        if self._server:
            self._server.close()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        if self._server:
            self._server.close()
            self._handle = None

    async def receive(self):
        qr = self._queue_reader
        data = None
        with qr.lock:
            if qr.queue:
                data = qr.queue.pop()
        return data


