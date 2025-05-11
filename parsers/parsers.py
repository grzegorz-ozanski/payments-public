from dateutil import parser
from datetime import date, timedelta
import re
from selenium.webdriver.remote.webelement import WebElement


def parse_amount(value, decimal_separator=','):
    if type(value) == WebElement:
        value = value.text
    try:
        value = re.sub(r"[^\d,.-]", "", value)
    except TypeError:
        value = f'{value:.2f}'
    value = value.replace(' ', '').replace('.', decimal_separator).replace(',', decimal_separator)
    if decimal_separator == '.':
        return float(value)
    return value


def parse_date(value):
    today = ["dzisiaj", "today"]
    tomorrow = ["jutro", "tomorrow"]
    yesterday = ["wczoraj", "yesterday"]
    if not isinstance(value, date):
        if isinstance(value, WebElement):
            value = value.text
        if value is None or any(item in value for item in today):
            value = date.today()
        elif any(item in value for item in tomorrow):
            value = date.today() + timedelta(days=1)
        elif any(item in value for item in yesterday):
            value = date.today() + timedelta(days=-1)
        else:
            value = parser.parse(value)
    return value.strftime('%d-%m-%Y')
