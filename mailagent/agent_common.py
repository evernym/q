import logging
import sys
import traceback

def log_exception():
    typ, text, trace = sys.exc_info()
    frame = traceback.extract_tb(trace, 1)[0]
    text = str(text)
    if text[-1].isalpha():
        text += '.'
    logging.error("%s at %s#%s: %s Code was: %s" % (
        typ.__name__, frame.filename, frame.lineno, text, frame.line.strip()))
