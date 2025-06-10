"""
    Multimedia (TV) provider module.
"""
from time import sleep
from typing import cast

from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, WebLogger
from payments import Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)

# === Multimedia specific constants - URLs, selectors and texts ===

SERVICE_URL = "https://ebok.multimedia.pl/panel-glowny.aspx"

USER_INPUT = PageElement(By.ID, "Login_SSO_UserName")
PASSWORD_INPUT = PageElement(By.ID, "Login_SSO_Password")
COOKIES_BUTTON = PageElement(By.ID, "cookiescript_accept")
RECAPTCHA_TOKEN = PageElement("HFreCaptchaToken", "03AFc")

INVOICE_CLASS = "invoiceInfo"
AMOUNT_CLASS = "kwota"
DUE_DATE_CLASS = "platnoscDo"

LOGIN_ERROR_TEXT = "span.logonFailureText"
PASSWORD_CHANGE_IDS = ("formPassword", "formConfirmation")
CAPTCHA_FORM_ID = "formCaptcha"

# for clarity, keep the first argument to browser.find_elements() even if it's equal to default By.ID
# noinspection PyArgumentEqualDefault
class Multimedia(Provider):
    """Multimedia TV provider."""

    def __init__(self, locations: dict[str, str]):
        """
        :param locations: Mapping from partial strings in amount fields to location names.
        """
        self._locations_map = locations
        locations_tuple = cast(tuple[str, ...], tuple(locations.values()))
        super().__init__(SERVICE_URL,
                         locations_tuple,
                         USER_INPUT,
                         PASSWORD_INPUT,
                         cookies_button=COOKIES_BUTTON,
                         recaptcha_token=RECAPTCHA_TOKEN,
                         pre_login_delay=1)

    def login(self, browser: Browser, weblogger: WebLogger, load: bool = True) -> None:
        """Retryable login with detection of CAPTCHA and password change."""
        wait = 5
        num_retries = 10
        for i in range(num_retries):
            log.debug(f'Login attempt {i + 1}')
            try:
                super().login(browser, weblogger, load if i == 0 else False)
            except Exception as ex:
                if i == num_retries - 1:
                    raise ex
                continue
            browser.wait_for_page_inactive(2)

            if browser.wait_for_element(By.CSS_SELECTOR, LOGIN_ERROR_TEXT, 2):
                log.debug(f'Login failed, retrying after {wait} seconds')
                weblogger.trace(f'failed-login-attempt-{i}')
            elif all(browser.find_elements(By.ID, id_) for id_ in PASSWORD_CHANGE_IDS):
                raise RuntimeError("Couldn't login, reason: password change required")
            else:
                return

        reason = "unknown"
        if browser.find_elements(By.ID, CAPTCHA_FORM_ID):
            reason = "CAPTCHA required"
        raise RuntimeError(f"Couldn't login in {num_retries} attempts! Reason: {reason}")

    def _get_location_by_amount(self, amount: str) -> str:
        """Find the first matching location for the given amount prefix."""
        try:
            return next(location for value, location in self._locations_map.items() if amount.startswith(value))
        except StopIteration:
            raise Exception(f"Cannot find suitable location for payment '{amount}'!")

    def _fetch_payments(self, browser: Browser, weblogger: WebLogger) -> list[Payment]:
        """Extracts payment records from the invoice list."""
        log.info("Getting payments...")
        sleep(0.1)
        payments = [Payment(self.name, location) for location in self.locations]
        invoices = browser.wait_for_elements(By.CLASS_NAME, INVOICE_CLASS)
        if invoices is None:
            return payments
        for invoice in invoices:
            amount = invoice.find_element(By.CLASS_NAME, AMOUNT_CLASS).text
            due_date = invoice.find_element(By.CLASS_NAME, DUE_DATE_CLASS).text
            log.debug("Got amount '%s'" % amount)
            location = self._get_location_by_amount(amount)
            index = payments.index(next(payment for payment in payments if payment.location == location))
            payments[index] = Payment(self.name, location, due_date, amount)
        return payments
