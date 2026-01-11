"""
    PGNiG (gas supply) provider module.
"""
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, Locator, WebLogger
from payments import Amount, Payment
from providers.provider import Provider

log = setup_logging(__name__)

# === PGNiG specific constants - URLs, selectors and texts ===

SERVICE_URL = 'https://ebok.pgnig.pl'

USER_INPUT = Locator(By.NAME, 'identificator')
PASSWORD_INPUT = Locator(By.NAME, 'accessPin')

READING_ADDRESS = Locator(By.CLASS_NAME, 'reading-adress')
INVOICES_MENU = Locator(By.XPATH, '//*[@class="menu-element" and normalize-space()="Faktury"]')

INVOICE_ROW = Locator(By.CLASS_NAME, 'main-row-container')
INVOICE_COLUMN = Locator(By.CLASS_NAME, 'columns')
INVOICE_BUTTON = Locator(By.CLASS_NAME, 'button')
INVOICE_PAY_CAPTION = 'Zapłać'


class Pgnig(Provider):
    """PGNiG provider for gas bill retrieval."""

    def __init__(self, *locations: str):
        """Initialize the PGNiG provider with input elements and locations."""
        overlays = [Locator(By.ID, 'CybotCookiebotDialogBodyButtonDecline'),
                    Locator(By.CLASS_NAME, 'modalCloseButton'),
                    Locator(By.CSS_SELECTOR, '.button.expanded.invert-colors'), ]
        super().__init__(SERVICE_URL, locations, USER_INPUT, PASSWORD_INPUT, overlay_buttons=overlays)

    def _fetch_payments(self, browser: Browser, weblogger: WebLogger) -> list[Payment]:
        """Return the list of unpaid invoices from the PGNiG eBOK portal."""
        log.info('Getting payments...')
        location_element = browser.wait_for_page_element(READING_ADDRESS)
        if location_element:
            location = self._get_location(location_element.text)
        else:
            raise RuntimeError(f"Cannot find location element '{READING_ADDRESS}'!")

        log.info('Getting invoices menu...')
        invoices_menu = browser.wait_for_page_element(INVOICES_MENU)
        log.info('Opening invoices menu...')
        weblogger.trace('pre-invoices-click')
        if not invoices_menu:
            message = 'Cannot open invoices'
            log.error('%s!', message)
            return [Payment(self.name, location, comment=message)]

        browser.click_element_using_js(invoices_menu)

        log.debug('Waiting for page load completed...')
        browser.wait_for_page_inactive()

        unpaid_invoices = None
        attempts = 10
        for i in range(attempts):
            index = 0
            item = None
            try:
                log.info('Getting filtered invoices list...')
                unpaid_invoices = []
                elements = browser.wait_for_page_elements(INVOICE_ROW)
                if elements is None:
                    raise RuntimeError('Cannot get invoices list!')
                for index, item in enumerate(elements):
                    if item.find_page_element(INVOICE_BUTTON).text == INVOICE_PAY_CAPTION:
                        unpaid_invoices.append(item)
                break
            except StaleElementReferenceException:
                log.warning('Stale element encountered during filtering invoices.\n'
                            'Element index: %s\n'
                            'Element details:\n%s',
                            index, browser.dump_element(item))

        log.debug('Creating payments dict...')
        payments_dict: dict[str, float] = {}
        if unpaid_invoices is None:
            raise RuntimeError(f'Failed to collect invoices after {attempts} attempts!')
        for invoice in unpaid_invoices:
            log.debug('Iterating over unpaid invoices...')
            columns = invoice.find_page_elements(INVOICE_COLUMN)
            log.debug('Adding payment...')
            payments_dict[columns[2].text] = payments_dict.get(columns[2].text, 0) + float(Amount(columns[3].text))

        payments = [Payment(self.name, location, date, amount) for date, amount in payments_dict.items()]
        return payments if payments else [Payment(self.name, location, comment='Failed to process unpaid invoices')]
