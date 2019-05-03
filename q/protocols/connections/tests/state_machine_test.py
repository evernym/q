import pytest

from ..state_machine import *


@pytest.fixture
def er():
    yield Inviter()


@pytest.fixture
def ee():
    yield Invitee()


def test_invitee_starts_null(ee):
    assert ee.state == NULL_STATE


def test_inviter_starts_null(er):
    assert er.state == NULL_STATE


def test_invitee_normal_sequence(ee):
    ee.handle(RECEIVE_INVITATION_EVENT)
    assert ee.state == INVITED_STATE
    ee.handle(SEND_CONN_REQ_EVENT)
    assert ee.state == REQUESTED_STATE
    ee.handle(RECEIVE_CONN_RESP_EVENT)
    assert ee.state == RESPONDED_STATE
    ee.handle(SEND_ACK_EVENT)
    assert ee.state == COMPLETE_STATE


def test_inviter_normal_sequence(er):
    er.handle(SEND_INVITATION_EVENT)
    assert er.state == INVITED_STATE
    er.handle(RECEIVE_CONN_REQ_EVENT)
    assert er.state == REQUESTED_STATE
    er.handle(SEND_CONN_RESP_EVENT)
    assert er.state == RESPONDED_STATE
    er.handle(RECEIVE_ACK_EVENT)
    assert er.state == COMPLETE_STATE
