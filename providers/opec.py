from time import sleep

from selenium.webdriver.common.by import By
from browser import setup_logging
from locations import Location
from payments import Amount, DueDate, Payment
from .provider import AuthElement, Provider

log = setup_logging(__name__)


class Opec(Provider):
    def __init__(self, *locations: Location):
        user_input = AuthElement(By.ID, "_58_login")
        password_input = AuthElement(By.ID, "_58_password")
        url = "https://ebok.opecgdy.com.pl/home"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, locations, user_input, password_input)

    def get_payments(self):
        self.save_trace_logs("pre-payments-click")
        self.browser.find_element(By.XPATH, '//a[text()="Płatności"]').click()
        self.save_trace_logs("pre-documents-click")
        self.browser.find_element(By.XPATH, '//a[contains(string(), "Dokumenty")]').click()
        self.browser.wait_for_network_inactive()
        sleep(1)
        invoices = self.browser.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
        amount = self.browser.find_element(By.NAME, "value").text
        due_date = None
        for invoice in invoices:
            columns = invoice.find_elements(By.TAG_NAME, 'td')
            value = Amount(columns[7].text) if columns[7].text else Amount(columns[5].text)
            if columns[6].text == "Zapłacony" and float(value) > 0:
                continue
            date = DueDate(columns[4].text).value
            if (due_date is None or date < due_date) and float(value) > 0:
                due_date = date
        return [Payment(amount, due_date if due_date else 'today', self.locations[0], self.name)]
