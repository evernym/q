from ..common import *

def test_msg_type_split_normal():
    assert msg_type_split(
        "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/notification/1.0/problem-report") == (
        "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/notification", "notification", "1.0", "problem-report")

def test_msg_type_split_no_prefix():
    assert msg_type_split(
        "did:sov:BzCbsNYhMrjHiqZDTUASHg.spec.notification/1.0/problem-report") == (
        "did:sov:BzCbsNYhMrjHiqZDTUASHg.spec.notification",
        "did:sov:BzCbsNYhMrjHiqZDTUASHg.spec.notification", "1.0", "problem-report")

def test_msg_type_split_no_version():
    assert msg_type_split(
        "x;y//problem-report") == ("x;y", "y", "", "problem-report")
