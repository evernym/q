import collections

PluginInfo = collections.namedtuple('PluginInfo', ['name', 'cls', 'pat', 'example'])


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
            item = PluginInfo(plugin, cls, module.PAT, module.EXAMPLE)
            # Move file plugin to the end since it matches anything.
            if plugin.startswith('file'):
                items.append(item)
            else:
                items.insert(0, item)
    return items


SENDERS = _load_plugins('Sender')
RECEIVERS = _load_plugins('Receiver')
del _load_plugins

SENDER_EX = [x.example for x in SENDERS]
RECEIVER_EX = [x.example for x in RECEIVERS]


def load(uri, items):
    for item in items:
        if item.pat.match(uri):
            return item.cls(uri)
    raise ValueError(f"Can't find a transport that matches {uri}.")