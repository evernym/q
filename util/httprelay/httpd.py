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
TRANSPORT = 'mail_transport.py'
MY_FOLDER = os.path.abspath(os.path.dirname(__file__))
IMPORT_FOLDERS = ['.', MY_FOLDER, os.path.abspath(os.path.join(MY_FOLDER, '../../mailagent'))]
for folder in IMPORT_FOLDERS:
    if os.path.isfile(os.path.join(folder, TRANSPORT)):
        sys.path.append(folder)
        break
import mail_transport

PORT = 8001

PENDING_PAT = re.compile('(?i)/pending/([a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12})$')
IN_PAT = re.compile('(?i)/in/?$')
OUT_PAT = re.compile('(?i)/out/([a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12})$')

def _match_special(path):
    for pat in [PENDING_PAT, IN_PAT, OUT_PAT]:
        m = pat.match(path)
        if m:
            return m, pat
    return None, None


trans = mail_transport.MailTransport(queue=mail_transport.MailQueue(os.path.expanduser('~/.httprelay/queue')))

class Handler(http.server.SimpleHTTPRequestHandler):

    def translate_path(self, path):
        m = OUT_PAT.match(path)
        if m:
            return trans.queue.path_for_id(m.group(1))
        return super().translate_path(path)

    def do_GET(self):
        try:
            m, pat = _match_special(self.path)
            if m:
                if pat == OUT_PAT:
                    super().do_GET()
                elif pat == PENDING_PAT:
                    id = m.group(1)
                    path = trans.queue.path_for_id(id)
                    if os.path.isfile(path):
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
                    id = str(uuid.uuid4())
                    clen = int(self.headers.get('Content-Length', 0))
                    ct = self.headers.get('Content-Type', 'application/octet-stream')
                    if clen:
                        postvars = None
                        ctype, pdict = cgi.parse_header(ct)
                        if ctype == 'multipart/form-data':
                            postvars = cgi.parse_multipart(self.rfile, pdict)
                        elif ctype == 'application/x-www-form-urlencoded':
                            postvars = urllib.parse.parse_qs(self.rfile.read(clen), keep_blank_values=1)
                        else:
                            txt = self.rfile.read(clen).decode('utf-8')
                        if postvars is not None:
                            if len(postvars):
                                txt = postvars.get('msg', postvars.keys()[0])
                            else:
                                txt = ''
                        trans.queue.push(txt.encode('utf-8'), id)
                    link = '/pending/' + id
                    self.send_status(202, {'Location':link})
                else:
                    self.send_error(405, explain='You must use GET with %s' % self.path)
            else:
                self.send_error(404)
                self.send_response()
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
    http.server.BaseHTTPRequestHandler.error_message_format = '''<html>
<head profile="http://www.w3.org/2005/10/profile">
    <link rel="stylesheet" type="text/css" href="/default.css">
    <link rel="icon" type="image/png" href="/favicon.png">
    <title>HTTP Relay - Error %(code)d</title>
</head>
<body>
    <h1>HTTP Relay - Error %(code)d</h1>
    <p>Message: %(message)s.</p>
    <p>Error code explanation: %(code)s - %(explain)s.</p>
</body>
</html>
'''
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            try:
                print("Serving at port %s..." % PORT)
                httpd.serve_forever()
            except KeyboardInterrupt:
                sys.stdout.write('\r' + ' '*20 + '\n')
        finally:
            httpd.socket.close()

