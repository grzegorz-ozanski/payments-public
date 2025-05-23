from time import sleep

from selenium.webdriver.common.by import By
from browser import setup_logging
from payments import Amount, DueDate, Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)


class Opec(Provider):
    def __init__(self, *locations: str):
        user_input = PageElement(By.ID, "_58_login")
        password_input = PageElement(By.ID, "_58_password")
        url = "https://ebok.opecgdy.com.pl/home"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, locations, user_input, password_input)

    def _read_payments(self) -> list[Payment]:
        self._weblogger.trace("pre-payments-click")
        self._browser.find_element(By.XPATH, '//a[text()="Płatności"]').click()
        self._weblogger.trace("pre-documents-click")
        self._browser.find_element(By.XPATH, '//a[contains(string(), "Dokumenty")]').click()
        self._browser.wait_for_network_inactive()
        sleep(1)
        invoices = self._browser.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
        amount = self._browser.find_element(By.NAME, "value").text
        due_date = ''
        for invoice in invoices:
            columns = invoice.find_elements(By.TAG_NAME, 'td')
            value = Amount(columns[7]) if columns[7].text else Amount(columns[5])
            if columns[6].text == "Zapłacony" and float(value) > 0:
                continue
            date = DueDate(columns[4].text)
            if (not due_date or date < due_date) and float(value) > 0:
                due_date = date
        return [Payment(self.name, self.locations[0], due_date, amount)]
