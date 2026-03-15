"""
    Nordhome estate manager provider.
"""
from browser import setup_logging
from .iok import IOK

BASE_URL = 'https://www.iok.nordhome.com.pl'
SERVICE_URL = 'content/InetObsKontr/login'

log = setup_logging(__name__)


class Nordhome(IOK):
    """Nordhome provider for estate management, based on the IOK system."""

    def __init__(self, location: str):
        """
        Initialize Nordhome provider with given location.

        :param location: Location name for this provider instance.
        """
        super().__init__(10, self.service_url(), log, location)

    def service_url(self) -> str:
        return f'{super().service_url() or BASE_URL}/{SERVICE_URL}'
