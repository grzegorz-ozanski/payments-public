"""Payments manager module"""
from dataclasses import dataclass, field

from browser import Browser
from locations import Location
from payments import Payment
from providers.provider import Provider


@dataclass
class PaymentsManager:
    """
    Collect and export all payments as alligned text
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

    def collect_payments(self, browser: Browser) -> str:
        """
        Collect payments for all providers and return them as string
        """
        for provider in self.providers:
            self.payments += provider.get_payments(browser)
        browser.quit()
        return self._payments_to_str()

    def collect_fake_payments(self, filename: str, *locations: Location) -> None:
        """
        Collect payments for all providers
        """
        with open(filename) as file:
            for line in file.readlines():
                provider, amount, location_name, due_date = line.strip().split(' ')
                if due_date == '{{TODAY}}':
                    due_date = 'today'
                self.payments += [Payment(provider,
                                          next(location for location in locations if location.name == location_name),
                                          due_date,
                                          amount)]

    def _payments_to_str(self) -> str:
        """
        Export all payments to string, adding padding
        """
        max_len_provider = 0
        max_len_amount = 0
        max_len_location = 0

        for payment in self.payments:
            max_len_provider = max(max_len_provider, len(payment.provider))
            max_len_amount = max(max_len_amount, len(str(payment.amount)))
            max_len_location = max(max_len_location, len(payment.location.name))
        return '\n'.join([payment.to_padded_string([max_len_provider, max_len_amount, max_len_location])
                          for payment in self.payments])
