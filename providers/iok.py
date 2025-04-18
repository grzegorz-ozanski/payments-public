from selenium.webdriver.common.by import By

from locations import Location
from payments import Payment
from .baseservice import AuthElement, BaseService
from datetime import date


class IOK(BaseService):
    def __init__(self, due_day, url, keystore_service, log, locations: tuple[Location, ...]):
        user_input = AuthElement(By.CSS_SELECTOR, "[aria-labelledby=login]")
        password_input = AuthElement(By.CSS_SELECTOR, "[aria-labelledby=haslo]")
        self.log = log
        today = date.today()
        self.due_date = date(today.year, today.month, due_day)
        super().__init__(url, keystore_service, locations, user_input, password_input)

    def get_payments(self):
        self.log.info("Getting payments...")
        self.browser.wait_for_page_load_completed()
        if len(self.browser.find_elements(By.CSS_SELECTOR, 'a.ng-star-inserted')) <= 1:
            return [Payment(0, self.due_date, self.locations[0])]
        amount = self.browser.wait_for_element(By.CLASS_NAME, 'home-amount')
        due_date = self.browser.wait_for_element(By.CLASS_NAME, 'home-info')
        due_date = due_date.find_element(By.TAG_NAME, 'span')

        self.log.debug(f"Got amount '{amount.text}' of location '{self.locations[0].name}'")
        return [Payment(amount, due_date, self.locations[0])]
