import re

def make_json_key_value_pat(key):
    pat_txt = r'"%s"\s*:\s*"([^"]+)"' % key
    return re.compile(pat_txt, re.S)

def make_json_key_pat(key):
    pat_txt = r'"%s"\s*:' % key


_BASE64_PAT = re.compile('^[a-zA-Z0-9/=]+$')

def is_base64(data):
    return _BASE64_PAT.match(data)


no_byte_converter = lambda x: x

def _get_byte_converter(data):
    return ord if isinstance(data, str) else no_byte_converter


def _span(big, big_idx, end, small, to_byte):
    while big_idx != end:
        byte = to_byte(big[big_idx])
        if byte not in small:
            break
        big_idx += 1
    return big_idx


_WHITESPACE_CHARS = b' \r\n\t'
_OPEN_BRACE_BYTE = 123 # {
_CLOSE_BRACE_BYTE = 125 # }
def is_likely_json(data: bytes) -> bool:
    if data:
        to_byte = _get_byte_converter(data)
        end = len(data)
        i = _span(data, 0, end, _WHITESPACE_CHARS, to_byte)
        if i < end:
            byte = to_byte(data[i])
            if byte != _OPEN_BRACE_BYTE:
                return False
            j = len(data)
            while j > i:
                j -= 1
                byte = to_byte(data[j])
                if byte not in _WHITESPACE_CHARS:
                    return byte == _CLOSE_BRACE_BYTE
            return False
    return False


_PROTECTED_KEY_PAT = re.compile(r'.{0,8192}"protected"\s*:\s*"', re.S)
_CIPHERTEXT_KEY_PAT = re.compile(r'.{0,8192}"ciphertext"\s*:\s*"', re.S)
_DOUBLE_QUOTE_BYTE = 34 # "
_COLON_BYTE = 58

def _match_bytes(big, big_idx, small):
    n = len(small)
    for i in range(n):
        if big[i + big_idx] != small[i]:
            return 0
    return n

def is_likely_wire_format(data, known_json=False):
    if not data:
        return False

    # A message can't be in wire format unless it has at least 4 fields, and the
    # "protected" field needs to contain at least about 100 bytes of base64 data
    # to be even marginally believable with zero recipients. So it's safe to assume
    # that anything less than about 120 bytes is not valid wire format.
    if len(data) < 120:
        return False

    if not known_json:
        if not is_likely_json(data):
            return False

    # We might get very large messages, and we don't want to run huge scans over them.
    # If we have a string, we use special regexes that limit how much gets scanned before
    # we give up. If we have bytes, we use an algorithm that's sort of like a limited
    # regex. We should be able to find a field named "protected" or "ciphertext" that's
    # quoted and followed by whitespace+colon+whitespace+double_quote in the first few
    # KB of a message.
    if isinstance(data, str):
        return _PROTECTED_KEY_PAT.match(data) or _CIPHERTEXT_KEY_PAT.match(data)

    n = min(len(data) - 100, 8192)
    for i in range(n):
        byte = data[i]
        if byte == _DOUBLE_QUOTE_BYTE:
            x = _match_bytes(data, i, b'"protected"')
            if not x:
                x = _match_bytes(data, i, b'"ciphertext"')
            if x:
                i = _span(data, i + x, n, _WHITESPACE_CHARS, no_byte_converter)
                if i < n and data[i] == _COLON_BYTE:
                    i = _span(data, i + 1, n, _WHITESPACE_CHARS, no_byte_converter)
                    return data[i] == _DOUBLE_QUOTE_BYTE
