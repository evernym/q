import os
import sys
test_folder = os.path.dirname(os.path.abspath(__file__))
root_module_folder = os.path.abspath(os.path.join(test_folder, '..'))

# This module will be imported more than once. Only do setup the first time
# it happens.
if root_module_folder not in sys.path:
    # Tell python that code in the parent folder should be searched
    # when processing import statementss
    sys.path.append(root_module_folder)

    # Make sure the logging code inside our various modules writes to test.log
    import logging
    test_log_path = os.path.join(test_folder, 'test.log')
    if os.path.isfile(test_log_path):
        os.unlink(test_log_path)
    logging.basicConfig(
        filename=test_log_path,
        format='%(asctime)s\t%(funcName)s@%(filename)s#%(lineno)s\t%(levelname)s\t%(message)s',
        level=logging.DEBUG)
