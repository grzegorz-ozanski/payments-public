from abc import ABC
from selenium.webdriver.common.by import By
from payment import Payment
from .service import AuthElement, BaseService
from datetime import date


class IOK(BaseService):
    def __init__(self, account_name, due_day, url, keystore_user, keystore_service, log):
        user_input = AuthElement(By.CSS_SELECTOR, "[aria-labelledby=login]")
        password_input = AuthElement(By.CSS_SELECTOR, "[aria-labelledby=haslo]")
        self.log = log
        self.account_name = account_name
        today = date.today()
        self.due_date = date(today.year, today.month, due_day)
        super().__init__(url, keystore_service, keystore_user, user_input, password_input)

    def get_payments(self):
        self.log.info("Getting payments...")
        self.browser.wait_for_page_load_completed()
        if len(self.browser.find_elements(By.CSS_SELECTOR, 'a.ng-star-inserted')) <= 1:
            return [Payment(0, self.due_date, self.account_name)]
        amount = self.browser.wait_for_element(By.CLASS_NAME, 'home-amount')
        due_date = self.browser.wait_for_element(By.CLASS_NAME, 'home-info')
        due_date = due_date.find_element(By.TAG_NAME, 'span')

        self.log.debug(f"Got amount '{amount.text}' of account '{self.account_name}'")
        return [Payment(amount, due_date, self.account_name)]
