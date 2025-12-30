"""
    OPEC (head and hot water) provider module.
"""
from time import sleep

from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, WebLogger
from payments import Amount, DueDate, DueDateT, Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)

# === OPEC specific constants - URLs, selectors and texts ===

SERVICE_URL = 'https://ebok.opecgdy.com.pl'

USER_INPUT = PageElement(By.ID, 'UserName')
PASSWORD_INPUT = PageElement(By.ID, 'Password')
AMOUNT = PageElement(By.CSS_SELECTOR, 'span.shf-s30.shf-w5.shf-csec')

TERMS_OF_SERVICE_TEXT = "Regulamin"

def _accept_terms_of_service(browser: Browser, weblogger: WebLogger):
    if browser.wait_for_element(By.XPATH, f"//h1[normalize-space(.)='{TERMS_OF_SERVICE_TEXT}']", 2):
        browser.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        browser.wait_for_element(By.TAG_NAME, 'h1', 2)
        browser.find_element(By.TAG_NAME, 'button').click()


class Opec2(Provider):
    """OPEC provider for hot water and heating."""

    def __init__(self, *locations: str):
        """Initialize OPEC service with given locations."""
        super().__init__(SERVICE_URL, locations, USER_INPUT, PASSWORD_INPUT)

    def _fetch_payments(self, browser: Browser, weblogger: WebLogger) -> list[Payment]:
        _accept_terms_of_service(browser, weblogger)
        return [Payment(self.name, self.locations[0],
                        amount=browser.wait_for_element(AMOUNT.by, AMOUNT.selector, 2))]
