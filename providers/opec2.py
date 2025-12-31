"""
    OPEC (head and hot water) provider module.
"""
from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, PageElement, WebLogger
from payments import Payment
from providers.provider import Provider

log = setup_logging(__name__)

# === OPEC specific constants - URLs, selectors and texts ===

SERVICE_URL = 'https://ebok.opecgdy.com.pl'

USER_INPUT = PageElement(By.ID, 'UserName')
PASSWORD_INPUT = PageElement(By.ID, 'Password')
AMOUNT = PageElement(By.CSS_SELECTOR, 'span.shf-s30.shf-w5.shf-csec')

class TermsOfService:
    """ OPEC2 terms of service popup. """
    HEADER = PageElement(By.XPATH, "//h1[normalize-space(.)='Regulamin']")
    BUTON_OPEN = PageElement(By.CSS_SELECTOR, "button[type=submit]")
    HEADER_CLOSE = PageElement(By.TAG_NAME, 'h1')
    BUTTON_CLOSE = PageElement(By.TAG_NAME, 'button')

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
        return [Payment(self.name, self.locations[0],
                        amount=browser.wait_for_page_element(AMOUNT, 2))]
