"""
    Energa provider module for reading payments via Selenium automation.
"""
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.common.by import By

from browser import setup_logging
from payments import Payment, DueDate
from .provider import PageElement, Provider

log = setup_logging(__name__)

# === Energa specific constants - URLs, selectors and texts ===

SERVICE_URL = "https://24.energa.pl"

LOGOUT_TEXT = "Wyloguj się"
SKIP_PAYMENT_BUTTON_TEXT = "Zapłać teraz"
INVOICES_TAB_TEXT = "Faktury"
DUE_DATE_LABEL_TEXT = "Termin płatności"
DASHBOARD_TEXT = "Pulpit konta"
ACCOUNTS_LIST_TEXT = "LISTA KONT"

OVERLAY_SELECTOR = 'div.popup.center'
POPUP_SELECTOR = 'div.popup__wrapper'
ACCOUNTS_LABEL_SELECTOR = 'label'
OVERLAY_BUTTON_SELECTOR = 'button.button.secondary'
LOCATION_NAME_SELECTOR = '.text.es-text.variant-body-bold.mlxs.mrm'
AMOUNT_SELECTOR = 'h1.text.es-text.variant-balance'


class Energa(Provider):
    """
    Provider integration for the Energa electricity platform.
    """

    def __init__(self, *locations: str):
        """
        Initialize provider with login fields and locations.
        """
        user_input = PageElement(By.ID, "email_login")
        password_input = PageElement(By.ID, "password")
        super().__init__(SERVICE_URL, locations, user_input, password_input)

    def logout(self) -> None:
        """
        Log out the user from the Energa web portal.
        """
        try:
            self._browser.wait_for_element_disappear(By.CSS_SELECTOR, OVERLAY_SELECTOR)
            self._browser.open_dropdown_menu(By.XPATH, '//button[contains(@class, "hover-submenu")]')
            self._weblogger.trace("pre-logout-click")
            self._browser.find_element(By.XPATH, f'//span[contains(text(), "{LOGOUT_TEXT}")]').click()
        except (AttributeError, ElementNotInteractableException) as e:
            self._weblogger.error()
            if type(e) is AttributeError:
                if 'move_to requires a WebElement' in str(e):
                    log.debug("Cannot click logout button. Are we even logged in?")
                else:
                    raise
        except NoSuchElementException:
            log.debug("Cannot click logout button. Are we even logged in?")

    def _fetch_payments(self) -> list[Payment]:
        """
        Read and return payment data for all user locations.
        """
        log.info("Getting payments...")
        self._browser.wait_for_page_load_completed()
        self._weblogger.trace("accounts-list")
        locations_list = self._browser.wait_for_elements(By.CSS_SELECTOR, ACCOUNTS_LABEL_SELECTOR)
        if not locations_list:
            button = self._browser.wait_for_element(By.CSS_SELECTOR, OVERLAY_BUTTON_SELECTOR)
            if button:
                self._browser.trace_click(button)
                self._browser.wait_for_page_load_completed()
                self._weblogger.trace("accounts-list-after-overlay")
                locations_list = self._browser.wait_for_elements(By.CSS_SELECTOR, ACCOUNTS_LABEL_SELECTOR)
            else:
                raise RuntimeError('Locations list is empty and no overlay was found!')
        log.debug("Identified %d locations" % len(locations_list))
        payments = []
        for location_id in range(len(locations_list)):
            print(f'...location {location_id + 1} of {len(locations_list)}')
            log.debug("Opening location page")
            self._browser.wait_for_element_disappear(By.CSS_SELECTOR, POPUP_SELECTOR)
            self._weblogger.trace("pre-location-click")
            self._browser.click_element_with_js(locations_list[location_id])
            # If a 'button.primary' exists, there is probably a message displayed that needs to be dismissed before continuing —
            # unless its text is "Zapłać teraz", which indicates we're already on the target page
            button = self._browser.wait_for_element(By.CSS_SELECTOR, 'button.button.primary', 1)
            if button and button.text != SKIP_PAYMENT_BUTTON_TEXT:
                self._browser.click_element_with_js(button)

            location = self._get_location(
                self._browser.wait_for_element(By.CSS_SELECTOR, LOCATION_NAME_SELECTOR, 30).text)
            log.debug("Getting payment")
            self._browser.wait_for_element_disappear(By.CSS_SELECTOR, POPUP_SELECTOR)
            self._weblogger.trace("pre-invoices-click")
            self._browser.find_element(By.XPATH, f'//a[contains(text(), "{INVOICES_TAB_TEXT}")]').click()
            self._browser.wait_for_page_inactive()
            self._browser.wait_for_element_disappear(By.CSS_SELECTOR, POPUP_SELECTOR)
            invoices = self._browser.wait_for_elements(
                By.XPATH,
                f'//span[contains(text(), "{DUE_DATE_LABEL_TEXT}")]/../..', 1)
            self._weblogger.trace("duedate-check")
            if invoices:
                due_date = invoices[0].text.split('\n')[1]
            else:
                due_date = DueDate.today
            self._browser.safe_click(By.XPATH, f'//a[contains(text(), "{DASHBOARD_TEXT}")]')
            amount = self._browser.wait_for_element(By.CSS_SELECTOR, AMOUNT_SELECTOR).text
            payments.append(Payment(self.name, location, due_date, amount))
            log.debug("Moving to the next location")
            self._browser.safe_click(By.XPATH, f'//span[contains(text(), "{ACCOUNTS_LIST_TEXT}")]/..')
            locations_list = self._browser.wait_for_elements(By.CSS_SELECTOR, ACCOUNTS_LABEL_SELECTOR)

        return payments
