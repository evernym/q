class ProtocolAnomaly(Exception):
    def __init__(self, protocol, role, state, msg):
        super().__init__('Anomaly in the %s@%s protocol with state="%s". %s' % (role, protocol, state, msg))