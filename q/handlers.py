HANDLERS_BY_MSG_TYPE = {}


def _register(module):
    '''
    Every handler must declare the message types it handles. Go find that
    list and index the handlers by each type, so we can quickly route a
    given message type to the appropriate handler without hard-coded logic.

    TODO: replace with custom importer or a more sophisticated dynamic plugin model?
    '''
    for typ in module.TYPES:
        if typ not in HANDLERS_BY_MSG_TYPE:
            HANDLERS_BY_MSG_TYPE[typ] = []
        list_for_this_type = HANDLERS_BY_MSG_TYPE[typ]
        if module not in list_for_this_type:
            list_for_this_type.append(module)


# List all handlers here.
from . import tp_handler
from . import ttt_handler

# Index the message types supported by these handlers,
# so we can route to the correct one as needed.
_register(ttt_handler)
_register(tp_handler)
