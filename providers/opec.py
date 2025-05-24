"""
    OPEC (head and hot water) provider module
"""
from time import sleep

from selenium.webdriver.common.by import By
from browser import setup_logging
from payments import Amount, DueDate, Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)


class Opec(Provider):
    """
    Represents the OPEC provider for interacting with its electronic platform.

    The class handles initialization of specific elements required to perform
    interactions with the OPEC web services. It inherits from the `Provider`
    base class to utilize shared functionalities.

    :ivar user_input: Element representing the username or email input field.
    :type user_input: PageElement
    :ivar password_input: Element representing the password input field.
    :type password_input: PageElement
    :ivar url: The base URL of the OPEC electronic platform.
    :type url: str
    :ivar keystore_service: Name of the keystore service associated with this provider.
    :type keystore_service: str
    """
    def __init__(self, *locations: str):
        """
        Represents an initialization method for setting up authentication page elements,
        URL, keystore service identifier, and resource locations for a specific service.

        :param locations: Positional arguments representing locations or resources needed
            for the service. Each location is specified as a string.
        """
        user_input = PageElement(By.ID, "_58_login")
        password_input = PageElement(By.ID, "_58_password")
        url = "https://ebok.opecgdy.com.pl/home"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, locations, user_input, password_input)

    def _read_payments(self) -> list[Payment]:
        """
        Reads and processes payment-related information from a web page. The function performs actions
        such as opening relevant sections on the page, extracting invoice details, and determining
        the earliest due date for payments. Returns a list of `Payment` objects containing the
        processed payment details.

        :return: A list of Payment objects containing payment details such as name, location,
                 earliest due date, and total amount extracted from the web page.
        :rtype: list[Payment]
        """
        self._weblogger.trace("pre-payments-click")
        self._browser.find_element(By.XPATH, '//a[text()="Płatności"]').click()
        self._weblogger.trace("pre-documents-click")
        self._browser.find_element(By.XPATH, '//a[contains(string(), "Dokumenty")]').click()
        self._browser.wait_for_network_inactive()
        sleep(1)
        invoices = self._browser.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
        amount = self._browser.find_element(By.NAME, "value").text
        due_date = ''
        for invoice in invoices:
            columns = invoice.find_elements(By.TAG_NAME, 'td')
            value = Amount(columns[7]) if columns[7].text else Amount(columns[5])
            if columns[6].text == "Zapłacony" and float(value) > 0:
                continue
            date = DueDate(columns[4].text)
            if (not due_date or date < due_date) and float(value) > 0:
                due_date = date
        return [Payment(self.name, self.locations[0], due_date, amount)]
