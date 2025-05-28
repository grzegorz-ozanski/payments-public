"""
    DueDate class unittests
"""
from datetime import date, timedelta
from unittest.mock import Mock

from selenium.webdriver.remote.webelement import WebElement

from payments.payment import DueDate

DATE_STRING = '05-10-2023'

# Tests for DueDate class
def test_duedate_with_today_string() -> None:
    """Test initializing DueDate with 'today' string."""
    due_date = DueDate("today")
    assert due_date.value == date.today()


def test_duedate_with_tomorrow_string() -> None:
    """Test initializing DueDate with 'tomorrow' string."""
    due_date = DueDate("tomorrow")
    assert due_date.value == date.today() + timedelta(days=1)


def test_duedate_with_yesterday_string() -> None:
    """Test initializing DueDate with 'yesterday' string."""
    due_date = DueDate("yesterday")
    assert due_date.value == date.today() - timedelta(days=1)


def test_duedate_with_valid_date_string() -> None:
    """Test initializing DueDate with a valid date string."""
    due_date = DueDate(DATE_STRING)
    assert due_date.value == date(2023, 10, 5)


def test_duedate_with_webelement_value() -> None:
    """Test initializing DueDate with a WebElement value."""
    web_element_mock = Mock(spec=WebElement)
    web_element_mock.text = DATE_STRING
    due_date = DueDate(web_element_mock)
    assert due_date.value == date(2023, 10, 5)


def test_duedate_repr() -> None:
    """Test the string representation of DueDate."""
    due_date = DueDate(DATE_STRING)
    assert repr(due_date) == "05-10-2023"


def test_duedate_equality_comparison() -> None:
    """Test equality comparison between two DueDates."""
    due_date_1 = DueDate(DATE_STRING)
    due_date_2 = DueDate(DATE_STRING)
    assert due_date_1 == due_date_2


def test_duedate_less_than_comparison() -> None:
    """Test less-than comparison between two DueDates."""
    due_date_1 = DueDate(DATE_STRING)
    due_date_2 = DueDate("2023-10-10")
    assert due_date_1 < due_date_2


def test_duedate_today_property() -> None:
    """Test the today class property of DueDate."""
    assert "today" in DueDate._today
