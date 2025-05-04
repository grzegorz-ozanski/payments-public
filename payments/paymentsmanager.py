from dataclasses import dataclass, field
from typing import List

from browser import Browser
from providers.baseservice import BaseService
from payments import Payment


@dataclass
class PaymentsManager:
    browser: Browser
    services: List[BaseService] | BaseService
    debug_mode: bool
    payments: List[Payment] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.services, list):
            self.services = [self.services]

    def _get_payments_for_service(self, service: BaseService):
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
