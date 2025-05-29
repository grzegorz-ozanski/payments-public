"""
    Base classes and utilities for payment data providers using Selenium.

    Includes:
    - Provider base class with login/logout logic and payment retrieval interface.
    - Credential helper for secure access to secrets.
    - PageElement dataclass for defining input/button locators.
"""
from os import environ
import time
from dataclasses import dataclass

import keyring
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from browser import setup_logging, Browser, WebLogger
from payments import Payment

log = setup_logging(__name__)

# === Shared constants ===

DEFAULT_LOGOUT_XPATH = (
    '//*[contains(string(), "Wyloguj") and not(.//*[contains(string(), "Wyloguj")])]'
)


def _sleep_with_message(amount: int, message: str):
    """Sleep for `amount` seconds, logging a debug message first."""
    if amount:
        log.debug(f"{message}: sleeping {amount} seconds")
        time.sleep(amount)


@dataclass
class PageElement:
    """Element locator used for finding inputs and buttons in the page."""
    by: str
    selector: str


class Credential:
    """
    Retrieve credentials from environment or system keyring.

    Priority: environment variable > keyring service.
    """
    def __init__(self, service_name, name, env_upper: bool = True):
        self.keyring_service = service_name
        self.keyring = name
        self.environ = f'{service_name}_{name}'
        if env_upper:
            self.environ = self.environ.upper()

    def get(self) -> str | None:
        """Return the credential value, or raise if not found."""
        if value := environ.get(self.environ):
            return value
        value = keyring.get_password(self.keyring_service, self.keyring)
        if value and value.strip():
            return value.strip()
        raise RuntimeError(f'"{self.keyring}" not found in env {self.environ} or keyring service {self.keyring_service}!')


