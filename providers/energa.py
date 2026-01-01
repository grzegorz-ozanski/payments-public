"""
    Energa provider module for reading payments via Selenium automation.
"""
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, PageElement, WebLogger
from payments import Amount, DueDate, Payment
from providers.provider import Provider

log = setup_logging(__name__)

# === Energa specific constants - URLs, selectors and texts ===

SERVICE_URL = "https://24.energa.pl"


SKIP_PAYMENT_BUTTON_TEXT = "Zapłać teraz"
INVOICES_TAB = PageElement( By.XPATH, f'//a[contains(., "Faktury")]')

DUE_DATE_LABEL_TEXT = "Termin płatności"
DUE_DATE_LABEL = PageElement(By.CSS_SELECTOR, f'td[data-headerlabel="{DUE_DATE_LABEL_TEXT}"] span')
DUE_DATE_LABEL_ALT = PageElement(By.XPATH, f'//span[contains(text(), "{DUE_DATE_LABEL_TEXT}")]/../..')

DASHBOARD = PageElement(By.XPATH, f'//a[contains(., "Pulpit konta")]')
ACCOUNTS_LIST = PageElement(By.XPATH, f'//span[contains(., "LISTA KONT")]/..')

OVERLAY = PageElement(By.CSS_SELECTOR, 'div.popup.center')
ACCOUNTS_LABEL = PageElement(By.CSS_SELECTOR, 'label')
OVERLAY_BUTTON = PageElement(By.CSS_SELECTOR, 'button.button')
LOCATION_NAME = PageElement(By.CSS_SELECTOR, '.text.es-text.variant-body-bold.mlxs.mrm')
AMOUNT = PageElement(By.CSS_SELECTOR, '.h1.text.es-text.variant-balance')
ALL_PAID = PageElement(By.XPATH, '//form[@novalidate]/div/div/p/strong')

USER_MENU = PageElement(By.XPATH, '//button[contains(@class, "hover-submenu")]')
LOGOUT_BUTTON = PageElement(By.XPATH, f'//span[contains(text(), "Wyloguj się")]')
MESSAGE_BOX_CLOSE_BUTTON = PageElement(By.CSS_SELECTOR, 'button.button.primary')

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
        super().__init__(SERVICE_URL, locations, user_input, password_input,
                         overlay_buttons=PageElement(By.ID, 'kc-switch-button'))

    def logout(self, browser: Browser, weblogger: WebLogger) -> None:
        """
        Log out the user from the Energa web portal.
        """

        if not self.logged_in:
            log.debug(f"Not logged in into service '{self.name}', skipping logout")
            return
        try:
            browser.wait_for_page_element_disappear(OVERLAY)
            browser.click_page_element(USER_MENU)
            weblogger.trace("pre-logout-click")
            browser.click_page_element(LOGOUT_BUTTON)
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
        locations_list_or_none = browser.wait_for_page_elements(ACCOUNTS_LABEL)
        if not locations_list_or_none:
            button = browser.wait_for_page_element(OVERLAY_BUTTON)
            if button:
                browser.trace_click(button)
                weblogger.trace("accounts-list-after-overlay")
                locations_list_or_none = browser.wait_for_page_elements(ACCOUNTS_LABEL)
            else:
                raise RuntimeError('Locations list is empty and no overlay was found!')
            if not locations_list_or_none:
                raise RuntimeError(
                    f'Locations list is empty even after clicking overlay button "{OVERLAY_BUTTON}"!')
        locations_list = browser.safe_list(locations_list_or_none)
        log.debug("Identified %d locations" % len(locations_list_or_none))
        payments = []
        for location_id in range(len(locations_list)):
            print(f'...location {location_id + 1} of {len(locations_list)}')
            log.debug("Opening location page")
            weblogger.trace("pre-location-click")
            browser.click_element_using_js(locations_list[location_id])
            # If a 'button.primary' exists, there is probably a message displayed that needs to be dismissed before continuing —
            # unless its text is "Zapłać teraz", which indicates we're already on the target page
            button = browser.wait_for_page_element(MESSAGE_BOX_CLOSE_BUTTON, 1)
            if button and button.text != SKIP_PAYMENT_BUTTON_TEXT:
                browser.click_element_using_js(button)

            location_element = browser.wait_for_page_element(LOCATION_NAME, 30)
            if location_element:
                location = self._get_location(location_element.text)
            else:
                log.error(f"Could not retrieve location #{location_id}!")
                continue
            log.debug("Getting payment")
            weblogger.trace("pre-invoices-click")
            invoices_button = browser.wait_for_page_element(INVOICES_TAB)
            if not invoices_button:
                raise RuntimeError(f"Could not find invoices button for location {location}!")
            browser.click_page_element_with_retry(invoices_button, INVOICES_TAB)
            due_date = None
            # First check if all invoices are already paid
            all_paid = browser.wait_for_page_element(ALL_PAID, 2)
            if all_paid is None:
                # Energa page renders invoices list in two ways
                invoices = browser.wait_for_page_element(DUE_DATE_LABEL)
                weblogger.trace("duedate-check")
                if invoices:
                    due_date = invoices.text
                else:
                    # If the first method of gettign data fails, try the second one
                    invoices_list = browser.wait_for_page_elements(DUE_DATE_LABEL_ALT)
                    if invoices_list:
                        due_date = invoices_list[0].text.split('\n')[1]
            browser.wait_for_page_element(DASHBOARD)
            browser.safe_click_page_element(DASHBOARD)
            amount_element = browser.wait_for_page_element(AMOUNT)
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
            browser.wait_for_page_element(ACCOUNTS_LIST)
            browser.safe_click_page_element(ACCOUNTS_LIST)
            locations_list = browser.safe_list(browser.wait_for_page_elements(ACCOUNTS_LABEL))

        return payments
