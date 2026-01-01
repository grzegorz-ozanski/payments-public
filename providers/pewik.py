"""
    PEWiK (water supply) provider module.
"""
from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, PageElement, WebLogger
from payments import Payment
from providers.provider import Provider

log = setup_logging(__name__)

# === PEWiK specific constants - URLs, selectors and texts ===

SERVICE_URL = "https://ebok.pewik.gdynia.pl/login"

USER_INPUT = PageElement(By.ID, "username")
PASSWORD_INPUT = PageElement(By.ID, "password")
LOGOUT_BUTTON = PageElement(By.CLASS_NAME, "btn-wyloguj")

COOKIES_PANEL = PageElement(By.CLASS_NAME, "panel-cookies")
COOKIES_CLOSE = PageElement(By.ID, "cookiesClose")

INVOICES_TAB = PageElement(By.XPATH, '//a[text()="Faktury i salda"]')
BALANCES_TAB = PageElement(By.XPATH, '//a[text()="Salda"]')

LOCATION = PageElement(By.CLASS_NAME, "select2-chosen")
BALANCE_TABLE = PageElement(By.ID, "saldaWplatyWykaz")

LOCATIONS_ARROW = PageElement(By.CLASS_NAME, "select2-arrow")
LOCATION_RESULT = PageElement(By.CLASS_NAME, "select2-result")


# for clarity, keep the first argument to browser.find_elements() even if it's equal to default By.ID
# noinspection PyArgumentEqualDefault
class Pewik(Provider):
    """PEWiK Gdynia provider."""

    def __init__(self, *locations: str):
        """Initialize the provider with given locations."""
        super().__init__(SERVICE_URL, locations, USER_INPUT, PASSWORD_INPUT, LOGOUT_BUTTON)

    def _fetch_payments(self, browser: Browser, weblogger: WebLogger) -> list[Payment]:
        """Extract payments from balances table, switching between locations."""
        payments = []
        next_id = 1

        # TODO Implement WebElementEx
        cookies_panel = browser.wait_for_page_element(COOKIES_PANEL, 1)
        if cookies_panel:
            browser.wait_for_page_element_clickable(COOKIES_PANEL)
            browser.click_element_with_js(cookies_panel.find_element(COOKIES_CLOSE.by, COOKIES_CLOSE.selector))

        browser.trace_click(browser.find_page_element(INVOICES_TAB))
        browser.trace_click(browser.find_page_element(BALANCES_TAB))
        browser.wait_for_page_load_completed()

        while True:
            location = self._get_location(
                # TODO Implement WebElementEx
                browser.find_page_element(LOCATION)
                    .find_elements(By.TAG_NAME, "span")[2].text
            )

            balances = (
                browser.find_page_element(BALANCE_TABLE)
                .find_element(By.TAG_NAME, "tbody")
                .find_elements(By.TAG_NAME, "tr")
            )

            for item in balances:
                columns = item.find_elements(By.TAG_NAME, "td")
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
