"""
    OPEC (head and hot water) provider module.
"""
from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, Locator, WebLogger
from payments import Payment
from providers.login.two_stage import TwoStageLogin
from providers.provider import Provider

log = setup_logging(__name__)

# === Vectra specific constants - URLs, selectors and texts ===

SERVICE_URL = 'https://ebok.vectra.pl'

USER_INPUT = Locator(By.NAME, 'username')
PASSWORD_INPUT = Locator(By.NAME, 'password')

INVOICES_BUTTON = Locator(By.XPATH, '//span[normalize-space(.)="Zobacz faktury"]')
INVOICES_LIST = Locator(By.XPATH, '(//table[contains(@class,"vectra-complex-table")])[1]/tbody/tr')

USER_MENU = Locator(By.CSS_SELECTOR, 'span.ico-avatar')
LOGOUT_BUTTON = Locator(By.XPATH, '//span[normalize-space(.)="Wyloguj się"]')

class Columns:
    """ Invoice list columns"""
    DueDate = 5
    Amount = 4


class Vectra(Provider):
    """OPEC provider for hot water and heating."""

    def __init__(self, *locations: str):
        """Initialize OPEC service with given locations."""
        super().__init__(SERVICE_URL, locations, USER_INPUT, PASSWORD_INPUT,
                         overlay_buttons=Locator(By.ID, 'cookiescript_accept'),
                         login_strategy=TwoStageLogin)

    def login(self, browser: Browser, weblogger: WebLogger, load: bool = True) -> None:
        if load:
            self.load(browser)

        if browser.wait_for_page_element(USER_MENU, 2):
            self.logged_in = True
            return

        super().login(browser, weblogger, False)

    def logout(self, browser: Browser, weblogger: WebLogger) -> None:
        """
        Log out the user from Vectra web portal.
        """

        if not self.logged_in:
            log.debug("Not logged in into service '%s', skipping logout", self.name)
            return
        user_menu = browser.wait_for_page_element(USER_MENU)
        if user_menu:
            user_menu.click()
            browser.wait_for_page_element(LOGOUT_BUTTON).click()
            browser.wait_for_page_element(USER_INPUT)
        else:
            log.debug("Logout error: user menu not found, are we logged in into service '%s?'", self.name)

    def _fetch_payments(self, browser: Browser, weblogger: WebLogger) -> list[Payment]:
        total = Payment(self.name, self.locations[0])
        # Open invoices
        invoices_button = browser.wait_for_page_element(INVOICES_BUTTON, 2)
        if invoices_button is None:
            return [total]
        invoices_button.click()
        # Get unpaid invoices
        unpaid_invoices = browser.wait_for_page_elements(INVOICES_LIST)
        for invoice in unpaid_invoices:
            columns = invoice.find_elements(By.TAG_NAME, 'td')
            payment = Payment(self.name, self.locations[0], columns[Columns.DueDate], columns[Columns.Amount])
            total.amount += payment.amount
            if payment.due_date < total.due_date:
                total.due_date = payment.due_date
        return [total]
