"""Payments manager module"""
import logging
import time
from pathlib import Path
from typing import Sequence

from browser import Browser, BrowserManager, BrowserOptions, setup_logging
from payments.lookuplist import LookupList
from payments.payments import Payment
from payments.providers.provider import Provider
from payments.console import print_progress

log = setup_logging(__name__)


def to_string(payments: list[Payment]) -> str:
    """
    Export all payments to string, adding padding
    """
    max_len_provider = 0
    max_len_amount = 0
    max_len_location = 0

    for payment in payments:
        max_len_provider = max(max_len_provider, len(payment.provider))
        max_len_amount = max(max_len_amount, len(str(payment.amount)))
        max_len_location = max(max_len_location, len(payment.location))
    return '\n'.join([payment.to_padded_string([max_len_provider, max_len_amount, max_len_location])
                      for payment in payments])


def _print_banner(message: str) -> None:
    print_progress(message)
    if log.level <= logging.DEBUG:
        sep = '*' * len(message)
        message = f'\n{sep}\n{message}\n{sep}'
        log.debug(message)


class PaymentsManager:
    """
    Collect and export all payments as alligned text
    """
    def __init__(self, providers: Sequence[Provider] | LookupList[Provider] | Provider) -> None:
        """
        If a single item is provided, change it into the one-element list
        """
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

    def collect_fake(self, filename: Path | None, delay: int = 0) -> str:
        """
        Collect payments for all providers
        """
        payments: list[Payment] = []
        if not filename:
            return ''
        with open(filename) as file:
            for line in file.readlines():
                provider, amount, location_name, due_date = ' '.join(line.split()).strip().split()
                if provider not in (prov.name for prov in self.providers):
                    continue
                if due_date == '{{TODAY}}':
                    due_date = 'today'
                if delay > 0:
                    print(f'Processing service {provider}...')
                payments += [Payment(provider,
                                     location_name,
                                     due_date,
                                     amount)]
                time.sleep(delay)
        return to_string(payments)

    def collect(self, options: BrowserOptions, browser_class: type[Browser] = Browser) -> str:
        """
        Collect payments for all providers and return them as string
        :param options: Browser options
        :param browser_class: Browser class
        :return:
        """
        payments: list[Payment] = []
        manager = BrowserManager(options, browser_class)
        try:
            for provider in self.providers:
                _print_banner(f'Processing service {provider.name}...')
                with manager.session(provider.needs_clear_user_profile) as browser:
                    payments += provider.get_payments(browser)
            return to_string(payments)
        finally:
            manager.close()
