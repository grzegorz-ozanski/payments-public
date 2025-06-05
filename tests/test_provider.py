"""
    Basic unittests for the provider module.
"""
from typing import Any
from unittest.mock import patch

import pytest
from _pytest.capture import CaptureFixture
from selenium.webdriver.common.by import By

from mocks import DummyProvider, MockBrowser
from payments import DueDate, Amount
from providers.provider import PageElement
from providers.provider import Provider


def test_location_order_map() -> None:
    """Test if the location order map is generated correctly."""
    provider = Provider(
        url="",
        locations=("X", "Y", "Z"),
        user_input=PageElement(By.ID, "user"),
        password_input=PageElement(By.ID, "pass")
    )
    assert provider._location_order == {"X": 0, "Y": 1, "Z": 2}


def test_get_location_known() -> None:
    """Test if a known location is correctly extracted from a string."""
    provider = Provider(
        url="",
        locations=("Sezamowa", "Bryla"),
        user_input=PageElement(By.ID, "u"),
        password_input=PageElement(By.ID, "p")
    )
    assert provider._get_location("Faktura: Sezamowa 123") == "Sezamowa"


def test_get_location_unknown_logs_error(caplog: pytest.LogCaptureFixture) -> None:
    """Test if an unknown location raises an error and logs appropriately."""
    provider = Provider(
        url="",
        locations=("Bryla",),
        user_input=PageElement(By.ID, "u"),
        password_input=PageElement(By.ID, "p")
    )
    with caplog.at_level("ERROR", logger="providers.provider"):
        with pytest.raises(RuntimeError):
            provider._get_location("Nieznana")
        assert "Cannot find location for provider" in caplog.text


@patch("providers.provider.Credential.get", return_value="dummy")
def test_payments_fetch_error(mock_cred: Any, capsys: CaptureFixture[str]) -> None:
    """Test whether payments are sorted according to known locations."""
    assert mock_cred is not None
    provider = DummyProvider(
        locations=("Sezamowa", "Bryla", "Hodowlana"),
    )
    with patch.object(provider, "_fetch_payments", side_effect=RuntimeError("Awaria")):
        payments = provider.get_payments(MockBrowser())
    assert [p.location for p in payments] == ["Sezamowa", "Bryla", "Hodowlana"]
    assert all(p.due_date == DueDate.unknown and
               p.amount == Amount.unknown and
               p.provider == DummyProvider.default_name for p in payments)
    out, _ = capsys.readouterr()
    assert "Cannot get payments for service dummyprovider!" in out


@patch("providers.provider.Credential.get", return_value="dummy")
def test_payment_sorting(mock_cred: Any) -> None:
    """Test whether payments are sorted according to known locations."""
    assert mock_cred is not None
    provider = DummyProvider(
        locations=("Sezamowa", "Bryla", "Hodowlana"),
    )
    payments = provider.get_payments(MockBrowser())
    assert [p.location for p in payments] == ["Sezamowa", "Bryla", "Nieznana"]
