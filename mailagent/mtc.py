import collections

MessageTrustContext = collections.namedtuple('MessageTrustContext',
    'confidentiality integrity authenticated_origin non_repudiation',
    defaults=[False, False, False, False])
'''
Describe the trust guarantees associated with a given message.
See http://bit.ly/2UutabT for more information.
'''

