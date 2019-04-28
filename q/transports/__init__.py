import collections
import re

PluginInfo = collections.namedtuple('PluginInfo', ['name', 'cls', 'match', 'examples'])


def _load_plugins(class_name):
    import os
    import re
    import importlib
    items = []
    pat = re.compile(f'(.*_{class_name.lower()})\\.py$')
    my_folder = os.path.dirname(os.path.abspath(__file__))
    for item in os.listdir(my_folder):
        x = None
        m = pat.match(item)
        if m:
            plugin = m.group(1)
            module = importlib.import_module(f'.{plugin}', __name__)
            cls = getattr(module, class_name)
            if hasattr(module, 'match') and hasattr(module, 'EXAMPLES'):
                item = PluginInfo(plugin, cls, module.match, module.EXAMPLES)
                # Move file plugin to the end since it matches anything.
                if plugin.startswith('file'):
                    items.append(item)
                else:
                    items.insert(0, item)
    return items


SENDERS = _load_plugins('Sender')
RECEIVERS = _load_plugins('Receiver')
del _load_plugins

SENDER_EX = [x.examples for x in SENDERS]
RECEIVER_EX = [x.examples for x in RECEIVERS]


_UNLIKELY_FSPATH_PATH = re.compile('^[a-z][a-z0-9_.]{1,9}:')
def _seems_like_fspath(uri):
    return not bool(_UNLIKELY_FSPATH_PATH.match(uri))


def load(uri, items):
    for item in items:
        if item.match(uri):
            return item.cls(uri) if items is RECEIVERS else item.cls()
    msg = f"Can't find a transport that matches {uri}."
    if _seems_like_fspath(uri):
        msg += " Did you reference a file or folder that doesn't exist?"
    raise ValueError(msg)