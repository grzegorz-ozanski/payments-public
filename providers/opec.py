from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

import parsers
from browser import setup_logging
from locations import Location
from payments import Payment
from .provider import AuthElement, Provider

log = setup_logging(__name__)


def _get_invoice_value(columns: list[WebElement]):
    if columns[7].text:
        return parsers.parse_amount(columns[7], '.')
    return parsers.parse_amount(columns[5], '.')


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
        amount = parsers.parse_amount(self.browser.find_element(By.NAME, "value"))
        due_date = None
        for invoice in invoices:
            columns = invoice.find_elements(By.TAG_NAME, 'td')
            value = _get_invoice_value(columns)
            if columns[6].text == "Zapłacony" and value > 0:
                continue
            date = parsers.parse_date(columns[4])
            if due_date is None or (date < due_date and value > 0):
                due_date = date
        return [Payment(amount, due_date, self.locations[0], self.name)]
