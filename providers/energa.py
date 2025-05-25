"""
Energa provider module for reading payments via Selenium automation.
"""
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.common.by import By

from browser import setup_logging
from payments import Payment
from .provider import PageElement, Provider

log = setup_logging(__name__)


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
        url = "https://24.energa.pl"
        name = self.__class__.__name__.lower()
        super().__init__(url, name, locations, user_input, password_input)

    def logout(self) -> None:
        """
        Log out the user from the Energa web portal.
        """
        try:
            self._browser.wait_for_element_disappear(By.CSS_SELECTOR, 'div.popup.center')
            self._browser.open_dropdown_menu(By.XPATH, '//button[contains(@class, "hover-submenu")]')
            self._weblogger.trace("pre-logout-click")
            self._browser.find_element(By.XPATH, '//span[contains(text(), "Wyloguj się")]').click()
        except (AttributeError, ElementNotInteractableException) as e:
            self._weblogger.error()
            if type(e) is AttributeError:
                if 'move_to requires a WebElement' in str(e):
                    log.debug("Cannot click logout button. Are we even logged in?")
                else:
                    raise
        except NoSuchElementException:
            log.debug("Cannot click logout button. Are we even logged in?")

    def _read_payments(self) -> list[Payment]:
        """
        Read and return payment data for all user locations.
        """
        log.info("Getting payments...")
        self._browser.wait_for_page_load_completed()
        self._weblogger.trace("accounts-list")
        locations_list = self._browser.wait_for_elements(By.CSS_SELECTOR, 'label')
        if not locations_list:
            button = self._browser.wait_for_element(By.CSS_SELECTOR, 'button.button.secondary')
            if button:
                self._browser.trace_click(button)
                self._browser.wait_for_page_load_completed()
                self._weblogger.trace("accounts-list-after-overlay")
                locations_list = self._browser.wait_for_elements(By.CSS_SELECTOR, 'label')
            else:
                raise RuntimeError('Locations list is empty and no overlay was found!')
        log.debug("Identified %d locations" % len(locations_list))
        payments = []
        for location_id in range(len(locations_list)):
            print(f'...location {location_id + 1} of {len(locations_list)}')
            log.debug("Opening location page")
            self._browser.wait_for_element_disappear(By.CSS_SELECTOR, 'div.popup__wrapper')
            self._weblogger.trace("pre-location-click")
            self._browser.click_element_with_js(locations_list[location_id])
            button = self._browser.wait_for_element(By.CSS_SELECTOR, 'button.button.primary', 1)
            if button and button.text != "Zapłać teraz":
                self._browser.click_element_with_js(button)
            location = self._get_location(
                self._browser.wait_for_element(By.CSS_SELECTOR, '.text.es-text.variant-body-bold.mlxs.mrm', 30).text)
            log.debug("Getting payment")
            self._browser.wait_for_element_disappear(By.CSS_SELECTOR, 'div.popup__wrapper')
            self._weblogger.trace("pre-invoices-click")
            self._browser.find_element(By.XPATH, '//a[contains(text(), "Faktury")]').click()
            self._browser.wait_for_page_inactive()
            self._browser.wait_for_element_disappear(By.CSS_SELECTOR, 'div.popup__wrapper')
            invoices = self._browser.find_elements(
                By.XPATH,
                '//span[contains(text(), "Termin płatności")]/../..')
            self._weblogger.trace("duedate-check")
            if invoices:
                due_date = invoices[0].text.split('\n')[1]
            else:
                due_date = 'today'
            self._browser.safe_click(By.XPATH, '//a[contains(text(), "Pulpit konta")]')
            amount = self._browser.wait_for_element(By.CSS_SELECTOR, 'h1.text.es-text.variant-balance').text
            payments.append(Payment(self.name, location, due_date, amount))
            log.debug("Moving to the next location")
            self._browser.safe_click(By.XPATH, '//span[contains(text(), "LISTA KONT")]/..')
            locations_list = self._browser.wait_for_elements(By.CSS_SELECTOR, 'label')

        return payments
