from aiohttp import web
import traceback
import re
import threading
import logging

from .. import mwc

PAT = re.compile('^http(s)?://([^:/]+)(?::([0-9]{1,5}))?(?:/(.*))?$')
EXAMPLE = 'http://localhost:8080'

def _resp(code, msg):
    return web.Response(text='%d %s' % (code, msg), headers={"Content-Type": "text/plain"})

class Receiver:
    def __init__(self, uri):
        m = PAT.match(uri)
        if m.group(1) == 's':
            raise ValueError("Can't listen over TLS (no certs available).")
        if m.group(2) not in ['localhost', '127.0.0.1']:
            raise ValueError('Can only listen on localhost or 127.0.0.1.')
        self.port = int(m.group(3))
        if m.group(4):
            raise ValueError("Can't bind to a path--only to host and port.")
        self.queue = []
        self.queue_lock = threading.Lock()
        self.web_server = None

    async def accept(self, request):
        try:
            if request.body_exists:
                logging.debug('About to await request')
                txt = await request.content.read()
                logging.debug('Responding to %s' % request.method)
                with self.queue_lock:
                    self.queue.append(mwc.MessageWithContext(txt))
                return _resp(202, 'OK')
            else:
                return _resp(400, 'No useful payload. Expected msg from form or query string')
        except:
            ex = traceback.format_exc()
            return _resp(500, ex)

    async def start(self):
        logging.debug('About to start web server on port %d' % self.port)
        app = web.Application()
        app.add_routes([web.post('/', self.accept)])
        self.web_server = web.AppRunner(app)
        await self.web_server.setup()
        site = web.TCPSite(self.web_server, 'localhost', self.port)
        try:
            await site.start()
            logging.debug('Started web server on port %d' % self.port)
        except:
            ex = traceback.format_exc()
            logging.debug('Failed to start web server. ' + ex)

    async def stop(self):
        with self.queue_lock:
            if self.web_server:
                await self.web_server.cleanup()
                self.web_server = None

    async def peek(self):
        with self.queue_lock:
            if not self.web_server:
                await self.start()
            if self.queue:
                return True

    async def receive(self):
        with self.queue_lock:
            if not self.web_server:
                await self.start()
            if self.queue:
                return self.queue.pop(0)
