"""Payments manager"""
import logging
import os
import time
from pathlib import Path
from typing import Sequence, Callable

from browser import Browser, BrowserManager, BrowserOptions, setup_logging
from payments.lookuplist import LookupList
from payments.payments.payment import Payment
from payments.payments.paymentslist import PaymentsList
from payments.providers.provider import Provider
from payments.console import print_progress

log = setup_logging(__name__)


def _print_banner(message: str) -> None:
    print_progress(message)
    if log.level <= logging.DEBUG:
        sep = '*' * len(message)
        message = f'\n{sep}\n{message}\n{sep}'
        log.debug(message)


class PaymentsManager:
    """
    Collect all payments, either from real web pages
    or from text data file (for debugging purpuses)
    """
    def __init__(self, providers: Sequence[Provider] | LookupList[Provider] | Provider) -> None:
        self.providers: LookupList[Provider]
        if isinstance(providers, Provider):
            # If a single item is provided, change it into the one-element list
            self.providers = LookupList[Provider](providers)
        elif isinstance(providers, Sequence) and not isinstance(providers, str):
            self.providers = LookupList[Provider](*providers)
        elif isinstance(providers, LookupList):
            self.providers = providers
        else:
            raise TypeError(f'Invalid type "{type(providers)}" for argument "providers"')

    def __repr__(self) -> str:
        return '\n'.join(map(str, self.providers))

    def collect_fake(self, filename: Path | None, delay: int = 0) -> PaymentsList:
        """
        Collect payments for all providers
        """
        payments: list[Payment] = []
        if not filename:
            return PaymentsList(payments)
        with open(filename) as file:
            print(f'Getting data from {filename}...')
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
        return PaymentsList(payments)

    def collect_real(self, options: BrowserOptions, browser_class: type[Browser] = Browser) -> PaymentsList:
        """
        Collect payments for all providers and return them as string
        :param options: Browser options
        :param browser_class: Browser class
        """
        payments: list[Payment] = []
        manager = BrowserManager(options, browser_class)
        try:
            for provider in self.providers:
                _print_banner(f'Processing service {provider.name}...')
                with manager.session(provider.needs_clear_user_profile) as browser:
                    payments += provider.get_payments(browser)
            return PaymentsList(payments)
        finally:
            manager.close()

    def collect(self,
                options_factory: Callable[[], BrowserOptions]) -> PaymentsList:
        """
        Collect payments either for all providers or from fake data file
        :param options_factory: Browser options factory
        :return PaymentsManager self object for pipelining
        """

        def is_fake_run() -> Path | None:
            """
            Returns path to artifical payments data if fake run (i.e. with no actual providers page parsing)
            is executed.
            """
            # PowerShell cuts off empty variables when passing the env to the child process,
            # so we cannot differenciate betweeen "set to empty" and "not set"
            path = os.getenv('PAYMENTS_FAKE_DATA', '')
            if not path:
                return None
            if path == '<default>':
                return Path('.github', 'data', 'test_output.txt')
            return Path(path)

        if (fake_data := is_fake_run()) is not None:
            return self.collect_fake(fake_data, int(os.getenv('PAYMENTS_FAKE_DELAY', '0')))
        return self.collect_real(options_factory())
