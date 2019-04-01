import re
import os

import file_transport
import http_sender
import http_receiver
import smtp_sender

IMAP_PAT = re.compile('^([A-Za-z0-9][^@:]*):([^@]*)@(.+):([0-9]{1,5})$')

def load(t, is_dest):
    http_matched = False
    if IMAP_PAT.match(t):
        raise ValueError('IMAP transport not yet supported.')
    elif smtp_sender.PAT.match(t):
        if is_dest:
            return smtp_sender.SmtpSender(t)
        else:
            raise ValueError("SMTP transport can only be a dest, not a source. Use IMAP instead.")
    if http_receiver.PAT.match(t):
        if not is_dest:
            return http_receiver.HttpReceiver(t)
        else:
            http_matched = True
    if http_sender.PAT.match(t):
        if is_dest:
            return http_sender.HttpSender(t)
        else:
            http_matched = True
    if http_matched:
        raise ValueError("HTTP arg reverses src and dest syntax.")
    else:
        t = os.path.expanduser(t)
        if not os.path.isdir(t):
            raise ValueError('Folder "%s" does not exist.' % t)
        return file_transport.FileTransport(t, is_dest)
