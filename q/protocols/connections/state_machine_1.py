from transitions import Machine

from q.protocols.exceptions import ProtocolAnomaly

NULL_STATE = INVITED_STATE = REQUESTED_STATE = RESPONDED_STATE = COMPLETE_STATE = 1

RECEIVE_ERROR_EVENT = SEND_ERROR_EVENT = RECEIVE_ACK_EVENT = SEND_ACK_EVENT = RECEIVE_INVITATION_EVENT \
    = SEND_INVITATION_EVENT = RECEIVE_CONN_REQ_EVENT = SEND_CONN_REQ_EVENT = RECEIVE_CONN_RESP_EVENT \
    = SEND_CONN_RESP_EVENT = 1

from .. import state_machine

# Make string arrays for all the numeric constants above
# TODO: Better keep lists for event names and state names and pass those lists rather than using globals
STATE_NAMES, EVENT_NAMES = state_machine.configure_constants(globals())

CONNECTIONS_PROTOCOL_NAME = "connections"


class NewStateMachineBase:
    def __init__(self, protocol, role, state_names, event_names, state, pre_hook=None, post_hook=None, error_hook=None):
        self._protocol = protocol
        self._role = role
        self._state_names = state_names
        self._event_names = event_names
        self._state = state
        self._pre_hook = pre_hook
        self._post_hook = post_hook
        self._error_hook = error_hook
        self._machine = Machine(model=self, states=state_names, initial=state)

    def raise_anomaly(self, event):
        raise ProtocolAnomaly(self.protocol, self.role, self.name_for_state(),
                              'Event "%s" isn\'t currently valid.' % self.name_for_event(event))

    def name_for_state(self, state=None):
        if state is None:
            state = self._state
        return self._state_names[state] if (0 <= state < len(self._state_names)) else str(state)

    def state_for_name(self, name):
        if name is None:
            name = self._state
        return self._state_names.index(name)

    def name_for_event(self, event):
        return self._event_names[event] if (0 <= event < len(self._event_names)) else str(event)

    def event_for_name(self, name):
        return self._event_names.index(name)

    @property
    def protocol(self):
        return self._protocol

    @property
    def role(self):
        return self._role

    @property
    def state(self):
        return self._state

    @property
    def pre_hook(self):
        return self._pre_hook

    @property
    def post_hook(self):
        return self._post_hook

    @property
    def error_hook(self):
        return self._error_hook

    def set_state_by_short_circuit(self, state: int):
        self._state = state

    def signal_error(self, state, msg):
        self._call_hook(self._error_hook, state, msg)

    def add_transition(self, event, initial_states, resulting_state):
        event = self.name_for_event(event)
        initial_states = [self.name_for_state(s) for s in initial_states]
        resulting_state = self.name_for_state(resulting_state)
        self._machine.add_transition(event, source=initial_states, dest=resulting_state,
                                     before=self._pre_hook, after=self._post_hook)

    def transition_to(self, state, event):
        # Question: Why is state necessary as an arg? The event should decide what the resulting state.
        # Ask permission before transitioning
        # if not _call_hook(self._pre_hook, state, event, True):
        #     return
        # self._state = state
        # return _call_hook(self._post_hook, state, event)
        event = self.name_for_event(event)
        try:
            self._machine.trigger(event)
        except AttributeError:
            self.raise_anomaly(event)
        self._state = self._machine.state

    def __str__(self):
        return self.role + '@' + self.protocol + ': ' + self.name_for_state()

    def to_json(self):
        return '{\n  "protocol": "%s",\n  "role": "%s",\n  "state": "%s"\n}' % (
            self.protocol, self.role, self.name_for_state())

    @staticmethod
    def _call_hook(hook, state, event, default_value=None):
        # TODO: Check if `hook` is a function with 2 args or better move that
        # check to `__init__` where hooks are accepted as args
        """
        Call `hook` if `hook` is not None else return `default_value`
        """
        if hook:
            return hook(state, event)
        return default_value


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


class Inviter(NewStateMachineBase):
    def __init__(self, pre_hook=None, post_hook=None, error_hook=None):
        super().__init__(CONNECTIONS_PROTOCOL_NAME, 'inviter', STATE_NAMES, EVENT_NAMES,
                         NULL_STATE, pre_hook, post_hook, error_hook)
        self.add_transition(SEND_INVITATION_EVENT, [NULL_STATE, INVITED_STATE], INVITED_STATE)
        self.add_transition(RECEIVE_CONN_REQ_EVENT, [INVITED_STATE, REQUESTED_STATE, RESPONDED_STATE], REQUESTED_STATE)
        self.add_transition(SEND_CONN_RESP_EVENT, REQUESTED_STATE, RESPONDED_STATE)
        self.add_transition(RECEIVE_ACK_EVENT, [RESPONDED_STATE, COMPLETE_STATE], COMPLETE_STATE)

    def handle(self, event):
        # Fixme: None arg
        self.transition_to(None, event)


class Invitee(NewStateMachineBase):
    def __init__(self, pre_hook=None, post_hook=None, error_hook=None):
        super().__init__(CONNECTIONS_PROTOCOL_NAME, 'invitee', STATE_NAMES, EVENT_NAMES,
                         NULL_STATE, pre_hook, post_hook, error_hook)
        self.add_transition(RECEIVE_INVITATION_EVENT, [NULL_STATE, INVITED_STATE], INVITED_STATE)
        self.add_transition(SEND_CONN_REQ_EVENT, [INVITED_STATE, REQUESTED_STATE, RESPONDED_STATE], REQUESTED_STATE)
        self.add_transition(RECEIVE_CONN_RESP_EVENT, REQUESTED_STATE, RESPONDED_STATE)
        self.add_transition(SEND_ACK_EVENT, [RESPONDED_STATE, COMPLETE_STATE], COMPLETE_STATE)
        self.add_transition(SEND_ERROR_EVENT, [RESPONDED_STATE, COMPLETE_STATE], COMPLETE_STATE)

    def handle(self, event):
        # Fixme: None arg
        self.transition_to(None, event)
