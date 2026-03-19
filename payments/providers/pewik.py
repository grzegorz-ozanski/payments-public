"""
    PEWiK (water supply) provider module.
"""
from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, Locator
from payments.payments import Payment
from payments.providers.provider import Provider

log = setup_logging(__name__)

# === PEWiK specific constants - URLs, selectors and texts ===

BASE_URL = 'https://ebok.pewik.gdynia.pl'
SERVICE_URL = 'login'

USER_INPUT = Locator(By.ID, 'username')
PASSWORD_INPUT = Locator(By.ID, 'password')
LOGOUT_BUTTON = Locator(By.CLASS_NAME, 'btn-wyloguj')

COOKIES_PANEL = Locator(By.CLASS_NAME, 'panel-cookies')
COOKIES_CLOSE = Locator(By.ID, 'cookiesClose')

INVOICES_TAB = Locator(By.XPATH, '//a[text()="Faktury i salda"]')
BALANCES_TAB = Locator(By.XPATH, '//a[text()="Salda"]')

LOCATION = Locator(By.CLASS_NAME, 'select2-chosen')
LOCATION_TEXT = Locator(By.TAG_NAME, 'span')

LOCATIONS_ARROW = Locator(By.CLASS_NAME, 'select2-arrow')
LOCATION_RESULT = Locator(By.CLASS_NAME, 'select2-result')


class BalanceTable:
    """ Balance table locators """
    ID = Locator(By.ID, 'saldaWplatyWykaz')
    BODY = Locator(By.TAG_NAME, 'tbody')
    ROW = Locator(By.TAG_NAME, 'tr')
    COLUMN = Locator(By.TAG_NAME, 'td')

    # for clarity, keep the first argument to browser.find_elements() even if it's equal to default By.ID


# noinspection PyArgumentEqualDefault
class Pewik(Provider):
    """PEWiK Gdynia provider."""

    def __init__(self, *locations: str):
        """Initialize the provider with given locations."""
        super().__init__(self.get_url(), locations, USER_INPUT, PASSWORD_INPUT, LOGOUT_BUTTON)

    def get_url(self) -> str:
        return self.service_url(BASE_URL, SERVICE_URL)

    def _fetch_payments(self, browser: Browser) -> list[Payment]:
        """Extract payments from balances table, switching between locations."""
        payments = []
        next_id = 1

        cookies_panel = browser.wait_for_page_element(COOKIES_PANEL, 1)
        if cookies_panel:
            browser.wait_for_page_element_clickable(COOKIES_PANEL)
            browser.click_element_using_js(cookies_panel.find_page_element(COOKIES_CLOSE))

        browser.trace_click(browser.find_page_element(INVOICES_TAB))
        browser.trace_click(browser.find_page_element(BALANCES_TAB))
        browser.wait_for_page_load_completed()

        while True:
            location = self._get_location(
                browser.find_page_element(LOCATION).find_page_elements(LOCATION_TEXT)[2].text
            )

            balances = (
                browser.find_page_element(BalanceTable.ID)
                .find_page_element(BalanceTable.BODY)
                .find_page_elements(BalanceTable.ROW)
            )

            for item in balances:
                columns = item.find_page_elements(BalanceTable.COLUMN)
                if len(columns) > 1:
                    payments.append(Payment(self.name, location, columns[3], columns[5]))
                else:
                    payments.append(Payment(self.name, location))

            locations_arrow = browser.find_page_element(LOCATIONS_ARROW)
            browser.trace_click(locations_arrow)
            locations = browser.find_page_elements(LOCATION_RESULT)

            if next_id < len(locations):
                browser.trace_click(locations[next_id])
                next_id += 1
            else:
                break

        return payments

    def _is_logged_in(self, browser: Browser) -> bool:
        return False
