def _compare(a, b):
    if not b: return 1
    if isinstance(b, str):
        b = DID(b)
    if a.value > b.value: return 1
    if a.value < b.value: return -1
    return 0

class DID:
    def __init__(self, value):
        if isinstance(value, DID):
            self.value == value
        else:
            self.value = value if value.startswith('did:') else 'did:sov:' + value

    def _split(self):
        j = -1
        i = self.value.index(':')
        if i > -1:
            j = self.value.index(':', i + 1)
        return i, j

    @property
    def nsi(self):
        i, j = self._split()
        if j > -1:
            return self.value[j+1:]

    @property
    def method(self):
        i, j = self._split()
        if i > -1 and j > i:
            return self.value[i+1:j]

    def __str__(self):
        return self.value

    def __lt__(self, other):
        return _compare(self, other) < 0

    def __le__(self, other):
        return _compare(self, other) <= 0

    def __eq__(self, other):
        return _compare(self, other) == 0

    def __ge__(self, other):
        return _compare(self, other) >= 0

    def __gt__(self, other):
        return _compare(self, other) > 0

    def __ne__(self, other):
        return _compare(self, other) != 0

    def __hash__(self):
        return hash(self.value)