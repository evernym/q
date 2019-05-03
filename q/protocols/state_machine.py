from transitions import Machine
from transitions.core import listify, MachineError

from q.protocols.common import attribute_dict
from .exceptions import ProtocolAnomaly, UnknownEvent


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


class StateMachineBase:
    def __init__(self, protocol, role, state_names, event_names, start_state,
                 pre_hooks=None, post_hooks=None, error_hooks=None,
                 pre_hooks_early_abort=False, post_hooks_early_abort=False,
                 error_hooks_early_abort=False):
        """
        :param protocol:
        :param role:
        :param state_names:
        :param event_names:
        :param start_state:
        :param pre_hooks: Hooks executed before any transition is performed
        :param post_hooks: Hooks executed after any transition is performed
        :param error_hooks: Hooks executed if error occurs during any transition. Note that there is no error hook if error occurs during execution of an error hook
        :param pre_hooks_early_abort: If true and error is encountered during any pre-hook execution, skip executing more pre-hooks.
        :param post_hooks_early_abort: If true and error is encountered during any post-hook execution, skip executing more post-hooks.
        :param error_hooks_early_abort: If true and error is encountered during any error-hook execution, skip executing more error-hooks.
        """
        self._protocol = protocol
        self._role = role
        self._state_names = state_names
        self._event_names = event_names
        self._state = start_state
        self._pre_hooks = []
        self._post_hooks = []
        self._error_hooks = []
        self._add_pre_hooks(pre_hooks)
        self._add_post_hooks(post_hooks)
        self._add_error_hooks(error_hooks)
        self._machine = Machine(model='self', states=state_names, initial=self.name_for_state(start_state),
                                send_event=True)

        # TODO: Implement later, will require more changes in transition
        # self.pre_hooks_early_abort = pre_hooks_early_abort
        # self.post_hooks_early_abort = post_hooks_early_abort
        # self.error_hooks_early_abort = error_hooks_early_abort

    def add_transition(self, event_name, initial_states, resulting_state,
                       pre_hooks=None, post_hooks=None, error_hooks=None):
        """
        Declare a transition that is valid only if the current state is one of `initial_states`.
        The state after the transition will be `resulting_state`.
        :param event_name:
        :param initial_states: Can be a string if single state or a list if many states. Can accept wildcard "*" for all possible states.
        :param resulting_state:
        :return:
        """
        event_name = self.name_for_event(event_name)
        initial_states = [self.name_for_state(s) for s in listify(initial_states)]
        resulting_state = self.name_for_state(resulting_state)
        # Not adding self._pre_hooks or self._post_hooks to `add_transition` for better control.
        # Otherwise self._pre_hooks+listify(pre_hooks) etc can be done.
        self._machine.add_transition(event_name, source=initial_states, dest=resulting_state,
                                     before=listify(pre_hooks),
                                     after=listify(post_hooks))

    def transition_to(self, event):
        """
        Handle event and possibly transition to a new state.
        Raises an exception if event is not known or transition is not valid or some hook results in error.
        If any pre-hook results in error, transition is not performed but post hooks are still executed.
        Error hooks are called if transition causes error
        :param event:
        :return:
        """
        event_name = self.name_for_event(event)

        # Tracks whether errors have occurred
        error_flag = 0

        # Creating object to match the structure of Event data object passed to hooks by transitions library
        event_data = attribute_dict()
        event_data.event = attribute_dict()
        event_data.state = attribute_dict()
        event_data.event.name = event_name
        event_data.state.name = self.state_name

        for h in self._pre_hooks:
            try:
                h(event_data)
            except Exception as e:
                print("Encountered exception while triggering pre-hook {} for {}", h, event_name)
                print(e)
                # To have flexibility in early return, hook methods can have an attribute set that indicates
                # whether to abort and return or continue executing next hook
                error_flag = 1

        if error_flag == 0:
            try:
                self._machine.trigger(event_name)
                self._state = self.state_for_name(self._machine.state)
            except AttributeError:
                # Not a foolproof implementation as some before/after callback can also result in AttributeError.
                # Change in transitions needed which raises specific error when event is not present
                error_flag = 2
            except MachineError:
                self._call_error_hooks(event_name, event_data)
                error_flag = 3
            # If any other exception occurs, let the caller catch it.

        event_data.state.name = self.state_name
        for h in self._post_hooks:
            try:
                h(event_data)
            except Exception as e:
                print("Encountered exception while triggering post-hook {} for {}", h, event_name)
                print(e)
                return -2

        if error_flag == 0:
            return 1
        if error_flag == 2:
            self.raise_unknown_event_error(event)
        if error_flag == 3:
            self.raise_anomaly(event)

    def raise_unknown_event_error(self, event):
        raise UnknownEvent(self.protocol, self.role, self.name_for_state(), event)

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
    def state_name(self):
        return self.name_for_state()

    @property
    def pre_hooks(self):
        return self._pre_hooks

    @property
    def post_hooks(self):
        return self._post_hooks

    @property
    def error_hooks(self):
        return self._error_hooks

    def set_state_by_short_circuit(self, state: int):
        self._machine.set_state(self.name_for_state(state))
        self._state = state

    def signal_error(self, state, msg):
        for h in self._error_hooks:
            self._call_hook(h, state, msg)

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

    def _add_pre_hooks(self, pre_hooks):
        self._pre_hooks += listify(pre_hooks)

    def _add_post_hooks(self, post_hooks):
        self._post_hooks += listify(post_hooks)

    def _add_error_hooks(self, error_hooks):
        self._error_hooks += listify(error_hooks)

    def _call_error_hooks(self, event_name, event_data):
        """
        Call error hooks. Return 1 only if error hooks executed successfully
        """
        error_flag = 0
        for h in self._error_hooks:
            try:
                h(event_data)
            except Exception as e:
                print("Encountered exception while triggering error-hook {} for {}", h, event_name)
                print(e)
                error_flag = 1
                # To have flexibility in early return, hook methods can have an attribute set that indicates
                # whether to abort and return or continue executing next hook

        return 1 - error_flag
