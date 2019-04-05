import asyncio
import datetime
import email
import imaplib
import logging
import os
import re

from .. import log_helpers
from .. import mtc
from .. import mwc

PAT = re.compile('^imap://([A-Za-z0-9][^@:]*):([^@]*)@(.+):([0-9]{1,5})$')
EXAMPLE = 'imap://user:pass@imapserver:993'

_TRUE_PAT = re.compile('(?i)-?1|t(rue)?|y(es)?|on')
_EMAIL_EXT = '.email'
_BYTES_TYPE = type(b'')
_STR_TYPE = type('')
_TUPLE_TYPE = type((1,2))


def _check_imap_ok(returned):
    """
    Analyze response from an IMAP server. If success, return data.
    Otherwise, raise a useful exception.
    """
    if type(returned) == _TUPLE_TYPE:
        code = returned[0]
        # Look at response from IMAP server. Decide if it is OK or not.
        # (Different versions of the IMAP library give different data types
        # for the return value. Some return a string, and some return a
        # bytes obj with byte[0] = 'O' and byte[1] = 'K'. This handles
        # both variants.
        if bool(((type(code) == _BYTES_TYPE) and (len(code) == 2) and (code[0] == 79) and (code[1] == 75))
            or ((type(code) == _STR_TYPE) and (code == 'OK'))):
            return returned[1]
    raise Exception('IMAP server returned %s' % returned)


def _timestamp_as_fname():
    return datetime.datetime.now().isoformat().replace(':', '-')


class MailQueue:
    """
    Allow messages to be downloaded from remote imap server and cached locally, then
    fetched and processed in the order retrieved.
    """
    def __init__(self, folder='mailqueue'):
        self.folder = folder
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

    def path_for_id(self, msg_id):
        return os.path.join(self.folder, msg_id + _EMAIL_EXT)

    def push(self, msg_bytes, msg_id=None):
        if not msg_id:
            msg_id = _timestamp_as_fname()
        path = os.path.join(self.folder, msg_id + _EMAIL_EXT)
        with open(path, 'wb') as f:
            f.write(msg_bytes)
        return msg_id

    def pop(self):
        items = os.listdir(self.folder)
        if items:
            items.sort()
            for item in items:
                path = os.path.join(self.folder, item)
                if path.endswith(_EMAIL_EXT) and os.path.isfile(path):
                    with open(path, 'rb') as f:
                        msg_bytes = f.read()
                    os.unlink(path)
                    return bytes


_PREFERRED_EXT_PATS = [
    re.compile(r'(?i).*\.dw$'),
    re.compile(r'(?i).*\.jwt$'),
    re.compile(r'(?i).*\.dp$'),
    re.compile(r'(?i).*\.json$'),
    re.compile(r'(?i).*\.dat$')
]
_JSON_CONTENT_PAT = re.compile(r'(?s)\s*({.*})')

_BAD_MSGS_FOLDER = 'bad_msgs'


def _save_bad_msg(msg):
    if not os.path.isdir(_BAD_MSGS_FOLDER):
        os.makedirs(_BAD_MSGS_FOLDER)
    fname = os.path.join(_BAD_MSGS_FOLDER, _timestamp_as_fname() + _EMAIL_EXT)
    with open(fname, 'wb') as f:
        f.write(bytes(msg))
    return fname


