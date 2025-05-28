"""
    Amount class unittests
"""
import pytest
from selenium.webdriver.remote.webelement import WebElement

from payments.payment import Amount


def test_amount_init_with_float() -> None:
    """Test initializing Amount with a float value."""
    amount = Amount(1234.56)
    assert amount.whole == "1234"
    assert amount.decimal == "56"


def test_amount_init_with_string() -> None:
    """Test initializing Amount with a string value."""
    amount = Amount("1 234.56 zł")
    assert amount.whole == "1234"
    assert amount.decimal == "56"


def test_amount_init_with_malformed_string() -> None:
    """Test initializing Amount with a string value."""
    with pytest.raises(ValueError, match=r"too many values to unpack \(expected 2\)"):
        amount = Amount("1,234.56")
        assert not hasattr(amount, "whole")
        assert not hasattr(amount, "decimal")


def test_amount_init_with_webelement(mocker) -> None:
    """Test initializing Amount with a WebElement value."""
    web_element_mock = mocker.Mock(spec=WebElement)
    web_element_mock.text = "1 234.56"
    amount = Amount(web_element_mock)
    assert amount.whole == "1234"
    assert amount.decimal == "56"


def test_amount_repr() -> None:
    """Test the string representation of the Amount."""
    amount = Amount("1 234.56")
    assert repr(amount) == "1234,56"


def test_amount_format() -> None:
    """Test formatting of Amount."""
    amount = Amount("1 234.56")
    assert format(amount, ">10") == "   1234,56"


def test_amount_to_float() -> None:
    """Test conversion of Amount to float."""
    amount = Amount("1234,56")
    assert float(amount) == 1234.56


def test_amount_is_zero() -> None:
    """Test the is_zero class method."""
    assert Amount.is_zero("0,00") is True
    assert Amount.is_zero("0,00 zł") is True
    assert Amount.is_zero("Płatność 0,00 zł") is True
    assert Amount.is_zero("123,45") is False
