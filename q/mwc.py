import re

from . import mtc


def _make_json_key_value_pat(key):
    pat_txt = r'"%s"\s*:\s*"([^"]+)"' % key
    return re.compile(pat_txt, re.S)


_ID_PAT = _make_json_key_value_pat('@id')
_TYPE_PAT = _make_json_key_value_pat('@type')
_SQUEEZE_PAT = re.compile('\\s*\n[\t ]*')


class MessageWithContext:
    """
    Hold a message plus its associated trust context, sender, and other metadata.
    """
    def __init__(self, raw: str = None, tc: mtc.MessageTrustContext = None):
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
        self.raw = raw
        self.unpacked = None
        self.obj = None
        if tc is None:
            tc = mtc.MessageTrustContext()
        self.tc = tc

    @property
    def sender(self):
        if self.unpacked:
            return self.unpacked.get('sender_verkey', None)

    def __bool__(self):
        return bool(self.raw)

    def __str__(self):
        msg_fragment = None
        if self.raw:
            raw = self.raw[:300]
            good_descriptors = []
            m = _TYPE_PAT.search(raw)
            if m:
                m = m.group(1)
                i = m.find(';')
                if i:
                    m = '...' + m[i + 1:]
                good_descriptors.append('"@type":"%s"' % m)
            m = _ID_PAT.search(raw)
            if m:
                good_descriptors.append('"@id":"%s"' % m.group(1))
            if good_descriptors:
                msg_fragment = '{...%s...}' % ','.join(good_descriptors)
            else:
                if len(self.raw) <= 40:
                    msg_fragment = _SQUEEZE_PAT.sub(' ', raw)
                else:
                    msg_fragment = raw[:60].strip().replace('\r','')
                    msg_fragment = _SQUEEZE_PAT.sub(' ', msg_fragment)
                    msg_fragment = msg_fragment[:37] + '...'
        else:
            msg_fragment = '(empty)'
        sender = self.sender if self.sender else 'nobody'
        if len(sender) > 8:
            sender = sender[:8] + '...'
        return '%s from %s with %s' % (msg_fragment, sender, str(self.tc))

    def get_type(self):
        if self.raw:
            match = _TYPE_PAT.search(self.raw)
            if match:
                return match.group(1)


"""A special global constant representing degenerate, empty MessageWithContext."""
NULL_MWC = MessageWithContext()
