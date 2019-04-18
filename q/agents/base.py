import inspect
import json
import logging
import os

import indy

from .. import log_helpers
from ..mtc import *
from ..dbc import *

DEFAULT_AGENT_LOG_LEVEL = 'INFO'


class Agent:

    def __init__(self, folder=None):
        mod = inspect.getmodule(self.__class__)
        self.deriving_module_name = os.path.splitext(os.path.basename(
            str(mod.__file__)))[0]
        if not folder:
            self.folder = '~/.q/' + self.deriving_module_name
        else:
            self.folder = folder
        self.conf_file_path = os.path.join(self.folder, 'conf')
        self.log_level = DEFAULT_AGENT_LOG_LEVEL
        # Object isn't fully inited; must call .configure() next.
        # Until then, these next properties don't have meaningful values.
        self.wallet_config = None
        self.wallet_credentials = None
        self.wallet_handle = None

    def configure_reset(self, cfg):
        cfg.add_argument('--rw', action='store_true', default=False,
                         help='Reset the wallet instead of keeping accumulated state.')
        cfg.add_argument('--rl', action='store_true', default=False,
                         help='Reset the log, purging events from old runs.')

    def configure(self, cfg):
        group = cfg.add_mutually_exclusive_group(required=True)
        group.add_argument('--phrase', metavar='PHRASE', help=
                "Passphrase to unlock wallet. This is convenient for testing, but is " +
                "insecure because the password is echoed to the screen.")
        group.add_argument('--promptphrase', action='store_true', help=
                "Prompt for passphrase to unlock wallet.")
        cfg.add_argument('--wallet', metavar='NAME', default='wallet', help=
                'Name of wallet to use.')
        cfg.add_argument('--loglevel', metavar='LVL', default=self.log_level,
                         help=f"Log level (default={self.log_level}).")
        cfg.add_argument('--folder', metavar='FOLDER', default=self.folder,
                         help=f"Folder where state is stored (default={self.folder}).")
        self.cfg = cfg
        args = cfg.parse_args()
        if args.promptphrase:
            import getpass
            args.phrase = getpass.getpass('Passphrase to unlock wallet: ')
        self.args = args
        self.wallet = args.wallet
        self.folder = os.path.expanduser(args.folder)
        self.log_level = log_helpers.get_numeric_loglevel(args)
        # Make sure agent's folder exists.
        if not os.path.isdir(self.folder):
            os.makedirs(self.folder, exist_ok=True)
        log_fname = os.path.join(self.folder, self.deriving_module_name + '.log')
        if hasattr(args, 'rl') and args.rl:
            if os.path.exists(log_fname):
                os.unlink(log_fname)
        logging.basicConfig(
            filename=log_fname,
            format='%(asctime)s\t%(funcName)s@%(filename)s#%(lineno)s\t%(levelname)s\t%(message)s',
            level=self.log_level)
        self.wallet_config = '{"id": "%s", "storage_config": {"path": "%s"}}' % (args.wallet, self.folder)
        self.wallet_credentials = '{"key": "%s"}' % args.phrase
        return args

    async def unpack(self, wc):
        if 'protected' in wc.ciphertext:
            wc.plaintext = json.loads(await indy.crypto.unpack_message(self.wallet_handle, wc.ciphertext.encode('utf-8')))
            wc.tc.affirm(CONFIDENTIALITY)
            wc.tc.affirm(INTEGRITY)
            if wc.get('sender_verkey', None):
                wc.tc.affirm(AUTHENTICATED_ORIGIN)
        else:
            wc.plaintext = {'message': json.loads(wc.ciphertext)}
        wc.obj = wc.plaintext.get('message')

    def norm_recipient_keys(self, keys, make_list=True):
        if '+' in keys:
            return [self.norm_recipient_keys(x, False) for x in keys.split('+') if x]
        return [keys] if (make_list and not isinstance(keys, list)) else keys

    async def pack(self, msg, sender_key, to):
        if isinstance(msg, bytes):
            msg = msg.decode('utf-8')
        if not isinstance(to, list):
            to = [to]
        if self.wallet_handle is None:
            await self.open_wallet()
        i = len(to) - 1
        while i >= 0:
            # Always anon-crypt to mediator
            if i == 0 and len(to) > 1:
                sender = None
            else:
                sender = sender_key
            recipients = self.norm_recipient_keys(to[i])
            msg = await indy.crypto.pack_message(self.wallet_handle, msg, recipients, sender)
            msg = msg.decode('utf-8')
            i -= 1
        return msg

    async def open_wallet(self):
        precondition(self.wallet_config is not None, 'Must call .configure() before open_wallet()')
        exists = os.path.isfile(self.wallet_file)
        if exists:
            if 'rw' in self.args:
                if self.args.rw:
                    os.path.unlink(self.wallet_file)
                    exists = False
        if not exists:
            await indy.wallet.create_wallet(self.wallet_config, self.wallet_credentials)
        self.wallet_handle = await indy.wallet.open_wallet(self.wallet_config, self.wallet_credentials)

    @property
    def wallet_folder(self):
        return os.path.join(self.folder, self.wallet)

    @property
    def wallet_file(self):
        return os.path.join(self.wallet_folder, 'sqlite.db')