from typing import List

from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from time import sleep

from accounts import Account
from payments import Payment
from .baseservice import AuthElement, BaseService
from browser import setup_logging
from datetime import date

log = setup_logging(__name__, 'DEBUG')


class Multimedia(BaseService):
    def __init__(self, locations: dict[str, Location]):
        user_input = AuthElement(By.ID, "Login_SSO_UserName")
        password_input = AuthElement(By.ID, "Login_SSO_Password")
        url = "https://ebok.multimedia.pl/panel-glowny.aspx"
        self._locations_map = locations
        keystore_service = self.__class__.__name__.lower()
        locations = cast(tuple[Location, ...], tuple(locations.values()))  # to satisfy static code analyzers
        super().__init__(url, keystore_service, locations, user_input, password_input, pre_login_delay= 5)

    def _get_location(self, amount: str):
        location = [location for value, location in self._locations_map.items() if amount.startswith(value)]
        if not location:
            raise Exception(f"Cannot find suitable location for payment '{amount}'!")
        return location[0]

    def get_payments(self):
        log.info("Getting payments...")
        payments = []
        while any(item.is_empty() for item in payments) or len(payments) == 0:
            sleep(0.1)
            payments = []
            invoices = self.browser.wait_for_elements(By.CLASS_NAME, "invoiceInfo")
            if invoices is None:
                today = date.today()
                due_date = date(today.year, today.month, 20)
                for account in self.accounts:
                    payments.append(Payment(0, due_date, account))
                return payments
            for invoice in invoices:
                try:
                    amount = invoice.find_element(By.CLASS_NAME, "kwota").text
                    due_date = invoice.find_element(By.CLASS_NAME, "platnoscDo")
                    log.debug("Got amount '%s'" % amount)
                    account = self._get_account(amount)
                    payments.append(Payment(amount, due_date, account))
                except StaleElementReferenceException:
                    log.debug("StaleElementReferenceException occurred, retrying")
                    payments.append(Payment())
        return payments
