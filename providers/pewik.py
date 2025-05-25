"""
    PEWiK (water supply) provider module
"""
from selenium.webdriver.common.by import By

from browser import setup_logging
from payments import Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)


class Pewik(Provider):
    """
    Represents a Pewik service provider for extracting payment information from a web portal.

    The Pewik class extends the Provider class and is specifically designed to interact with
    the Pewik Gdynia web portal. It facilitates logging in, managing session cookies, navigating
    through the portal, and extracting payment data from the invoices and balances section.

    :ivar user_input: A PageElement representing the input field for the username.
    :type user_input: PageElement
    :ivar password_input: A PageElement representing the input field for the password.
    :type password_input: PageElement
    :ivar logout_button: A PageElement representing the logout button on the portal.
    :type logout_button: PageElement
    :ivar url: The login URL for the Pewik Gdynia web portal.
    :type url: str
    :ivar keystore_service: The name of the keystore service, derived from the class name in lowercase.
    :type keystore_service: str
    """
    def __init__(self, *locations: str):
        """
        Initializes the class and sets up necessary attributes such as username input,
        password input, logout button, URL, and keystore service. It also calls the
        parent class initializer with relevant parameters.

        :param locations: List of location strings to be used for initialization.
        :type locations: str
        """
        user_input = PageElement(By.ID, "username")
        password_input = PageElement(By.ID, "password")
        logout_button = PageElement(By.CLASS_NAME, 'btn-wyloguj')
        url = "https://ebok.pewik.gdynia.pl/login"
        name = self.__class__.__name__.lower()
        super().__init__(url, name, locations, user_input, password_input, logout_button)

    def _fetch_payments(self) -> list[Payment]:
        """
        Parses payment data from a web page and returns a list of `Payment` objects.

        This method interacts with a browser instance to navigate specific pages, handle cookies,
        and extract structured information about payments and balances. It navigates through
        different payment locations on the webpage and collects relevant data to construct
        a list of `Payment` instances.

        The method ensures page elements are loaded, checks for and interacts with pop-up panels
        (e.g., cookies panel), navigates between pages using browser actions, and extracts
        payment details by iterating through table rows. It also manages navigation between
        different locations using a dropdown arrow and stops when all locations have been processed.

        :raises Exception: If any required elements are not found or actions fail unexpectedly
        :param self: Instance of the class containing the method
        :rtype: list[Payment]
        :return: A list of `Payment` objects, with each object representing payment details
            extracted from the web page.
        """
        payments = []
        next_id = 1
        cookies_panel = self._browser.find_element(By.CLASS_NAME, 'panel-cookies')
        if cookies_panel:
            self._browser.wait_for_element_clickable(By.CLASS_NAME, 'panel-cookies')
            self._browser.click_element_with_js(cookies_panel.find_element(value='cookiesClose'))
        invoice = self._browser.find_element(By.XPATH, '//a[text()="Faktury i salda"]')
        self._browser.trace_click(invoice)
        invoice = self._browser.find_element(By.XPATH, '//a[text()="Salda"]')
        self._browser.trace_click(invoice)
        self._browser.wait_for_page_load_completed()
        while True:
            location = self._get_location(
                self._browser.find_element(By.CLASS_NAME, 'select2-chosen').find_elements(By.TAG_NAME, 'span')[2].text)
            balances = self._browser.find_element(By.ID, 'saldaWplatyWykaz'). \
                find_element(By.TAG_NAME, 'tbody'). \
                find_elements(By.TAG_NAME, 'tr')
            for item in balances:
                columns = item.find_elements(By.TAG_NAME, 'td')
                if len(columns) > 1:
                    payments.append(Payment(self.name, location, columns[3], columns[5]))
                else:
                    payments.append(Payment(self.name, location))
            locations_arrow = self._browser.find_element(By.CLASS_NAME, 'select2-arrow')
            self._browser.trace_click(locations_arrow)
            locations = self._browser.find_elements(By.CLASS_NAME, 'select2-result')
            if next_id < len(locations):
                self._browser.trace_click(locations[next_id])
                next_id += 1
            else:
                break
        return payments
