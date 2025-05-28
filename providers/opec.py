"""
    OPEC (head and hot water) provider module.
"""
from time import sleep

from selenium.webdriver.common.by import By

from browser import setup_logging, Browser
from payments import Amount, DueDate, DueDateT, Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)

# === OPEC specific constants - URLs, selectors and texts ===

SERVICE_URL = "https://ebok.opecgdy.com.pl/home"

USER_INPUT = PageElement(By.ID, "_58_login")
PASSWORD_INPUT = PageElement(By.ID, "_58_password")

PAYMENTS_TAB = '//a[text()="Płatności"]'
DOCUMENTS_TAB = '//a[contains(string(), "Dokumenty")]'

TABLE_BODY = 'tbody'
TABLE_ROW = 'tr'
COLUMN_TAG = 'td'
AMOUNT_FIELD_NAME = 'value'


class Opec(Provider):
    """OPEC provider for hot water and heating."""

    def __init__(self, *locations: str):
        """Initialize OPEC service with given locations."""
        super().__init__(SERVICE_URL, locations, USER_INPUT, PASSWORD_INPUT)

    def _fetch_payments(self, browser: Browser) -> list[Payment]:
        """Click through the UI and return earliest unpaid invoice."""
        self._weblogger.trace("pre-payments-click")
        browser.find_element(By.XPATH, PAYMENTS_TAB).click()
        self._weblogger.trace("pre-documents-click")
        browser.find_element(By.XPATH, DOCUMENTS_TAB).click()
        browser.wait_for_network_inactive()
        sleep(1)

        invoices = browser.find_element(By.TAG_NAME, TABLE_BODY).find_elements(By.TAG_NAME, TABLE_ROW)
        amount = browser.find_element(By.NAME, AMOUNT_FIELD_NAME).text
        due_date: DueDateT | DueDate = ''

        for invoice in invoices:
            columns = invoice.find_elements(By.TAG_NAME, COLUMN_TAG)
            value = Amount(columns[7]) if columns[7].text else Amount(columns[5])
            if columns[6].text == "Zapłacony" and float(value) > 0:
                continue
            date = DueDate(columns[4].text)
            if (not due_date or date < due_date) and float(value) > 0:
                due_date = date

        return [Payment(self.name, self.locations[0], due_date, amount)]
