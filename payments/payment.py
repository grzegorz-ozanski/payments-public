"""
Payments module
"""
import re
from typing import TextIO

from browser import setup_logging
from locations import Location

log = setup_logging(__name__)

from dateutil import parser
from datetime import date, timedelta


class Amount:
    """
    Payment amount
    """

    def __init__(self, value: str) -> None:
        """
        Constructor
        :param value: amount value
        """
        separator = '|'
        amount = re.sub(r'[^\d,.-]', '', value)
        amount = re.sub(r'[,.]', separator, amount)
        self.whole, self.decimal = amount.split(separator) if separator in amount else (amount, '0')

    def __str__(self) -> str:
        """
        Converts amount to string
        :return: string value
        """
        return f'{self.whole},{self.decimal:02}'

    def __float__(self) -> float:
        """
        Converts amount to float
        :return: float value
        """
        return float(f'{self.whole}.{self.decimal}')


class DueDate:
    """
    Payment due date
    """
    today = ['dzisiaj', 'today']
    tomorrow = ['jutro', 'tomorrow']
    yesterday = ['wczoraj', 'yesterday']

    def __init__(self, value: date | str) -> None:
        """
        Constuctor
        :param value: either date object or its string representation
        """
        if isinstance(value, str):
            if any(item in value for item in self.today):
                value = date.today()
            elif any(item in value for item in self.tomorrow):
                value = date.today() + timedelta(days=1)
            elif any(item in value for item in self.yesterday):
                value = date.today() + timedelta(days=-1)
            else:
                value = parser.parse(value, dayfirst=True)
        self.value = value

    def __str__(self) -> str:
        """
        Converts date to string
        :return: string representation of the date
        """
        return self.value.strftime('%d-%m-%Y')


class Payment:
    """
    Single payment
    """

    def __init__(self,
                 amount: str = '0,0',
                 due_date: date | str = 'today',
                 location: Location | None = None,
                 provider: str = '',
                 invalid: bool = False) -> None:
        """
        Payment constructor

        :param amount: amount
        :param due_date: due date
        :param location: location
        :param provider: provider
        :param invalid: 'True' to indicate that payment data could not be retrieved from a provider
        """
        if invalid:
            log.debug(f'Creating payment object: {provider=}, <unknown>, {location=}, <unknown>')
        else:
            log.debug(f'Creating payment object: {provider=}, {amount=}, {location=}, {due_date=}')
        if invalid:
            self.amount = '<unknown>'
            self.due_date = '<unknown>'
        else:
            self.amount = Amount(amount)
            self.due_date = DueDate(due_date)
        self.location = location
        self.provider = provider

    def __str__(self) -> str:
        return f'{self.location.name} {self.due_date} {self.amount}'

    def is_empty(self) -> bool:
        """
        Check if object is empty
        :return: 'True' if object is empty, 'False' otherwise
        """
        return self.amount is None or self.due_date is None or self.location is None

    def print(self, stream: TextIO = None) -> None:
        """
        Print the object
        :param stream: Stream to print to ('None' to print to stdout)
        """
        print(f'{self.provider + " " if self.provider else ""}'
              f'{self.amount} {self.location.name} {self.due_date}', file=stream)
