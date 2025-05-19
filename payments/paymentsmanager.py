"""
Payments manager module
"""
from dataclasses import dataclass, field

from browser import Browser
from payments import Payment
from providers.provider import Provider


@dataclass
class PaymentsManager:
    """
    Payments manager
    """
    browser: Browser
    providers: list[Provider] | Provider
    payments: list[Payment] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        If single item is provided, change it into one-element list
        """
        if not isinstance(self.providers, list):
            self.providers = [self.providers]

    def collect(self) -> None:
        """
        Collect payments for all providers
        """
        for provider in self.providers:
            self.payments += provider.payments
        self.browser.quit()

    def print(self) -> None:
        """
        Print payments for all providers
        """
        for payment in self.payments:
            payment.print()

    def write(self, filename: str) -> None:
        """
        Write payments to file
        :param filename: file name
        """
        with open(filename, 'w') as stream:
            for payment in self.payments:
                payment.print(stream)
