"""
    Actum estate manager provider module
"""
from browser import setup_logging
from .iok import IOK

log = setup_logging(__name__)


class Actum(IOK):
    """
    Actum class.

    The Actum class is a specialized extension of the IOK class. It is designed
    to handle specific functionality related to the Actum estate provider by
    providing initialization and configuration necessary for the operation
    with the Actum system. The class is linked to a specific location
    when instantiated.

    """
    def __init__(self, location: str):
        """
        Represents an initialization for a specific service configuration.

        This class initializer method initializes a configuration necessary for
        a service. The location parameter is used to provide a specific location string
        to initialize the service context.

        :param location: The string representing the location necessary to configure
            the service.
        :type location: str
        """
        url = "https://iok.actum.pl/InetObsKontr/LoginPage"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(20, url, keystore_service, log, location)
