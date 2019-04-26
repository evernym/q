import datetime
import json

from .mtc import *
from .data_formats import *

_ID_PAT = make_json_key_value_pat('@id')
_TYPE_PAT = make_json_key_value_pat('@type')
_SQUEEZE_PAT = re.compile('\\s*\n[\t ]*')
_MSG_TYPE_URI_PAT = re.compile(r'(.*?)([a-z0-9._-]+)/(\d[^/]*)/([a-z0-9._-]+)$')

MAX_MESSAGE_SIZE = 1024 * 1024 * 10

def _check_size(data, tc: MessageTrustContext, force = False):
    if force:
        tc.undefine(SIZE_OK)
    if force or (tc.trust_for(SIZE_OK) is None):
        if data and (len(data) > MAX_MESSAGE_SIZE):
            raise ValueError("Size exceeds %d; message can't be processed." % MAX_MESSAGE_SIZE)
        tc.affirm(SIZE_OK)


class MessageWithContext:
    """
    Hold a message plus its associated trust context, sender, and other metadata.

    The message must be init'ed with raw message content. Preferably, this content is a
    byte array, but strings also work. The raw content may be encrypted or not. If encrypted,
    then the raw content is assigned to .ciphertext, and .plaintext is None until a
    decryption is performed and .plaintext is assigned. If not encrypted, then .ciphertext is
    None, but .plaintext is immediately useful.

    .plaintext is always a string.

    Whenever .plaintext is assigned, .obj is also built. .obj is a dict built by deserializing
    .plaintext. It may be None, if deserialization has failed.
    """
    def __init__(self, raw: bytes = None, tc: MessageTrustContext = None):
        self.in_time = datetime.datetime.utcnow()
        if tc is None:
            tc = MessageTrustContext()
        self.tc = tc
        self._ciphertext = None
        self._plaintext = None
        self._obj = None
        self.id = None
        self.thid = None
        self.type = None
        self.interaction = None
        self.state_machine = None
        _check_size(raw, tc)
        try_deserialize = True
        if is_likely_json(raw):
            if is_likely_wire_format(raw):
                self._ciphertext = raw
                # We can't affirm anything about the ciphertext until we try to decrypt
            else:
                tc.deny(CONFIDENTIALITY | INTEGRITY | AUTHENTICATED_ORIGIN)
        else:
            tc.deny(DESERIALIZE_OK)
            try_deserialize = False
        # If we get here, we don't have reason to believe the message is encrypted.
        # Therefore, treat it like plaintext.
        self._set_plaintext_and_obj(raw, try_deserialize)

    @property
    def sender(self):
        if self.obj:
            return self.obj.get('sender_verkey', None)

    @property
    def ciphertext(self):
        return self._ciphertext

    @property
    def plaintext(self):
        return self._plaintext

    @plaintext.setter
    def plaintext(self, value):
        _check_size(value, self.tc, force=True)
        self._set_plaintext_and_obj(value)

    def _set_plaintext_and_obj(self, value, try_deserialize=True):
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        self._plaintext = value
        self._obj = self.type = self.id = self.thid = None
        if value:
            if try_deserialize:
                self.tc.undefine(DESERIALIZE_OK)
                try:
                    obj = json.loads(value)
                    self._obj = obj
                    self.tc.affirm(DESERIALIZE_OK)
                    self.type = obj.get('@type')
                    self.id = obj.get('@id')
                    self.thid = obj.get('~thread', {}).get('thid')
                except:
                    self.tc.deny(DESERIALIZE_OK) # Let caller discover problem on their own

    @property
    def obj(self):
        return self._obj

    def __bool__(self):
        return bool(self._ciphertext) or bool(self._plaintext) or bool(self._obj)

    def __str__(self):
        """
        Provides a short, friendly description of the message, suitable for logging or adding
        to a problem report.
        """
        msg_fragment = None
        txt = self.plaintext
        if txt:
            txt = txt[:300]
        else:
            txt = self.ciphertext
            if txt:
                txt = txt[:300]
                if isinstance(txt, bytes):
                    txt = txt.decode('utf-8')
        if txt:
            good_descriptors = []
            m = _TYPE_PAT.search(txt)
            if m:
                mturi = m.group(1)
                m = _MSG_TYPE_URI_PAT.match(mturi)
                if m:
                    m = '...' + m.group(2) + '/' + m.group(3) + '/' + m.group(4)
                else:
                    i = mturi.find(';')
                    if i:
                        m = '...' + mturi[i + 1:]
                    else:
                        m = mturi
                good_descriptors.append('"@type":"%s"' % m)
            m = _ID_PAT.search(txt)
            if m:
                good_descriptors.append('"@id":"%s"' % m.group(1))
            if good_descriptors:
                msg_fragment = '{...%s...}' % ','.join(good_descriptors)
            else:
                if len(txt) <= 40:
                    msg_fragment = _SQUEEZE_PAT.sub(' ', txt)
                else:
                    msg_fragment = txt[:60].strip().replace('\r','')
                    msg_fragment = _SQUEEZE_PAT.sub(' ', msg_fragment)
                    msg_fragment = msg_fragment[:37] + '...'
        else:
            msg_fragment = '(empty)'
        sender = self.sender if self.sender else 'nobody'
        if len(sender) > 8:
            sender = sender[:8] + '...'
        return '%s from %s with mtc=%s' % (msg_fragment, sender, str(self.tc))

    def get_type(self):
        if self.ciphertext:
            match = _TYPE_PAT.search(self.ciphertext)
            if match:
                return match.group(1)


"""A special global constant representing degenerate, empty MessageWithContext."""
NULL_MWC = MessageWithContext()