class Receiver:

    def __init__(self, uri, queue=None):
        m = PAT.match(uri)
        self.user = m.group(1)
        self.password = m.group(2)
        self.host = m.group(3)
        self.port = int(m.group(4))
        self.ssl = bool(self.port != 143)
        if queue is None:
            queue = MailQueue()
        self.queue = queue

    def bytes_to_mwc(self, msg_bytes):
        """
        Look through an email to find the didcomm message it contains. Return a
        mwc.MessageWithContext, which may be empty if nothing is found.

        Email messages are potentially very complex (multipart within multipart within
        multipart), with attachments and alternate versions of the same content (e.g.,
        plain text vs. html). This method prefers to find an Agent Wire message (*.aw or
        *.jwt) as an attachment. Failing that, it looks for an Agent Plaintext message
        (*.ap or *.json or *.js) as an attachment. Failing that, it looks for an Agent
        Plaintext msg as a message body.
        """
        try:
            msg = email.message_from_bytes(msg_bytes)
            best_part_ext_idx = 100
            best_part = None
            wc = mwc.MessageWithContext()
            for part in msg.walk():
                if not part.is_multipart():
                    fname = part.get_filename()
                    if fname:
                        # Look at file extension. If it's one that we can handle,
                        # see if it's the best attachment we've seen so far.
                        for i in range(len(_PREFERRED_EXT_PATS)):
                            pat = _PREFERRED_EXT_PATS[i]
                            if pat.match(fname):
                                if i < best_part_ext_idx:
                                    best_part = part
                                    best_part_ext_idx = i
                                    if i == 0:
                                        # Stop: we found an attachment that was our top preference.
                                        break
                    elif (not wc) and (part.get_content_type() == 'text/plain'):
                        this_txt = part.get_payload()
                        match = _JSON_CONTENT_PAT.match(this_txt)
                        if match:
                            wc.raw = match.group(1)

            if best_part:
                wc.raw = best_part.get_payload(decode=True)
                if best_part_ext_idx < 2:
                    # TODO: decrypt and then, if authcrypted, add authenticated_origin in
                    wc.tc = mtc.MessageTrustContext(confidentiality=True, integrity=True)
            elif wc.raw:
                wc.tc = mtc.MessageTrustContext()
            else:
                fname = _save_bad_msg(msg)
                logging.error('No useful a2a message found in %s/%s. From: %s; Date: %s; Subject: %s.' % (
                    _BAD_MSGS_FOLDER, fname,
                    msg.get('from', 'unknown sender'), msg.get('date', 'at unknown time'), msg.get('subject', 'empty')
                ))
            return wc
        except:
            log_helpers.log_exception()
        return mwc.MessageWithContext()

    def get_imap_session(self):
        host = self.host
        cls = imaplib.IMAP4_SSL if self.ssl else imaplib.IMAP4
        imap = cls(host)
        try:
            _check_imap_ok(imap.login(self.user, self.password))
            # Select Inbox, which is the default mailbox (folder).
            _check_imap_ok(imap.select())
            return imap
        except:
            imap.close()
            raise

    def get_pending_msg_ids(self, imap):
        # Get a list of all message IDs in the folder. We are calling .uid() here so
        # our list will come back with message IDs that are stable no matter how
        # the mailbox changes.
        message_ids = _check_imap_ok(imap.uid('SEARCH', None, "ALL"))
        msg_ids_str = message_ids[0].decode("utf-8")
        return msg_ids_str.split(' ')

    def fetch(self, imap, msg_id):
        msg_data = _check_imap_ok(imap.uid('FETCH', msg_id, '(RFC822)'))
        return msg_data[0][1]

    def delete(self, imap, msg_id):
        imap.uid('STORE', msg_id, '+X-GM-LABELS', '\\Trash')

    async def receive(self, their_email = None, initial=False):
        """
        Get the next message from our inbox and return it as a
        mwc.MessageWithContext, which may be empty if nothing is found.
        """

        def do_receive():
            # First see if we have any messages queued on local hard drive.
            bytes = self.queue.pop()
            if bytes:
                return self.bytes_to_mwc(bytes)

            try:
                imap = self.get_imap_session()
                with imap:
                    message_ids_list = self.get_pending_msg_ids(imap)
                    if message_ids_list:
                        to_trash = []
                        try:
                            # Download all messages from remote server to local hard drive
                            # so we don't depend on server again for a while.
                            for i in range(0, len(message_ids_list)):
                                this_id = message_ids_list[i]
                                if this_id:
                                    raw = self.fetch(imap, this_id)
                                    self.queue.push(raw)
                                    to_trash.append(this_id)
                            # If we downloaded anything, return first item.
                            msg_bytes = self.queue.pop()
                            if msg_bytes:
                                return self.bytes_to_mwc(msg_bytes)
                        finally:
                            if to_trash:
                                for msg_id in to_trash:
                                    self.delete(imap, msg_id)
                            # Not technically required, since we're inside a 'with'
                            # statement--but graceful.
                            imap.close()

            except KeyboardInterrupt:
                # Don't bother logging this, but do raise it.
                raise
            except:
                log_helpers.log_exception()

            # If we got here, we were unable to fetch a message. Return an empty one.
            return mwc.MessageWithContext()

        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, do_receive)
        return await future
