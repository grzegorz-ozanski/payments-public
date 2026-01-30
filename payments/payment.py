"""
    Payment-related classes (Payment, Amount and DueDate)
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from functools import total_ordering

from dateutil import parser
from selenium.webdriver.remote.webelement import WebElement

from browser import setup_logging, PageElement

log = setup_logging(__name__)

AmountT = str | float | WebElement | PageElement

DueDateT = str | date | WebElement | PageElement


class Amount:
    """
        Represents payment amount either as float or decimal value with comma (',') decimal separator
    """
    _zero = '0,00'
    unknown = '<unknown>'

    def __init__(self, value: AmountT) -> None:
        """
        Constructor
        :param value: payment value
        """
        self.value = str(value.text) if isinstance(value, (PageElement, WebElement)) else str(value)
        self.whole, self.decimal = self._split()

    def __iadd__(self, other: Amount) -> Amount:
        value = float(self) + float(other)
        self.value = str(value)
        self.whole, self.decimal = self._split()
        return self

    def __eq__(self, other: object) -> bool:
        """
            Compare amounts for equality.
        """
        if not isinstance(other, Amount):
            if isinstance(other, str):
                return self.value == other
            return NotImplemented
        if self.is_unknown():
            return True if other.is_unknown() else False
        return self.whole == other.whole and self.decimal == other.decimal

    def __float__(self) -> float:
        """
            Convert amount to float for numeric operations.
        """
        if self.is_unknown():
            raise ValueError('Cannot convert unknown amount to float.')
        return float(f'{self.whole}.{self.decimal}')

    def __format__(self, format_spec: str) -> str:
        """
            Format amount for aligned output (e.g., currency alignment).
        """
        return format(str(self), format_spec)

    def __repr__(self) -> str:
        """
            Return string representation of the Amount.
        """
        return self.value if self.is_unknown() else f'{self.whole},{self.decimal:02}'

    def _split(self) -> tuple[str, str]:
        if self.is_unknown():
            return '', ''
        separator = '|'
        amount = re.sub(r'[^\d,.-]', '', self.value)
        amount = re.sub(r'[,.]', separator, amount)
        whole, dec = amount.split(separator) if separator in amount else (amount, '0')
        return whole, dec

    def is_unknown(self) -> bool:
        """
        Checks if the amount is unknown.
        :return: True if unknown, False otherwise
        """
        return self.value == self.unknown

    @classmethod
    def is_zero(cls, value: str) -> bool:
        """
        Checks if the given value evaluates into zero.
        :param value: amount value
        :return: True if provided value evaluates into zero, False otherwise
        """
        return re.search(r'^\D*\b0,00\b', value) is not None

    @staticmethod
    def create_from(value: AmountT | Amount | None) -> 'Amount':
        """
        Creates Amount object from any compatible value
        :param value: source value
        :return: Proper Amount object
        """
        if value is None:
            return Amount(Amount.unknown)
        if isinstance(value, Amount):
            return value
        return Amount(value)


@total_ordering
class DueDate:
    """
    Date object handling special values ('today', 'tomorrow', 'yesterday' in English and Polist)
    """
    _today = ['dzisiaj', 'today']
    _tomorrow = ['jutro', 'tomorrow']
    _yesterday = ['wczoraj', 'yesterday']
    _unknown_str = '<unknown>'
    unknown = date.min

    def __init__(self, value: DueDateT) -> None:
        """
        Constructor
        :param value: either date object or its string representation
        """
        if isinstance(value, WebElement):
            value = value.text
        if isinstance(value, str):
            if value == '' or any(item in value for item in self._today):
                value = date.today()
            elif any(item in value for item in self._tomorrow):
                value = date.today() + timedelta(days=1)
            elif any(item in value for item in self._yesterday):
                value = date.today() + timedelta(days=-1)
            else:
                # day is first only if a 4-digit year is last
                value = parser.parse(value, dayfirst=re.match(r'.*\d\d\d\d$', value) is not None).date()
        self.value = value

    def __eq__(self, other: object) -> bool:
        """
            Compare dates for equality.
        """
        if isinstance(other, date):
            return self.value == other
        if not isinstance(other, DueDate):
            return NotImplemented
        return self.value == other.value

    def __lt__(self, other: object) -> bool:
        """
            Compare dates for sorting (less than).
        """
        if isinstance(other, date):
            return self.value < other
        if not isinstance(other, DueDate):
            return NotImplemented
        return True if other.value == DueDate.unknown else self.value < other.value

    def __repr__(self) -> str:
        """
            Return string representation of the DueDate.
        """
        return self._unknown_str if self.value == DueDate.unknown else self.value.strftime('%d-%m-%Y')

    @classmethod
    def today(cls) -> str:
        """
        Returns a magic string allowing to create a DueDate object with today's date.

        :return: The current day's date
        :rtype: str
        """
        return cls._today[0]

    @staticmethod
    def create_from(value: 'DueDateT | DueDate | None') -> 'DueDate':
        """
        Creates DueDate object from any compatible value
        :param value: source value
        :return: Proper DueDate object
        """
        if value is None:
            return DueDate(date.min)
        if isinstance(value, DueDate):
            return value
        return DueDate(value)


class Payment:
    """
    Payment class. Stores either valid payment properly acquired from a provider's page
    (with amount and due_date containing actual values),
    or an invalid one otherwise (amount and due_date set to '<unknown>')
    """

    def __init__(self,
                 provider: str,
                 location: str,
                 due_date: DueDate | DueDateT | None = '',
                 amount: Amount | AmountT | None = '0,0',
                 comment: str = '') -> None:
        """
        Payment constructor

        :param amount: amount
        :param due_date: due date
        :param location: location
        :param provider: provider
        """

        self.amount = Amount.create_from(amount)
        self.due_date = DueDate.create_from(due_date)
        self.location = location
        self.provider = provider
        self.comment = comment
        log.debug('Created payment object:'
                  'provider=%s, location=%s, '
                  'due_date=%s, amount=%s, comment=%s'
                  'self.due_date=%s, self.amount=%s',
                  provider, location,
                  due_date, amount, comment,
                  self.due_date, self.amount
        )

    def __repr__(self) -> str:
        return f'{self.location} {self.due_date} {self.amount}'

    def to_padded_string(self, padding: list[int] | None = None) -> str:
        """
        Export to string
        :param padding: fields padding list
        """
        if padding is None or len(padding) < 3:
            padding = padding or []
            padding += [0] * (3 - len(padding))
        return (f'{self.provider or "": <{padding[0] + 1}}'
                f'{self.amount: <{padding[1]}} '
                f'{self.location: <{padding[2]}} '
                f'{self.due_date}'
                f'{" #" + self.comment if self.comment else ""}')
