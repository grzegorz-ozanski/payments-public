import time
from dataclasses import dataclass
from datetime import datetime

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import keyring
from log import setup_logging

log = setup_logging(__name__, 'DEBUG')


@dataclass
class AuthElement:
    by: By
    selector: str

class BaseService:
    def __init__(self, url: str, keystore_service: str, keystore_user: str,
                 user_input: AuthElement, password_input: AuthElement, logout_button: AuthElement | None = None,
                 pre_login_delay: int = 0, post_login_delay: int = 0):
        self.browser = None
        self.url = url
        self.name = keystore_service
        self.keystore_service = keystore_service
        self.keystore_user = keystore_user
        self.user_input = user_input
        self.password_input = password_input
        if not logout_button:
            logout_button = AuthElement(
                By.XPATH,
                # lowest element in the DOM tree containing 'Wyloguj' string
                '//*[contains(string(), "Wyloguj") and not(.//*[contains(string(), "Wyloguj")])]'
            )
        self.logout_button = logout_button
        self.pre_login_delay = pre_login_delay
        self.post_login_delay = post_login_delay

    def _save_error_logs(self):
        file_name = f"{datetime.today().strftime('%Y-%m-%d %H-%M-%S')} {self.name}-error"
        self.browser.save_screenshot(f"{file_name}.png")
        with open(f"{file_name}.html", "w", encoding="utf-8") as error_file:
            error_file.write(self.browser.page_source)

    def login(self, browser, load=True):
        self.browser = browser
        try:
            if load:
                log.debug("Opening %s" % self.url)
                self.browser.goto_url_forcefully(self.url)
            log.info("Logging into service...")
            self.browser.wait_for_page_load_completed()
            print(f"Sleeping {self.pre_login_delay} seconds")
            time.sleep(self.pre_login_delay)
            input_user = self.browser.wait_for_element(self.user_input.by, self.user_input.selector)
            if input_user is None:
                print(f"No user input {self.user_input} found!")
                self._save_error_logs()
            assert input_user is not None
            input_password = self.browser.wait_for_element(self.password_input.by, self.password_input.selector)
            assert input_password is not None
            input_user.clear()
            input_user.send_keys(self.keystore_user)
            password = keyring.get_password(self.keystore_service, self.keystore_user)
            if password is not None:
                input_password.clear()
                input_password.send_keys(password)
            else:
                raise Exception(f"No valid password found for service '{self.keystore_service}', user '{self.keystore_user}'!")
            input_password.send_keys(Keys.ENTER)
            # TODO workaround for Energa issue
            try:
                input_password.send_keys(Keys.ENTER)
            except Exception:
                pass
            self.browser.wait_for_page_load_completed()
            print(f"Sleeping {self.post_login_delay} seconds")
            time.sleep(self.post_login_delay)
            log.info("Done.")
        except Exception as e:
            log.info("Cannot login into service: %s" % e)
            self._save_error_logs()
            raise

    def get_payments(self):
        raise NotImplementedError

    def logout(self):
        try:
            self.browser.click_element(self.logout_button.by, self.logout_button.selector)
        except NoSuchElementException:
            log.debug("Cannot click logout button. Are we even logged in?")
