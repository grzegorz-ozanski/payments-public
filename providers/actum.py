from browser import setup_logging
from locations import Location
from .iok import IOK

log = setup_logging(__name__)


class Actum(IOK):
    def __init__(self, location: Location):
        url = "https://iok.actum.pl/InetObsKontr/LoginPage"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(20, url, keystore_service, log, location)
