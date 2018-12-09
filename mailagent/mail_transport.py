import os, imaplib, re, traceback, sys, email



#import asyncio
#import time
import re
import logging
#import smtplib
#from email.mime.multipart import MIMEMultipart
#from email.mime.text import MIMEText
#from email.mime.base import MIMEBase
#from email import encoders
#from indy import crypto, did, wallet

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

class MailTransport:

    def __init__(self, cfg=None):
        self.imap_cfg = _apply_cfg(cfg, 'imap', _default_imap_cfg)
        self.smtp_cfg = _apply_cfg(cfg, 'smtp', _default_smtp_cfg)

    def send(self, payload, destination):
        pass

    def receive(self):
        '''Get the next message from our inbox and return it. If no messages are currently available,
        return None.'''

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
                                msg = email.message_from_bytes(msg_data[0][1])
                                to_trash.append(this_id)
                                return msg
                    finally:
                        if to_trash:
                            for id in to_trash:
                                m.uid('MOVE', id, '[Gmail]/Trash')
                        m.close()
                logging.info('got inside')

        except:
            typ, text, trace = sys.exc_info()
            frame = traceback.extract_tb(trace, 1)[0]
            text = str(text)
            if text[-1].isalpha():
                text += '.'
            logging.error("%s at %s#%s: %s Code was: %s" % (typ.__name__, frame.filename, frame.lineno, text, frame.line.strip()))
