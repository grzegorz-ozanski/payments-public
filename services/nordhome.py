from selenium.webdriver.common.by import By
from payment import Payment
from .service import AuthElement, Service
from log import setup_logging

log = setup_logging(__name__, 'DEBUG')


class Nordhome(Service):
    def __init__(self, keystore_user):
        user_input = AuthElement(By.NAME, "nazwaUzytkownika")
        password_input = AuthElement(By.NAME, "hasloUzytkownika")
        url = "https://www.iok.nordhome.com.pl/content/InetObsKontr/login"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, keystore_user, user_input, password_input)

    def get_payments(self):
        return [Payment()]
