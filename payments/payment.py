from locations import Location
from browser import setup_logging

from parsers import *

log = setup_logging(__name__)

class Payment:
    def __init__(self, amount=0, due_date=None, location: Location | None = None):
        self.amount = parse_amount(amount)
        self.due_date = parse_date(due_date)
        self.location = location

    def __str__(self):
        return "{0} {1} {2}".format(self.location.name, self.due_date, self.amount)

    def is_empty(self):
        # log.debug("amount: %s, due_date: %s, acc")
        return self.amount is None or self.due_date is None or self.location is None

    def print(self, long: bool):
        if long:
            print("%s %s %s" % (self.amount, self.location.name, self.due_date))
        else:
            print("%s %s" % (self.amount, self.due_date))
