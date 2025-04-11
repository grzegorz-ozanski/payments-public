from dateutil import parser
from datetime import date
from log import setup_logging
import re
from selenium.webdriver.remote.webelement import WebElement

log = setup_logging(__name__, 'DEBUG')


def get_amount(value, decimal=False):
    if value is None:
        return value
    if type(value) == WebElement:
        value = value.text
    try:
        value = re.sub(r"[^\d,.-]", "", value)
    except TypeError:
        value = f'{value:.2f}'
    # Replace any coma with correct locale decimal separator
    # decimal_sep = locale.format_string('%.1f', 0)[1]
    value = value.replace(' ', '')
    if decimal:
        decimal_sep = '.'
    else:
        decimal_sep = ','
    value = value.replace('.', decimal_sep).replace(',', decimal_sep)
    if decimal:
        return float(value)
    return value


def get_date(value):
    if value is None:
        value = date.today()
    elif type(value) == WebElement:
        value = value.text
    if "dzisiaj" in value:
        return date.today().strftime('%d-%m-%Y')
    try:
        return parser.parse(value).strftime('%d-%m-%Y')
    except TypeError:
        return value.strftime('%d-%m-%Y')


class Payment:
    def __init__(self, amount=None, due_date=None, account=''):
        self.amount = get_amount(amount)
        self.due_date = get_date(due_date)
        self.account = account

    def __str__(self):
        return "{0} {1} {2}".format(self.account, self.due_date, self.amount)

    def is_empty(self):
        # log.debug("amount: %s, due_date: %s, acc")
        return self.amount is None or self.due_date is None or self.account is None

    def print(self, long: bool):
        if long:
            print("%s %s %s" % (self.amount, self.account, self.due_date))
        else:
            # print("%s" % self.amount)
            print("%s %s" % (self.amount, self.due_date))
