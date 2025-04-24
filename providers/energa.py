from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.common.by import By

from locations import Location
from payments import Payment
from .baseservice import AuthElement, BaseService
from browser import setup_logging

log = setup_logging(__name__, 'DEBUG')


class Energa(BaseService):
    def __init__(self, *locations: Location):
        user_input = AuthElement(By.ID, "email_login")
        password_input = AuthElement(By.ID, "password")
        url = "https://24.energa.pl"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, locations, user_input, password_input)

    def logout(self):
        try:
            self.browser.wait_for_element_disappear(By.CSS_SELECTOR, 'div.popup.center')
            self.browser.open_dropdown_menu(By.XPATH, '//button[contains(@class, "hover-submenu")]')
            self.browser.find_element(By.XPATH, '//span[contains(text(), "Wyloguj się")]').click()
        except (AttributeError, ElementNotInteractableException) as e:
            self.save_error_logs()
            if type(e) is AttributeError:
                if 'move_to requires a WebElement' in str(e):
                    log.debug("Cannot click logout button. Are we even logged in?")
                else:
                    raise

    def get_payments(self):
        log.info("Getting payments...")
        self.browser.wait_for_page_load_completed()
        locations_list = self.browser.wait_for_elements(By.CSS_SELECTOR, 'label')
        log.debug("Identified %d locations" % len(locations_list))
        payments = []
        for location_id in range(len(locations_list)):
            print(f'...location {location_id+1} of {len(locations_list)}')
            log.debug("Opening location page")
            self.browser.wait_for_element_disappear(By.CSS_SELECTOR, 'div.popup.center')
            locations_list[location_id].click()
            location = self._get_location(
                self.browser.wait_for_element(By.CSS_SELECTOR, '.text.es-text.variant-body-bold.mlxs.mrm', 30).text)
            log.debug("Getting payment")
            self.browser.wait_for_element_disappear(By.CSS_SELECTOR, 'div.popup__wrapper')
            self.browser.find_element(By.XPATH, '//a[contains(text(), "Faktury")]').click()
            invoices = self.browser.find_elements(
                By.XPATH,
                '//span[contains(text(), "Termin płatności")]/../..//*[contains(@class, "variant-body")]')
            if invoices:
                due_date = invoices[1].text
            else:
                due_date = None
            self.browser.safe_click(By.XPATH, '//a[contains(text(), "Pulpit konta")]')
            amount = self.browser.wait_for_element(By.CSS_SELECTOR, 'h1.text.es-text.variant-balance').text
            payments.append(Payment(amount, due_date, location))
            log.debug("Moving to the next location")
            self.browser.trace_click(self.browser.wait_for_element_clickable(By.XPATH, '//span[contains(text(), "LISTA KONT")]/..'))
            locations_list = self.browser.wait_for_elements(By.CSS_SELECTOR, 'label')

        return payments
