from browser import setup_logging
from .iok import IOK

log = setup_logging(__name__)


class Nordhome(IOK):
    def __init__(self, location: str):
        url = "https://www.iok.nordhome.com.pl/content/InetObsKontr/login"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(10, url, keystore_service, log, location)
