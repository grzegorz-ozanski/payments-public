from abc import ABC
from selenium.webdriver.common.by import By
from payment import Payment
from .service import AuthElement, Service


class IOK(Service, ABC):
    def __init__(self, account_name, url, keystore_user, keystore_service, log):
        user_input = AuthElement(By.CSS_SELECTOR, "[aria-labelledby=login]")
        password_input = AuthElement(By.CSS_SELECTOR, "[aria-labelledby=haslo]")
        self.log = log
        self.account_name = account_name
        super().__init__(url, keystore_service, keystore_user, user_input, password_input)

    def get_payments(self):
        self.log.info("Getting payments...")
        amount = self.browser.wait_for_element('home-amount', By.CLASS_NAME)
        due_date = self.browser.wait_for_element('home-info', By.CLASS_NAME)
        due_date = due_date.find_element(By.TAG_NAME, 'span')
        account = self._get_account(self.account_name)

        self.log.debug(f"Got amount '{amount.text}' of account '{account.name}'")
        return [Payment(amount, due_date, account)]
