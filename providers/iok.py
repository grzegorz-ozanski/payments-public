"""
    Base module for providers using IOK-based customer service portals (eBOK).

    IOK is a common framework used by utility providers to build online customer portals.
"""
from datetime import date

from selenium.webdriver.common.by import By

from payments import Payment
from .provider import PageElement, Provider


class IOK(Provider):
    """
    Represents the IOK provider responsible for handling payment-related operations.

    This class interacts with the user login, password inputs, and logout functionality tied to the
    specific provider's web interface. It also provides methods to read payment details such as
    amount and due date from the interface.

    :ivar due_date: Represents the calculated due date for payments based on the provided due day.
    :type due_date: datetime.date
    :ivar log: Logger instance used for logging messages and debugging information.
    :type log: Any
    :ivar timeout: Timeout duration in seconds for waiting for elements to load on the page.
    :type timeout: float
    """
    def __init__(self, due_day, url, name, log, location: str):
        """
        Initialize the class with the provided parameters.

        The class constructor requires specific parameters to set up the necessary
        attributes of the object. These parameters configure the due date, logging,
        location details, and setup connections with the backend service.

        :param due_day: The day of the current month when the task is due. Must be a valid
            day of the month.
        :param url: The URL that the system will interact with for data operations.
        :param name: Service object responsible for managing secure key storage.
        :param log: Logger instance used for logging system events and messages.
        :param location: The geographic or operational location associated with the object.
        """
        user_input = PageElement(By.CSS_SELECTOR, "[aria-labelledby=login]")
        password_input = PageElement(By.CSS_SELECTOR, "[aria-labelledby=haslo]")
        logout_button = PageElement(By.CSS_SELECTOR, "button.wcag.bg.navTxtColor")
        self.log = log
        self.timeout = 0.1
        today = date.today()
        self.due_date = date(today.year, today.month, due_day)
        super().__init__(url, name, (location,), user_input, password_input, logout_button)

    def _fetch_payments(self) -> list[Payment]:
        """
        Reads payment details by interacting with the browser interface. This method uses
        the configured browser instance to retrieve the visible payment amount and due
        date displayed on the webpage. If elements corresponding to the payment details
        cannot be located, it defaults to creating a `Payment` with placeholder
        information.

        :raises TimeoutException: If the browser fails to find required elements within
            the specified timeout.
        :raises WebDriverException: If there is an issue with the browser interaction.
        :rtype: list[Payment]
        :return: A list containing one `Payment` object. The object includes the
            retrieved or default values for the name, location, due date, and amount.
        """
        self.log.info("Getting payments...")
        self._browser.wait_for_page_inactive()
        amount = self._browser.wait_for_element(By.CLASS_NAME, 'home-amount', self.timeout)
        due_date = self._browser.wait_for_element(By.CLASS_NAME, 'home-info', self.timeout)
        if amount is None or due_date is None:
            return [Payment(self.name, self.locations[0], self.due_date)]
        due_date = due_date.find_elements(By.TAG_NAME, 'span')
        due_date = due_date[-1] if due_date else 'today'
        self.log.debug(f"Got amount '{amount.text}' of location '{self.locations[0]}'")
        return [Payment(self.name, self.locations[0], due_date, amount)]
