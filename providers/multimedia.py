from datetime import date
from time import sleep
from typing import cast

from selenium.webdriver.common.by import By

from browser import setup_logging
from locations import Location
from payments import Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)


class Multimedia(Provider):
    def __init__(self, locations: dict[str, Location]):
        user_input = PageElement(By.ID, "Login_SSO_UserName")
        password_input = PageElement(By.ID, "Login_SSO_Password")
        cookies_button = PageElement(By.ID, "cookiescript_accept")
        url = "https://ebok.multimedia.pl/panel-glowny.aspx"
        self._locations_map = locations
        keystore_service = self.__class__.__name__.lower()
        locations = cast(tuple[Location, ...], tuple(locations.values()))  # to satisfy static code analyzers
        today = date.today()
        self.logged_in = False
        super().__init__(url, keystore_service, locations, user_input, password_input,
                         cookies_button=cookies_button, pre_login_delay=1)

    def _get_location(self, amount: str):
        try:
            return next(location for value, location in self._locations_map.items() if amount.startswith(value))
        except StopIteration:
            raise Exception(f"Cannot find suitable location for payment '{amount}'!")

    def login(self, browser, load=True):
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
            else:
                return
        reason = "unknown"
        if self._browser.find_elements(By.ID, "formCaptcha"):
            reason = "CAPTCHA required"
        raise RuntimeError(f"Couldn't log in in {num_retries} attempts! Reason: {reason}")

    def _read_payments(self):
        log.info("Getting payments...")
        sleep(0.1)
        payments = [Payment(location=location, provider=self.name) for location in self.locations]
        invoices = self._browser.wait_for_elements(By.CLASS_NAME, "invoiceInfo")
        if invoices is None:
            return payments
        for invoice in invoices:
            amount = invoice.find_element(By.CLASS_NAME, "kwota").text
            due_date = invoice.find_element(By.CLASS_NAME, "platnoscDo").text
            log.debug("Got amount '%s'" % amount)
            location = self._get_location(amount)
            index = payments.index(next(payment for payment in payments if payment.location == location))
            payments[index] = Payment(amount, due_date, location, self.name)
        return payments
