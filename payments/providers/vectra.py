"""
    OPEC (head and hot water) provider module.
"""
from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, Locator
from payments.payments import Payment, DueDate, Amount
from payments.payments.exceptions import PaymentError
from payments.providers.auth_flow import TwoStageLogin
from payments.providers.provider import Provider

log = setup_logging(__name__)

# === Vectra specific constants - URLs, selectors and texts ===

SERVICE_URL = 'https://ebok.vectra.pl'

USER_INPUT = Locator(By.NAME, 'username')
PASSWORD_INPUT = Locator(By.NAME, 'password')

MAIN_DASHBOARD = Locator(By.CSS_SELECTOR, 'div.main-page.dashboard')
INVOICES_BUTTON = Locator(By.XPATH, '//span[normalize-space(.)="Zobacz faktury"]')
INVOICES_LIST = Locator(By.XPATH, '(//table[contains(@class,"vectra-complex-table")])[1]/tbody/tr')
TWO_FACTOR_AUTH_BUTTON = Locator(By.XPATH, '//h3[normalize-space(.)="Wpisz kod weryfikacyjny"]')
TOTAL = Locator(By.XPATH, '//div[contains(@class, "left-column")]//h3')

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
        self.payment_comment = ''
        super().__init__(self.service_url(), locations, USER_INPUT, PASSWORD_INPUT,
                         overlay_buttons=[Locator(By.ID, 'cookiescript_accept')],
                         login_strategy=TwoStageLogin)


    def service_url(self) -> str:
        return f'{super().service_url() or SERVICE_URL}'

    def login(self, browser: Browser, load: bool = True) -> None:
        if load:
            self.load(browser)

        if browser.wait_for_page_element(USER_MENU, 2):
            self.logged_in = True
            return

        super().login(browser, False)
        if browser.wait_for_page_element(TWO_FACTOR_AUTH_BUTTON, 2):
            if browser.options.headless:
                self.payment_comment = '2FA is needed to login to service'
                log.error('%s, aborting', self.payment_comment)
                self.logged_in = False
                return
            else:
                input('2FA is needed to login to service. '
                      'Input 2FA code in the page and press <ENTER> to continue...')

    def logout(self, browser: Browser) -> None:
        """
        Log out the user from Vectra web portal.
        """

        if not self.logged_in:
            log.debug("Not logged in into service '%s', skipping logout", self.name)
            return
        user_menu = browser.wait_for_page_element(USER_MENU)
        if user_menu:
            user_menu.click()
            logout_button = browser.wait_for_page_element(LOGOUT_BUTTON)
            if logout_button:
                logout_button.click()
            else:
                raise PaymentError('Unexpected error while logging out: logout button missing in user menu')
            browser.wait_for_page_element(USER_INPUT)
        else:
            log.debug("Logout error: user menu not found, are we logged in?")

    def _fetch_payments(self, browser: Browser) -> list[Payment]:
        # Verify if we are logged in
        if not browser.wait_for_page_element(MAIN_DASHBOARD):
            return [Payment(self.name,
                            self.locations[0],
                            None,
                            None,
                            self.payment_comment or 'Unexpected timeout waiting for main dashboard')]
        total = Payment(self.name, self.locations[0], None)
        total_amount = browser.wait_for_page_element(TOTAL, 2)
        if total_amount and Amount.is_zero(total_amount.text):
            total.due_date = DueDate('today')
            return [total]
        # Open invoices
        invoices_button = browser.wait_for_page_element(INVOICES_BUTTON, 2)
        if not invoices_button:
            total.comment = 'Timed out waiting for invoices button'
            return [total]
        invoices_button.click()
        # Get unpaid invoices
        unpaid_invoices = browser.wait_for_page_elements(INVOICES_LIST)
        if not unpaid_invoices:
            total.comment = 'Timed out waiting for invoices list to open'
            return [total]
        for invoice in unpaid_invoices:
            columns = invoice.find_elements(By.TAG_NAME, 'td')
            payment = Payment(self.name, self.locations[0], columns[Columns.DueDate], columns[Columns.Amount])
            total.amount += payment.amount
            if payment.due_date < total.due_date:
                total.due_date = payment.due_date
        if total.due_date == DueDate.unknown:
            total.due_date = DueDate('today')
        return [total]
