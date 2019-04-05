import re

# This pat isn't perfect. It's very close, but it doesn't enforce
# the restriction that numeric values in prerelease and build can't
# have leading zeros. It seemed easier to enforce this in the ctor.
PAT = re.compile(r'''(?i)                # ignore case
^                                        # match from beginning only
(0|[1-9]\d{0,2})                         # major (group 1)
(?:
  \.(0|[1-9]\d{0,2})                     # dot minor (group 2)
  (?:
    \.(0|[1-9]\d{0,6})                   # dot patch (group 3)
    (?:
      -([0-9a-z-]+(?:\.[0-9a-z-]+)*)     # dash prerelease (group 4)
    )?                                   # prerelease is optional
    (?:
      \+([0-9a-z-]+(?:\.[0-9a-z-]+)*)    # plus build (group 5)
    )?                                   # build is optional
  )?                                     # patch is optional
)?                                       # minor is optional
$                                        # match all the way to the end
''', re.VERBOSE)

_LEADING_ZEROS_PAT = re.compile(r'(^|[.])0\d+($|[.])')
_NOT_PURE_NUMBERS_PAT = re.compile('[^0-9]')


def _compare_attrib(a, b, attrib_name):
    a_val = getattr(a, attrib_name)
    b_val = getattr(b, attrib_name)
    if a_val is None:
        return 0 if b_val is None else -1
    elif b_val is None:
        return 1
    else:
        if a_val < b_val: return -1
        return 1 if a_val > b_val else 0


def _compare_prerelease(a, b):
    if a is None:
        # With prerelease, None comes *after* a value
        return 0 if b is None else 1
    elif b is None:
        return -1
    else:
        # Have to compare each segment, either numerically
        # or lexically.
        a = a.split('.')
        b = b.split('.')
        len_b = len(b)
        for i in range(len(a)):
            if i > len_b:
                return 1
            # Numeric segments come before non-numeric.
            a_num = not bool(_NOT_PURE_NUMBERS_PAT.search(a[i]))
            b_num = not bool(_NOT_PURE_NUMBERS_PAT.search(b[i]))
            if a_num:
                if b_num:
                    if a[i] != b[i]:
                        a_n = int(a[i])
                        b_n = int(b[i])
                        return a_n - b_n
                else:
                    return -1
            elif b_num:
                return 1
            else:
                if a[i] < b[i]: return -1
                if a[i] > b[i]: return 1
        # If we get here, then none of the segments in a
        # differed with b. Does b have more segments?
        return 0 if len_b == i else -1


def _compare(a, b):
    i = a.major - b.major
    if i != 0:
        return i
    i = _compare_attrib(a, b, 'minor')
    if i or a.minor is None: return i
    i = _compare_attrib(a, b, 'patch')
    if i or a.patch is None: return i
    # Semver says that prerelease versions sort before same-numbered
    # versions without prerelease decorators, and that they compare
    # numerically when they have numbers, and lexically when they have
    # alphas. See https://semver.org/#spec-item-11.
    i = _compare_prerelease(a.prerelease, b.prerelease)
    if i != 0: return i
    # If we get here, the only remaining attribute we can compare is
    # build. Semver says that builds are NOT a differentiator; two
    # semver values that differ only here are equal in terms of
    # precedence. However, we want python sorting to be deterministic.
    # The way we'll have our cake and eat it too is that we'll return
    # a float for our answer here. If cast to an integer, the distinction
    # will disappear--but if kept as a float, it will give a total
    # ordering.
    if a.build is None:
        # With prerelease, None comes *after* a value
        return 0 if b.build is None else -0.4
    elif b.build is None:
        return .4
    return 0.4 if a.build > b.build else (-0.4 if a.build < b.build else 0)


class Semver:

    def __init__(self, value):
        def complain(hint):
            msg = 'Bad semver value (%s). Study semver.org syntax carefully.' % hint
            raise AssertionError(msg)
        if not value: complain('empty')
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        elif isinstance(value, Semver):
            value = value.value
        m = PAT.match(value)
        if not m:
            complain('regex fails')
        self.value = value
        g = m.groups()
        self.major = int(g[0])
        if g[1]:
            self.minor = int(g[1])
            if g[2]:
                self.patch = int(g[2])
                if g[3]:
                    if _LEADING_ZEROS_PAT.search(g[3]):
                        complain('leading zeros')
                    self.prerelease = g[3]
                else:
                    self.prerelease = None
                if g[4]:
                    if _LEADING_ZEROS_PAT.search(g[4]):
                        complain('leading zeros')
                    self.build = g[4]
                else:
                    self.build = None
            else:
                self.patch = self.prerelease = self.build = None
        else:
            self.minor = self.patch = self.prerelease = self.build = None

    def __str__(self):
        return self.value

    def __lt__(self, other):
        return _compare(self, other) < 0

    def __le__(self, other):
        return _compare(self, other) <= 0

    def __eq__(self, other):
        return self.value == other.value

    def __ge__(self, other):
        return _compare(self, other) >= 0

    def __gt__(self, other):
        return _compare(self, other) > 0

    def __ne__(self, other):
        return self.value != other.value

    def __hash__(self):
        return hash(self.value)