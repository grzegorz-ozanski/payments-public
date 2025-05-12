"""
Payments module
"""
from typing import TextIO

from locations import Location
from browser import setup_logging

from parsers import *

log = setup_logging(__name__)

class Payment:
    """
    Single payment
    """
    def __init__(self,
                 amount: int = 0,
                 due_date: object = None,
                 location: Location | None = None,
                 provider: str = '') -> None:
        """
        Payment constructor

        :param amount: payment amount
        :param due_date: payment due date
        :param location: payment location
        :param provider: payment provider
        """
        self.amount = parse_amount(amount)
        self.due_date = parse_date(due_date)
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
        :param stream: Stream to print to ('None' to pring to stdout)
        """
        print(f'{self.provider + " " if self.provider else ""}'
              f'{self.amount} {self.location.name} {self.due_date}', file=stream)
