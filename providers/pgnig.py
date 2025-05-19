from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from browser import setup_logging
from locations import Location
from payments import Amount, Payment
from .provider import AuthElement, Provider

log = setup_logging(__name__)


class Pgnig(Provider):
    def __init__(self, *locations: Location):
        user_input = AuthElement(By.NAME, "identificator")
        password_input = AuthElement(By.NAME, "accessPin")
        url = "https://ebok.pgnig.pl"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, locations, user_input, password_input)

    def _payments(self):
        log.info("Getting payments...")
        location = self._get_location(self._browser.wait_for_element(By.CLASS_NAME, 'reading-adress').text)
        log.info("Getting invoices menu...")
        invoices_menu = self._browser.find_element(By.XPATH,
                                                  '//*[@class="menu-element" and normalize-space()="Faktury"]')
        log.info("Opening invoices menu...")
        self.save_trace_logs("pre-invoices-click")
        invoices_menu.click()
        log.debug("Waiting for page load completed...")
        self._browser.wait_for_page_inactive()
        unpaid_invoices = None
        for i in range(10):
            index = 0
            item = None
            try:
                log.info("Getting filtered invoices list...")
                unpaid_invoices = []
                for index, item in enumerate(self._browser.wait_for_elements(By.CLASS_NAME, "main-row-container")):
                    if item.find_element(By.CLASS_NAME, 'button').text == "Zapłać":
                        unpaid_invoices.append(item)
                break
            except StaleElementReferenceException:
                log.warning(f"Stale element encountered during filtering invoices.\n"
                            f"Element index: {index}\n"
                            f"Element details:\n{self._browser.dump_element(item)}")
        log.debug("Creating payments dict...")
        payments_dict = {}
        for invoice in unpaid_invoices:
            log.debug("Iterating over unpaid invoices...")
            columns = invoice.find_elements(By.CLASS_NAME, "columns")
            log.debug("Adding payment...")
            payments_dict[columns[2].text] = payments_dict.get(columns[2].text, 0) + float(Amount(columns[3].text))
        payments = []
        for date, amount in payments_dict.items():
            payments.append(Payment(str(amount), date, location, self.name))
        return payments if payments else [Payment(location=location, provider=self.name)]
