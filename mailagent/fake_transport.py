class FakeTransport:

    def __init__(self):
        self.queue = []

    def push(self, msg):
        self.queue.push(msg)

    def pop(self):
        if self.queue:
            return self.queue.pop(0)

    def send(self, payload, destination):
        pass

    def receive(self):
        return self.pop()