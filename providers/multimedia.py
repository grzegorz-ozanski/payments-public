from time import sleep
from typing import cast

from selenium.webdriver.common.by import By

from browser import setup_logging, Browser
from payments import Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)


class Multimedia(Provider):
    def __init__(self, locations: dict[str, str]):
        self._locations_map = locations
        locations = cast(tuple[str, ...], tuple(locations.values()))  # to satisfy static code analyzers
        super().__init__("https://ebok.multimedia.pl/panel-glowny.aspx",
                         self.__class__.__name__.lower(),
                         locations,
                         PageElement(By.ID, "Login_SSO_UserName"),
                         PageElement(By.ID, "Login_SSO_Password"),
                         cookies_button=PageElement(By.ID, "cookiescript_accept"),
                         recaptcha_token=PageElement("HFreCaptchaToken", "03AFc"),
                         pre_login_delay=1)

    def _get_location(self, amount: str):
        try:
            return next(location for value, location in self._locations_map.items() if amount.startswith(value))
        except StopIteration:
            raise Exception(f"Cannot find suitable location for payment '{amount}'!")

    def login(self, browser: Browser, load: bool=True) -> None:
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
                self.save_trace_logs(f'failed-login-attempt-{i}')
            elif self._browser.find_elements(By.ID, 'formPassword') and self._browser.find_elements(By.ID, 'formConfirmation'):
                raise RuntimeError(f"Couldn't login, reason: password change required")
            else:
                return
        reason = "unknown"
        if self._browser.find_elements(By.ID, "formCaptcha"):
            reason = "CAPTCHA required"
        raise RuntimeError(f"Couldn't login in {num_retries} attempts! Reason: {reason}")

    def _read_payments(self) -> list[Payment]:
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
