import pytest

from ..semver import Semver as S

VALID = {
    '0': (0, None, None, None, None),
    '0.2': (0, 2, None, None, None),
    '27.9': (27, 9, None, None, None),
    '1.0.3': (1, 0, 3, None, None),
    '0.42.92348+arm.3987': (0, 42, 92348, None, 'arm.3987'),
    '25.406.0-alpha1': (25, 406, 0, 'alpha1', None),
    '4.11.26-beta.2+x686.2948': (4, 11, 26, 'beta.2', 'x686.2948'),
    '1.2.3+build-alpha': (1, 2, 3, None, 'build-alpha'),
    '1.2.3--': (1, 2, 3, '-', None),  # Yes, this is really valid, per the spec.
    '1.2.3+-': (1, 2, 3, None, '-'),  # Ditto.
    b'1.2.3': (1, 2, 3, None, None),
    u'1.2.3': (1, 2, 3, None, None),
    S('1.1'): (1, 1, None, None, None)
}

INVALID = [
    '00', '1.00', '1.2.00', '.1.2', '1.2.', '1,2', ' 1.2', '1.2 ', '1..3',
    '1.2.3.4', '1.2a', '1a.2', '1.2.3a', '01', '1.01', '1.2.01',
    '1.2.3++', '1.2.3-+', '', None, (1, 2, 3, 'a', 'b'), ['1','.','2'],
    [1, 2, 3, 'a', 'b'],
    '1.2.3-a.03', '1.2.3+04.b'
]


def test_valid_semvers():
    ok = True
    for value, expected in VALID.items():
        # Using pytest.raises() didn't report which item had failed...
        try:
            s = S(value)
        except AssertionError:
            print("Should have been valid, but wasn't: " + value)
            ok = False
            continue
        assert s.major == expected[0]
        assert s.minor == expected[1]
        assert s.patch == expected[2]
        assert s.prerelease == expected[3]
        assert s.build == expected[4]
    assert ok

def test_invalid_semvers():
    ok = True
    for value in INVALID:
        # Using pytest.raises() didn't report which item had failed...
        try:
            s = S(value)
            print("Should have been invalid, but wasn't: " + value)
            ok = False
        except AssertionError:
            pass
        except TypeError:
            pass
    assert ok


def check_less_than(lesser, greater):
    try:
        assert lesser < greater
        assert lesser <= greater
        assert greater > lesser
        assert greater >= lesser
        assert lesser != greater
        assert greater != lesser
        assert not lesser == greater
        assert not greater == lesser
        assert lesser == lesser
        assert greater == greater
    except AssertionError:
        print('Lesser was %s, greater was %s' % (lesser, greater))
        raise


def test_sort_semvers_easy():
    s1 = S('1')
    s2 = S('2')
    s11 = S('1.1')
    s12 = S('1.2')
    s111 = S('1.1.1')
    s112 = S('1.1.2')
    s111a = S('1.1.1-a')
    s111b = S('1.1.1-b')
    s111x = S('1.1.1+x')
    s111y = S('1.1.1+y')

    check_less_than(s1, s2)
    check_less_than(s1, s11)
    check_less_than(s11, s12)
    check_less_than(s111, s112)
    check_less_than(s111a, s111)
    check_less_than(s111a, s111b)
    check_less_than(s111a, s111x)
    check_less_than(s111x, s111y)


def test_sort_semvers_prerelease():
    s1A = S('1.2.3-1.A')
    s1a = S('1.2.3-1.a')
    s11a = S('1.2.3-11.a')
    s1aa = S('1.2.3-1.aa')
    s1b = S('1.2.3-1.b')
    s2a = S('1.2.3-2.a')
    sa1 = S('1.2.3-a.1')
    sb1 = S('1.2.3-b.1')
    sa2 = S('1.2.3-a.2')

    check_less_than(s1a, s1b)
    check_less_than(s1b, s2a)
    check_less_than(s1a, sa1)
    check_less_than(s11a, sa1)
    check_less_than(s1a, s11a)
    check_less_than(sa1, sb1)
    check_less_than(sa1, sa2)
    check_less_than(s1A, s1a)
    check_less_than(s1a, s1aa)

def test_semver_str():
    ok = True
    for value in VALID:
        if not isinstance(value, str):
            continue
        try:
            assert value == str(S(value))
        except AssertionError:
            print('Converted %s --> semver --> str, got %s' % (value, str(S(value))))
            ok = False
    assert ok


a_1digit = S('1')
a = S('1.2')
aa = S('1.2.1')
aa_prerelease = S('1.2.1-alpha')
aa_build = S('1.2.1+9876')
aa_prebuild = S('1.2.1-alpha+9876')
ab = S('1.2.2')
b = S('1.3')
c = S('2.0')
d = S('0.9')
e = S('0.8')

def test_semver_sort_self_bug():
    assert not (aa_prerelease < aa_prerelease)

def test_semver_compatible_with_major_0():
    assert d.compatible_with(e) == 0
    assert d.compatible_with(d) == 2

def test_semver_compatible_with_self():
    assert a.compatible_with(a) == 2
    assert aa.compatible_with(aa) == 3
    assert aa_prerelease.compatible_with(aa_prerelease) == 4
    assert aa_build.compatible_with(aa_build) == 5
    assert aa_prebuild.compatible_with(aa_prebuild) == 5

def test_semver_compatible_with():
    assert a_1digit.compatible_with(c) == 0
    assert abs(a_1digit.compatible_with(a)) == 1
    assert abs(a.compatible_with(b)) == 1
    assert abs(a.compatible_with(aa)) == 2
    assert abs(a.compatible_with(ab)) == 2
    assert abs(aa.compatible_with(ab)) == 2

def test_semver_bad_regex_reports_bad_text():
    ex_text = ''
    try:
        s = S('abc')
        ex_text = "No exception raised!"
    except AssertionError as ex:
        ex_text = str(ex)
    assert 'abc' in ex_text