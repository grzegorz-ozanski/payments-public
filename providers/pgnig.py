"""
    PGNiG (gas supply) provider module.
"""
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from browser import setup_logging
from payments import Amount, Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)

# === PGNiG specific constants - URLs, selectors and texts ===

SERVICE_URL = "https://ebok.pgnig.pl"

USER_INPUT = PageElement(By.NAME, "identificator")
PASSWORD_INPUT = PageElement(By.NAME, "accessPin")

READING_ADDRESS_CLASS = "reading-adress"
INVOICES_MENU_XPATH = '//*[@class="menu-element" and normalize-space()="Faktury"]'

INVOICE_ROW_CLASS = "main-row-container"
INVOICE_COLUMN_CLASS = "columns"
INVOICE_BUTTON_CLASS = "button"


class Pgnig(Provider):
    """PGNiG provider for gas bill retrieval."""

    def __init__(self, *locations: str):
        """Initialize PGNiG provider with input elements and locations."""
        super().__init__(SERVICE_URL, locations, USER_INPUT, PASSWORD_INPUT)

    def _fetch_payments(self) -> list[Payment]:
        """Return list of unpaid invoices from PGNiG eBOK portal."""
        log.info("Getting payments...")
        location = self._get_location(
            self._browser.wait_for_element(By.CLASS_NAME, READING_ADDRESS_CLASS).text
        )

        log.info("Getting invoices menu...")
        invoices_menu = self._browser.find_element(By.XPATH, INVOICES_MENU_XPATH)
        log.info("Opening invoices menu...")
        self._weblogger.trace("pre-invoices-click")
        invoices_menu.click()

        log.debug("Waiting for page load completed...")
        self._browser.wait_for_page_inactive()

        unpaid_invoices = None
        for i in range(10):
            index = 0
            item = None
            try:
                log.info("Getting filtered invoices list...")
                unpaid_invoices = []
                for index, item in enumerate(self._browser.wait_for_elements(By.CLASS_NAME, INVOICE_ROW_CLASS)):
                    if item.find_element(By.CLASS_NAME, INVOICE_BUTTON_CLASS).text == "Zapłać":
                        unpaid_invoices.append(item)
                break
            except StaleElementReferenceException:
                log.warning(f"Stale element encountered during filtering invoices.\n"
                            f"Element index: {index}\n"
                            f"Element details:\n{self._browser.dump_element(item)}")

        log.debug("Creating payments dict...")
        payments_dict = {}
        for invoice in unpaid_invoices:
            log.debug("Iterating over unpaid invoices...")
            columns = invoice.find_elements(By.CLASS_NAME, INVOICE_COLUMN_CLASS)
            log.debug("Adding payment...")
            payments_dict[columns[2].text] = payments_dict.get(columns[2].text, 0) + float(Amount(columns[3].text))

        payments = [Payment(self.name, location, date, amount) for date, amount in payments_dict.items()]
        return payments if payments else [Payment(self.name, location)]
