"""
    Mocks for PyTesting
"""
from typing import Any

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from browser import Browser, WebLogger
from payments.payment import Payment
from providers.provider import PageElement
from providers.provider import Provider


class DummyProvider(Provider):
    """Flexible test provider that returns hardcoded or injected payments."""
    default_name = "dummyprovider"

    def __init__(
            self,
            name: str = default_name,
            locations: tuple[str, ...] = ("Sezamowa", "Bryla", "Hodowlana"),
            payments: list[Payment] | None = None,
    ):
        super().__init__(
            url='',
            locations=locations,
            user_input=PageElement(By.ID, "user"),
            password_input=PageElement(By.ID, "pass")
        )
        self.name = name
        self._test_payments = payments

    def login(self, browser: Browser, weblogger: WebLogger, load: bool = True) -> None:
        pass

    def _fetch_payments(self, browser: Browser, weblogger: WebLogger) -> list[Payment]:
        """Return predefined payments or static defaults."""
        if self._test_payments is not None:
            return self._test_payments
        return [
            Payment(self.name, "Bryla", "2025-06-01", "100"),
            Payment(self.name, "Sezamowa", "2025-06-02", "200"),
            Payment(self.name, "Nieznana", "2025-06-03", "300"),
        ]


# we do want not to invoke an actual constructor for this mock
# noinspection PyMissingConstructor
class MockBrowser(Browser):
    """Simplified mock of the Browser interface."""
    save_trace_logs: bool = False

    def __init__(self) -> None:
        self.user_data_dir = None
        # library variable: out of scope
        self.session_id = 'testsession'  # type: ignore[assignment]
        pass

    @property
    def page_source(self) -> str:
        """Mock page_source property."""
        return "<html></html>"

    def click_element_with_js(self, element: WebElement, by: str = '', value: str = '',
                              timeout: int | None = None) -> None:
        """Mock click_element_with_js method."""
        pass

    def find_and_click_element_with_js(self, by: str, value: str) -> None:
        """Mock find_and_click_element_with_js method."""
        pass

    def open_in_new_tab(self, url: str, close_old_tab: bool = True) -> None:
        """Mock force_get method."""
        pass

    def quit(self) -> None:
        """ Mock quit method. """
        pass

    def save_screenshot(self, filename: str) -> bool:
        """Mock save_screenshot method."""
        return True

    def wait_for_page_inactive(self, timeout: int | None = None) -> Any:
        """Mock wait_for_page_inactive method."""
        pass

    def wait_for_element(self, by: str, value: str, timeout: int | None = None) -> WebElement | None:
        """Mock wait_for_element method."""
        assert self is not None
        assert by is not None
        assert value is not None
        return MockWebElement()

    def wait_for_page_load_completed(self) -> None:
        """Mock wait_for_page_load_completed method."""
        pass


class MockWebElement(WebElement):
    """Mock of a Selenium WebElement."""

    def __init__(self) -> None:
        super().__init__('', '')

    def get_attribute(self, name: str) -> str:
        """Mock get_attribute method."""
        return ""

    def send_keys(self, *value: str) -> None:
        """Mock send_keys method."""
        pass

class MockWeblogger(WebLogger):
    """Mock implementation of a weblogger for testing."""

    # we do want not to invoke an actual constructor for this mock
    # noinspection PyMissingConstructor
    def __init__(self, _: str, __: MockBrowser) -> None:
        pass

    def error(self) -> None:
        """Mock error method."""
        pass

    def trace(self, suffix: str) -> None:
        """Mock trace method."""
        pass


