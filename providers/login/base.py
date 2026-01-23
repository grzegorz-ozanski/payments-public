"""
    Base login strategy module
"""
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from browser import Browser, Locator, PageElement, setup_logging
from credentials.credentials import Credentials

log = setup_logging(__name__)

class BaseLogin:
    """Base login strategy class."""
    def __init__(self, service_name: str, user_input: Locator, password_input: Locator, credentials: Credentials):
        self.service_name = service_name
        self.user_input_selector = user_input
        self.password_input_selector = password_input
        self.credentials = credentials

    def execute(self, browser: Browser) -> None:
        """
        Executes login to a service.

        :param browser: Browser object
        """
        raise NotImplementedError(f'{self.__class__.__name__} must override execute().')

    def find_username_input(self, browser: Browser) -> PageElement | None:
        """
        Finds the username input for the service.

        :param browser: Browser object

        :return: username input found or None if timeout expired
        """
        input_user = browser.wait_for_page_element(self.user_input_selector)
        if input_user is None:
            print(f'No user input {self.user_input_selector} found!')
            log.web_error()
        return input_user

    def find_password_input(self, browser: Browser, timeout: int | None = None) -> PageElement | None:
        """
        Finds the password input for the service.
        :param browser: Browser object
        :param timeout: timeout value or None if default browser timeout should be used

        :return: password input found or None if timeout expired
        """
        input_password = browser.wait_for_page_element(self.password_input_selector, timeout)
        if input_password is None:
            print(f'No password input {self.password_input_selector} found!')
            log.web_error()
        return input_password

    def input_username(self, browser: Browser, username_input_box: WebElement, username: str) -> None:
        """
        Input the username for the service to the input box provided.
        :param browser: Browser object
        :param username_input_box: Username input box
        :param username: username
        """
        browser.click_page_element_with_retry_using_js(username_input_box, self.user_input_selector)
        time.sleep(0.5)
        self.input(username_input_box, username)

    def input_password(self, password_input_box: WebElement, password: str) -> None:
        """
        Input the password for the service to the input box provided.
        :param password_input_box: Password input box
        :param password: password
        """
        self.input(password_input_box, password)
        time.sleep(0.5)

    def get_credentials(self) -> tuple[str, str]:
        """
        Get username and password for the service.
        :return: Tuple (username, password)
        """
        username_value = self.credentials.username.get()
        if username_value is None:
            raise RuntimeError(f"No valid username found for service '{self.service_name}'!")

        password_value = self.credentials.password.get()
        if password_value is None:
            raise RuntimeError(f"No valid password found for service '{self.service_name}', user '{username_value}'!")

        return username_value, password_value


    @staticmethod
    def input(control: WebElement, text: str) -> None:
        """
        Clear the input field and type the given text.
        :param control: input field to be cleared
        :param text: text to be typed
        """
        time.sleep(0.5)
        if control.get_attribute('value') != '':
            control.send_keys(Keys.CONTROL, 'a')
            time.sleep(0.05)
            control.send_keys(Keys.DELETE)
        control.send_keys(text)

