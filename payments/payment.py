from accounts import Account
from log import setup_logging

from parsers import *

log = setup_logging(__name__, 'DEBUG')

class Payment:
    def __init__(self, amount=None, due_date=None, account: Account | None = None):
        self.amount = get_amount(amount)
        self.due_date = get_date(due_date)
        self.account = account

    def __str__(self):
        return "{0} {1} {2}".format(self.account.name, self.due_date, self.amount)

    def is_empty(self):
        # log.debug("amount: %s, due_date: %s, acc")
        return self.amount is None or self.due_date is None or self.account is None

    def print(self, long: bool):
        if long:
            print("%s %s %s" % (self.amount, self.account.name, self.due_date))
        else:
            print("%s %s" % (self.amount, self.due_date))
