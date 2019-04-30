import threading
import weakref

_all = {}
_all_lock = threading.Lock()


class Queue:
    def __init__(self, name):
        self.name = name
        self.lock = threading.Lock()
        self.items = []
        with _all_lock:
            _all[name] = self

    async def send(self, payload):
        # Adds element to the end of queue
        with self.lock:
            self.items.append(payload)
            return True

    async def peek(self, filter=None):
        with self.lock:
            if self.items:
                return True

    async def receive(self, filter=None):
        # Removes element from beginning of the queue
        with self.lock:
            if self.items:
                return self.items.pop(0)


class RamTransport:

    def __init__(self, name):
        self.queue = None
        with _all_lock:
            if name in _all:
                self.queue = _all[name]()
        if self.queue is None:
            self.queue = Queue(name)
            with _all_lock:
                _all[name] = weakref.ref(self.queue)
        self.endpoint = 'ram://' + name

    async def send(self, payload, endpoint):
        return await self.queue.send(payload)

    async def peek(self, filter=None):
        return await self.queue.peek(filter)

    async def receive(self, filter=None):
        return await self.queue.receive(filter)
