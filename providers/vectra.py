"""
    OPEC (head and hot water) provider module.
"""
from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, PageElement, WebLogger
from payments import Payment
from providers.login.two_stage import TwoStageLogin
from providers.provider import Provider

log = setup_logging(__name__)

# === Vectra specific constants - URLs, selectors and texts ===

SERVICE_URL = 'https://ebok.vectra.pl'

USER_INPUT = PageElement(By.ID, 'UserName')
PASSWORD_INPUT = PageElement(By.ID, 'Password')
AMOUNT = PageElement(By.CSS_SELECTOR, 'span.shf-s30.shf-w5.shf-csec')

TERMS_OF_SERVICE_TEXT = "Regulamin"

class Vectra(Provider):
    """OPEC provider for hot water and heating."""

    def __init__(self, *locations: str):
        """Initialize OPEC service with given locations."""
        super().__init__(SERVICE_URL, locations, USER_INPUT, PASSWORD_INPUT, login_strategy=TwoStageLogin)

    def _fetch_payments(self, browser: Browser, weblogger: WebLogger) -> list[Payment]:
        return [Payment(self.name, self.locations[0],
                        amount=browser.wait_for_element(AMOUNT.by, AMOUNT.selector, 2))]
