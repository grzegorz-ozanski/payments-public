from dataclasses import dataclass, field
from typing import List

from accountmanager import AccountsManager
from browser import Browser
from services.service import BaseService
from payment import Payment


@dataclass
class PaymentsManager:
    browser: Browser
    services: List[BaseService]
    accounts: AccountsManager
    debug_mode: bool
    payments: List[Payment] = field(default_factory=list)

    def collect(self):
        for service in self.services:
            try:
                print("Processing service %s..." % service.name)
                service.login(self.browser)
                self.payments += sorted(service.get_payments(),
                                        key=lambda value: self.accounts.sort_key(value.account))
                service.logout()
            except Exception as e:
                print(e)
                print("Cannot get payments for service %s!" % service.name)

    def print(self):
        for payment in self.payments:
            # payment.print(self.debug_mode)
            payment.print(True)
        self.browser.quit()
