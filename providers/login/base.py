import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from browser import Browser, Locator, WebLogger
from credentials import Credentials

class BaseLogin:
    def __init__(self, service_name: str, user_input: Locator, password_input: Locator, credentials: Credentials):
        self.service_name = service_name
        self.user_input_selector = user_input
        self.password_input_selector = password_input
        self.credentials = credentials

    def execute(self, browser: Browser, weblogger: WebLogger):
        raise NotImplementedError(f'{self.__class__.__name__} must override login().')

    def find_username_input(self, browser: Browser, weblogger: WebLogger):
        input_user = browser.wait_for_page_element(self.user_input_selector)
        if input_user is None:
            print(f'No user input {self.user_input_selector} found!')
            weblogger.error()
        return input_user

    def find_password_input(self, browser: Browser, weblogger: WebLogger):
        input_password = browser.wait_for_page_element(self.password_input_selector)
        if input_password is None:
            print(f'No password input {self.password_input_selector} found!')
            weblogger.error()
        return input_password

    def input_username(self, input_box: WebElement, username: str | None, browser: Browser):
        browser.click_page_element_with_retry_using_js(input_box, self.user_input_selector)
        time.sleep(0.5)
        self.input(input_box, username)

    def input_password(self, input_box: WebElement, password: str | None):
        self.input(input_box, password)
        time.sleep(0.5)

    def get_credentials(self) -> tuple[str, str]:
        username_value = self.credentials.username.get()
        if username_value is None:
            raise RuntimeError(f"No valid username found for service '{self.service_name}'!")

        password_value = self.credentials.password.get()
        if password_value is None:
            raise RuntimeError(f"No valid password found for service '{self.service_name}', user '{username_value}'!")

        return username_value, password_value


    @staticmethod
    def input(control: WebElement, text: str) -> None:
        """Clear the input field and type the given text."""
        time.sleep(0.5)
        if control.get_attribute('value') != '':
            control.send_keys(Keys.CONTROL, 'a')
            time.sleep(0.05)
            control.send_keys(Keys.DELETE)
        control.send_keys(text)

