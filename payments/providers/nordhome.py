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
        super().__init__(10, self.url(), log, location)

    def url(self) -> str:
        return f'{super().url() or BASE_URL}/{SERVICE_URL}'
