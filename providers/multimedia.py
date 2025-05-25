"""
    Multimedia (TV) provider module
"""
from time import sleep
from typing import cast

from selenium.webdriver.common.by import By

from browser import setup_logging, Browser
from payments import Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)


class Multimedia(Provider):
    """
    Handles operations related to the Multimedia provider, such as authentication
    and fetching payment information.

    This class implements the required functionality for interacting with the
    Multimedia provider's UI and services. It supports logging in, resolving
    payment locations, and reading payment details such as due dates and amounts.

    :ivar _locations_map: A mapping of location identifiers to their respective
        string representations used to resolve payment locations.
    :type _locations_map: dict[str, str]
    """
    def __init__(self, locations: dict[str, str]):
        """
        Class constructor to initialize an instance of the class with specific parameters and
        settings necessary for interaction with a web panel. This initializer configures
        location mapping, provides authentication-related elements, and manages certain
        additional parameters like cookies button and recaptcha token required for pre-login
        activities.

        :param locations: A dictionary mapping identifiers to their respective string
            representations used in the application context.
        :type locations: dict[str, str]
        """
        self._locations_map = locations
        locations = cast(tuple[str, ...], tuple(locations.values()))  # to satisfy static code analyzers
        name = self.__class__.__name__.lower()
        super().__init__("https://ebok.multimedia.pl/panel-glowny.aspx",
                         name,
                         locations,
                         PageElement(By.ID, "Login_SSO_UserName"),
                         PageElement(By.ID, "Login_SSO_Password"),
                         cookies_button=PageElement(By.ID, "cookiescript_accept"),
                         recaptcha_token=PageElement("HFreCaptchaToken", "03AFc"),
                         pre_login_delay=1)

    def _get_location(self, amount: str) -> str:
        """
        Determines the location based on the provided amount by checking the 
        given `_locations_map`. It iterates over the mapping and returns the 
        first location whose associated string value is a prefix of the given 
        `amount`. Raises an exception if no suitable location is found.

        :param amount: The string amount to locate.
        :type amount: str
        :return: The location corresponding to the given amount.
        :rtype: str
        :raises Exception: If no suitable location is found for the provided amount.
        """
        try:
            return next(location for value, location in self._locations_map.items() if amount.startswith(value))
        except StopIteration:
            raise Exception(f"Cannot find suitable location for payment '{amount}'!")

    def login(self, browser: Browser, load: bool=True) -> None:
        """
        Logs in to the application using the given browser instance. The login process
        is retried up to a defined number of attempts with a delay between retries in
        case of failures. Specific conditions such as CAPTCHA requirement or password
        change may raise exceptions.

        This method overrides the login functionality to include retry logic and additional
        checks after each retry.

        :param browser: The browser instance to use for the login process
        :type browser: Browser
        :param load: Indicates whether to perform a full page load during the login attempt
        :type load: bool
        :return: None
        :rtype: None
        :raises RuntimeError: Raised when login fails due to conditions such as CAPTCHA or
            password change being required or if the maximum number of retries is reached
            without a successful login
        """
        wait = 5
        num_retries = 10
        for i in range(num_retries):
            log.debug(f'Login attempt {i + 1}')
            try:
                super().login(browser, load if i == 0 else False)
            except Exception as ex:
                if i == num_retries - 1:
                    raise ex
            self._browser.wait_for_page_inactive(2)
            if self._browser.wait_for_element(By.CSS_SELECTOR, 'span.logonFailureText', 2):
                log.debug(f'Login failed, retrying after {wait} seconds')
                self._weblogger.trace(f'failed-login-attempt-{i}')
            elif self._browser.find_elements(By.ID, 'formPassword') and self._browser.find_elements(By.ID, 'formConfirmation'):
                raise RuntimeError(f"Couldn't login, reason: password change required")
            else:
                return
        reason = "unknown"
        if self._browser.find_elements(By.ID, "formCaptcha"):
            reason = "CAPTCHA required"
        raise RuntimeError(f"Couldn't login in {num_retries} attempts! Reason: {reason}")

    def _read_payments(self) -> list[Payment]:
        """
        Reads and retrieves a list of payments associated with the current instance.

        This method retrieves payment data, including location, due date, and amount
        information. Initially, it generates a list of `Payment` objects using the
        configured locations. Subsequently, it collects additional invoice details from
        the browser and updates the corresponding payment records with due dates and
        amounts.

        :returns: A list of `Payment` objects containing payment details.
        :rtype: list[Payment]
        """
        log.info("Getting payments...")
        sleep(0.1)
        payments = [Payment(self.name, location) for location in self.locations]
        invoices = self._browser.wait_for_elements(By.CLASS_NAME, "invoiceInfo")
        if invoices is None:
            return payments
        for invoice in invoices:
            amount = invoice.find_element(By.CLASS_NAME, "kwota").text
            due_date = invoice.find_element(By.CLASS_NAME, "platnoscDo").text
            log.debug("Got amount '%s'" % amount)
            location = self._get_location(amount)
            index = payments.index(next(payment for payment in payments if payment.location == location))
            payments[index] = Payment(self.name, location, due_date, amount)
        return payments
