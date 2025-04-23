from selenium.webdriver.common.by import By

from locations import Location
from payments import Payment
from datetime import date
from .baseservice import AuthElement, BaseService
from browser import setup_logging

log = setup_logging(__name__, 'DEBUG')


class Pewik(BaseService):
    def __init__(self, *locations: Location):
        user_input = AuthElement(By.ID, "username")
        password_input = AuthElement(By.ID, "password")
        logout_button = AuthElement(By.CLASS_NAME, 'btn-wyloguj')
        url = "https://ebok.pewik.gdynia.pl/login"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, locations, user_input, password_input, logout_button)

    def get_payments(self):
        payments = []
        next_id = 1
        cookies_panel = self.browser.find_element(By.CLASS_NAME, 'panel-cookies')
        if cookies_panel:
            self.browser.wait_for_element_clickable(By.CLASS_NAME, 'panel-cookies')
            self.browser.trace_click(cookies_panel.find_element(value='cookiesClose'))
        invoice = self.browser.find_element(By.XPATH, '//a[text()="Faktury i salda"]')
        self.browser.trace_click(invoice)
        invoice = self.browser.find_element(By.XPATH, '//a[text()="Salda"]')
        self.browser.trace_click(invoice)
        self.browser.wait_for_page_load_completed()
        while True:
            location = self._get_location(
                self.browser.find_element(By.CLASS_NAME, 'select2-chosen').find_elements(By.TAG_NAME, 'span')[2].text)
            balances = self.browser.find_element(By.ID, 'saldaWplatyWykaz').\
                find_element(By.TAG_NAME, 'tbody').\
                find_elements(By.TAG_NAME, 'tr')
            for item in balances:
                columns = item.find_elements(By.TAG_NAME, 'td')
                if len(columns) > 1:
                    payments.append(Payment(columns[5], columns[3], location))
                else:
                    payments.append(Payment(0, date.today(), location))
            locations_arrow = self.browser.find_element(By.CLASS_NAME, 'select2-arrow')
            self.browser.trace_click(locations_arrow)
            locations = self.browser.find_elements(By.CLASS_NAME, 'select2-result')
            if next_id < len(locations):
                self.browser.trace_click(locations[next_id])
                next_id += 1
            else:
                break
        return payments
