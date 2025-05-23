from datetime import date

from selenium.webdriver.common.by import By

from locations import Location
from payments import Payment
from .provider import PageElement, Provider


class IOK(Provider):
    def __init__(self, due_day, url, keystore_service, log, location: Location):
        user_input = PageElement(By.CSS_SELECTOR, "[aria-labelledby=login]")
        password_input = PageElement(By.CSS_SELECTOR, "[aria-labelledby=haslo]")
        logout_button = PageElement(By.CSS_SELECTOR, "button.wcag.bg.navTxtColor")
        self.log = log
        self.timeout = 0.1
        today = date.today()
        self.due_date = date(today.year, today.month, due_day)
        super().__init__(url, keystore_service, (location,), user_input, password_input, logout_button)

    def _read_payments(self):
        self.log.info("Getting payments...")
        self._browser.wait_for_page_inactive()
        amount = self._browser.wait_for_element(By.CLASS_NAME, 'home-amount', self.timeout)
        due_date = self._browser.wait_for_element(By.CLASS_NAME, 'home-info', self.timeout)
        if amount is None or due_date is None:
            return [Payment(self.name, self.locations[0], self.due_date)]
        due_date = due_date.find_elements(By.TAG_NAME, 'span')
        due_date = due_date[-1] if due_date else 'today'
        self.log.debug(f"Got amount '{amount.text}' of location '{self.locations[0].name}'")
        return [Payment(self.name, self.locations[0], due_date, amount)]
