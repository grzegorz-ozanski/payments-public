"""
This module contains the base class for all payment providers, along with some utility classes and functions
"""
import time
from dataclasses import dataclass
from os import environ

import keyring
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from browser import setup_logging, Browser, WebLogger
from payments import Payment

log = setup_logging(__name__)


def _sleep_with_message(amount: int, message: str):
    """
    Pauses execution for a specified number of seconds while logging a message.

    This function logs a debug message and pauses the program for the given
    amount of time, measured in seconds. Useful for introducing delays during
    program execution with associated logging for debugging purposes.

    :param amount: Number of seconds to sleep. Must be an integer.
    :type amount: int
    :param message: Log message to display before sleeping.
    :type message: str
    :return: None
    """
    if amount:
        log.debug(f"{message}: sleeping {amount} seconds")
        time.sleep(amount)


@dataclass
class PageElement:
    """
    Represents a web page element locator.

    The `PageElement` class serves as a data structure to hold information about
    a specific web element's location strategy and selector. It is typically used
    in automated web testing to identify and interact with elements on a webpage.

    :ivar by: Locator strategy used to identify the element, such as "id", "xpath",
        or "css selector".
    :type by: str
    :ivar selector: Selector string that corresponds to the chosen locator strategy.
    :type selector: str
    """
    by: str
    selector: str


class Credential:
    """
    Represents a credential management utility for retrieving credentials via environment variables
    or a keyring service.

    This class allows easy access to credentials that are stored either as environment variables
    or within a keyring service. Users can specify the service name and credential name, and the class
    provides methods for retrieving the credential securely.

    :ivar keyring: The name of the credential stored in the keyring service.
    :type keyring: str
    :ivar environ: The name of the corresponding environment variable used to retrieve the credential.
    :type environ: str
    """
    keyring: str
    environ: str

    def __init__(self, service_name, name, env_upper: bool = True):
        """
        Initializes the keyring settings with the provided service name, name,
        and an optional environment uppercase flag.

        :param service_name: The name of the keyring service.
        :type service_name: str
        :param name: The specific keyring name within the service.
        :type name: str
        :param env_upper: A boolean flag indicating whether the environment
            variable name should be converted to uppercase. Defaults to True.
        :type env_upper: bool
        """
        self.keyring_service = service_name
        self.keyring = name
        self.environ = f'{service_name}_{name}'
        if env_upper:
            self.environ = self.environ.upper()

    def get(self) -> str | None:
        """
        Retrieve a value from the environment variable or keyring service.

        This method attempts to retrieve a value by first checking the specified
        environment variable. If a value exists, it is immediately returned.
        If not, it proceeds to retrieve the value from the keyring service
        associated with the provided key and service name. If the keyring also
        does not contain a value, a `RuntimeError` is raised indicating that the
        value cannot be found in either the environment variable or the keyring
        service.

        :raises RuntimeError: If the value is not found in either the environment
            variable or the keyring service.

        :return: The retrieved value as a string if it exists in the environment
            variable or keyring service; None if no value is found in the keyring
            service and the value from the environment variable is empty.
        :rtype: str | None
        """
        if value := environ.get(self.environ):
            return value
        value = keyring.get_password(self.keyring_service, self.keyring).strip()
        if value:
            return value
        raise RuntimeError(f'"{self.keyring}" cannot be found in ether {self.environ} environment variable '
                           f'or {self.keyring_service} keyring service!')


