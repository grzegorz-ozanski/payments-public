"""
    Nordhome estate manager provider.
"""
from browser import setup_logging
from .iok import IOK

SERVICE_URL = "https://www.iok.nordhome.com.pl/content/InetObsKontr/login"

log = setup_logging(__name__)


class Nordhome(IOK):
    """Nordhome provider for estate management, based on the IOK system."""

    def __init__(self, location: str):
        """
        Initialize Nordhome provider with given location.

        :param location: Location name for this provider instance.
        """
        super().__init__(10, SERVICE_URL, log, location)
