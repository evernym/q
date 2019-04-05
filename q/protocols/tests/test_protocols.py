from ... import protocols


def test_plugins_load():
    assert len(protocols.HANDLERS_BY_MSG_TYPE) >= 2


if __name__ == '__main__':
    import pytest
    pytest.main([__file__])