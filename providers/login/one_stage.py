"""
    Module for a simple page with both username and password inputs visible when the page is opened
"""
from selenium.webdriver.common.keys import Keys

from browser import Browser, Locator, setup_logging
from providers.login.base import BaseLogin
from credentials.providersecrets import ProviderSecrets

log = setup_logging(__name__)


class OneStageLogin(BaseLogin):
    """
    Login page that has both username and password inputs visible at the moment of opening.
    """
    def __init__(self, service_name: str, user_input: Locator, password_input: Locator, credentials: ProviderSecrets):
        super().__init__(service_name, user_input, password_input, credentials)

    def execute(self, browser: Browser) -> None:
        username_input = self.find_username_input(browser)
        assert username_input is not None

        password_input = self.find_password_input(browser)
        assert password_input is not None

        username_value, password_value = self.get_credentials()
        self.input_username(browser, username_input, username_value)
        log.web_trace("username-input")
        username_input.send_keys(Keys.TAB)

        self.input_password(password_input, password_value)
        log.web_trace("password-input")
        password_input.send_keys(Keys.ENTER)
