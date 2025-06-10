"""Payments manager module"""
from typing import Sequence

from browser import Browser
from payments import Payment
from providers.provider import Provider
from lookuplist import LookupList


class PaymentsManager:
    """
    Collect and export all payments as alligned text
    """
    def __init__(self, providers: Sequence[Provider] | LookupList[Provider] | Provider) -> None:
        """
        If a single item is provided, change it into the one-element list
        """
        self.payments: list[Payment] = []
        self.providers: LookupList[Provider]
        if isinstance(providers, Provider):
            self.providers = LookupList[Provider](providers)
        elif isinstance(providers, Sequence) and not isinstance(providers, str):
            self.providers = LookupList[Provider](*providers)
        elif isinstance(providers, LookupList):
            self.providers = providers
        else:
            raise TypeError(f'Invalid type "{type(providers)}" for argument "providers"')

    def __repr__(self) -> str:
        return '\n'.join(map(str, self.providers))

    def collect_fake_payments(self, filename: str) -> None:
        """
        Collect payments for all providers
        """
        with open(filename) as file:
            for line in file.readlines():
                provider, amount, location_name, due_date = line.strip().split(' ')
                if due_date == '{{TODAY}}':
                    due_date = 'today'
                self.payments += [Payment(provider,
                                          location_name,
                                          due_date,
                                          amount)]

    def collect_payments(self, browser: Browser) -> None:
        """
        Collect payments for all providers and return them as string
        :param browser: Browser instance
        :return:
        """
        for provider in self.providers:
            self.payments += provider.get_payments(browser)
        browser.quit()

    def to_string(self) -> str:
        """
        Export all payments to string, adding padding
        """
        max_len_provider = 0
        max_len_amount = 0
        max_len_location = 0

        for payment in self.payments:
            max_len_provider = max(max_len_provider, len(payment.provider))
            max_len_amount = max(max_len_amount, len(str(payment.amount)))
            max_len_location = max(max_len_location, len(payment.location))
        return '\n'.join([payment.to_padded_string([max_len_provider, max_len_amount, max_len_location])
                          for payment in self.payments])
