"""
    Actum estate manager provider.
"""
from browser import setup_logging
from .iok import IOK

log = setup_logging(__name__)

BASE_URL = 'https://iok.actum.pl'
SERVICE_URL = 'InetObsKontr/LoginPage'


class Actum(IOK):
    """Actum provider for estate management, based on the IOK system."""

    def __init__(self, location: str):
        """
        Initialize Actum provider with a given location.

        :param location: Location name for this provider instance.
        """
        super().__init__(20, self.service_url(), log, location)

    def service_url(self) -> str:
        return f'{super().service_url() or BASE_URL}/{SERVICE_URL}'
