"""
    OPEC (head and hot water) provider module.
"""
from time import sleep

from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, Locator
from payments import Amount, DueDate, DueDateT, Payment
from providers.provider import Provider

log = setup_logging(__name__)

# === OPEC specific constants - URLs, selectors and texts ===

SERVICE_URL = 'https://stary-ebok.opecgdy.com.pl/web/ebok/home'

USER_INPUT = Locator(By.ID, '_58_login')
PASSWORD_INPUT = Locator(By.ID, '_58_password')

PAYMENTS_TAB = Locator(By.XPATH, '//a[text()="Płatności"]')
DOCUMENTS_TAB = Locator(By.XPATH, '//a[contains(string(), "Dokumenty")]')

TABLE_BODY = Locator(By.TAG_NAME, 'tbody')
TABLE_ROW = Locator(By.TAG_NAME, 'tr')
COLUMN_TAG = 'td'
AMOUNT_FIELD_NAME = 'value'
INVOICE_PAID_TEXT = 'Zapłacony'
INVOICE_UNPAID_TEXT = 'Niezapłacony'

class Columns:
    """ Invoices table columns """
    DueDate = 4
    Amount = 5
    Status = 6
    AmountLeft = 7

class Opec(Provider):
    """OPEC provider for hot water and heating."""

    def __init__(self, *locations: str):
        """Initialize OPEC service with given locations."""
        super().__init__(SERVICE_URL, locations, USER_INPUT, PASSWORD_INPUT)

    def _fetch_payments(self, browser: Browser) -> list[Payment]:
        """Click through the UI and return the earliest unpaid invoice."""
        log.web_trace('pre-payments-click')
        browser.find_page_element(PAYMENTS_TAB).click()
        log.web_trace('pre-documents-click')
        browser.find_page_element(DOCUMENTS_TAB).click()
        browser.wait_for_network_inactive()
        sleep(1)

        invoices = browser.find_page_element(TABLE_BODY).find_elements(TABLE_ROW.type, TABLE_BODY.value)
        amount = 0.0
        due_date: DueDateT | DueDate = ''

        for invoice in invoices:
            columns = invoice.find_elements(By.TAG_NAME, COLUMN_TAG)
            if len(columns) > Columns.Status:
                value = float(Amount(columns[Columns.AmountLeft]) if columns[Columns.AmountLeft].text else Amount(columns[Columns.Amount]))
                if columns[Columns.Status].text == INVOICE_PAID_TEXT and value > 0:
                    continue
                if columns[Columns.Status].text == INVOICE_UNPAID_TEXT and value > 0:
                    amount += value
                date = DueDate(columns[Columns.DueDate].text)
                if (not due_date or date < due_date) and value > 0:
                    due_date = date

        return [Payment(self.name, self.locations[0], due_date, amount)]
