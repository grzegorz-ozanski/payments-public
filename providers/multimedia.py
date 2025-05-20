from datetime import date
from time import sleep
from typing import cast

from selenium.common.exceptions import StaleElementReferenceException
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
        self.default_due_date = date(today.year, today.month, 20)
        self.logged_in = False
        super().__init__(url, keystore_service, locations, user_input, password_input, pre_login_delay=5)

    def _get_location(self, amount: str):
        location = [location for value, location in self._locations_map.items() if amount.startswith(value)]
        if not location:
            raise Exception(f"Cannot find suitable location for payment '{amount}'!")
        return location[0]

    def login(self, browser, load=True):
        wait = 10
        num_retries = 10
        for i in range(num_retries):
            log.debug(f'Login attempt {i + 1}')
            try:
                super().login(browser, load)
            except Exception as ex:
                if i == num_retries - 1:
                    raise ex
            self._browser.wait_for_page_inactive()
            if self._browser.wait_for_element(By.CSS_SELECTOR, 'span.logonFailureText'):
                log.debug(f'Login failed, retrying after {wait} seconds')
                self.save_trace_logs(f'failed-login-attempt-{i}')
            else:
                self.logged_in = True
                return

    def _read_payments(self):
        log.info("Getting payments...")
        payments = []
        if not self.logged_in:
            raise RuntimeError("Not logged in!")
        while any(item.is_empty() for item in payments) or len(payments) == 0:
            sleep(0.1)
            payments = []
            invoices = self._browser.wait_for_elements(By.CLASS_NAME, "invoiceInfo")
            if invoices is None:
                for location in self.locations:
                    payments.append(Payment(due_date=self.default_due_date, location=location, provider=self.name))
                return payments
            for invoice in invoices:
                try:
                    amount = invoice.find_element(By.CLASS_NAME, "kwota").text
                    due_date = invoice.find_element(By.CLASS_NAME, "platnoscDo").text
                    log.debug("Got amount '%s'" % amount)
                    location = self._get_location(amount)
                    payments.append(Payment(amount, due_date, location, self.name))
                except StaleElementReferenceException:
                    log.debug("StaleElementReferenceException occurred, retrying")
                    payments.append(Payment())
        return payments
