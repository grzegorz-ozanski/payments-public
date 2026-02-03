"""
    Module for a simple page with both username and password inputs visible when the page is opened
"""
import random
import string
import time
from argparse import Namespace

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from browser import Browser, Locator, setup_logging
from payments.providers.auth_flow import BaseLogin
from payments.providers.secrets import Secrets
from payments.providers.auth_flow.mouse_move import move_from_to

log = setup_logging(__name__)


def _input_delay(low: float = 0.05, high: float = 0.2) -> float:
    """
    Generates a random input delay from a specified range

    :param low: Lower bound of the range
    :param high: Upper bound of the range
    :return: Generated random value
    """
    return random.uniform(low, high)


def _input_with_error(control: WebElement, text: str, error_rate: float) -> None:
    """
    Clear the input field and type the given text, introducing human-like errors at a specified rate
    :param control: input field to be cleared
    :param text: text to be typed
    :param error_rate: Value from range [0, 1] determing how ofted a "mistake" should happen during input
    """
    time.sleep(0.5)
    if control.get_attribute('value') != '':
        # Clear the input first if already contains any value
        control.send_keys(Keys.CONTROL, 'a')
        time.sleep(_input_delay())
        if random.random() < 0.5:
            control.send_keys(Keys.DELETE)
        else:
            control.send_keys(Keys.BACKSPACE)
    for char in text:
        control.send_keys(char)
        if random.random() < error_rate:
            log.debug('Wrong char entered on purpose')
            # Generate random incorrect inputs
            control.send_keys(random.choice(string.ascii_letters))
            time.sleep(random.uniform(0.5, 2))
            control.send_keys(Keys.BACKSPACE)
        time.sleep(_input_delay())


class RecaptchaLogin(BaseLogin):
    """
    Log into a page that has both username and password inputs visible at the moment of opening.
    Try to be non-deterministic not to alert reCAPTCHA v3.
    """

    def __init__(self,
                 service_name: str,
                 user_input: Locator,
                 password_input: Locator,
                 credentials: Secrets):
        super().__init__(service_name, user_input, password_input, credentials)
        self.login_button: Locator | None = None
        self.error_treshold = Namespace(user=random.uniform(0.01, 0.2),
                                        password=random.uniform(0.01, 0.1))
        self.login_button_treshold = random.uniform(0.01, 0.4)
        self.tab_key_treshold = random.uniform(0.01, 0.4)

    def input_username(self, browser: Browser, username_input_box: WebElement, username: str) -> None:
        """
        Input the username for the service to the input box provided, emulating some inperfections
        :param browser: Browser object
        :param username_input_box: Username input box
        :param username: username
        """
        browser.click_page_element_with_retry_using_js(username_input_box, self.user_input_selector)
        time.sleep(0.5)
        _input_with_error(username_input_box, username, self.error_treshold.user)

    def input_password(self, password_input_box: WebElement, password: str) -> None:
        """
        Input the password for the service to the input box provided, emulating some inperfections
        :param password_input_box:
        :param password: password
        """
        _input_with_error(password_input_box, password, self.error_treshold.password)
        time.sleep(0.5)

    def execute(self, browser: Browser) -> None:
        if self.login_button is None:
            raise RuntimeError('Login button locator must be set before executing reCAPTCHA login strategy')
        username_input = self.find_username_input(browser)
        assert username_input is not None

        password_input = self.find_password_input(browser)
        assert password_input is not None

        username_value, password_value = self.get_credentials()
        self.input_username(browser, username_input, username_value)
        log.web_trace("username-input")
        move_from_to(browser, username_input, password_input)
        if random.random() < self.tab_key_treshold:
            log.debug('Using <TAB> to move to password input')
            password_input.send_keys(Keys.TAB)
        else:
            log.debug('Using mouse to move to password input')
            browser.click_page_element_with_retry_using_js(password_input, self.user_input_selector)

        self.input_password(password_input, password_value)
        log.web_trace("password-input")
        if random.random() < self.login_button_treshold:
            log.debug('Using <ENTER> to submit a form')
            password_input.send_keys(Keys.ENTER)
        else:
            log.debug('Using mouse to submit a form')
            browser.find_page_element(self.login_button).click()
