import http.server
import socketserver
import traceback
import cgi
import urllib
import re
import threading

import mwc

PAT = re.compile('^http(s)?://([^:/]+)(?::([0-9]{1,5}))?(?:/(.*))?$')

class WebServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class HttpReceiver:
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

        # We have a challenge because our web server creates a new instance of
        # Handler class every time a request arrives, and we can't pass args to
        # its constructor. Yet we want each new instance to be connected back to
        # the queue of the HttpReceiver object. The way around this is to create
        # a class factory (a function that takes a class and creates a new variation
        # of it, where the args we want are known to all instances of the class,
        # not just to a specific instance). See https://stackoverflow.com/a/21631948/2953158.
        def make_handler_class(queue, queue_lock):
            class Handler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    # This is the magic. We're giving the instance a variable
                    # without passing the variable in our constructor. We can
                    # do this because the class is being created by a function
                    # that knows what the class needs. NOTE: we have to init
                    # these variables before calling super's init, because
                    # the ctor of super actually processes the request.
                    self.queue = queue
                    self.queue_lock = queue_lock
                    super(Handler, self).__init__(*args, **kwargs)
                def do_HEAD(self):
                    self.send_error(405, explain='Only POST is supported.')
                def do_GET(self):
                    self.send_error(405, explain='Only POST is supported.')
                def do_POST(self):
                    try:
                        clen = int(self.headers.get('Content-Length', 0))
                        ct = self.headers.get('Content-Type', 'application/octet-stream')
                        txt = None
                        if clen:
                            postvars = None
                            ctype, pdict = cgi.parse_header(ct)
                            if ctype == 'multipart/form-data':
                                postvars = cgi.parse_multipart(self.rfile, pdict)
                            elif ctype == 'application/x-www-form-urlencoded':
                                postvars = urllib.parse.parse_qs(self.rfile.read(clen))
                            else:
                                txt = self.rfile.read(clen).decode('utf-8')
                            if postvars is not None:
                                matches = postvars.get('msg', postvars.get(b'msg', ''))
                                if matches:
                                    txt = matches[0]
                        if txt:
                            # Remember what was just posted. The relay that uses us will
                            # shortly ask us for it.
                            with self.queue_lock:
                                self.queue.append(mwc.MessageWithContext(txt))
                            self.send_status(202)
                        else:
                            self.send_error(400, explain='No useful payload. Expected msg from form or query string')
                    except:
                        ex = traceback.format_exc()
                        self.send_error(500, explain=ex)
                def send_status(self, code, strings=None):
                    self.send_response(code)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    txt = "HTTP status code %d" % code
                    self.wfile.write(txt.encode("utf-8"))
            return Handler

        # Use our class factory function to define a special subclass of Handler
        # that knows about the queue and queue_lock it needs.
        HandlerClass = make_handler_class(self.queue, self.queue_lock)
        self.keep_serving = True
        def run_web_server():
            with WebServer(("", self.port), HandlerClass) as httpd:
                try:
                    httpd.timeout = 1
                    while self.keep_serving:
                        httpd.handle_request()
                finally:
                    httpd.socket.close()
        self.server_thread = threading.Thread(target=run_web_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop_serving(self):
        self.keep_serving = False

    def peek(self):
        with self.queue_lock:
            if self.queue:
                return True

    def receive(self):
        with self.queue_lock:
            if self.queue:
                return self.queue.pop(0)
