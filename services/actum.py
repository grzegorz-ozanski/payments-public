from selenium.webdriver.common.by import By
from payment import Payment
from datetime import date
from .service import AuthInput, Service
from log import setup_logging

log = setup_logging(__name__, 'DEBUG')


class Actum(Service):
    def __init__(self, keystore_user):
        user_input = AuthInput(By.CSS_SELECTOR, "[aria-labelledby=login]")
        password_input = AuthInput(By.CSS_SELECTOR, "[aria-labelledby=haslo]")
        url = "https://iok.actum.pl/InetObsKontr/LoginPage"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, keystore_user, user_input, password_input)

    def get_payments(self):
        log.info("Getting payments...")
        amount = self.browser.wait_for_element('home-amount', By.CLASS_NAME)
        due_date = self.browser.wait_for_element('home-info', By.CLASS_NAME)
        due_date = due_date.find_element(By.TAG_NAME, 'span')
        account = self._get_account('Hodowlana')

        log.debug(f"Got amount '{amount.text}' of account '{account.name}'")
        return [Payment(amount, due_date, account)]

    def logout(self):
        self.browser.find_elements(By.TAG_NAME, 'button')[2].click()
