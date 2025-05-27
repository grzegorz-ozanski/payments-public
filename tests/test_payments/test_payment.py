from unittest.mock import patch

from payments.payment import Payment


@patch("payments.payment.log.debug")
def test_payment_initialization(mock_log_debug) -> None:
    """Test initialization of Payment with valid and invalid values."""
    payment = Payment(provider="TestProvider", location="TestLocation", due_date="12-10-2023", amount="123,45")
    assert payment.provider == "TestProvider"
    assert payment.location == "TestLocation"
    assert str(payment.due_date) == "12-10-2023"
    assert str(payment.amount) == "123,45"
    mock_log_debug.assert_called_once()


def test_payment_to_padded_string() -> None:
    """Test the to_padded_string method."""
    payment = Payment(provider="ProviderA", location="LocationA", due_date="14-10-2023", amount="456,78")
    padded_str = payment.to_padded_string(padding=[10, 10, 10])
    assert "ProviderA " in padded_str
    assert "456,78 " in padded_str
    assert "LocationA " in padded_str
    assert "14-10-2023" in padded_str
    assert padded_str == 'ProviderA  456,78     LocationA  14-10-2023'
    assert (payment.to_padded_string(padding=[20, 20, 20]) ==
            'ProviderA            456,78               LocationA            14-10-2023')
    assert payment.to_padded_string(padding=[10, 10]) == 'ProviderA  456,78     LocationA 14-10-2023'
    assert payment.to_padded_string(padding=[10]) == 'ProviderA  456,78 LocationA 14-10-2023'
    assert payment.to_padded_string() == 'ProviderA456,78 LocationA 14-10-2023'


