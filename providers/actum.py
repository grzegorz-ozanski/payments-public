from locations import Location
from browser import setup_logging
from .iok import IOK

log = setup_logging(__name__)


class Actum(IOK):
    def __init__(self, *locations: Location):
        url = "https://iok.actum.pl/InetObsKontr/LoginPage"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(20, url, keystore_service, log, locations)
