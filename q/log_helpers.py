import logging
import sys
import traceback


def get_numeric_loglevel(args):
    """
    Turn a symbolic log level name like "DEBUG" into its numeric equivalent;
    raise ValueError if it can't be done.
    """
    ll = ('DIWEC'.index(args.loglevel[0].upper()) + 1) * 10
    if ll <= 0:
        try:
            ll = int(args.loglevel)
        except:
            raise ValueError('Unrecognized loglevel %s.' % args.loglevel)
    return ll


def log_exception(ctx: str = ''):
    typ, text, trace = sys.exc_info()
    frame = traceback.extract_tb(trace, 1)[0]
    text = str(text)
    if text and text[-1].isalpha():
        text += '.'
    if ctx:
        ctx += ', '
    logging.error("%s%s at %s#%s: %s Code was: %s" % (
        ctx, typ.__name__, frame.filename, frame.lineno, text, frame.line.strip()))
