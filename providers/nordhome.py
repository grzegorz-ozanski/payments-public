"""
    Nordhome estate manager provider.
"""

from browser import setup_logging
from .iok import IOK

log = setup_logging(__name__)


class Nordhome(IOK):
    """Nordhome provider for estate management, based on the IOK system."""

    def __init__(self, location: str):
        """
        Initialize Nordhome provider with given location.

        :param location: Location name for this provider instance.
        """
        url = "https://www.iok.nordhome.com.pl/content/InetObsKontr/login"
        name = self.__class__.__name__.lower()
        super().__init__(10, url, name, log, location)
