"""
    PGNiG (gas supply) provider module.
"""
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, PageElement, WebLogger
from payments import Amount, Payment
from providers.provider import Provider

log = setup_logging(__name__)

# === PGNiG specific constants - URLs, selectors and texts ===

SERVICE_URL = "https://ebok.pgnig.pl"

USER_INPUT = PageElement(By.NAME, "identificator")
PASSWORD_INPUT = PageElement(By.NAME, "accessPin")

READING_ADDRESS = PageElement(By.CLASS_NAME, "reading-adress")
INVOICES_MENU = PageElement(By.XPATH, '//*[@class="menu-element" and normalize-space()="Faktury"]')

INVOICE_ROW = PageElement(By.CLASS_NAME, "main-row-container")
INVOICE_COLUMN = PageElement(By.CLASS_NAME, "columns")
INVOICE_BUTTON = PageElement(By.CLASS_NAME, "button")


class Pgnig(Provider):
    """PGNiG provider for gas bill retrieval."""

    def __init__(self, *locations: str):
        """Initialize the PGNiG provider with input elements and locations."""
        overlays = [PageElement(By.ID, 'CybotCookiebotDialogBodyButtonDecline'),
                    PageElement(By.CLASS_NAME, 'modalCloseButton'),
                    PageElement(By.CSS_SELECTOR, '.button.expanded.invert-colors'),]
        super().__init__(SERVICE_URL, locations, USER_INPUT, PASSWORD_INPUT, overlay_buttons=overlays)

    def _fetch_payments(self, browser: Browser, weblogger: WebLogger) -> list[Payment]:
        """Return the list of unpaid invoices from the PGNiG eBOK portal."""
        log.info("Getting payments...")
        location_element = browser.wait_for_page_element(READING_ADDRESS)
        if location_element:
            location = self._get_location(location_element.text)
        else:
            raise RuntimeError(f"Cannot find location element '{READING_ADDRESS}'!")

        log.info("Getting invoices menu...")
        invoices_menu = browser.wait_for_page_element(INVOICES_MENU)
        log.info("Opening invoices menu...")
        weblogger.trace("pre-invoices-click")
        if not invoices_menu:
            log.error("Cannot open invoices!")
            return [Payment(self.name, location)]

        browser.click_element_with_js(invoices_menu)

        log.debug("Waiting for page load completed...")
        browser.wait_for_page_inactive()

        unpaid_invoices = None
        attempts = 10
        for i in range(attempts):
            index = 0
            item = None
            try:
                log.info("Getting filtered invoices list...")
                unpaid_invoices = []
                elements = browser.wait_for_page_elements(INVOICE_ROW)
                if elements is None:
                    raise RuntimeError("Cannot get invoices list!")
                for index, item in enumerate(browser.safe_list(elements)):
                    # TODO Implement WebElementEx
                    if item.find_element(INVOICE_BUTTON.by, INVOICE_BUTTON.selector).text == "Zapłać":
                        unpaid_invoices.append(item)
                break
            except StaleElementReferenceException:
                log.warning(f"Stale element encountered during filtering invoices.\n"
                            f"Element index: {index}\n"
                            f"Element details:\n{browser.dump_element(item)}")

        log.debug("Creating payments dict...")
        payments_dict: dict[str, float] = {}
        if unpaid_invoices is None:
            raise RuntimeError(f"Failed to collect invoices after {attempts} attempts!")
        for invoice in unpaid_invoices:
            log.debug("Iterating over unpaid invoices...")
            columns = invoice.find_elements(By.CLASS_NAME, INVOICE_COLUMN_CLASS)
            log.debug("Adding payment...")
            payments_dict[columns[2].text] = payments_dict.get(columns[2].text, 0) + float(Amount(columns[3].text))

        payments = [Payment(self.name, location, date, amount) for date, amount in payments_dict.items()]
        return payments if payments else [Payment(self.name, location)]