class Provider:
    """
    Represents a provider for handling login, logout, and retrieving payments for specific services.

    This class is designed to automate interactions with web services by managing user credentials,
    logging in, retrieving payment information, and performing logout actions. It can handle services
    with additional complexities such as cookie consent pop-ups and reCAPTCHA verification. It requires
    specific configuration of input elements and selectors to integrate with the targeted web service and
    streamline the user's interaction.

    :ivar url: The URL of the service to log in to.
    :type url: str
    :ivar name: Provider name.
    :type name: str
    :ivar locations: List of the names of the locations for the service.
    :type locations: tuple[str, ...]
    :ivar user_input: Input element for the username.
    :type user_input: PageElement
    :ivar password_input: Input element for the password.
    :type password_input: PageElement
    :ivar username: Credential instance for the stored username.
    :type username: Credential
    :ivar password: Credential instance for the stored password.
    :type password: Credential
    :ivar logout_button: Button element for logging out of the service.
    :type logout_button: PageElement | None
    :ivar cookies_button: Element for handling cookie consent pop-up.
    :type cookies_button: PageElement | None
    :ivar recaptcha_token: Element for reCAPTCHA token handling.
    :type recaptcha_token: PageElement | None
    :ivar recaptcha_token_prefix: Expected prefix of the reCAPTCHA token value.
    :type recaptcha_token_prefix: str | None
    :ivar pre_login_delay: Delay in seconds before attempting the login process.
    :type pre_login_delay: int
    :ivar post_login_delay: Delay in seconds after the login process completes.
    :type post_login_delay: int
    """
    def __init__(self, url: str, name: str, locations: tuple[str, ...],
                 user_input: PageElement, password_input: PageElement,
                 logout_button: PageElement | None = None, cookies_button: PageElement | None = None,
                 recaptcha_token: PageElement | None = None, recaptcha_token_prefix: str | None = None,
                 pre_login_delay: int = 0, post_login_delay: int = 0):
        """
        Initializes the class with required configuration for web interactions, including URL,
        keystore service, element locators, CAPTCHA settings, and optional delays. Designed for
        handling automated interactions such as filling credentials and managing session elements
        in a browser context while providing a structured approach with support for pre-defined
        logging and error handling utilities.

        :param url: The URL of the web application to interact with.
        :type url: str
        :param name: Provider name.
        :type name: str
        :param locations: A tuple of location identifiers specifying areas of interaction or
            navigation in the web application.
        :type locations: tuple[str, ...]
        :param user_input: The locator for the username input field on the web page.
        :type user_input: PageElement
        :param password_input: The locator for the password input field on the web page.
        :type password_input: PageElement
        :param logout_button: Optional locator for the logout button element. If not provided,
            a default locator targeting the button element with "Wyloguj" text will be used.
        :type logout_button: PageElement | None
        :param cookies_button: Optional locator for the cookies acceptance button, if present
            on the web page.
        :type cookies_button: PageElement | None
        :param recaptcha_token: Optional locator for a CAPTCHA-related token element,
            if utilized in the web application.
        :type recaptcha_token: PageElement | None
        :param recaptcha_token_prefix: Optional prefix string to be used when locating CAPTCHA
            tokens.
        :type recaptcha_token_prefix: str | None
        :param pre_login_delay: An optional delay (in seconds) to wait before initiating the
            login process.
        :type pre_login_delay: int
        :param post_login_delay: An optional delay (in seconds) to wait after completing
            the login process.
        :type post_login_delay: int
        """
        self._browser = None
        self.url = url
        self.name = name
        self.locations = locations
        self._location_order = {location: i for i, location in enumerate(self.locations)}
        self.user_input = user_input
        self.password_input = password_input
        self.username = Credential(name, 'username')
        self.password = Credential(name, 'password')
        self._weblogger = WebLogger(self.name)
        if not logout_button:
            logout_button = PageElement(
                By.XPATH,
                # lowest element in the DOM tree containing 'Wyloguj' string
                '//*[contains(string(), "Wyloguj") and not(.//*[contains(string(), "Wyloguj")])]'
            )
        self.logout_button = logout_button
        self.cookies_button = cookies_button
        self.recaptcha_token = recaptcha_token
        self.recaptcha_token_prefix = recaptcha_token_prefix
        self.pre_login_delay = pre_login_delay
        self.post_login_delay = post_login_delay

    def __repr__(self) -> str:
        return f'{self.name}: [{", ".join(map(str, self.locations))}]'

    def _get_location(self, name_string: str) -> str:
        """
        Get the first matching location from a list of locations present in the input string.

        The function attempts to retrieve and return the first location from an internal
        list of valid locations that matches (is a substring of) the provided name_string.
        If no valid location is found, an error is logged, and the exception is raised.

        :param name_string: Input string that potentially contains a location
        :type name_string: str
        :return: The first matching location found in locations
        :rtype: str
        :raises RuntimeEror: If no matching location is found
        """
        try:
            return next(location for location in self.locations if location in name_string)
        except StopIteration:
            log.error(f"Cannot find a valid location for service {self.name}!\n"
                      f"Location name provided: '{name_string}'.\n"
                      f"Valid service locations: {','.join(self.locations)}")
            raise RuntimeError(f"Cannot find a valid location for service {self.name}!")

    # noinspection PyPep8Naming
    def _wait_for_reCAPTCHA_v3_token(self) -> None:
        """
        Waits for a reCAPTCHA v3 token to be generated and checks if the token
        matches the specified prefix.

        This method ensures the browser waits for a specific reCAPTCHA token to
        appear on a page and validates the token's value against a given prefix.

        :param self: Instance of the class.
        """
        if self.recaptcha_token and self.recaptcha_token_prefix:
            self._browser.wait_for_condition(
                lambda d: d.find_element(self.recaptcha_token.by, self.recaptcha_token.selector).get_attribute(
                    "value").startswith(self.recaptcha_token_prefix))

    @staticmethod
    def input(control: WebElement, text: str) -> None:
        """
        Handles text input for a given web element by clearing it and then sending the specified input.

        This method ensures the input field is cleared if it already contains any value. It waits briefly
        to allow actions to be processed before proceeding. The text input is then sent to the web element.
        The method is static and can be called without creating an instance of the class.

        :param control: The web element where text input will be performed.
        :type control: WebElement
        :param text: The text to be input into the web element.
        :type text: str
        :return: None
        """
        time.sleep(0.5)
        if control.get_attribute('value') != '':
            control.send_keys(Keys.CONTROL, 'a')
            time.sleep(0.05)
            control.send_keys(Keys.DELETE)
        control.send_keys(text)

    def login(self, browser: Browser, load: bool = True) -> None:
        """
        Logs into the service by interacting with the browser instance. Handles pre-login setup,
        input of user credentials, bypassing CAPTCHA, logging state, and post-login actions. In
        case of an issue, logs the error and raises an exception.

        :param browser: The browser instance used to perform login actions.
        :type browser: Browser
        :param load: A flag that determines whether to load the service URL. Defaults to True.
        :type load: bool
        :return: None
        """
        self._browser = browser
        self._weblogger.browser = browser
        self._browser.error_log_dir = "error"
        try:
            if load:
                log.debug("Opening %s" % self.url)
                self._browser.force_get(self.url)
                self._browser.wait_for_page_inactive(2)
                if (self.cookies_button and
                        self._browser.wait_for_element(self.cookies_button.by, self.cookies_button.selector, 2)):
                    self._browser.safe_click(self.cookies_button.by, self.cookies_button.selector)
            log.info("Logging into service...")
            self._weblogger.trace("pre-login")
            _sleep_with_message(self.pre_login_delay, "Pre-login")
            input_user = self._browser.wait_for_element(self.user_input.by, self.user_input.selector)
            if input_user is None:
                print(f"No user input {self.user_input} found!")
                self._weblogger.error()
            assert input_user is not None
            input_password = self._browser.wait_for_element(self.password_input.by, self.password_input.selector)
            assert input_password is not None
            username = self.username.get()
            self._browser.click_element_with_js(input_user)
            time.sleep(0.5)
            self.input(input_user, username)
            self._weblogger.trace("username-input")
            password = self.password.get()
            if password is not None:
                input_user.send_keys(Keys.TAB)
                self.input(input_password, password)
                time.sleep(0.5)
            else:
                raise Exception(f"No valid password found for service '{self.name}', user '{username}'!")
            self._weblogger.trace("password-input")
            self._wait_for_reCAPTCHA_v3_token()
            input_password.send_keys(Keys.ENTER)
            self._browser.wait_for_page_load_completed()
            _sleep_with_message(self.post_login_delay, "Post-login")
            self._weblogger.trace("post-login")
            log.info("Done.")
        except Exception as e:
            log.info("Cannot login into service: %s" % e)
            self._weblogger.error()
            raise

    def _read_payments(self) -> list[Payment]:
        """
        Reads and retrieves a list of payment records. This method is intended
        to be implemented by subclasses, and it serves as a placeholder to
        ensure that any subclass explicitly defines functionality for reading
        payment data in a specific manner.

        The method does not contain implementation in this base class and will
        raise `NotImplementedError` if not overridden.

        :return: A list of Payment objects representing the payment records.
        :rtype: list[Payment]
        """
        raise NotImplementedError

    def get_payments(self, browser: Browser) -> list[Payment]:
        """
        Retrieves a sorted list of payment records for the service. The method processes
        the payment data by first logging into the service via the provided browser
        instance, retrieving and sorting payments based on location order, and handling
        any exceptions that occur during the process. In the event of an error, it logs
        the error and returns default payment records for each location. The method
        ensures to log out of the service after execution, regardless of the outcome.

        :param browser: Browser instance used to perform login and interact with the
            service.
        :type browser: Browser
        :return: List of Payment objects sorted according to the defined location order.
        :rtype: list[Payment]
        """
        try:
            print(f'Processing service {self.name}...')
            self._browser = browser
            self.login(self._browser)
            payments = sorted(self._read_payments(),
                              key=lambda value: self._location_order.get(value.location, float('inf')))
        except Exception as e:
            print(f'{e.__class__.__name__}:{str(e)}\n'f'Cannot get payments for service {self.name}!')
            payments = [Payment(self.name, location, None, None)
                        for location in self.locations]
            self._weblogger.error()
        finally:
            self.logout()
        return payments

    def logout(self) -> None:
        """
        Logs the user out of the application by interacting with the browser element specified
        and ensures the page becomes inactive after the logout action. It handles potential issues
        if the logout button is not found or a general browser-related exception occurs.

        :raises NoSuchElementException: Raised when the logout button is not found.
        :raises WebDriverException: Raised when any issue occurs with the WebDriver during the
            logout process.

        :return: None
        """
        try:
            self._weblogger.trace("pre-logout")
            self._browser.find_and_click_element_with_js(self.logout_button.by, self.logout_button.selector)
            self._browser.wait_for_page_inactive(2)
            self._weblogger.trace("post-logout")
        except NoSuchElementException:
            log.debug("Cannot click logout button. Are we even logged in?")
        except WebDriverException:
            self._weblogger.error()
