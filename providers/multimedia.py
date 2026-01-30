"""
    Multimedia (TV) provider module.
"""
from os import getenv
from time import sleep

from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, Locator
from payments import Payment
from providers.login.recaptcha import RecaptchaLogin
from providers.provider import Provider

log = setup_logging(__name__)

# === Multimedia specific constants - URLs, selectors and texts ===

SERVICE_URL = 'https://ebok.multimedia.pl/'

USER_INPUT = Locator(By.ID, 'Login_SSO_UserName')
PASSWORD_INPUT = Locator(By.ID, 'Login_SSO_Password')
COOKIES_BUTTON = Locator(By.ID, 'cookiescript_accept')

INVOICE = Locator(By.CLASS_NAME, 'invoiceInfo')
AMOUNT = Locator(By.CLASS_NAME, 'kwota')
DUE_DATE = Locator(By.CLASS_NAME, 'platnoscDo')

LOGIN_ERROR_TEXT = Locator(By.CSS_SELECTOR, 'span.logonFailureText')
PASSWORD_CHANGE_ELEMENTS = (Locator(By.ID, 'formPassword'), Locator(By.ID, 'formConfirmation'))
CAPTCHA_FORM = Locator(By.ID, 'formCaptcha')

# for clarity, keep the first argument to browser.find_elements() even if it's equal to default By.ID
# noinspection PyArgumentEqualDefault
class Multimedia(Provider):
    """Multimedia TV provider."""

    def __init__(self, locations: dict[str, str]):
        """
        :param locations: Mapping from partial strings in amount fields to location names.
        """
        self._locations_map = locations
        locations_tuple = tuple(locations.values())
        self.debug_login = getenv('PAYMENTS_DEBUG_MULTIMEDIA_LOGIN', '0') == '1'
        super().__init__(SERVICE_URL,
                         locations_tuple,
                         USER_INPUT,
                         PASSWORD_INPUT,
                         overlay_buttons=[COOKIES_BUTTON],
                         needs_clear_user_profile=True,
                         pre_login_delay=1,
                         login_strategy=RecaptchaLogin)
        self.login_strategy.login_button = Locator(By.ID, 'LoginButton')

    def login(self, browser: Browser, load: bool = True) -> None:
        """Retryable login with detection of CAPTCHA and password change."""
        num_retries = 10
        for i in range(num_retries):
            print(f'Login attempt {i + 1}')
            if self.debug_login and i > 0:
                input('Press ENTER to continue...')
            try:
                super().login(browser, load if i == 0 else False)
            except Exception as ex:
                log.debug('Unexpectedly unhandled exception in %s.login(): %s',
                          self.__class__.__bases__[0].__name__, ex)
                if i == num_retries - 1:
                    raise ex
                continue
            browser.wait_for_page_inactive(2)

            if not self.logged_in or browser.wait_for_page_element(LOGIN_ERROR_TEXT, 2):
                log.debug('Login failure detected, retrying...')
                log.web_trace(f'failed-login-attempt-{i}')
            elif all(browser.find_page_elements(element) for element in PASSWORD_CHANGE_ELEMENTS):
                raise RuntimeError("Couldn't login, reason: password change required")
            else:
                # Either super().login() ended with success, or due to some misterious ways
                # we ended up here with page correctly logged in (i.e. no login elements are present)
                if self.logged_in or not any(
                        browser.wait_for_page_element(element, 1)
                        for element in [USER_INPUT, PASSWORD_INPUT]
                ):
                    self.logged_in = True
                    return
                log.debug('Undetected login failure, retrying...')
                log.web_trace(f'failed-login-attempt-unknown-{i}')

        reason = 'unknown'
        if browser.find_page_elements(CAPTCHA_FORM):
            reason = 'CAPTCHA required'
        raise RuntimeError(f"Couldn't login in {num_retries} attempts! Reason: {reason}")

    def _get_location_by_amount(self, amount: str) -> str:
        """Find the first matching location for the given amount prefix."""
        try:
            return next(location for value, location in self._locations_map.items() if amount.startswith(value))
        except StopIteration:
            raise Exception(f"Cannot find suitable location for payment '{amount}'!")

    def _fetch_payments(self, browser: Browser) -> list[Payment]:
        """Extracts payment records from the invoice list."""
        log.info('Getting payments...')
        sleep(0.1)
        payments = [Payment(self.name, location) for location in self.locations]
        invoices = browser.wait_for_page_elements(INVOICE)
        if invoices is None:
            for payment in payments:
                payment.comment = 'Timed out waiting for invoices list'
            return payments
        for invoice in invoices:
            amount = invoice.find_page_element(AMOUNT).text
            due_date = invoice.find_page_element(DUE_DATE).text
            log.debug("Got amount '%s'" % amount)
            location = self._get_location_by_amount(amount)
            index = payments.index(next(payment for payment in payments if payment.location == location))
            payments[index] = Payment(self.name, location, due_date, amount)
        return payments
