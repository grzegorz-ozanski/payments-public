"""
    OPEC (head and hot water) provider module.
"""
from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, Locator, WebLogger
from payments import Amount, Payment
from providers.provider import Provider

log = setup_logging(__name__)

# === OPEC specific constants - URLs, selectors and texts ===

SERVICE_URL = 'https://ebok.opecgdy.com.pl'

USER_INPUT = Locator(By.ID, 'UserName')
PASSWORD_INPUT = Locator(By.ID, 'Password')
AMOUNT = Locator(By.XPATH, '//sh-blok/div[2]/div/div/span')

TABLE_XPATH = 'ancestor::div[contains(@class,"sh-card")]/table[contains(@class,"sh-table")]'
MONTHS_TABLE = Locator(By.XPATH, f'//h2[text()="Historia finansowa"]/{TABLE_XPATH}')
MONTH_TABLE_ROW = Locator(By.CSS_SELECTOR, 'tr.exe')
PAYMENTS_TABLE = Locator(By.XPATH, f'//h2[contains(text(), "Zapisy finansowe w miesiącu")]/{TABLE_XPATH}')
PAYMENTS_TABLE_ROW = Locator(By.XPATH, '//tbody/tr')

class Columns:
    """ Payments list columns"""
    DueDate = Locator(By.CSS_SELECTOR, 'td[data-label="Data płatności"]')
    Amount = Locator(By.CSS_SELECTOR, 'td[data-label="Obciążenia"]')

class TermsOfService:
    """ OPEC2 terms of service popup. """
    HEADER = Locator(By.XPATH, '//h1[normalize-space(.)="Regulamin"]')
    BUTON_OPEN = Locator(By.CSS_SELECTOR, 'button[type=submit]')
    HEADER_CLOSE = Locator(By.TAG_NAME, 'h1')
    BUTTON_CLOSE = Locator(By.TAG_NAME, 'button')

    def __init__(self, browser: Browser) -> None:
        self.browser = browser

    def accept(self) -> None:
        """ Closes the popup"""
        if self.browser.wait_for_page_element(self.HEADER, 2):
            self.browser.find_page_element(self.BUTON_OPEN).click()
            self.browser.wait_for_page_element(self.HEADER_CLOSE, 2)
            self.browser.find_page_element(self.BUTTON_CLOSE).click()

class Opec2(Provider):
    """OPEC provider for hot water and heating."""

    def __init__(self, *locations: str):
        """Initialize OPEC service with given locations."""
        super().__init__(SERVICE_URL, locations, USER_INPUT, PASSWORD_INPUT)

    def _fetch_payments(self, browser: Browser, weblogger: WebLogger) -> list[Payment]:
        TermsOfService(browser).accept()
        amount = browser.wait_for_page_element(AMOUNT, 2).text
        months_table = browser.find_page_element(MONTHS_TABLE)
        if not months_table:
            return [Payment(self.name, self.locations[0], amount=amount)]
        month_entries = len(months_table.find_page_elements(MONTH_TABLE_ROW))
        due_date = ''
        for i in range(month_entries):
            if i > 0:
                months_table = browser.wait_for_page_element(MONTHS_TABLE)
            months = months_table.find_page_elements(MONTH_TABLE_ROW)
            months[i].click()
            payments = browser.wait_for_page_element(PAYMENTS_TABLE, 1)
            if payments:
                matches = [row.find_page_element(Columns.DueDate).text
                           for row in payments.find_page_elements(PAYMENTS_TABLE_ROW)
                           if Amount(row.find_page_element(Columns.Amount)) == Amount(amount)]
                if matches:
                    due_date = matches[0]
                    if len(matches) > 1:
                        log.warning('Multiple matches found for payment due date, first chosen:\n%s', matches)
                    break
            browser.back()
        return [Payment(self.name, self.locations[0], due_date, amount)]
