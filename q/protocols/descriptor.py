import re

_MAX_FQNAME_LEN = 240
_FQNAME_PAT = re.compile('(?i)[a-z0-9][^\r\n\t]{1,%d}[a-z0-9]' % (_MAX_FQNAME_LEN - 2))
_DELIM_CHARS = ';/!?&'


class Descriptor:

    def __init__(self, fqname, version):
        if not _FQNAME_PAT.match(fqname):
            raise AssertionError('Bad fqname "{fqname}". Expected a short single-line str that begins and ends with alphanumeric.')
        self.fqname = fqname
        self._name_idx = -1
        self.version = version

    def _split(self):
        if self._name_idx == -1:
            self._name_idx = 0
            i = len(self.fqname) - 2
            while i > 0:
                if self.fqname[i] in _DELIM_CHARS:
                    self._name_idx = i + 1
                    break
                i -= 1

    @property
    def name(self):
        self._split()
        return self.fqname[self._name_idx:]

    @property
    def prefix(self):
        self._split()
        return self.fqname[:self._name_idx]

    def __str__(self):
        return '%s/%s' % (self.fqname, self.version)