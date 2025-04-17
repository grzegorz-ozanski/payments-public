from typing import List

from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.common.by import By

from accounts import Account
from payments import Payment
from .baseservice import AuthElement, BaseService
from log import setup_logging

log = setup_logging(__name__, 'DEBUG')


class Energa(BaseService):
    def __init__(self, keystore_user: str, accounts: List[Account]):
        user_input = AuthElement(By.ID, "email_login")
        password_input = AuthElement(By.ID, "password")
        url = "https://24.energa.pl"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, keystore_user, accounts, user_input, password_input)

    def logout(self):
        try:
            self.browser.open_dropdown_menu(By.XPATH, '//button[contains(@class, "hover-submenu")]')
            self.browser.find_element(By.XPATH, '//span[contains(text(), "Wyloguj się")]').click()
        except AttributeError as e:
            if 'move_to requires a WebElement' in str(e):
                log.debug("Cannot click logout button. Are we even logged in?")
            else:
                raise

    def get_payments(self):
        log.info("Getting payments...")
        self.browser.wait_for_page_load_completed()
        accounts_lists = self.browser.wait_for_elements(By.CSS_SELECTOR, 'label')
        log.debug("Identified %d accounts" % len(accounts_lists))
        payments = []
        for account_id in range(len(accounts_lists)):
            print(f'...account {account_id+1} of {len(accounts_lists)}')
            log.debug("Opening account page")
            self.browser.wait_for_element_disappear(By.CSS_SELECTOR, 'div.popup.center')
            accounts_lists[account_id].click()
            account = self._get_account(
                self.browser.wait_for_element(By.CSS_SELECTOR, '.text.es-text.variant-body-bold.mlxs.mrm').text)
            log.debug("Getting payment")
            amount = self.browser.wait_for_element(By.CSS_SELECTOR, 'h1.text.es-text.variant-balance').text
            self.browser.wait_for_element_disappear(By.CSS_SELECTOR, 'div.popup__wrapper')
            self.browser.find_element(By.XPATH, '//a[contains(text(), "Faktury")]').click()
            invoices = self.browser.find_elements(
                By.XPATH,
                '//span[contains(text(), "Termin płatności")]/../..//*[contains(@class, "variant-body")]')
            if invoices:
                due_date = invoices[1].text
            else:
                due_date = None
            payments.append(Payment(amount, due_date, account))
            log.debug("Moving to the next account")
            self.browser.find_element(By.XPATH, '//span[contains(text(), "LISTA KONT")]/..').click()
            accounts_lists = self.browser.wait_for_elements(By.CSS_SELECTOR, 'label')

        return payments
