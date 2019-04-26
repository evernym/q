import os

def match_uri_to_filesys(uri, fstype_func, special_fname=None):
    """
    A helper function that various filesystem-based channels use to match URIs.
    :param uri: URI to match
    :param fstype_func: a function like os.path.isfile that can be used to test
      characteristics of a file system item.
    :param special_fname: a special name like "stdin" or "stdout" that represents
      a label for a file system construct other than normal ones.
    :return: True if the URI meets all the criteria.
    """
    try:
        if uri.startswith('~'):
            uri = os.path.expanduser(uri)
        elif special_fname and (uri.lower() == special_fname):
            return True
        return fstype_func(uri)
    except:
        return False
