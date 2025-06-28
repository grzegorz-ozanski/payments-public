"""
    Energa provider module for reading payments via Selenium automation.
"""
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from browser import setup_logging, Browser, WebLogger
from payments import Amount, DueDate, Payment
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
AMOUNT_SELECTOR = '.h1.text.es-text.variant-balance'


class Energa(Provider):
    """
    Provider integration for the Energa electricity platform.
    """

    def __init__(self, *locations: str):
        """
        Initialize the provider with login fields and locations.
        """
        user_input = PageElement(By.ID, "username")
        password_input = PageElement(By.ID, "password")
        super().__init__(SERVICE_URL, locations, user_input, password_input)

    def logout(self, browser: Browser, weblogger: WebLogger) -> None:
        """
        Log out the user from the Energa web portal.
        """
        def click_or_raise(webelement: WebElement | None) -> None:
            """
            Click element if not None, or raise an exception
            :param webelement: WebElement to click or None
            :raises NoSuchElementException if webelement is None
            """
            if not webelement:
                raise NoSuchElementException
            webelement.click()

        if not self.logged_in:
            log.debug(f"Not logged in into service '{self.name}', skipping logout")
            return
        try:
            browser.wait_for_element_disappear(By.CSS_SELECTOR, OVERLAY_SELECTOR)
            click_or_raise(browser.wait_for_element(By.XPATH, '//button[contains(@class, "hover-submenu")]'))
            weblogger.trace("pre-logout-click")
            click_or_raise(browser.wait_for_element(By.XPATH, f'//span[contains(text(), "{LOGOUT_TEXT}")]'))
        except (AttributeError, ElementNotInteractableException, TimeoutError) as e:
            weblogger.error()
            if type(e) is AttributeError:
                if 'move_to requires a WebElement' in str(e):
                    log.debug("Cannot click logout button. Are we even logged in?")
                else:
                    raise
        except NoSuchElementException:
            log.debug("Cannot click logout button. Are we even logged in?")

    def _fetch_payments(self, browser: Browser, weblogger: WebLogger) -> list[Payment]:
        """
        Read and return payment data for all user locations.
        """
        log.info("Getting payments...")
        weblogger.trace("accounts-list")
        locations_list_or_none = browser.wait_for_elements(By.CSS_SELECTOR, ACCOUNTS_LABEL_SELECTOR)
        if not locations_list_or_none:
            button = browser.wait_for_element(By.CSS_SELECTOR, OVERLAY_BUTTON_SELECTOR)
            if button:
                browser.trace_click(button)
                weblogger.trace("accounts-list-after-overlay")
                locations_list_or_none = browser.wait_for_elements(By.CSS_SELECTOR, ACCOUNTS_LABEL_SELECTOR)
            else:
                raise RuntimeError('Locations list is empty and no overlay was found!')
            if not locations_list_or_none:
                raise RuntimeError(
                    f'Locations list is empty even after clicking overlay button "{OVERLAY_BUTTON_SELECTOR}"!')
        locations_list = browser.safe_list(locations_list_or_none)
        log.debug("Identified %d locations" % len(locations_list_or_none))
        payments = []
        for location_id in range(len(locations_list)):
            print(f'...location {location_id + 1} of {len(locations_list)}')
            log.debug("Opening location page")
            weblogger.trace("pre-location-click")
            browser.click_element_with_js(locations_list[location_id])
            # If a 'button.primary' exists, there is probably a message displayed that needs to be dismissed before continuing —
            # unless its text is "Zapłać teraz", which indicates we're already on the target page
            button = browser.wait_for_element(By.CSS_SELECTOR, 'button.button.primary', 1)
            if button and button.text != SKIP_PAYMENT_BUTTON_TEXT:
                browser.click_element_with_js(button)

            location_element = browser.wait_for_element(By.CSS_SELECTOR, LOCATION_NAME_SELECTOR, 30)
            if location_element:
                location = self._get_location(location_element.text)
            else:
                log.error(f"Could not retrieve location #{location_id}!")
                continue
            log.debug("Getting payment")
            weblogger.trace("pre-invoices-click")
            invoices_button = browser.wait_for_element(By.XPATH, f'//a[contains(., "{INVOICES_TAB_TEXT}")]')
            if not invoices_button:
                raise RuntimeError(f"Could not find invoices button for location {location}!")
            browser.click_with_retry(invoices_button, By.XPATH, f'//a[contains(., "{INVOICES_TAB_TEXT}")]')
            invoices = browser.wait_for_element(By.CSS_SELECTOR, f'td[data-headerlabel="{DUE_DATE_LABEL_TEXT}"] span')
            weblogger.trace("duedate-check")
            if invoices:
                due_date = invoices.text
            else:
                due_date = None
            browser.wait_for_element(By.XPATH, f'//a[contains(., "{DASHBOARD_TEXT}")]')
            browser.safe_click(By.XPATH, f'//a[contains(., "{DASHBOARD_TEXT}")]')
            amount_element = browser.wait_for_element(By.CSS_SELECTOR, AMOUNT_SELECTOR)
            if amount_element:
                amount = amount_element.text
            else:
                log.error(f"Could not retrieve amount value for location {location}.")
                amount = Amount.unknown
            if due_date is None:
                if Amount.is_zero(amount):
                    due_date = DueDate.today()
                else:
                    log.error(f"Could not retrieve due date for non-zero payment '{amount}', location '{location}'.")
            payments.append(Payment(self.name, location, due_date, amount))
            log.debug("Moving to the next location")
            browser.wait_for_element(By.XPATH, f'//span[contains(., "{ACCOUNTS_LIST_TEXT}")]/..')
            browser.safe_click(By.XPATH, f'//span[contains(., "{ACCOUNTS_LIST_TEXT}")]/..')
            locations_list = browser.safe_list(browser.wait_for_elements(By.CSS_SELECTOR, ACCOUNTS_LABEL_SELECTOR))

        return payments
