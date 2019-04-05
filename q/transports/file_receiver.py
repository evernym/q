import re

from . import file_transport

PAT = re.compile('.*')
EXAMPLE = '~/myfolder'

class Receiver(file_transport.FileTransport):
    def __init__(self, folder):
        super().__init__(folder, False)