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
    providers: list[Provider] | Provider
    payments: list[Payment] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        If single item is provided, change it into one-element list
        """
        if not isinstance(self.providers, list):
            self.providers = [self.providers]

    def __repr__(self) -> str:
        return '\n'.join(map(str, self.providers))

    def collect_payments(self, browser: Browser) -> None:
        """
        Collect payments for all providers
        """
        for provider in self.providers:
            self.payments += provider.get_payments(browser)
        browser.quit()

    def print_payments(self) -> None:
        """
        Print payments for all providers
        """
        max_len_provider = 0
        max_len_amount = 0
        max_len_location = 0

        for payment in self.payments:
            max_len_provider = max(max_len_provider, len(payment.provider))
            max_len_amount = max(max_len_amount, len(str(payment.amount)))
            max_len_location = max(max_len_location, len(payment.location.name))
        for payment in self.payments:
            payment.print(padding=[max_len_provider, max_len_amount, max_len_location])

    def export_payments(self, filename: str) -> None:
        """
        Write payments to file
        :param filename: file name
        """
        with open(filename, 'w') as stream:
            for payment in self.payments:
                payment.print(stream)
