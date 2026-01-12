"""
    Base module for providers using IOK-based customer service portals (eBOK).

    IOK is a common framework used by utility providers to build online customer portals.
"""
from datetime import date
from logging import Logger

from selenium.webdriver.common.by import By

from browser import Browser, Locator, WebLogger
from payments import Payment
from providers.provider import Provider

# === Shared constants for IOK-based portals ===

USER_INPUT = Locator(By.CSS_SELECTOR, '[aria-labelledby=login]')
PASSWORD_INPUT = Locator(By.CSS_SELECTOR, '[aria-labelledby=haslo]')
LOGOUT_BUTTON = Locator(By.CSS_SELECTOR, 'button.wcag.bg.navTxtColor')

NO_OVERDUE = Locator(By.XPATH, '//span[contains(text(), "Brak zaległości")]')
AMOUNT = Locator(By.CLASS_NAME, 'home-amount')
DUE_DATE = Locator(By.CLASS_NAME, 'home-info')
DEFAULT_TIMEOUT = 1


class IOK(Provider):
    """Base provider for IOK-based portals."""

    def __init__(self, due_day: int, url: str, log: Logger, location: str) -> None:
        """
        :param due_day: Day of month for default due date.
        :param url: Login URL for the service.
        :param log: Logger instance.
        :param location: Single location this provider handles.
        """
        self.log = log
        self.timeout = DEFAULT_TIMEOUT
        today = date.today()
        self.due_date = date(today.year, today.month, due_day)
        super().__init__(url, (location,), USER_INPUT, PASSWORD_INPUT, LOGOUT_BUTTON)

    def _fetch_payments(self, browser: Browser, weblogger: WebLogger) -> list[Payment]:
        """Extract payment info from the page. Return fallback if missing."""
        self.log.info('Getting payments...')
        browser.wait_for_page_inactive()
        no_overdue = browser.wait_for_page_element(NO_OVERDUE, 2)
        if no_overdue:
            return [Payment(self.name, self.locations[0])]
        amount = browser.wait_for_page_element(AMOUNT, self.timeout)
        due_date_element = browser.wait_for_page_element(DUE_DATE, self.timeout)

        if amount is None or due_date_element is None:
            return [Payment(self.name, self.locations[0], self.due_date, amount,
                            comment=f'Timed out waiting for {"amount" if amount is None else "due date"}')]

        due_dates = due_date_element.find_elements(By.TAG_NAME, 'span')
        due_date = due_dates[-1] if due_dates else 'today'

        self.log.debug("Got amount '%s' of location '%s'", amount.text, self.locations[0])
        return [Payment(self.name, self.locations[0], due_date, amount)]
