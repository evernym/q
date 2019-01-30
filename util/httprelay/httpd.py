#!/usr/bin/env python

import http.server
import socketserver
import uuid
import re
import traceback
import cgi
import urllib

import os
import sys

# Support running mail transport either from its location
# relative to this utility, or from CWD, or from same folder
# as this script.
TRANSPORT = 'file_transport.py'
MY_FOLDER = os.path.abspath(os.path.dirname(__file__))
IMPORT_FOLDERS = ['.', MY_FOLDER, os.path.abspath(os.path.join(MY_FOLDER, '../../mailagent'))]
for folder in IMPORT_FOLDERS:
    if os.path.isfile(os.path.join(folder, TRANSPORT)):
        sys.path.append(folder)
        break
import file_transport

PORT = 8000

PENDING_PAT = re.compile('(?i)/pending/([a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12})$')
IN_PAT = re.compile('(?i)/in/?$')
OUT_PAT = re.compile('(?i)/out/([a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12})$')

def _match_special(path):
    for pat in [PENDING_PAT, IN_PAT, OUT_PAT]:
        m = pat.match(path)
        if m:
            return m, pat
    return None, None

trans = file_transport.FileTransport(os.path.expanduser('~/.httprelay/queue'))

class Handler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        try:
            m, pat = _match_special(self.path)
            if m:
                id = m.group(1)
                ready = trans.peek(id)
                if pat == OUT_PAT:
                    if ready:
                        mwc = trans.receive(id)
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/ssi-agent-wire')
                        self.send_header('Content-Length', len(mwc.msg))
                        self.end_headers()
                        self.wfile.write(mwc.msg)
                    else:
                        self.send_error(404, 'Response not yet available.')
                elif pat == PENDING_PAT:
                    if ready:
                        self.send_status(303, {'Location':'/out/' + id})
                    else:
                        self.send_status(200)
                else:
                    self.send_error(405, explain='You must use POST with %s' % self.path)
            else:
                # Serve static html.
                super().do_GET()
        except:
            self.send_error(500, explain=traceback.format_exc())

    def do_POST(self):
        try:
            m, pat = _match_special(self.path)
            if m:
                if pat == IN_PAT:
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
                        id = trans.send(txt)
                        link = '/pending/' + id
                        self.send_status(202, {'Location':link})
                    else:
                        self.send_error(400, explain='No useful payload. Expected msg from form or query string')
                else:
                    self.send_error(405, explain='You must use GET with %s' % self.path)
            else:
                self.send_error(404)
        except:
            self.send_error(500, explain=traceback.format_exc())
    
    def send_status(self, code, strings=None):
        fname = os.path.join(MY_FOLDER, str(code) + '.html')
        with open(fname, 'rt') as f:
            txt = f.read()
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        if strings:
            txt = txt % strings
            if 'Location' in strings:
                self.send_header('Location', strings['Location'])
        self.end_headers()
        self.wfile.write(txt.encode("utf-8"))

if __name__ == '__main__':
    # Change the format of error messages so they use our preferred style.
    with open(os.path.join(MY_FOLDER, 'error.html'), 'rt') as f:
        http.server.BaseHTTPRequestHandler.error_message_format = f.read()
    # Run a server until Ctrl+C
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            try:
                print("Serving at port %s..." % PORT)
                httpd.serve_forever()
            except KeyboardInterrupt:
                sys.stdout.write('\r' + ' '*20 + '\n')
        finally:
            httpd.socket.close()

