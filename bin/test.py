if __name__ == '__main__':
    import os
    import sys
    import pytest

    root_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../q'))
    pytest.main([root_dir] + sys.argv[1:])
