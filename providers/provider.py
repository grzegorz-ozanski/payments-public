import inspect
import os
import time
from dataclasses import dataclass
from datetime import datetime
from os import environ

import keyring
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from browser import setup_logging, Browser
from locations import Location
from payments import Payment

log = setup_logging(__name__)


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
class PageElement:
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
        value = keyring.get_password(self.keyring_service, self.keyring).strip()
        if value:
            return value
        raise RuntimeError(f'"{self.keyring}" cannot be found in ether {self.environ} environment variable '
                           f'or {self.keyring_service} keyring service!')


class Provider:
    root_trace_dir = []

    def __init__(self, url: str, keystore_service: str, locations: tuple[Location, ...],
                 user_input: PageElement, password_input: PageElement,
                 logout_button: PageElement | None = None, cookies_button: PageElement | None = None,
                 pre_login_delay: int = 0, post_login_delay: int = 0):
        self._browser = None
        self.url = url
        self.name = keystore_service
        self.keystore_service = keystore_service
        self.locations = locations
        self.user_input = user_input
        self.password_input = password_input
        self.username = Credential(keystore_service, 'username')
        self.password = Credential(keystore_service, 'password')
        self.trace_id = 0
        if not logout_button:
            logout_button = PageElement(
                By.XPATH,
                # lowest element in the DOM tree containing 'Wyloguj' string
                '//*[contains(string(), "Wyloguj") and not(.//*[contains(string(), "Wyloguj")])]'
            )
        self.logout_button = logout_button
        self.cookies_button = cookies_button
        self.pre_login_delay = pre_login_delay
        self.post_login_delay = post_login_delay

    def __repr__(self) -> str:
        return f'{self.name}: [{", ".join(map(str, self.locations))}]'

    def _get_location(self, name_string: str):
        try:
            return next(location for location in self.locations if location.name in name_string)
        except StopIteration:
            log.error(f"Cannot find a valid location for service {self.name}!\n"
                      f"Location name provided: '{name_string}'.\n"
                      f"Valid service locations: {','.join([location.name for location in self.locations])}")
            raise

    @classmethod
    def _path_already_created(cls, path: str) -> bool:
        if path in cls.root_trace_dir:
            return True
        cls.root_trace_dir.append(path)
        return False

    def _save_logs(self, suffix: str = '', path: str = '') -> None:
        self.trace_id += 1
        timestamp = datetime.today().isoformat(sep=' ', timespec='milliseconds').replace(':', '-')
        filename = f"{self.trace_id:0>3} {timestamp} {_get_caller()}{' ' + suffix if suffix else ''}"
        if path:
            if not self._path_already_created(path):
                if os.path.exists(path):
                    last_number = max([int(d.split('.')[1]) if '.' in d else 0
                                       for d in os.listdir()
                                       if d.startswith(f"{path}") and os.path.isdir(d)], default=0)
                    os.rename(path, f'{path}.{last_number + 1:>03}')
            if path != "error":
                path = os.path.join(path, self.name)
            os.makedirs(path, exist_ok=True)
            filename = os.path.join(path, filename)
        self._browser.save_screenshot(f"{filename}.png")
        with open(f"{filename}.html", "w", encoding="utf-8") as page_source_file:
            page_source_file.write(self._browser.page_source)

    def save_error_logs(self):
        self._save_logs(path="error")

    def save_trace_logs(self, suffix: str = ''):
        if self._browser.save_trace_logs:
            self._save_logs(suffix, "trace")

    def input(self, control: WebElement, text: str) -> None:
        time.sleep(0.5)
        if control.get_attribute('value') != '':
            control.send_keys(Keys.CONTROL, 'a')
            time.sleep(0.05)
            control.send_keys(Keys.DELETE)
        for character in text:
            control.send_keys(character)
            time.sleep(0.05)

    def login(self, browser, load=True):
        self._browser = browser
        self._browser.error_log_dir = "error"
        try:
            if load:
                log.debug("Opening %s" % self.url)
                self._browser.force_get(self.url)
                self._browser.wait_for_page_inactive(2)
                if (self.cookies_button and
                        self._browser.wait_for_element(self.cookies_button.by, self.cookies_button.selector, 2)):
                    self._browser.safe_click(self.cookies_button.by, self.cookies_button.selector)
            log.info("Logging into service...")
            self.save_trace_logs("pre-login")
            _sleep_with_message(self.pre_login_delay, "Pre-login")
            input_user = self._browser.wait_for_element(self.user_input.by, self.user_input.selector)
            if input_user is None:
                print(f"No user input {self.user_input} found!")
                self.save_error_logs()
            assert input_user is not None
            input_password = self._browser.wait_for_element(self.password_input.by, self.password_input.selector)
            assert input_password is not None
            username = self.username.get()
            input_user.click()
            time.sleep(0.5)
            input_user.send_keys(username)
            # self.input(input_user, username)
            self.save_trace_logs("username-input")
            password = self.password.get()
            if password is not None:
                input_user.send_keys(Keys.TAB)
                input_password.send_keys(password)
                # self.input(input_password, password)
                time.sleep(0.5)
            else:
                raise Exception(f"No valid password found for service '{self.keystore_service}', user '{username}'!")
            self.save_trace_logs("password-input")
            input_password.send_keys(Keys.ENTER)
            self._browser.wait_for_page_load_completed()
            _sleep_with_message(self.post_login_delay, "Post-login")
            self.save_trace_logs("post-login")
            log.info("Done.")
        except Exception as e:
            log.info("Cannot login into service: %s" % e)
            self.save_error_logs()
            raise

    def _read_payments(self) -> list[Payment]:
        raise NotImplementedError

    def get_payments(self, browser: Browser) -> list[Payment]:
        try:
            print(f'Processing service {self.name}...')
            self._browser = browser
            self.login(self._browser)
            payments = sorted(self._read_payments(), key=lambda value: value.location.key)
        except Exception as e:
            print(f'{e.__class__.__name__}:{str(e)}\n'f'Cannot get payments for service {self.name}!')
            payments = [Payment(location=location, provider=self.name, invalid=True) for location in self.locations]
            self.save_error_logs()
        finally:
            self.logout()
        return payments

    def logout(self):
        try:
            self.save_trace_logs("pre-logout")
            self._browser.find_and_click_element_with_js(self.logout_button.by, self.logout_button.selector)
            self._browser.wait_for_page_inactive(2)
            self.save_trace_logs("post-logout")
        except NoSuchElementException:
            log.debug("Cannot click logout button. Are we even logged in?")
        except WebDriverException:
            self.save_error_logs()
