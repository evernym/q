import datetime
import os
import email
import imaplib
import re
import logging

import agent_common
import mtc
import mwc

_default_imap_cfg = {
    'server': 'imap.gmail.com',
    'username': 'indyagent1@gmail.com',
    'password': 'I 0nly talk via email!',
    'ssl': '1',
    'port': '993'
}

_default_smtp_cfg = {
    'server': 'smtp.gmail.com',
    'username': 'indyagent1@gmail.com',
    'password': 'Open, sesame!',
    'port': '587'
}

def _apply_cfg(cfg, section, defaults):
    x = defaults
    if cfg and (section in cfg):
        src = cfg[section]
        for key in src:
            x[key] = src[key]
    return x

_bytes_type = type(b'')
_str_type = type('')
_tuple_type = type((1,2))

def _is_imap_ok(code):
    return bool(((type(code) == _bytes_type) and (len(code) == 2) and (code[0] == 79) and (code[1] == 75))
            or ((type(code) == _str_type) and (code == 'OK')))

def _check_imap_ok(returned):
    '''
    Analyze response from an IMAP server. If success, return data.
    Otherwise, raise a useful exception.
    '''
    if type(returned) == _tuple_type:
        code = returned[0]
        if _is_imap_ok(code):
            return returned[1]
    raise Exception(_describe_imap_error(returned))

def _describe_imap_error(returned):
    return 'IMAP server returned %s' % (returned)

_true_pat = re.compile('(?i)-?1|t(rue)?|y(es)?|on')

class MailQueue:
    '''
    Allow messages to be downloaded from remote imap server and cached locally, then
    fetched and processed in the order retrieved.
    '''
    def __init__(self, folder='queue'):
        self.folder = folder
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
    def push(self, bytes):
        fname = datetime.datetime.now().isoformat().replace(':', '-') + '.email'
        path = os.path.join(self.folder, fname)
        with open(path, 'wb') as f:
            f.write(bytes)
    def pop(self):
        items = os.listdir(self.folder)
        if items:
            items.sort()
            for item in items:
                path = os.path.join(self.folder, item)
                if path.endswith('.email') and os.path.isfile(path):
                    with open(path, 'rb') as f:
                        bytes = f.read()
                    os.unlink(path)
                    return bytes

_preferred_ext_pats = [
    re.compile(r'(?i).*\.aw$'),
    re.compile(r'(?i).*\.jwt$'),
    re.compile(r'(?i).*\.ap$'),
    re.compile(r'(?i).*\.json$')
]
_json_content_pat = re.compile(r'(?s)\s*{.*}\s*$')

def _find_a2a(msg):
    '''
    Look through an email to find the a2a message it contains. Return a mwc.MessageWithContext, which may
    be empty if nothing is found.

    Email messages are potentially very complex (multipart within multipart within multipart), with attachments
    and alternate versions of the same content (e.g., plain text vs. html). This method prefers to find an
    Agent Wire message (*.aw or *.jwt) as an attachment. Failing that, it looks for an Agent Plaintext
    message (*.ap or *.json or *.js) as an attachment. Failing that, it looks for an Agent Plaintext msg
    as a message body.
    '''
    best_part_ext_idx = 100
    best_part = None
    wc = mwc.MessageWithContext()
    for part in msg.walk():
        if not part.is_multipart():
            fname = part.get_filename()
            if fname:
                # Look at file extension. If it's one that we can handle,
                # see if it's the best attachment we've seen so far.
                for i in range(len(_preferred_ext_pats)):
                    pat = _preferred_ext_pats[i]
                    if pat.match(fname):
                        if i < best_part_ext_idx:
                            best_part = part
                            best_part_ext_idx = i
                            if i == 0:
                                # Stop: we found an attachment that was our top preference.
                                break
            elif (not wc) and (part.get_content_type() == 'text/plain'):
                this_txt = part.get_payload()
                if _json_content_pat.match(this_txt):
                    wc.msg = this_txt

    if best_part:
        wc.msg = best_part.get_payload()
        if best_part_ext_idx < 2:
            # TODO: decrypt and then, if authcrypted, add authenticated_origin in
            wc.tc = mtc.MessageTrustContext(confidentiality=True, integrity=True)
    elif wc.msg:
       wc.tc = mtc.MessageTrustContext()
    else:
        logging.error('No useful a2a message found in email. From: %s; Date: %s; Subject: %s.' % (
            msg.get('from', 'unknown sender'), msg.get('date', 'at unknown time'), msg.get('subject', 'empty')
        ))

    if not wc.sender:
        wc.sender = msg['from']
    return wc

class MailTransport:

    @staticmethod
    def bytes_to_a2a_message(bytes):
        '''
        Look through an email to find the a2a message it contains. Return a mwc.MessageWithContext, which may
        be empty if nothing is found.
        '''
        try:
            emsg = email.message_from_bytes(bytes)
            wc =_find_a2a(emsg)
            return wc
        except:
            agent_common.log_exception()
        return mwc.MessageWithContext()

    def __init__(self, cfg=None, queue=None):
        self.imap_cfg = _apply_cfg(cfg, 'imap', _default_imap_cfg)
        self.smtp_cfg = _apply_cfg(cfg, 'smtp', _default_smtp_cfg)
        if queue is None:
            queue = MailQueue()
        self.queue = queue

    def send(self, payload, destination):
        pass

    def receive(self):
        '''
        Get the next message from our inbox and return it as a Return a mwc.MessageWithContext, which may
        be empty if nothing is found.
        '''

        bytes = self.queue.pop()
        if bytes:
            return MailTransport.bytes_to_a2a_message(bytes)

        svr = self.imap_cfg['server']
        try:
            m = imaplib.IMAP4_SSL(svr) if _true_pat.match(self.imap_cfg['ssl']) else imaplib.IMAP4(svr)
            with m:
                _check_imap_ok(m.login(self.imap_cfg['username'], self.imap_cfg['password']))
                # Select Inbox, which is the default mailbox (folder).
                _check_imap_ok(m.select())
                # Get a list of all message IDs in the folder. We are calling .uid() here so
                # our list will come back with message IDs that are stable no matter how
                # the mailbox changes.
                message_ids = _check_imap_ok(m.uid('SEARCH', None, 'ALL'))
                if message_ids:
                    to_trash = []
                    try:
                        for i in range(0, len(message_ids)):
                            this_id = message_ids[i]
                            if this_id:
                                msg_data = _check_imap_ok(m.uid('FETCH', this_id, '(RFC822)'))
                                raw = msg_data[0][1]
                                self.queue.push(raw)
                                wc = MailTransport.bytes_to_a2a_message(raw)
                                to_trash.append(this_id)
                                return wc
                    finally:
                        if to_trash:
                            for id in to_trash:
                                m.uid('MOVE', id, '[Gmail]/Trash')
                        m.close()

        except KeyboardInterrupt:
            raise
        except:
            agent_common.log_exception()
        return mwc.MessageWithContext()