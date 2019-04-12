from ..data_formats import *

def test_not_is_likely_json():
    assert not is_likely_json(None)
    assert not is_likely_json("test")
    assert not is_likely_json({})

def test_is_likely_json():
    assert is_likely_json('{}')
    assert is_likely_json('{ abc xyz }')
    assert is_likely_json('\r\r\n\t { abc xyz }  \t\n')
    assert is_likely_json(b'{}')
    assert is_likely_json(b'{ abc xyz }')
    assert is_likely_json(b'\r\r\n\t { abc xyz }  \t\n')

def test_not_is_likely_wire_format():
    assert not is_likely_wire_format(None)
    assert not is_likely_wire_format("test")
    assert not is_likely_wire_format({})
    assert not is_likely_wire_format('{}')
    assert not is_likely_wire_format('{ abc xyz }')
    filler = 'x'*8192
    assert not is_likely_wire_format('{ "iv": "' + filler + '", "protected": "xyz" }')
    assert not is_likely_wire_format('{ "iv": "' + filler + '", "ciphertext": "xyz" }')

ACTUAL_WIRE_MESSAGE = """
{
    "protected"
    :       "eyJlbmMiOiJ4Y2hhY2hhMjBwb2x5MTMwNV9pZXRmIiwidHlwIjoiSldNLzEuMCIsImFsZyI6IkF1dGhjcnlwdCIsInJlY2lwaWVudHMiOlt7ImVuY3J5cHRlZF9rZXkiOiJMNVhEaEgxNVBtX3ZIeFNlcmFZOGVPVEc2UmZjRTJOUTNFVGVWQy03RWlEWnl6cFJKZDhGVzBhNnFlNEpmdUF6IiwiaGVhZGVyIjp7ImtpZCI6IkdKMVN6b1d6YXZRWWZOTDlYa2FKZHJRZWpmenRONFhxZHNpVjRjdDNMWEtMIiwiaXYiOiJhOEltaW5zdFhIaTU0X0otSmU1SVdsT2NOZ1N3RDlUQiIsInNlbmRlciI6ImZ0aW13aWlZUkc3clJRYlhnSjEzQzVhVEVRSXJzV0RJX2JzeERxaVdiVGxWU0tQbXc2NDE4dnozSG1NbGVsTThBdVNpS2xhTENtUkRJNHNERlNnWkljQVZYbzEzNFY4bzhsRm9WMUJkREk3ZmRLT1p6ckticUNpeEtKaz0ifX0seyJlbmNyeXB0ZWRfa2V5IjoiZUFNaUQ2R0RtT3R6UkVoSS1UVjA1X1JoaXBweThqd09BdTVELTJJZFZPSmdJOC1ON1FOU3VsWXlDb1dpRTE2WSIsImhlYWRlciI6eyJraWQiOiJIS1RBaVlNOGNFMmtLQzlLYU5NWkxZajRHUzh1V0NZTUJ4UDJpMVk5Mnp1bSIsIml2IjoiRDR0TnRIZDJyczY1RUdfQTRHQi1vMC05QmdMeERNZkgiLCJzZW5kZXIiOiJzSjdwaXU0VUR1TF9vMnBYYi1KX0pBcHhzYUZyeGlUbWdwWmpsdFdqWUZUVWlyNGI4TVdtRGR0enAwT25UZUhMSzltRnJoSDRHVkExd1Z0bm9rVUtvZ0NkTldIc2NhclFzY1FDUlBaREtyVzZib2Z0d0g4X0VZR1RMMFE9In19XX0=",
    "iv": "ZqOrBZiA-RdFMhy2",
    "ciphertext" : "K7KxkeYGtQpbi-gNuLObS8w724mIDP7IyGV_aN5AscnGumFd-SvBhW2WRIcOyHQmYa-wJX0MSGOJgc8FYw5UOQgtPAIMbSwVgq-8rF2hIniZMgdQBKxT_jGZS06kSHDy9UEYcDOswtoLgLp8YPU7HmScKHSpwYY3vPZQzgSS_n7Oa3o_jYiRKZF0Gemamue0e2iJ9xQIOPodsxLXxkPrvvdEIM0fJFrpbeuiKpMk",
    "tag": "kAuPl8mwb0FFVyip1omEhQ=="
}
"""

def test_is_likely_wire_format():
    assert is_likely_wire_format(ACTUAL_WIRE_MESSAGE)
    assert is_likely_wire_format(ACTUAL_WIRE_MESSAGE.encode('utf-8'))