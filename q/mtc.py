import re

# These constants all need to begin with a different letter, and must be
# declared at the very top of the module, to make automated stringization
# work.

"""Size isn't too big"""
SIZE_OK = 1
"""Deserializes as JSON"""
JSON_OK = 2
"""Has correct keys/structure for type"""
KEYS_OK = 4
"""Field values are correct size and data types"""
VALUES_OK = 8
"""Message was sent encrypted"""
CONFIDENTIALITY = 16
"""Message was tamper-proof"""
INTEGRITY = 32
"""Message was sent by someone other than anonymous"""
AUTHENTICATED_ORIGIN = 64
"""Message origin can be proved to third party"""
NONREPUDIATION = 128

# Now derive other constants out of these
def _derive_constants(g):
    max_flag = 0
    x = {}
    for key in g:
        if key.startswith('_'):
            continue
        n = g[key]
        if not isinstance(n, int):
            continue
        if n > max_flag:
            max_flag = n
        i = 1
        while n > 1:
            n /= 2
            i += 1
        x[i] = key
    labels = []
    initials = []
    i = 1
    n = 1
    while n <= max_flag:
        label = x[i].replace('_OK', '').lower()
        labels.append(label)
        initials.append(label[0])
        n *= 2
        i += 1
    return labels, initials, max_flag

FLAG_LABELS, FLAG_INITIALS, _MAX_FLAG = _derive_constants(globals())
del _derive_constants


class MessageTrustContext:
    """
    Describe the trust guarantees associated with a given message.
    See http://bit.ly/2UutabT for more information.
    """
    def __init__(self, flags: int = 0):
        self.flags = flags

    @classmethod
    def from_initials(cls, initials):
        n = 0
        if initials:
            for c in initials:
                try:
                    i = FLAG_INITIALS.index(c.lower())
                    n |= 2**i
                except ValueError:
                    pass
        return MessageTrustContext(n)

    @classmethod
    def from_labels(cls, labels):
        n = 0
        if labels:
            if isinstance(labels, str):
                labels = labels.split(',')
            labels = [x.strip() for x in labels]
            labels = [x.lower() for x in labels if x]
            for c in labels:
                try:
                    i = FLAG_LABELS.index(c)
                    n |= 2**i
                except ValueError:
                    pass
        return MessageTrustContext(n)

    @property
    def initials(self):
        """
        Return a string that summarizes which flags are set.
        """
        if self.flags == 0:
            return "0"
        x = ''
        i = 0
        n = 1
        while n < _MAX_FLAG:
            if (self.flags & n) == n:
                x += FLAG_INITIALS[i]
            n *= 2
            i += 1
        return x

    @property
    def labels(self):
        """
        Return a string that summarizes which flags are set.
        """
        if self.flags == 0:
            return "0"
        x = []
        i = 0
        n = 1
        while n < _MAX_FLAG:
            if (self.flags & n) == n:
                x.append(FLAG_LABELS[i])
            n *= 2
            i += 1
        return ', '.join(x)

    def __str__(self):
        return self.initials