import os
import pytest
import tempfile

from ... import transports


def test_plugins_load():
    assert len(transports.SENDERS) > 2
    assert len(transports.RECEIVERS) > 2


def check_examples(item, tweaks):
    examples = item.examples.replace('~/myfile.dat', tweaks[0]).replace(
        '~/myfolder', tweaks[1])
    for example in examples.split('|'):
        assert item.match(example)


@pytest.fixture(scope="module")
def file_and_folder():
    x = tempfile.TemporaryDirectory()
    fname = os.path.join(x.name, 'x')
    with open(fname, 'wb') as f:
        pass
    yield fname, x.name
    x.cleanup()


def test_receiver_examples_match_patterns(file_and_folder):
    for item in transports.RECEIVERS:
        check_examples(item, file_and_folder)


def test_sender_examples_match_patterns(file_and_folder):
    for item in transports.SENDERS:
        check_examples(item, file_and_folder)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__])