class Provider:
    """Base class for a payment provider using Selenium."""

    def __init__(self, url: str, locations: tuple[str, ...],
                 user_input: PageElement, password_input: PageElement,
                 logout_button: PageElement | None = None, cookies_button: PageElement | None = None,
                 recaptcha_token: PageElement | None = None, recaptcha_token_prefix: str | None = None,
                 pre_login_delay: int = 0, post_login_delay: int = 0):
        """
        :param url: URL of the login page
        :param locations: List of location names handled by this provider
        :param user_input: Locator for username input field
        :param password_input: Locator for password input field
        :param logout_button: Optional locator for logout button (default: "Wyloguj")
        :param cookies_button: Optional locator for cookie consent
        :param recaptcha_token: Optional locator for reCAPTCHA v3 token
        :param recaptcha_token_prefix: Prefix required in reCAPTCHA value
        :param pre_login_delay: Sleep before login form fill
        :param post_login_delay: Sleep after login submit
        """
        self.url = url
        self.name = self.__class__.__name__.lower()
        self.locations = locations
        self._location_order = {location: i for i, location in enumerate(self.locations)}
        self.user_input = user_input
        self.password_input = password_input
        self.username = Credential(self.name, 'username')
        self.password = Credential(self.name, 'password')

        if not logout_button:
            logout_button = PageElement(By.XPATH, DEFAULT_LOGOUT_XPATH)
        self.logout_button = logout_button
        self.cookies_button = cookies_button
        self.recaptcha_token = recaptcha_token
        self.recaptcha_token_prefix = recaptcha_token_prefix
        self.pre_login_delay = pre_login_delay
        self.post_login_delay = post_login_delay

    def __repr__(self) -> str:
        """Provider name and list of supported locations."""
        return f'{self.name}: [{", ".join(map(str, self.locations))}]'

    def _get_location(self, name_string: str) -> str:
        """Return first matching location from name_string or raise."""
        try:
            return next(location for location in self.locations if location in name_string)
        except StopIteration:
            log.error(f"Cannot find location for {self.name} (input: '{name_string}')")
            raise RuntimeError(f"Cannot find a valid location for service {self.name}!")

    # we want this method name to include reCAPTCHA name as is, not in lower case
    # noinspection PyPep8Naming
    def _wait_for_reCAPTCHA_v3_token(self, browser: Browser) -> None:
        """Wait until reCAPTCHA v3 token appears and matches expected prefix."""
        if self.recaptcha_token and self.recaptcha_token_prefix:
            browser.wait_for_condition(
                lambda d: d.find_element(self.recaptcha_token.by, self.recaptcha_token.selector)
                          .get_attribute("value")
                          .startswith(self.recaptcha_token_prefix)
            )

    @staticmethod
    def input(control: WebElement, text: str) -> None:
        """Clear the input field and type the given text."""
        time.sleep(0.5)
        if control.get_attribute('value') != '':
            control.send_keys(Keys.CONTROL, 'a')
            time.sleep(0.05)
            control.send_keys(Keys.DELETE)
        control.send_keys(text)

    def login(self, browser: Browser, weblogger: WebLogger, load: bool = True) -> None:
        """Perform login in the web application."""
        try:
            if load:
                log.debug("Opening %s" % self.url)
                browser.force_get(self.url)
                browser.wait_for_page_inactive(2)
                if (self.cookies_button and
                        browser.wait_for_element(self.cookies_button.by, self.cookies_button.selector, 2)):
                    browser.safe_click(self.cookies_button.by, self.cookies_button.selector)

            log.info("Logging into service...")
            weblogger.trace("pre-login")
            _sleep_with_message(self.pre_login_delay, "Pre-login")

            input_user = browser.wait_for_element(self.user_input.by, self.user_input.selector)
            if input_user is None:
                print(f"No user input {self.user_input} found!")
                weblogger.error()
            assert input_user is not None

            input_password = browser.wait_for_element(self.password_input.by, self.password_input.selector)
            assert input_password is not None

            username = self.username.get()
            if username is not None:
                browser.click_element_with_js(input_user)
                time.sleep(0.5)
                self.input(input_user, username)
            else:
                raise RuntimeError(f"No valid username found for service '{self.name}'!")
            weblogger.trace("username-input")

            password = self.password.get()
            if password is not None:
                input_user.send_keys(Keys.TAB)
                self.input(input_password, password)
                time.sleep(0.5)
            else:
                raise RuntimeError(f"No valid password found for service '{self.name}', user '{username}'!")

            weblogger.trace("password-input")
            self._wait_for_reCAPTCHA_v3_token(browser)
            input_password.send_keys(Keys.ENTER)

            browser.wait_for_page_load_completed()
            _sleep_with_message(self.post_login_delay, "Post-login")
            weblogger.trace("post-login")
            log.info("Done.")
        except Exception as e:
            log.info("Cannot login into service: %s" % e)
            weblogger.error()
            raise

    def _fetch_payments(self, browser: Browser, weblogger: WebLogger) -> list[Payment]:
        """Must be overridden in subclasses to return actual payments."""
        raise NotImplementedError(f"{self.__class__.__name__} must override _fetch_payments().")

    def get_payments(self, browser: Browser) -> list[Payment]:
        """Log in and fetch payments, return fallback on failure."""
        weblogger = WebLogger(self.name, browser)
        try:
            print(f'Processing service {self.name}...')
            self.login(browser, weblogger)
            payments = sorted(self._fetch_payments(browser, weblogger),
                              key=lambda value: self._location_order.get(value.location, float('inf')))
        except Exception as e:
            print(f'{e.__class__.__name__}:{str(e)}\nCannot get payments for service {self.name}!')
            payments = [Payment(self.name, location, None, None) for location in self.locations]
            weblogger.error()
        finally:
            self.logout(browser, weblogger)
        return payments

    def logout(self, browser: Browser, weblogger: WebLogger) -> None:
        """Click the logout button and wait for the page to finish logging out."""
        try:
            weblogger.trace("pre-logout")
            browser.find_and_click_element_with_js(self.logout_button.by, self.logout_button.selector)
            browser.wait_for_page_inactive(2)
            weblogger.trace("post-logout")
        except NoSuchElementException:
            log.debug("Cannot click logout button. Are we even logged in?")
        except WebDriverException:
            weblogger.error()
