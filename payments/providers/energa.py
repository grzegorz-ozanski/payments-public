"""
    Energa provider module for reading payments via Selenium automation.
"""
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By

from browser import setup_logging, Browser, Locator
from payments.payments import Amount, DueDate, Payment
from payments.providers.provider import Provider, FetchError
from payments.console import print_stage

log = setup_logging(__name__)

# === Energa specific constants - URLs, selectors and texts ===

SERVICE_URL = 'https://24.energa.pl'


SKIP_PAYMENT_BUTTON_TEXT = 'Zapłać teraz'
INVOICES_TAB = Locator(By.XPATH, '//a[contains(., "Faktury")]')

DUE_DATE_LABEL_TEXT = 'Termin płatności'
DUE_DATE_LABEL = Locator(By.CSS_SELECTOR, f'td[data-headerlabel="{DUE_DATE_LABEL_TEXT}"] span')
DUE_DATE_LABEL_ALT = Locator(By.XPATH, f'//span[contains(text(), "{DUE_DATE_LABEL_TEXT}")]/../..')

DASHBOARD = Locator(By.XPATH, '//a[contains(., "Pulpit konta")]')
ACCOUNTS_LIST = Locator(By.XPATH, '//span[contains(., "LISTA KONT")]/..')

OVERLAY = Locator(By.CSS_SELECTOR, 'div.popup.center')
ACCOUNTS_LABEL = Locator(By.CSS_SELECTOR, 'label')
OVERLAY_BUTTON = Locator(By.CSS_SELECTOR, 'button.button')
LOCATION_NAME = Locator(By.CSS_SELECTOR, '.text.es-text.variant-body-bold.mlxs.mrm')
AMOUNT = Locator(By.CSS_SELECTOR, '.h1.text.es-text.variant-balance')
ALL_PAID = Locator(By.XPATH, '//form[@novalidate]/div/div/p/strong')

USER_MENU = Locator(By.XPATH, '//button[contains(@class, "hover-submenu")]')
LOGOUT_BUTTON = Locator(By.XPATH, '//span[contains(text(), "Wyloguj się")]')
MESSAGE_BOX_CLOSE_BUTTON = Locator(By.CSS_SELECTOR, 'button.button.primary')
CLOSE_ACCESSIBILITY_MODAL = Locator(By.CSS_SELECTOR, "button[aria-label='Zamknij modal']")

MAINTENANCE_PATTERN = 'aktuali'

DUE_DATE_TIMEOUT = 30


def _close_accesibility_modal(browser: Browser) -> None:
    buttons = browser.find_page_elements(CLOSE_ACCESSIBILITY_MODAL)
    if buttons:
        buttons[0].click()


