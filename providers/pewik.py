"""
    PEWiK (water supply) provider module.
"""
from selenium.webdriver.common.by import By

from browser import setup_logging
from payments import Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)

# === PEWiK specific constants - URLs, selectors and texts ===

SERVICE_URL = "https://ebok.pewik.gdynia.pl/login"

USER_INPUT = PageElement(By.ID, "username")
PASSWORD_INPUT = PageElement(By.ID, "password")
LOGOUT_BUTTON = PageElement(By.CLASS_NAME, "btn-wyloguj")

COOKIES_PANEL_CLASS = "panel-cookies"
COOKIES_CLOSE_ID = "cookiesClose"

INVOICES_TAB = '//a[text()="Faktury i salda"]'
BALANCES_TAB = '//a[text()="Salda"]'

LOCATION_CLASS = "select2-chosen"
BALANCE_TABLE_ID = "saldaWplatyWykaz"

LOCATIONS_ARROW_CLASS = "select2-arrow"
LOCATION_RESULT_CLASS = "select2-result"


# noinspection PyArgumentEqualDefault
class Pewik(Provider):
    """PEWiK Gdynia provider."""

    def __init__(self, *locations: str):
        """Initialize provider with given locations."""
        super().__init__(SERVICE_URL, locations, USER_INPUT, PASSWORD_INPUT, LOGOUT_BUTTON)

    def _fetch_payments(self) -> list[Payment]:
        """Extract payments from balances table, switching between locations."""
        payments = []
        next_id = 1

        cookies_panel = self._browser.find_element(By.CLASS_NAME, COOKIES_PANEL_CLASS)
        if cookies_panel:
            self._browser.wait_for_element_clickable(By.CLASS_NAME, COOKIES_PANEL_CLASS)
            self._browser.click_element_with_js(cookies_panel.find_element(value=COOKIES_CLOSE_ID))

        self._browser.trace_click(self._browser.find_element(By.XPATH, INVOICES_TAB))
        self._browser.trace_click(self._browser.find_element(By.XPATH, BALANCES_TAB))
        self._browser.wait_for_page_load_completed()

        while True:
            location = self._get_location(
                self._browser.find_element(By.CLASS_NAME, LOCATION_CLASS)
                    .find_elements(By.TAG_NAME, "span")[2].text
            )

            balances = (
                self._browser.find_element(By.ID, BALANCE_TABLE_ID)
                .find_element(By.TAG_NAME, "tbody")
                .find_elements(By.TAG_NAME, "tr")
            )

            for item in balances:
                columns = item.find_elements(By.TAG_NAME, "td")
                if len(columns) > 1:
                    payments.append(Payment(self.name, location, columns[3], columns[5]))
                else:
                    payments.append(Payment(self.name, location))

            locations_arrow = self._browser.find_element(By.CLASS_NAME, LOCATIONS_ARROW_CLASS)
            self._browser.trace_click(locations_arrow)
            locations = self._browser.find_elements(By.CLASS_NAME, LOCATION_RESULT_CLASS)

            if next_id < len(locations):
                self._browser.trace_click(locations[next_id])
                next_id += 1
            else:
                break

        return payments
