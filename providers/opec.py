import time
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from accounts import Account
from payments import Payment, get_amount, get_date
from .baseservice import AuthElement, BaseService
from log import setup_logging

log = setup_logging(__name__, 'DEBUG')


def _get_invoice_value(columns: List[WebElement]):
    if columns[7].text:
        return get_amount(columns[7], True)
    return get_amount(columns[5], True)


class Opec(BaseService):
    def __init__(self, keystore_user: str, accounts: List[Account]):
        user_input = AuthElement(By.ID, "_58_login")
        password_input = AuthElement(By.ID, "_58_password")
        url = "https://ebok.opecgdy.com.pl/home"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, keystore_user, accounts, user_input, password_input)

    def get_payments(self):
        self.browser.find_element_ex(By.TAG_NAME, 'a', 'text=Płatności').click()
        self.browser.find_element_ex(By.TAG_NAME, 'a', 'text=Dokumenty').click()
        self.browser.wait_for_network_inactive()
        time.sleep(1)
        invoices = self.browser.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
        amount = 0
        due_date = None
        for invoice in invoices:
            columns = invoice.find_elements(By.TAG_NAME, 'td')
            value = _get_invoice_value(columns)
            if columns[6].text == "Zapłacony" and value > 0:
                    continue
            amount += value
            date = get_date(columns[4])
            if due_date is None or (date < due_date and value > 0):
                due_date = date
        return [Payment(amount, due_date, self.accounts[0])]
