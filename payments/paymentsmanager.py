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
    services: list[Provider] | Provider
    payments: list[Payment] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        If single item is provided, change it into one-element list
        """
        if not isinstance(self.services, list):
            self.services = [self.services]

    def _get_payments_for_service(self, service: Provider) -> list[Payment]:
        payments = []
        try:
            print(f'Processing service {service.name}...')
            service.login(self.browser)
            payments = sorted(service.get_payments(), key=lambda value: value.location.key)
        except Exception as e:
            print(f'{e.__class__.__name__}:{str(e)}\n'
                  f'Cannot get payments for service {service.name}!')
            service.save_error_logs()
        finally:
            service.logout()
        return payments

    def collect(self) -> None:
        """
        Collect payments for all providers
        """
        try:
            for service in self.services:
                self.payments += self._get_payments_for_service(service)
        finally:
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
