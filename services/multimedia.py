from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from time import sleep

from accountmanager import AccountsManager
from payment import Payment
from .service import AuthElement, Service
from log import setup_logging
from datetime import date

log = setup_logging(__name__, 'DEBUG')


class Multimedia(Service):
    def __init__(self, keystore_user):
        user_input = AuthElement(By.ID, "Login_SSO_UserName")
        password_input = AuthElement(By.ID, "Login_SSO_Password")
        url = "https://ebok.multimedia.pl/panel-glowny.aspx"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, keystore_user, user_input, password_input)

    def get_payments(self, accounts: AccountsManager):
        log.info("Getting payments...")
        payments = []
        while any(item.is_empty() for item in payments) or len(payments) == 0:
            sleep(0.1)
            payments = []
            invoices = self.browser.wait_for_elements(By.CLASS_NAME, "invoiceInfo")
            if invoices is None:
                today = date.today()
                due_date = date(today.year, today.month, 20)
                for account_name in ["Hodowlana", "Sezamowa"]:
                    payments.append(Payment(0, due_date, accounts.get(account_name)))
                return payments
            for invoice in invoices:
                try:
                    amount = invoice.find_element(By.CLASS_NAME, "kwota").text
                    due_date = invoice.find_element(By.CLASS_NAME, "platnoscDo")
                    log.debug("Got amount '%s'" % amount)
                    if amount.startswith("77,00"):
                        account = accounts.get("Sezamowa")
                    elif amount.startswith("90,00"):
                        account = accounts.get("Hodowlana")
                    else:
                        raise Exception(f"Cannot find suitable account for payment '{amount}'!")
                    payments.append(Payment(amount, due_date, account))
                except StaleElementReferenceException:
                    log.debug("StaleElementReferenceException occurred, retrying")
                    payments.append(Payment())
        return payments
