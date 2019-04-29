from .exceptions import ProtocolAnomaly


def configure_constants(g):
    """
    Assign unique integer value to each state name constant and event name constant.
    Values of state constants and event constants are not mutually exclusive.
    :param g: The dictionary to look for state names and event names
    :return: Returns 2 lists, for state names and event names
    """
    sn = []
    en = []
    for key in g:
        if key[0] != '_':
            value = g[key]
            if isinstance(value, int):
                if key.endswith('_STATE'):
                    g[key] = len(sn)
                    sn.append(key.replace('_STATE', '').lower())
                elif key.endswith('_EVENT'):
                    g[key] = len(en)
                    en.append(key.replace('_EVENT', '').lower())
    return sn, en


def _call_hook(hook, state, event, default_value=None):
    # TODO: Move it to StateMachineBase
    # TODO: Check if `hook` is a function or better move that check to `__init__`
    """
    Call `hook` if `hook` is not None else return `default_value`
    """
    if hook:
        return hook(state, event)
    return default_value


# TODO: The following logic can be declaratively achieve using transitions library.
#  Transitions can be constrained from a list of sources to a destination, pre/post hooks,
class StateMachineBase:
    def __init__(self, protocol, role, state_names, event_names, state, pre_hook=None, post_hook=None, error_hook=None):
        self._protocol = protocol
        self._role = role
        self._state_names = state_names
        self._event_names = event_names
        self._state = state
        self._pre_hook = pre_hook
        self._post_hook = post_hook
        self._error_hook = error_hook

    def raise_anomaly(self, event):
        raise ProtocolAnomaly(self.protocol, self.role, self.name_for_state(),
                              'Event "%s" isn\'t currently valid.' % self.name_for_event(event))

    def check_state_for_event(self, event, *valid_states):
        if self.state not in valid_states:
            self.raise_anomaly(event)

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
        _call_hook(self._error_hook, state, msg)

    def transition_to(self, state, event):
        # Ask permission before transitioning
        if not _call_hook(self._pre_hook, state, event, True):
            return
        self._state = state
        return _call_hook(self._post_hook, state, event)

    def __str__(self):
        return self.role + '@' + self.protocol + ': ' + self.name_for_state()

    def to_json(self):
        return '{\n  "protocol": "%s",\n  "role": "%s",\n  "state": "%s"\n}' % (
            self.protocol, self.role, self.name_for_state())
