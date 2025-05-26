"""
    Base module for providers using IOK-based customer service portals (eBOK).

    IOK is a common framework used by utility providers to build online customer portals.
"""

from datetime import date

from selenium.webdriver.common.by import By

from payments import Payment
from .provider import PageElement, Provider

# === Shared constants for IOK-based portals ===

USER_INPUT = PageElement(By.CSS_SELECTOR, "[aria-labelledby=login]")
PASSWORD_INPUT = PageElement(By.CSS_SELECTOR, "[aria-labelledby=haslo]")
LOGOUT_BUTTON = PageElement(By.CSS_SELECTOR, "button.wcag.bg.navTxtColor")

AMOUNT_CLASS = 'home-amount'
DUE_DATE_CLASS = 'home-info'
DEFAULT_TIMEOUT = 0.1


class IOK(Provider):
    """Base provider for IOK-based portals."""

    def __init__(self, due_day, url, name, log, location: str):
        """
        :param due_day: Day of month for default due date.
        :param url: Login URL for the service.
        :param name: Provider name.
        :param log: Logger instance.
        :param location: Single location this provider handles.
        """
        self.log = log
        self.timeout = DEFAULT_TIMEOUT
        today = date.today()
        self.due_date = date(today.year, today.month, due_day)
        super().__init__(url, name, (location,), USER_INPUT, PASSWORD_INPUT, LOGOUT_BUTTON)

    def _fetch_payments(self) -> list[Payment]:
        """Extract payment info from the page. Return fallback if missing."""
        self.log.info("Getting payments...")
        self._browser.wait_for_page_inactive()
        amount = self._browser.wait_for_element(By.CLASS_NAME, AMOUNT_CLASS, self.timeout)
        due_date = self._browser.wait_for_element(By.CLASS_NAME, DUE_DATE_CLASS, self.timeout)

        if amount is None or due_date is None:
            return [Payment(self.name, self.locations[0], self.due_date)]

        due_date = due_date.find_elements(By.TAG_NAME, 'span')
        due_date = due_date[-1] if due_date else 'today'

        self.log.debug(f"Got amount '{amount.text}' of location '{self.locations[0]}'")
        return [Payment(self.name, self.locations[0], due_date, amount)]
