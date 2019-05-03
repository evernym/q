NULL_STATE = INVITED_STATE = REQUESTED_STATE = RESPONDED_STATE = COMPLETE_STATE = 1

RECEIVE_ERROR_EVENT = SEND_ERROR_EVENT = RECEIVE_ACK_EVENT = SEND_ACK_EVENT = RECEIVE_INVITATION_EVENT \
    = SEND_INVITATION_EVENT = RECEIVE_CONN_REQ_EVENT = SEND_CONN_REQ_EVENT = RECEIVE_CONN_RESP_EVENT \
    = SEND_CONN_RESP_EVENT = 1

from .. import state_machine

# Make string arrays for all the numeric constants above
# TODO: Better keep lists for event names and state names and pass those lists rather than using globals
STATE_NAMES, EVENT_NAMES = state_machine.configure_constants(globals())

CONNECTIONS_PROTOCOL_NAME = "connections"


# TODO: Following logic is supported by transitions library. Should be replaced.
def handle_common_event(state_machine, event):
    handled = False
    if event == SEND_ERROR_EVENT:
        state_machine.add_transition(event, REQUESTED_STATE, NULL_STATE)
        handled = True
    elif event == RECEIVE_ERROR_EVENT:
        state_machine.add_transition(event, [REQUESTED_STATE, RESPONDED_STATE], INVITED_STATE)
        handled = True
    return handled


class Inviter(state_machine.StateMachineBase):
    def __init__(self, pre_hook=None, post_hook=None, error_hook=None):
        super().__init__(CONNECTIONS_PROTOCOL_NAME, 'inviter', STATE_NAMES, EVENT_NAMES,
                         NULL_STATE, pre_hook, post_hook, error_hook)
        self.add_transition(SEND_INVITATION_EVENT, [NULL_STATE, INVITED_STATE], INVITED_STATE)
        self.add_transition(RECEIVE_CONN_REQ_EVENT, [INVITED_STATE, REQUESTED_STATE, RESPONDED_STATE], REQUESTED_STATE)
        self.add_transition(SEND_CONN_RESP_EVENT, REQUESTED_STATE, RESPONDED_STATE)
        self.add_transition(RECEIVE_ACK_EVENT, [RESPONDED_STATE, COMPLETE_STATE], COMPLETE_STATE)

    def handle(self, event):
        self.transition_to(event)


class Invitee(state_machine.StateMachineBase):
    def __init__(self, pre_hook=None, post_hook=None, error_hook=None):
        super().__init__(CONNECTIONS_PROTOCOL_NAME, 'invitee', STATE_NAMES, EVENT_NAMES,
                         NULL_STATE, pre_hook, post_hook, error_hook)
        self.add_transition(RECEIVE_INVITATION_EVENT, [NULL_STATE, INVITED_STATE], INVITED_STATE)
        self.add_transition(SEND_CONN_REQ_EVENT, [INVITED_STATE, REQUESTED_STATE, RESPONDED_STATE], REQUESTED_STATE)
        self.add_transition(RECEIVE_CONN_RESP_EVENT, REQUESTED_STATE, RESPONDED_STATE)
        self.add_transition(SEND_ACK_EVENT, [RESPONDED_STATE, COMPLETE_STATE], COMPLETE_STATE)
        self.add_transition(SEND_ERROR_EVENT, [RESPONDED_STATE, COMPLETE_STATE], COMPLETE_STATE)

    def handle(self, event):
        self.transition_to(event)
