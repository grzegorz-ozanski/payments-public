from typing import List

from selenium.webdriver.common.by import By

from accounts import Account
from log import setup_logging
from payments import Payment, get_amount
from .baseservice import AuthElement, BaseService

log = setup_logging(__name__, 'DEBUG')


class Pgnig(BaseService):
    def __init__(self, keystore_user: str, accounts: List[Account]):
        user_input = AuthElement(By.NAME, "identificator")
        password_input = AuthElement(By.NAME, "accessPin")
        url = "https://ebok.pgnig.pl"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, keystore_user, accounts, user_input, password_input)

    def get_payments(self):
        log.info("Getting payments...")
        account = self._get_account(self.browser.wait_for_element(By.CLASS_NAME, 'reading-adress').text)
        log.info("Getting invoices menu...")
        invoices_menu = self.browser.find_element_ex(By.CLASS_NAME, "menu-element", 'text = Faktury')
        log.info("Opening invoices menu...")
        invoices_menu.click()
        log.info("Getting invoices list...")
        invoices = self.browser.wait_for_elements(By.CLASS_NAME, "main-row-container")
        log.info("Filtering unpaid invoices...")
        unpaid_invoices = [item for item in invoices if item.find_element(By.CLASS_NAME, 'button').text == "Zapłać"]
        payments_dict = {}
        for invoice in unpaid_invoices:
            columns = invoice.find_elements(By.CLASS_NAME, "columns")
            payments_dict[columns[2].text] = payments_dict.get(columns[2].text, 0) + float(get_amount(columns[3], '.'))
        payments = []
        for date, amount in payments_dict.items():
            payments.append(Payment(amount, date, account))
        return payments
