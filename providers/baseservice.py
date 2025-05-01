import inspect
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List

from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import keyring
from payments import Payment
from os import environ
from locations import Location
from browser import setup_logging

log = setup_logging(__name__, 'DEBUG')


def _sleep_with_message(amount: int, message: str):
    if amount:
        log.debug(f"{message}: sleeping {amount} seconds")
        time.sleep(amount)


def _get_caller(level: int = 3) -> str:
    # get callers name of the parent
    frame = inspect.stack()[level].frame

    # get method name
    method_name = inspect.stack()[level].function

    # get class name if available
    class_name = None
    if 'self' in frame.f_locals:
        class_name = frame.f_locals['self'].__class__.__name__

    return f'{class_name}_{method_name}'


@dataclass
class AuthElement:
    by: str
    selector: str


class Credential:
    keyring: str
    environ: str

    def __init__(self, service_name, name, env_upper: bool = True):
        self.keyring_service = service_name
        self.keyring = name
        self.environ = f'{service_name}_{name}'
        if env_upper:
            self.environ = self.environ.upper()

    def get(self) -> str | None:
        if value := environ.get(self.environ):
            return value
        value = keyring.get_password(self.keyring_service, self.keyring)
        if value:
            return value
        raise RuntimeError(f'"{self.keyring}" cannot be found in ether {self.environ} environment variable '
                           f'or {self.keyring_service} keyring service!')


class BaseService:
    def __init__(self, url: str, keystore_service: str, locations: tuple[Location, ...],
                 user_input: AuthElement, password_input: AuthElement, logout_button: AuthElement | None = None,
                 pre_login_delay: int = 0, post_login_delay: int = 0):
        self.browser = None
        self.url = url
        self.name = keystore_service
        self.keystore_service = keystore_service
        self.locations = locations
        self.user_input = user_input
        self.password_input = password_input
        self.username = Credential(keystore_service, 'username')
        self.password = Credential(keystore_service, 'password')
        if not logout_button:
            logout_button = AuthElement(
                By.XPATH,
                # lowest element in the DOM tree containing 'Wyloguj' string
                '//*[contains(string(), "Wyloguj") and not(.//*[contains(string(), "Wyloguj")])]'
            )
        self.logout_button = logout_button
        self.pre_login_delay = pre_login_delay
        self.post_login_delay = post_login_delay

    def _get_location(self, name_string: str):
        try:
            return next(location for location in self.locations if location.name in name_string)
        except StopIteration:
            log.error(f"Cannot find a valid location for service {self.name}!\n"
                      f"Location name provided: '{name_string}'.\n"
                      f"Valid service locations: {','.join([location.name for location in self.locations])}")
            raise

    def _save_logs(self, suffix: str = '', path: str = '') -> None:
        filename = f"{datetime.today().strftime('%Y-%m-%d %H-%M-%S')} {self.name} {_get_caller()}{' ' + suffix if suffix else ''}"
        if path:
            if path != "error":
                path = os.path.join(path, self.name)
            os.makedirs(path, exist_ok=True)
            filename = os.path.join(path, filename)
        self.browser.save_screenshot(f"{filename}.png")
        with open(f"{filename}.html", "w", encoding="utf-8") as page_source_file:
            page_source_file.write(self.browser.page_source)

    def save_error_logs(self):
        self._save_logs(path="error")

    def save_trace_logs(self, suffix: str=''):
        # Trace only in CI
        if os.environ.get("GITHUB_JOB"):
            self._save_logs(suffix, "trace")

    def login(self, browser, load=True):
        self.browser = browser
        try:
            if load:
                log.debug("Opening %s" % self.url)
                self.browser.force_get(self.url)
            log.info("Logging into service...")
            self.browser.wait_for_page_inactive(2)
            self.save_trace_logs("pre-login")
            _sleep_with_message(self.pre_login_delay, "Pre-login")
            input_user = self.browser.wait_for_element(self.user_input.by, self.user_input.selector)
            if input_user is None:
                print(f"No user input {self.user_input} found!")
                self.save_error_logs()
            assert input_user is not None
            input_password = self.browser.wait_for_element(self.password_input.by, self.password_input.selector)
            assert input_password is not None
            username = self.username.get()
            input_user.send_keys(username)
            self.save_trace_logs("username-input")
            password = self.password.get()
            if password is not None:
                input_password.send_keys(password)
            else:
                raise Exception(f"No valid password found for service '{self.keystore_service}', user '{username}'!")
            self.save_trace_logs("password-input")
            input_password.send_keys(Keys.ENTER)
            self.browser.wait_for_page_load_completed()
            _sleep_with_message(self.post_login_delay, "Post-login")
            self.save_trace_logs("post-login")
            log.info("Done.")
        except Exception as e:
            log.info("Cannot login into service: %s" % e)
            self.save_error_logs()
            raise

    def get_payments(self) -> List[Payment]:
        raise NotImplementedError

    def logout(self):
        try:
            self.browser.wait_for_page_inactive(2)
            self.save_trace_logs("pre-logout")
            self.browser.find_and_click_element_with_js(self.logout_button.by, self.logout_button.selector)
            self.browser.wait_for_page_inactive(2)
            self.save_trace_logs("post-logout")
        except NoSuchElementException:
            log.debug("Cannot click logout button. Are we even logged in?")
        except WebDriverException:
            self.save_error_logs()
