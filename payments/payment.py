"""Payment related classes (Payment, Amount and DueDate)"""
import re
from functools import total_ordering
from typing import TypeVar

from selenium.webdriver.remote.webelement import WebElement

from browser import setup_logging

log = setup_logging(__name__)

from dateutil import parser
from datetime import date, timedelta

AmountT = TypeVar("AmountT", str, float, WebElement)

DueDateT = TypeVar("DueDateT", str, date, WebElement)


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
        if isinstance(value, WebElement):
            value = value.text
        if isinstance(value, float):
            value = str(value)
        separator = '|'
        amount = re.sub(r'[^\d,.-]', '', value)
        amount = re.sub(r'[,.]', separator, amount)
        self.whole, self.decimal = amount.split(separator) if separator in amount else (amount, '0')

    def __repr__(self) -> str:
        """
            Return string representation of the Amount.
        """
        return f'{self.whole},{self.decimal:02}'

    def __format__(self, format_spec: str) -> str:
        """
            Format amount for aligned output (e.g., currency alignment).
        """
        return format(str(self), format_spec)

    def __float__(self) -> float:
        """
            Convert amount to float for numeric operations.
        """
        return float(f'{self.whole}.{self.decimal}')

    @classmethod
    def is_zero(cls, value: str) -> bool:
        """
        Checks if the given value evaluates into zero.
        :param value: amount value
        :return: True if provided value evaluates into zero, False otherwise
        """
        return re.search(r"^\D*\b0,00\b", value) is not None


@total_ordering
class DueDate:
    """
    Date object handling special values ('today', 'tomorrow', 'yesterday' in English and Polist)
    """
    _today = ['dzisiaj', 'today']
    _tomorrow = ['jutro', 'tomorrow']
    _yesterday = ['wczoraj', 'yesterday']
    unknown = '<unknown>'

    def __init__(self, value: DueDateT) -> None:
        """
        Constuctor
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
                value = parser.parse(value, dayfirst=True)
        self.value = value

    def __repr__(self) -> str:
        """
            Return string representation of the DueDate.
        """
        return self.value.strftime('%d-%m-%Y')

    def __eq__(self, other: object) -> bool:
        """
            Compare dates for equality.
        """
        if not isinstance(other, DueDate):
            return NotImplemented
        return self.value == other.value

    def __lt__(self, other: object) -> bool:
        """
            Compare dates for sorting (less than).
        """
        if not isinstance(other, DueDate):
            return NotImplemented
        return self.value < other.value

    @classmethod
    @property
    def today(cls) -> str:
        """
        Returns a magic string allowing to create a DueDate object with today's date.

        :return: The current day's date
        :rtype: str
        """
        return cls._today[0]

class Payment:
    """
    Payment class. Stores either valid payment properly acquired from a provider's page
    (with amount and due_date containing actual values),
    or an invalid one otherwise (amount and due_date set to '<unknown>')
    """

    def __init__(self,
                 provider: str,
                 location: str,
                 due_date: DueDateT | None = '',
                 amount: AmountT | None = '0,0') -> None:
        """
        Payment constructor

        :param amount: amount
        :param due_date: due date
        :param location: location
        :param provider: provider
        """

        self.amount = Amount(amount) if amount is not None else '<unknown>'
        self.due_date = DueDate(due_date) if due_date is not None else '<unknown>'
        self.location = location
        self.provider = provider
        log.debug(f'Created payment object:'
                  f'{provider=}, {location=}, '
                  f'{due_date=}, {amount=}, '
                  f'{self.due_date=}, {self.amount=}')

    def __repr__(self) -> str:
        return f'{self.location} {self.due_date} {self.amount}'

    def to_padded_string(self, padding: list | None = None) -> str:
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
                f'{self.due_date}')
