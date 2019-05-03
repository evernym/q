class ProtocolAnomaly(Exception):
    def __init__(self, protocol, role, state, msg):
        super().__init__('Anomaly in the %s@%s protocol with state="%s". %s' % (role, protocol, state, msg))


class UnknownEvent(Exception):
    def __init__(self, protocol, role, state, event):
        super().__init__('Event %s in the %s@%s protocol with state="%s".' % (event, role, protocol, state))
