from typing import List

from account import Account
from log import setup_logging
from .iok import IOK

log = setup_logging(__name__, 'DEBUG')


class Actum(IOK):
    def __init__(self, keystore_user: str, accounts: List[Account]):
        url = "https://iok.actum.pl/InetObsKontr/LoginPage"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(20, url, keystore_user, keystore_service, log, accounts)
