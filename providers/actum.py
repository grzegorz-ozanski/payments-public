"""
    Actum estate manager provider.
"""
from browser import setup_logging
from .iok import IOK

log = setup_logging(__name__)

SERVICE_URL = "https://iok.actum.pl/InetObsKontr/LoginPage"


class Actum(IOK):
    """Actum provider for estate management, based on the IOK system."""

    def __init__(self, location: str):
        """
        Initialize Actum provider with given location.

        :param location: Location name for this provider instance.
        """
        super().__init__(20, SERVICE_URL
                         , log, location)
