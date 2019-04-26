NULL_STATE = INVITED_STATE = REQUESTED_STATE = RESPONDED_STATE = COMPLETE_STATE = 1

RECEIVE_ERROR_EVENT = SEND_ERROR_EVENT = RECEIVE_ACK_EVENT = SEND_ACK_EVENT = RECEIVE_INVITATION_EVENT \
    = SEND_INVITATION_EVENT = RECEIVE_CONN_REQ_EVENT = SEND_CONN_REQ_EVENT = RECEIVE_CONN_RESP_EVENT \
    = SEND_CONN_RESP_EVENT = 1

from .. import state_machine

# Make string arrays for all the numeric constants above
STATE_NAMES, EVENT_NAMES = state_machine.configure_constants(globals())

CONNECTIONS_PROTOCOL_NAME = "connections"


def handle_common_event(state_machine, event):
    handled = False
    if event == SEND_ERROR_EVENT:
        state_machine.check_state_for_event(event, REQUESTED_STATE)
        state_machine.transition_to(NULL_STATE)
        handled = True
    elif event == RECEIVE_ERROR_EVENT:
        state_machine.check_state_for_event(event, REQUESTED_STATE, RESPONDED_STATE)
        state_machine.transition_to(INVITED_STATE)
        handled = True
    return handled


class Inviter(state_machine.StateMachineBase):
    def __init__(self, pre_hook=None, post_hook=None, error_hook=None):
        super().__init__(CONNECTIONS_PROTOCOL_NAME, 'inviter', STATE_NAMES, EVENT_NAMES,
                         NULL_STATE, pre_hook, post_hook, error_hook)

    def handle(self, event):
        if event == SEND_INVITATION_EVENT:
            self.check_state_for_event(event, NULL_STATE, INVITED_STATE)
            self.transition_to(INVITED_STATE, event)
        elif event == RECEIVE_CONN_REQ_EVENT:
            self.check_state_for_event(event, INVITED_STATE, REQUESTED_STATE, RESPONDED_STATE)
            self.transition_to(REQUESTED_STATE, event)
        elif event == SEND_CONN_RESP_EVENT:
            self.check_state_for_event(event, REQUESTED_STATE)
            self.transition_to(RESPONDED_STATE, event)
        elif event == RECEIVE_ACK_EVENT:
            self.check_state_for_event(event, RESPONDED_STATE, COMPLETE_STATE)
            self.transition_to(COMPLETE_STATE, event)
        else:
            if not handle_common_event(self, event):
                self.raise_anomaly(event)

class Invitee(state_machine.StateMachineBase):
    def __init__(self, pre_hook=None, post_hook=None, error_hook=None):
        super().__init__(CONNECTIONS_PROTOCOL_NAME, 'invitee', STATE_NAMES, EVENT_NAMES,
                         NULL_STATE, pre_hook, post_hook, error_hook)

    def handle(self, event):
        s = self.state
        if event == RECEIVE_INVITATION_EVENT:
            self.check_state_for_event(event, NULL_STATE, INVITED_STATE)
            self.transition_to(INVITED_STATE, event)
        elif event == SEND_CONN_REQ_EVENT:
            self.check_state_for_event(event, INVITED_STATE, REQUESTED_STATE, RESPONDED_STATE)
            self.transition_to(REQUESTED_STATE, event)
        elif event == RECEIVE_CONN_RESP_EVENT:
            self.check_state_for_event(event, REQUESTED_STATE)
            self.transition_to(RESPONDED_STATE, event)
        elif event == SEND_ACK_EVENT:
            self.check_state_for_event(event, RESPONDED_STATE, COMPLETE_STATE)
            self.transition_to(COMPLETE_STATE, event)
        else:
            if not handle_common_event(self, event):
                self.raise_anomaly(event)
