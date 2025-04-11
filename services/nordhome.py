from log import setup_logging
from .iok import IOK

log = setup_logging(__name__, 'DEBUG')


class Nordhome(IOK):
    def __init__(self, keystore_user):
        url = "https://www.iok.nordhome.com.pl/content/InetObsKontr/login"
        keystore_service = self.__class__.__name__.lower()
        super().__init__('Bryla', 10, url, keystore_user, keystore_service, log)
