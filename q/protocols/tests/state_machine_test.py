import json
import pytest

from ..exceptions import ProtocolAnomaly, UnknownEvent

"""
Invent simple state machines to order fast food. The script these state machines
goes like this:

1. employee (greet, c:null->ordering)
    "Welcome to McDonald's. Can I take your order?"
2. customer (add_item, e:null->ordering)
    "I'd like menu item X"
3. employee (confirm_ask_all, no state change)
    "Okay. Will that be all?"
(repeat steps 2-3 as much as you'd like)
4. customer (confirm_all, e:ordering->confirming_order)
    "Yes." 
5. employee (ask_confirm_items, c:ordering->confirming_order)
    "Okay. I have <items in order>. Is that correct?"
6. customer
    "Yes" --> goto 7 (confirm_items, e:->arranging_payment)
    "No" --> goto 2
7. employee (ask_for_payment, c:->arranging_payment)
    "Okay, that'll be $23.57."
8. customer (present_payment, c,e:->done)
    "Here's my card."
"""

# The numeric values of these constants don't matter, as long as they are distinct.
# They are made distinct when .configure_constants() is called below.
NULL_STATE = ORDERING_STATE = CONFIRMING_ORDER_STATE = ARRANGING_PAYMENT_STATE = DONE_STATE = 0
GREET_EVENT = ADD_ITEM_EVENT = CONFIRM_ASK_ALL_EVENT = CONFIRM_ALL_EVENT = ASK_CONFIRM_ITEMS_EVENT = \
    CONFIRM_ITEMS_EVENT = DENY_ITEMS_EVENT = ASK_FOR_PAYMENT_EVENT = PRESENT_PAYMENT_EVENT = 0

from .. import state_machine

STATE_NAMES, EVENT_NAMES = state_machine.configure_constants(globals())


class EmployeeStateMachine(state_machine.StateMachineBase):
    def __init__(self, pre=None, post=None, err=None):
        super().__init__("order_food/1.0", 'employee', STATE_NAMES, EVENT_NAMES, NULL_STATE, pre, post, err)
        self.add_transition(ADD_ITEM_EVENT, [NULL_STATE, ORDERING_STATE], ORDERING_STATE)
        self.add_transition(CONFIRM_ALL_EVENT, ORDERING_STATE, CONFIRMING_ORDER_STATE)
        self.add_transition(CONFIRM_ITEMS_EVENT, CONFIRMING_ORDER_STATE, ARRANGING_PAYMENT_STATE)
        self.add_transition(PRESENT_PAYMENT_EVENT, ARRANGING_PAYMENT_STATE, DONE_STATE)

    def handle(self, event):
        return self.transition_to(event)


class CustomerStateMachine(state_machine.StateMachineBase):
    def __init__(self, pre=None, post=None, err=None):
        super().__init__("order_food/1.0", 'customer', STATE_NAMES, EVENT_NAMES, NULL_STATE, pre, post, err)
        self.add_transition(GREET_EVENT, NULL_STATE, ORDERING_STATE)
        self.add_transition(CONFIRM_ASK_ALL_EVENT, ORDERING_STATE, ORDERING_STATE)
        self.add_transition(ASK_CONFIRM_ITEMS_EVENT, ORDERING_STATE, CONFIRMING_ORDER_STATE)
        self.add_transition(ASK_FOR_PAYMENT_EVENT, CONFIRMING_ORDER_STATE, ARRANGING_PAYMENT_STATE)

    def handle(self, event):
        return self.transition_to(event)


@pytest.fixture
def e():
    yield EmployeeStateMachine()


@pytest.fixture
def c():
    yield CustomerStateMachine()


def test_employee_starts_null(e):
    assert e.state == NULL_STATE


def test_customer_starts_null(c):
    assert c.state == NULL_STATE


def test_normal_customer_sequence(c):
    c.handle(GREET_EVENT)
    assert c.state == ORDERING_STATE
    c.handle(CONFIRM_ASK_ALL_EVENT)
    assert c.state == ORDERING_STATE
    c.handle(ASK_CONFIRM_ITEMS_EVENT)
    assert c.state == CONFIRMING_ORDER_STATE
    c.handle(ASK_FOR_PAYMENT_EVENT)
    assert c.state == ARRANGING_PAYMENT_STATE