class Energa(Provider):
    """
    Provider integration for the Energa electricity platform.
    """

    def __init__(self, *locations: str):
        """
        Initialize the provider with login fields and locations.
        """
        user_input = Locator(By.ID, 'username')
        password_input = Locator(By.ID, 'password')
        super().__init__(self.service_url(), locations, user_input, password_input,
                         overlay_buttons=[Locator(By.ID, 'CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll'),
                                          Locator(By.ID, 'kc-switch-button')])
        self.under_maintenance = False
        
    def service_url(self) -> str:
        return f'{super().service_url() or SERVICE_URL}'

    def login(self, browser: Browser, load: bool = True) -> None:
        try:
            super().login(browser, load)
        except Exception as _:
            # If page title contains maintenance string, assume that login raised exception because of page maintenace
            if MAINTENANCE_PATTERN in browser.title.lower():
                self.under_maintenance = True
                return
            raise

    def logout(self, browser: Browser) -> None:
        """
        Log out the user from the Energa web portal.
        """

        if not self.logged_in:
            log.debug("Not logged in into service '%s', skipping logout", self.name)
            return
        try:
            browser.wait_for_page_element_disappear(OVERLAY)
            browser.click_page_element(USER_MENU)
            log.web_trace('pre-logout-click')
            browser.click_page_element(LOGOUT_BUTTON)
        except (AttributeError, ElementNotInteractableException, TimeoutError) as e:
            log.web_error()
            if type(e) is AttributeError:
                if 'move_to requires a WebElement' in str(e):
                    log.debug('Cannot click logout button. Are we even logged in?')
                else:
                    raise
        except NoSuchElementException:
            log.debug('Cannot click logout button. Are we even logged in?')

    def _is_logged_in(self, browser: Browser) -> bool:
        if browser.wait_for_page_element(USER_MENU, 2):
            self.logged_in = True
            return True
        return False

    def _fetch_payments(self, browser: Browser) -> list[Payment]:
        """
        Read and return payment data for all user locations.
        """
        log.info('Getting payments...')
        if self.under_maintenance:
            return [Payment(self.name, location, None, None, 'Page under maintenance')
                    for location in self.locations]
        log.web_trace('accounts-list')
        locations_list_or_none = browser.wait_for_page_elements(ACCOUNTS_LABEL)
        if not locations_list_or_none:
            button = browser.wait_for_page_element(OVERLAY_BUTTON)
            if button:
                browser.trace_click(button)
                log.web_trace('accounts-list-after-overlay')
                _close_accesibility_modal(browser)
                locations_list_or_none = browser.wait_for_page_elements(ACCOUNTS_LABEL)
            else:
                raise FetchError('Locations list is empty and no overlay was found!')
            if not locations_list_or_none:
                raise FetchError(
                    f'Locations list is empty even after clicking overlay button "{OVERLAY_BUTTON}"!')
        locations_list = locations_list_or_none
        log.debug('Identified %d locations' % len(locations_list))
        payments = []
        for location_id in range(len(locations_list)):
            print_stage('location', location_id, len(locations_list))
            log.debug('Opening location page')
            log.web_trace(f'location-{location_id}-pre-location-click')
            browser.click_element_using_js(locations_list[location_id])
            # If a 'button.primary' exists, there is probably a message displayed
            # that needs to be dismissed before continuing —  unless its text is "Zapłać teraz",
            # which indicates we're already on the target page
            while True:
                try:
                    button = browser.wait_for_page_element(MESSAGE_BOX_CLOSE_BUTTON, 1)
                    if button and button.text != SKIP_PAYMENT_BUTTON_TEXT:
                        browser.click_element_using_js(button)
                    break
                except StaleElementReferenceException:
                    pass
            location_element = browser.wait_for_page_element(LOCATION_NAME, 30)
            if location_element:
                location = self._get_location(location_element.text)
            else:
                log.error("Could not retrieve location #%s!", location_id)
                continue
            log.debug('Getting payment')
            log.web_trace(f'location-{location_id}pre-invoices-click')
            invoices_button = browser.wait_for_page_element(INVOICES_TAB)
            if not invoices_button:
                raise FetchError(f'Could not find invoices button for location {location}!')
            _close_accesibility_modal(browser)
            browser.click_page_element_with_retry(invoices_button, INVOICES_TAB)
            due_date = None
            # First check if all invoices are already paid
            all_paid = browser.wait_for_page_element(ALL_PAID, 2)
            if all_paid is None:
                # Energa page renders invoices list in two ways
                invoices = browser.wait_for_page_element(DUE_DATE_LABEL, DUE_DATE_TIMEOUT)
                log.web_trace(f'location-{location_id}duedate-check')
                if invoices:
                    due_date = invoices.text
                else:
                    # If the first method of gettign data fails, try the second one
                    invoices_list = browser.wait_for_page_elements(DUE_DATE_LABEL_ALT, DUE_DATE_TIMEOUT)
                    if invoices_list:
                        due_date = invoices_list[0].text.split('\n')[1]
            browser.wait_for_page_element(DASHBOARD)
            browser.safe_click_page_element(DASHBOARD)
            amount_element = browser.wait_for_page_element(AMOUNT)
            comment = ''
            if amount_element:
                amount = amount_element.text
            else:
                log.error("Could not retrieve amount value for location %s.", location)
                comment = 'Could not retrieve amount'
                amount = Amount.unknown
            if due_date is None:
                if Amount.is_zero(amount):
                    due_date = DueDate.today()
                else:
                    log.error("Could not retrieve due date for non-zero payment '%s', location '%s'.",
                              amount, location)
                    comment = 'Could not retrieve due date'
            payments.append(Payment(self.name, location, due_date, amount, comment))
            log.debug('Moving to the next location')
            browser.wait_for_page_element(ACCOUNTS_LIST)
            browser.safe_click_page_element(ACCOUNTS_LIST)
            if (locations_list_or_none := browser.wait_for_page_elements(ACCOUNTS_LABEL)) is None:
                raise FetchError('Unexpected error: locations list is empty after page reload!')
            locations_list = locations_list_or_none

        return payments
