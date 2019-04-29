import json
import pytest

from ..exceptions import ProtocolAnomaly

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

    def handle(self, event):
        if event == ADD_ITEM_EVENT:
            self.check_state_for_event(event, NULL_STATE, ORDERING_STATE)
            self.transition_to(ORDERING_STATE, event)
        elif event == CONFIRM_ALL_EVENT:
            self.check_state_for_event(event, ORDERING_STATE)
            self.transition_to(CONFIRMING_ORDER_STATE, event)
        elif event == CONFIRM_ITEMS_EVENT:
            self.check_state_for_event(event, CONFIRMING_ORDER_STATE)
            self.transition_to(ARRANGING_PAYMENT_STATE, event)
        elif event == PRESENT_PAYMENT_EVENT:
            self.check_state_for_event(event, ARRANGING_PAYMENT_STATE)
            self.transition_to(DONE_STATE, event)
        else:
            self.raise_anomaly(event)


class CustomerStateMachine(state_machine.StateMachineBase):
    def __init__(self, pre=None, post=None, err=None):
        super().__init__("order_food/1.0", 'customer', STATE_NAMES, EVENT_NAMES, NULL_STATE, pre, post, err)

    def handle(self, event):
        if event == GREET_EVENT:
            self.check_state_for_event(event, NULL_STATE)
            self.transition_to(ORDERING_STATE, event)
        elif event == CONFIRM_ASK_ALL_EVENT:
            self.check_state_for_event(event, ORDERING_STATE)
            # No transition
        elif event == ASK_CONFIRM_ITEMS_EVENT:
            self.check_state_for_event(event, ORDERING_STATE)
            self.transition_to(CONFIRMING_ORDER_STATE, event)
        elif event == ASK_FOR_PAYMENT_EVENT:
            self.check_state_for_event(event, CONFIRMING_ORDER_STATE)
            self.transition_to(ARRANGING_PAYMENT_STATE, event)
        else:
            self.raise_anomaly(event)


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
    with pytest.raises(ProtocolAnomaly):
        c.handle(5000)

def test_bad_eployee_event(e):
    with pytest.raises(ProtocolAnomaly):
        e.handle(GREET_EVENT)

def test_state_machine_to_str(e):
    e.handle(ADD_ITEM_EVENT)
    assert str(e) == 'employee@order_food/1.0: ordering'

def test_pre_hook_can_cancel_transition(e):
    e._pre_hook = lambda state, event: False
    assert e.state == NULL_STATE
    e.handle(ADD_ITEM_EVENT)
    assert e.state == NULL_STATE

def test_post_hook_is_called(e):
    class Hook:
        def __init__(self):
            self.called = False
        def __call__(self, state, event):
            self.called = True
    e._post_hook = Hook()
    assert e.state == NULL_STATE
    e.handle(ADD_ITEM_EVENT)
    assert e.state == ORDERING_STATE
    assert e._post_hook.called

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