def test_normal_employee_sequence(e):
    e.handle(ADD_ITEM_EVENT)
    assert e.state == ORDERING_STATE
    e.handle(CONFIRM_ALL_EVENT)
    assert e.state == CONFIRMING_ORDER_STATE
    e.handle(CONFIRM_ITEMS_EVENT)
    assert e.state == ARRANGING_PAYMENT_STATE


def test_bad_customer_sequences(c):
    with pytest.raises(ProtocolAnomaly):
        c.handle(CONFIRM_ASK_ALL_EVENT)
    c.handle(GREET_EVENT)
    with pytest.raises(ProtocolAnomaly):
        c.handle(GREET_EVENT)
    with pytest.raises(ProtocolAnomaly):
        c.handle(ASK_FOR_PAYMENT_EVENT)
    c.handle(CONFIRM_ASK_ALL_EVENT)
    c.handle(ASK_CONFIRM_ITEMS_EVENT)


def test_bad_customer_event(c):
    with pytest.raises(UnknownEvent):
        c.handle(5000)


def test_bad_eployee_event(e):
    with pytest.raises(UnknownEvent):
        e.handle(GREET_EVENT)


def test_state_machine_to_str(e):
    e.handle(ADD_ITEM_EVENT)
    assert str(e) == 'employee@order_food/1.0: ordering'


def test_pre_hook_can_cancel_transition(e):
    # If pre-hook fails, transition is cancelled
    def raise_(ex):
        raise ex
    pre_hook = lambda event_data: raise_(Exception)
    e._add_pre_hooks(pre_hook)
    assert e.state == NULL_STATE
    e.handle(ADD_ITEM_EVENT)
    assert e.state == NULL_STATE


def test_post_hook_is_called(e):
    # After successful transition, post hook is called
    class Hook:
        def __init__(self):
            self.called = False

        def __call__(self, event_data):
            self.called = True
            assert event_data.event.name == EVENT_NAMES[ADD_ITEM_EVENT]
            assert event_data.state.name == STATE_NAMES[ORDERING_STATE]

    post_hook = Hook()
    e._add_post_hooks(post_hook)
    assert e.state == NULL_STATE
    e.handle(ADD_ITEM_EVENT)
    assert e.state == ORDERING_STATE
    assert post_hook.called


def test_error_and_post_hook_are_called(e):
    # After unsuccessful transition, both error hook and post hook are called

    class Hook:
        def __init__(self):
            self.called = False

        def __call__(self, event_data):
            self.called = True
            assert event_data.event.name == EVENT_NAMES[CONFIRM_ALL_EVENT]
            assert event_data.state.name == STATE_NAMES[NULL_STATE]

    error_hook = Hook()
    post_hook = Hook()
    e._add_post_hooks(post_hook)
    e._add_error_hooks(error_hook)

    assert e.state == NULL_STATE
    with pytest.raises(ProtocolAnomaly):
        e.handle(CONFIRM_ALL_EVENT)
    assert e.state == NULL_STATE

    assert error_hook.called
    assert post_hook.called


def test_set_state_short_circuit(c):
    c.handle(GREET_EVENT)
    assert c.state == ORDERING_STATE
    # GREET_EVENT is only valid for NULL_STATE
    with pytest.raises(ProtocolAnomaly):
        c.handle(GREET_EVENT)

    c.set_state_by_short_circuit(NULL_STATE)
    assert c.state == NULL_STATE

    # GREET_EVENT works now
    c.handle(GREET_EVENT)
    assert c.state == ORDERING_STATE


def test_constants(e):
    assert NULL_STATE != DONE_STATE
    assert STATE_NAMES[ORDERING_STATE] == 'ordering'
    assert STATE_NAMES[CONFIRMING_ORDER_STATE] == 'confirming_order'
    assert GREET_EVENT != PRESENT_PAYMENT_EVENT
    assert EVENT_NAMES[DENY_ITEMS_EVENT] == "deny_items"


def test_to_json(c):
    c.set_state_by_short_circuit(ARRANGING_PAYMENT_STATE)
    x = c.to_json()
    y = json.loads(x)
    assert y.get('state') == "arranging_payment"
    assert y.get('protocol') == "order_food/1.0"
    assert y.get('role') == 'customer'
