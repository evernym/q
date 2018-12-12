BY_NAME = {}
BY_TYPE = {}
BAD = []

_loaded = False
def _load():
    '''
    Dynamically discover all properly defined protocols, and make each of them callable.
    '''
    global _loaded
    if _loaded:
        return

    _loaded = True
    import os
    import sys
    import logging

    import agent_common

    BAD = []
    protocols_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'protocols')
    items = os.listdir(protocols_folder)
    for item in items:
        path = os.path.join(protocols_folder, item)
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, 'handler.py')):
            sys.path.insert(0, path)
            try:
                try:
                    import handler as x
                    missing = []
                    for attr in ['handle', 'TYPES']:
                        if not hasattr(x, attr):
                            missing.append(attr)
                    if missing:
                        logging.error('Invalid %s protocol handler. Missing: %s.' % (item, ', '.join(missing)))
                        bad.append(item)
                    else:
                        logging.info('Loaded %s protocol handler.')
                        BY_NAME[item] = x
                        for typ in x.TYPES:
                            if typ not in BY_TYPE:
                                BY_TYPE[typ] = []
                            BY_TYPE[typ].append(x)
                    del x
                except:
                    agent_common.log_exception('While trying to import %s protocol handler' % item)
                    BAD.append(item)
            finally:
                sys.path.pop(0)

_load()
