import asyncio
import os
import pytest
import tempfile
from unittest.mock import patch, call

from .. import imap_receiver
from ...mtc import *

_DATA_FILES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../messages/email')


class InMemoryQueue:
    def __init__(self):
        self.q = []
        
    def pop(self):
        if self.q:
            return self.q.pop(0)
        
    def push(self, bytes):
        self.q.append(bytes)


@pytest.fixture
def imap():
    return imap_receiver.Receiver(queue=InMemoryQueue())


@pytest.fixture
def scratch_space():
    x = tempfile.TemporaryDirectory()
    yield x
    x.cleanup()


@pytest.fixture
def testqueue(scratch_space):
    return imap_receiver.MailQueue(scratch_space.name)


def test_queue_pop_empty(testqueue):
    assert not bool(testqueue.pop())
    
    
def test_queue_push1(testqueue):
    testqueue.push(b'hi')
    assert bool(testqueue.pop())
    assert not bool(testqueue.pop())


def _get_sample_email(which):
    fname = os.path.join(_DATA_FILES_FOLDER, which + '.email')
    with open(fname, 'rb') as f:
        return f.read()


def _get_sample_email_tweaked(which, search_for, replace_with):
    return _get_sample_email(which).decode('utf-8').replace(search_for, replace_with).encode('utf-8')


# A class that short-circuits the logic in Receiver.__init__,
# since we don't need it.
class UninitedReceiver(imap_receiver.Receiver):
    def __init__(self):
        pass


@pytest.fixture
def urec():
    return UninitedReceiver()


def _get_mwc_from_sample_email(which):
    raw = _get_sample_email(which)
    receiver = UninitedReceiver()
    return receiver.bytes_to_mwc(raw)


def test_bytes_to_mwc_dp_body():
    wc = _get_mwc_from_sample_email('dp_body')
    assert bool(wc.plaintext)


def test_bytes_to_mwc_jwt_attached(urec):
    raw = _get_sample_email_tweaked('dw_attached', 'tiny.dw', 'tiny.jwt')
    wc = urec.bytes_to_mwc(raw)
    assert bool(wc.ciphertext)
    assert wc.tc.trust_for(CONFIDENTIALITY | INTEGRITY) == True


def test_bytes_to_mwc_dw_attached():
    wc = _get_mwc_from_sample_email('dw_attached')
    assert bool(wc.ciphertext)
    assert wc.tc.trust_for(CONFIDENTIALITY | INTEGRITY) == True


def test_bytes_to_mwc_dp_attached():
    wc = _get_mwc_from_sample_email('dp_attached')
    assert bool(wc.plaintext)
    assert wc.tc.trust_for(CONFIDENTIALITY | INTEGRITY) == False


def test_bytes_to_mwc_json_attached(urec):
    raw = _get_sample_email_tweaked('dp_attached', 'sample.dp', 'sample.json')
    wc = urec.bytes_to_mwc(raw)
    assert bool(wc.plaintext)
    assert wc.tc.trust_for(CONFIDENTIALITY | INTEGRITY) == False

@pytest.fixture
def inmemrec():
    return imap_receiver.Receiver(imap_receiver.EXAMPLE, InMemoryQueue())

@pytest.mark.asyncio
async def test_receive_from_local_queue(inmemrec):
    inmemrec.queue.push(_get_sample_email('dp_body'))
    assert bool(await inmemrec.receive())


@pytest.mark.asyncio
async def test_receive_over_mocked_imap(inmemrec):
    # Mock the class that imap_receiver creates when it builds an imap session.
    with patch(__name__ + '.imap_receiver.imaplib.IMAP4_SSL', autospec=True) as patched:
        # patched.return_value = the mock that's returned from the constructor
        # of the class.
        mock = patched.return_value
        # Make the login method of the mock instance return this tuple.
        mock.login.return_value = ('OK', None)
        # Have the .select() method return OK as bytes.
        mock.select.return_value = ('OK'.encode('utf-8'), None)
        # Have the .uid() method return data for uid('SEARCH') on first call,
        # data for uid('FETCH') on second call, and OK for uid('DELETE') on
        # third call.
        mock.uid.side_effect = [('OK', [b"id1"]),
                                    ('OK', [(b"id1", _get_sample_email('dw_attached'))]),
                                    ('OK', None)]
        assert bool(await inmemrec.receive())
        mock.login.assert_called_once()
        mock.select.assert_called_once()
        mock.uid.assert_called()
        mock.close.assert_called_once()


if __name__ == '__main__':
    asyncio.get_event_loop().set_debug(True)
    pytest.main(['-k', 'test_bytes_to_mwc_dp_body'])