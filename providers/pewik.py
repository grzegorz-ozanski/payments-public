from typing import List

from selenium.webdriver.common.by import By

from accounts import Account
from payments import Payment
from datetime import date
from .baseservice import AuthElement, BaseService
from log import setup_logging

log = setup_logging(__name__, 'DEBUG')


class Pewik(BaseService):
    def __init__(self, keystore_user: str, accounts: List[Account]):
        user_input = AuthElement(By.ID, "username")
        password_input = AuthElement(By.ID, "password")
        url = "https://ebok.pewik.gdynia.pl/login"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, keystore_user, accounts, user_input, password_input)

    def get_payments(self):
        payments = []
        next_id = 1
        cookies_panel = self.browser.find_element(By.CLASS_NAME, 'panel-cookies')
        if cookies_panel:
            cookies_panel.find_element(value='cookiesClose').click()
        invoice = self.browser.find_element_ex(By.TAG_NAME, 'a', "text=Faktury i salda")
        invoice.click()
        invoice = self.browser.find_element_ex(By.TAG_NAME, 'a', "text=Salda")
        invoice.click()
        self.browser.wait_for_page_load_completed()
        while True:
            account = self._get_account(
                self.browser.find_element(By.CLASS_NAME, 'select2-chosen').find_elements(By.TAG_NAME, 'span')[2].text)
            balances = self.browser.find_element(By.ID, 'saldaWplatyWykaz').\
                find_element(By.TAG_NAME, 'tbody').\
                find_elements(By.TAG_NAME, 'tr')
            for item in balances:
                columns = item.find_elements(By.TAG_NAME, 'td')
                if len(columns) > 1:
                    payments.append(Payment(columns[5], columns[3], account))
                else:
                    payments.append(Payment(0, date.today(), account))
            accounts_arrow = self.browser.find_element(By.CLASS_NAME, 'select2-arrow')
            accounts_arrow.click()
            accounts = self.browser.find_elements(By.CLASS_NAME, 'select2-result')
            if next_id < len(accounts):
                accounts[next_id].click()
                next_id += 1
            else:
                break
        return payments

    def logout(self):
        self.browser.find_element(By.CLASS_NAME, 'btn-wyloguj').click()