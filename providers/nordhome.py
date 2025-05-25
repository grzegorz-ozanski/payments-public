"""
    Nordhome estate manager provider module
"""
from browser import setup_logging
from .iok import IOK

log = setup_logging(__name__)


class Nordhome(IOK):
    """
    Represents the Nordhome subclass inheriting from IOK.

    This class is specifically designed to be used with the IOK system and
    initializes the necessary attributes for the Nordhome instance. It constructs
    with parameters related to configuration like URL, keystore service name,
    log, and location, and passes them to the parent class via super.

    """
    def __init__(self, location: str):
        """
        Initializes the class with specified location and initializes the parent class
        with additional parameters.

        :param location: The geographical or logical location to be used by
            the object initialization.
        :type location: str
        """
        url = "https://www.iok.nordhome.com.pl/content/InetObsKontr/login"
        name = self.__class__.__name__.lower()
        super().__init__(10, url, name, log, location)
