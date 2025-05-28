"""
    Mocks for PyTesting
"""
from selenium.webdriver.common.by import By

from browser import Browser
from payments.payment import Payment
from providers.provider import PageElement
from providers.provider import Provider


class MockWeblogger:
    """Mock implementation of a weblogger for testing."""

    def trace(self, suffix: str) -> None:
        """Mock trace method."""
        pass

    def error(self) -> None:
        """Mock error method."""
        pass


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
        self._weblogger = MockWeblogger()

    def login(self, browser: Browser, load: bool = True) -> None:
        pass

    def _fetch_payments(self) -> list[Payment]:
        """Return predefined payments or static defaults."""
        if self._test_payments is not None:
            return self._test_payments
        return [
            Payment(self.name, "Bryla", "2025-06-01", "100"),
            Payment(self.name, "Sezamowa", "2025-06-02", "200"),
            Payment(self.name, "Nieznana", "2025-06-03", "300"),
        ]

class MockBrowser:
    """Simplified mock of the Browser interface."""

    def force_get(self, url: str) -> None:
        """Mock force_get method."""
        pass

    def wait_for_page_inactive(self, timeout: int = 2) -> None:
        """Mock wait_for_page_inactive method."""
        pass

    def wait_for_element(self, *args, **kwargs) -> "MockWebElement":
        """Mock wait_for_element method."""
        assert self is not None
        assert args is not None
        assert kwargs is not None
        return MockWebElement()

    def click_element_with_js(self, elem: object) -> None:
        """Mock click_element_with_js method."""
        pass

    def wait_for_page_load_completed(self) -> None:
        """Mock wait_for_page_load_completed method."""
        pass

    def find_and_click_element_with_js(self, *args, **kwargs) -> None:
        """Mock find_and_click_element_with_js method."""
        pass

    save_trace_logs: bool = False

    def save_screenshot(self, path: str) -> None:
        """Mock save_screenshot method."""
        pass

    @property
    def page_source(self) -> str:
        """Mock page_source property."""
        return "<html></html>"

    def quit(self) -> None:
        """ Mock quit method. """
        pass


class MockWebElement:
    """Mock of a Selenium WebElement."""

    def get_attribute(self, key: str) -> str:
        """Mock get_attribute method."""
        assert self is not None
        assert key is not None
        return ""

    def send_keys(self, *args) -> None:
        """Mock send_keys method."""
        pass

