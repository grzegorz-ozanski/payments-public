"""
    PGNiG (gas supply) provider module
"""
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from browser import setup_logging
from payments import Amount, Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)


class Pgnig(Provider):
    """
    Provides functionality for interacting with PGNiG's eBOK service to
    retrieve payment information.

    This class extends the Provider class and specializes in handling PGNiG's
    specific user login, navigation, and invoice management processes. The class
    is designed to connect to the PGNiG eBOK portal, authenticate the user,
    access billing information, and extract unpaid invoice data to generate a
    list of payment objects.

    :ivar url: The URL of the PGNiG eBOK service.
    :type url: str
    :ivar keystore_service: The lowercase name of the class, used for keystore service identification.
    :type keystore_service: str
    :ivar user_input: Page element for the username or identifier input field on the login page.
    :type user_input: PageElement
    :ivar password_input: Page element for the password PIN input field on the login page.
    :type password_input: PageElement
    """
    def __init__(self, *locations: str):
        """
        Initializes the class with specified locations, user input element, password input element, URL,
        and keystore service.

        :param locations: Variable-length argument list representing the locations to be used for
           the configuration.
        :type locations: str
        """
        user_input = PageElement(By.NAME, "identificator")
        password_input = PageElement(By.NAME, "accessPin")
        url = "https://ebok.pgnig.pl"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, locations, user_input, password_input)

    def _read_payments(self) -> list[Payment]:
        """
        Retrieves a list of unpaid payments based on retrieved invoice information by interacting
        with a browser automation tool. Filters invoices to identify only unpaid ones and generates
        a list of payment objects.

        :raises StaleElementReferenceException: If web elements become stale during processing
        :raises ValueError: If the amount in the invoice is invalid for conversion
        :raises AttributeError: If elements on the page do not contain expected attributes or structure

        :return: A list of unpaid `Payment` objects. If no payments are found,
            a list containing a default payment object for the current location
            is returned instead.
        :rtype: list[Payment]
        """
        log.info("Getting payments...")
        location = self._get_location(self._browser.wait_for_element(By.CLASS_NAME, 'reading-adress').text)
        log.info("Getting invoices menu...")
        invoices_menu = self._browser.find_element(By.XPATH,
                                                  '//*[@class="menu-element" and normalize-space()="Faktury"]')
        log.info("Opening invoices menu...")
        self._weblogger.trace("pre-invoices-click")
        invoices_menu.click()
        log.debug("Waiting for page load completed...")
        self._browser.wait_for_page_inactive()
        unpaid_invoices = None
        for i in range(10):
            index = 0
            item = None
            try:
                log.info("Getting filtered invoices list...")
                unpaid_invoices = []
                for index, item in enumerate(self._browser.wait_for_elements(By.CLASS_NAME, "main-row-container")):
                    if item.find_element(By.CLASS_NAME, 'button').text == "Zapłać":
                        unpaid_invoices.append(item)
                break
            except StaleElementReferenceException:
                log.warning(f"Stale element encountered during filtering invoices.\n"
                            f"Element index: {index}\n"
                            f"Element details:\n{self._browser.dump_element(item)}")
        log.debug("Creating payments dict...")
        payments_dict = {}
        for invoice in unpaid_invoices:
            log.debug("Iterating over unpaid invoices...")
            columns = invoice.find_elements(By.CLASS_NAME, "columns")
            log.debug("Adding payment...")
            payments_dict[columns[2].text] = payments_dict.get(columns[2].text, 0) + float(Amount(columns[3].text))
        payments = []
        for date, amount in payments_dict.items():
            payments.append(Payment(self.name, location, date, amount))
        return payments if payments else [Payment(self.name, location)]
