from selenium.webdriver.common.by import By

from browser import setup_logging
from payments import Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)


class Pewik(Provider):
    def __init__(self, *locations: str):
        user_input = PageElement(By.ID, "username")
        password_input = PageElement(By.ID, "password")
        logout_button = PageElement(By.CLASS_NAME, 'btn-wyloguj')
        url = "https://ebok.pewik.gdynia.pl/login"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, locations, user_input, password_input, logout_button)

    def _read_payments(self) -> list[Payment]:
        payments = []
        next_id = 1
        cookies_panel = self._browser.find_element(By.CLASS_NAME, 'panel-cookies')
        if cookies_panel:
            self._browser.wait_for_element_clickable(By.CLASS_NAME, 'panel-cookies')
            self._browser.click_element_with_js(cookies_panel.find_element(value='cookiesClose'))
        invoice = self._browser.find_element(By.XPATH, '//a[text()="Faktury i salda"]')
        self._browser.trace_click(invoice)
        invoice = self._browser.find_element(By.XPATH, '//a[text()="Salda"]')
        self._browser.trace_click(invoice)
        self._browser.wait_for_page_load_completed()
        while True:
            location = self._get_location(
                self._browser.find_element(By.CLASS_NAME, 'select2-chosen').find_elements(By.TAG_NAME, 'span')[2].text)
            balances = self._browser.find_element(By.ID, 'saldaWplatyWykaz'). \
                find_element(By.TAG_NAME, 'tbody'). \
                find_elements(By.TAG_NAME, 'tr')
            for item in balances:
                columns = item.find_elements(By.TAG_NAME, 'td')
                if len(columns) > 1:
                    payments.append(Payment(self.name, location, columns[3], columns[5]))
                else:
                    payments.append(Payment(self.name, location))
            locations_arrow = self._browser.find_element(By.CLASS_NAME, 'select2-arrow')
            self._browser.trace_click(locations_arrow)
            locations = self._browser.find_elements(By.CLASS_NAME, 'select2-result')
            if next_id < len(locations):
                self._browser.trace_click(locations[next_id])
                next_id += 1
            else:
                break
        return payments
