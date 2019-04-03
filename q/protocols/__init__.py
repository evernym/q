import collections

HANDLERS_BY_MSG_TYPE = {}

PluginInfo = collections.namedtuple('PluginInfo', ['name', 'cls', 'pat', 'example'])


def _register(module):
    """
    Every handler must declare the message types it handles. Go find that
    list and index the handlers by each type, so we can quickly route a
    given message type to the appropriate handler without hard-coded logic.
    """
    for typ in module.TYPES:
        if typ not in HANDLERS_BY_MSG_TYPE:
            HANDLERS_BY_MSG_TYPE[typ] = []
        list_for_this_type = HANDLERS_BY_MSG_TYPE[typ]
        if module not in list_for_this_type:
            list_for_this_type.append(module)


def _load_plugins():
    import importlib
    import os
    items = []
    my_folder = os.path.dirname(os.path.abspath(__file__))
    for item in os.listdir(my_folder):
        if item == 'tests' or item.startswith('_') or '.' in item or not os.path.isdir(os.path.join(my_folder, item)):
            continue
        handler = importlib.import_module(f'.{item}', __name__)
        _register(handler)


_load_plugins()
del _register
del _load_plugins
