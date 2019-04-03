from .. import transports


def test_plugins_load():
    assert transports.SENDERS
    assert transports.RECEIVERS


def check_example_against_pattern(item):
    assert item.pat.match(item.example)


def test_sender_examples_match_patterns():
    for item in transports.SENDERS:
        check_example_against_pattern(item)


def test_receiver_examples_match_patterns():
    for item in transports.RECEIVERS:
        check_example_against_pattern(item)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__])