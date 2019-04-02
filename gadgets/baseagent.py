import inspect
import logging
import os

from indy import wallet

DEFAULT_AGENT_LOG_LEVEL = 'DEBUG'


def _get_numeric_loglevel(args):
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
        cfg.add_argument('-r', '--reset', action='store_true', default=False,
                         help='reset the wallet instead of keeping accumulated state')

    def configure(self, cfg):
        cfg.add_argument('-p', metavar='PHRASE', required=True, help="Passphrase used to unlock wallet")
        cfg.add_argument('--wallet', metavar='NAME', default='wallet', help='Name of wallet to use')
        cfg.add_argument('--loglevel', metavar='LVL', default=self.log_level,
                         help="Log level (default=%s)" % self.log_level)
        cfg.add_argument('--folder', metavar='FOLDER', default=self.folder,
                         help="Folder where state is stored (default=%s)" % self.folder)
        self.cfg = cfg
        args = cfg.parse_args()
        self.args = args
        self.wallet = args.wallet
        self.folder = os.path.expanduser(args.folder)
        self.log_level = _get_numeric_loglevel(args)
        # Make sure agent's folder exists.
        if not os.path.isdir(self.folder):
            os.makedirs(self.folder, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(self.folder, self.deriving_module_name + '.log'),
            format='%(asctime)s\t%(funcName)s@%(filename)s#%(lineno)s\t%(levelname)s\t%(message)s',
            level=self.log_level)
        self.wallet_config = '{"id": "%s", "storage_config": {"path": "%s"}}' % (args.wallet, self.folder)
        self.wallet_credentials = '{"key": "%s"}' % args.p
        return args

    async def open_wallet(self):
        if self.wallet_config is None:
            raise AssertionError('Must call .configure() before open_wallet()')
        exists = os.path.isfile(self.wallet_file)
        if exists:
            if 'reset' in self.args:
                if self.args.reset:
                    os.path.unlink(self.wallet_file)
                    exists = False
        if not exists:
            await wallet.create_wallet(self.wallet_config, self.wallet_credentials)
        self.wallet_handle = await wallet.open_wallet(self.wallet_config, self.wallet_credentials)

    @property
    def wallet_folder(self):
        return os.path.join(self.folder, self.wallet)

    @property
    def wallet_file(self):
        return os.path.join(self.wallet_folder, 'sqlite.db')

