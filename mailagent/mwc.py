import re

import mtc

_id_pat = re.compile(r'"@id"\s*:\s*"([^"]+)"', re.S)
_squeeze_pat = re.compile('\\s*\n[\t ]*')

class MessageWithContext:
    '''
    Hold a message plus its associated trust context, sender, and other metadata.
    '''
    def __init__(self, msg:str=None, tc:mtc.MessageTrustContext=None):
        self.msg = msg
        if tc is None:
            tc = mtc.MessageTrustContext()
        self.tc = tc
    def __bool__(self):
        return bool(self.msg)
    def __str__(self):
        msg_fragment = None
        if self.msg:
            m = _id_pat.search(self.msg)
            if m:
                msg_fragment = '{..."@id":"%s"...}' % m.group(1)
            else:
                if len(self.msg) <= 40:
                    msg_fragment = _squeeze_pat.sub(' ', self.msg)
                else:
                    msg_fragment = self.msg[:60].strip().replace('\r','')
                    msg_fragment = _squeeze_pat.sub(' ', msg_fragment)
                    msg_fragment = msg_fragment[:37] + '...'
        else:
            msg_fragment = '(empty)'
        return '%s with %s' % (msg_fragment, str(self.tc))

'''A special global constant representing degenerate, empty MessageWithContext.'''
NULL_MWC = MessageWithContext()
