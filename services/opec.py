from selenium.webdriver.common.by import By
from payment import Payment, get_amount, get_date
from .service import AuthInput, Service
from log import setup_logging
log = setup_logging(__name__, 'DEBUG')


class Opec(Service):
    def __init__(self, keystore_user):
        user_input = AuthInput(By.ID, "_58_login")
        password_input = AuthInput(By.ID, "_58_password")
        url = "https://ebok.opecgdy.com.pl/home"
        keystore_service = self.__class__.__name__.lower()
        self.account = Service._get_account('Sezamowa')
        super().__init__(url, keystore_service, keystore_user, user_input, password_input)

    def get_payments(self):
        self.browser.find_element_ex(By.TAG_NAME, 'a', 'text=Płatności').click()
        self.browser.find_element_ex(By.TAG_NAME, 'a', 'text=Dokumenty').click()
        invoices = self.browser.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
        amount = 0
        due_date = None
        for invoice in invoices:
            columns = invoice.find_elements(By.TAG_NAME, 'td')
            if columns[6].text == "Zapłacony":
                continue
            try:
                amount += get_amount(columns[7], True)
            except ValueError:
                amount += get_amount(columns[5], True)
            date = get_date(columns[4])
            if due_date is None or date < due_date:
                due_date = date
        return [Payment(amount, due_date, self.account)]
