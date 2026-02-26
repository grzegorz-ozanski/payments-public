"""
    Base classes and utilities for payment data providers using Selenium.

    Includes:
    - Provider base class with login/logout logic and payment retrieval interface.
    - Credential helper for secure access to secrets.
    - PageElement dataclass for defining input/button locators.
"""
import time

from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from selenium.webdriver.common.by import By

from browser import Browser, Locator, setup_logging
from payments.payments import Payment
from payments.providers.auth_flow import BaseLogin, OneStageLogin
from payments.providers.secrets.core import Secrets
from payments.console import print_progress, print_done

log = setup_logging(__name__)

# === Shared constants ===

DEFAULT_LOGOUT_XPATH = (
    '//*[contains(string(), "Wyloguj") and not(.//*[contains(string(), "Wyloguj")])]'
)


def _sleep_with_message(amount: int, message: str) -> None:
    """Sleep for `amount` seconds, logging a debug message first."""
    if amount:
        log.debug('%s: sleeping %s seconds', message, amount)
        time.sleep(amount)


class PaymentError(Exception):
    """
    General payment error
    """
    def __init__(self, message: str) -> None:
        self.reason = message
        super().__init__(message)


class LoginError(PaymentError):
    """
    Login error
    """
    ...


class FetchError(PaymentError):
    """
    Payments fetch error
    """
    ...


class Provider:
    """Base class for a payment provider using Selenium."""

    def __init__(self,
                 url: str,
                 locations: tuple[str, ...],
                 user_input: Locator,
                 password_input: Locator,
                 logout_button: Locator | None = None,
                 overlay_buttons: list[Locator] | None = None,
                 needs_clear_user_profile: bool = False,
                 pre_login_delay: int = 0,
                 post_login_delay: int = 0,
                 login_strategy: type[BaseLogin] = OneStageLogin):
        """
        :param url: URL of the login page
        :param locations: List of location names handled by this provider
        :param user_input: Locator for username input field
        :param password_input: Locator for password input field
        :param logout_button: Optional locator for logout button (default: "Wyloguj")
        :param overlay_buttons: Optional locator(s) for cookie consent or other overlays
        :param needs_clear_user_profile: True if providers web page needs clear user profile for proper operation
        False otherwise
        :param pre_login_delay: Sleep before the login form fill
        :param post_login_delay: Sleep after the login form submitted
        """
        self.url = url
        self.name = self.__class__.__name__.lower()
        self.locations = locations
        self._location_order = {location: i for i, location in enumerate(self.locations)}
        self.login_strategy = login_strategy(self.name, user_input, password_input,
                                             Secrets(self.name, 'username', 'password'))

        self.logout_button = logout_button or Locator(By.XPATH, DEFAULT_LOGOUT_XPATH)
        self.overlay_buttons = [] if overlay_buttons is None else overlay_buttons
        self.needs_clear_user_profile = needs_clear_user_profile
        self.pre_login_delay = pre_login_delay
        self.post_login_delay = post_login_delay
        self.logged_in = False  # TODO: consider refactoring after all providers have _is_logged_in implemented

    def __repr__(self) -> str:
        """Provider name and list of supported locations."""
        return f'{self.name}: [{", ".join(map(str, self.locations))}]'

    def get_payments(self, browser: Browser) -> list[Payment]:
        """Log in and fetch payments, return fallback on failure."""
        with log.browser(browser), log.group(self.name):
            try:
                message = f'Getting payments for service {self.name}...'
                log.debug(message)
                print_progress('logging in...')
                self.login(browser)
                if self.logged_in:
                    print_progress('fetching payments...')
                    payments = sorted(self._fetch_payments(browser),
                                      key=lambda value: self._location_order.get(value.location, float('inf')))
                    print_done('done.')
                else:
                    payments = self._default_payments('Login error')
            except (LoginError, FetchError) as e:
                msg = f'{e.__class__.__name__}: {str(e)}'
                log.exception(msg)
                print(msg)
                log.web_error()
                payments = self._default_payments(e.reason)
            except Exception as e:
                msg = f'{e.__class__.__name__}: {str(e)}\nCannot get payments for service {self.name}!'
                log.exception(msg)
                print(msg)
                log.web_error()
                payments = self._default_payments(str(e))
            finally:
                self.logout(browser)
            return payments

    def load(self, browser: Browser) -> None:
        """ Opens the login page """
        log.debug('Opening "%s" in a new tab' % self.url)
        browser.open_in_new_tab(self.url)
        log.debug('Wating 2 seconds')
        browser.wait_for_page_inactive(2)
        for overlay_button in self.overlay_buttons:
            log.debug('Checking overlay button %s', overlay_button)
            webelement = browser.wait_for_page_element(overlay_button, 2)
            if webelement:
                log.debug('Overlay button %s found, closing', overlay_button)
                try:
                    browser.safe_click_page_element(overlay_button)
                    browser.wait_for_page_element_disappear(overlay_button, 2)
                except TimeoutException:
                    log.debug('Timeout expired waiting for button %s to become clickable!', overlay_button)

    def login(self, browser: Browser, load: bool = True) -> None:
        """Perform login in the web application."""
        if self._is_logged_in(browser):
            return
        try:
            if load:
                self.load(browser)

            log.info('Logging into service...')
            log.web_trace('pre-login')
            _sleep_with_message(self.pre_login_delay, 'Pre-login')

            self.login_strategy.execute(browser)
            log.debug('Form submitted')

            browser.wait_for_page_load_completed()
            browser.wait_for_page_inactive()
            _sleep_with_message(self.post_login_delay, 'Post-login')
            log.web_trace('post-login')
            log.info('Done.')
            self.logged_in = self.login_strategy.verify(browser)
        except Exception as e:
            if 'Timed out receiving message from renderer' in str(e):
                # Let the further code decide if the page really failed to load
                return
            log.info('Cannot login into service: %s' % e)
            log.web_error()
            raise

    def logout(self, browser: Browser) -> None:
        """Click the logout button and wait for the page to finish logging out."""
        if not self.logged_in:
            log.debug("Not logged in into service '%s', skipping logout", self.name)
            return
        try:
            log.web_trace('pre-logout')
            browser.find_and_click_page_element_using_js(self.logout_button)
            browser.wait_for_page_inactive(2)
            log.web_trace('post-logout')
        except NoSuchElementException:
            log.debug('Cannot click logout button. Are we even logged in?')
        except WebDriverException:
            log.web_error()

    def _default_payments(self, message: str = '') -> list[Payment]:
        return [Payment(self.name,
                        location,
                        None,
                        None,
                        message)
                for location in self.locations]

    def _is_logged_in(self, browser: Browser) -> bool:
        return False

    def _fetch_payments(self, browser: Browser) -> list[Payment]:
        """Must be overridden in subclasses to return actual payments."""
        raise NotImplementedError(f'{self.__class__.__name__} must override _fetch_payments().')

    def _get_location(self, name_string: str) -> str:
        """Return the first matching location from name_string or raise."""
        try:
            return next(location for location in self.locations if location in name_string)
        except StopIteration:
            log.error("Cannot find location for %s (input: '%s')",
                      self.name, name_string)
            raise RuntimeError(f'Cannot find a valid location for service {self.name}!')
