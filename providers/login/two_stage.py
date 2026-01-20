"""
    Module for a login page that shows password input only after the username was typed in
"""
from selenium.webdriver.common.keys import Keys

from browser import Browser, Locator, setup_logging
from providers.login.base import BaseLogin
from credentials.credentials import Credentials

log = setup_logging(__name__)


class TwoStageLogin(BaseLogin):
    """
    Login page that shows password input only after the username was typed in
    """
    def __init__(self, service_name:str, user_input: Locator, password_input: Locator, credentials: Credentials):
        super().__init__(service_name, user_input, password_input, credentials)

    def execute(self, browser: Browser) -> None:
        username_input = self.find_username_input(browser)
        assert username_input is not None

        username_value, password_value = self.get_credentials()
        self.input_username(browser, username_input, username_value)
        log.web_trace("username-input")
        username_input.send_keys(Keys.ENTER)

        password_input = self.find_password_input(browser, 30)
        assert password_input is not None

        self.input_password(password_input, password_value)
        log.web_trace("password-input")
        password_input.send_keys(Keys.ENTER)
