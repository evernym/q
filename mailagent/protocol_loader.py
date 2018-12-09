import os
import sys
import logging

import agent_common

HANDLERS = {}

def load_all():
    bad = []
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
                    for attr in ['handle']:
                        if not hasattr(x, attr):
                            missing.append(attr)
                    if missing:
                        logging.error('Invalid %s protocol handler. Missing: %s.' % (item, ', '.join(missing)))
                        bad.append(item)
                    else:
                        logging.info('Loaded %s protocol handler.')
                        HANDLERS[item] = x
                    del x
                except:
                    agent_common.log_exception('While trying to import %s protocol handler' % item)
                    bad.append(item)
            finally:
                sys.path.pop(0)
    return bad
