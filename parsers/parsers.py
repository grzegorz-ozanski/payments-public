from dateutil import parser
from datetime import date
import re
from selenium.webdriver.remote.webelement import WebElement


def get_amount(value, decimal=False):
    if value is None:
        return value
    if type(value) == WebElement:
        value = value.text
    try:
        value = re.sub(r"[^\d,.-]", "", value)
    except TypeError:
        value = f'{value:.2f}'
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
    if not isinstance(value, date):
        if isinstance(value, WebElement):
            value = value.text
        if value is None or "dzisiaj" in value:
            value = date.today()
        else:
            value = parser.parse(value)
    return value.strftime('%d-%m-%Y')
