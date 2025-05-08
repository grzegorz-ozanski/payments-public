from dataclasses import dataclass, field

from browser import Browser
from payments import Payment
from providers.provider import Provider


@dataclass
class PaymentsManager:
    browser: Browser
    services: list[Provider] | Provider
    debug_mode: bool
    payments: list[Payment] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.services, list):
            self.services = [self.services]

    def _get_payments_for_service(self, service: Provider):
        payments = []
        try:
            print("Processing service %s..." % service.name)
            service.login(self.browser)
            payments = sorted(service.get_payments(), key=lambda value: value.location.key)
        except Exception as e:
            print(f"{e.__class__.__name__}:{str(e)}")
            print("Cannot get payments for service %s!" % service.name)
            service.save_error_logs()
        finally:
            service.logout()
        return payments

    def collect(self):
        try:
            for service in self.services:
                self.payments += self._get_payments_for_service(service)
        finally:
            self.browser.quit()

    def print(self):
        for payment in self.payments:
            payment.print()

    def write(self, filename):
        with open(filename, 'w') as stream:
            for payment in self.payments:
                payment.print(stream)
