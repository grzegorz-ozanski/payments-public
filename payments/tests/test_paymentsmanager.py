"""
    PaymentsManager class unittests
"""
from browser import BrowserOptions
from mocks import DummyProvider, MockBrowser
from payments import Payment, PaymentsList, PaymentsManager


def test_collect_payments_combines_results() -> None:
    payments = [
        Payment('p1', 'L1', '2025-06-01', '123'),
        Payment('p2', 'L2', '2025-06-02', '456'),
    ]
    providers = [DummyProvider('p1', ('L1',), [payments[0]]),
                 DummyProvider('p2', ('L2',), [payments[1]])]

    mgr = PaymentsManager(providers)
    result = str(mgr.collect(lambda: BrowserOptions(__file__, False, False, ''),
                             MockBrowser))
    assert 'p1' in result
    assert 'p2' in result
    assert '123' in result
    assert '456' in result


def test_payments_to_str_padding() -> None:
    from payments.payments.payment import Payment

    payments = [
        Payment('p', 'loc', '2025-06-01', '1'),
        Payment('prov', 'location', '2025-06-02', '100')
    ]
    result = str(PaymentsList(payments))

    lines = result.strip().splitlines()
    assert len(lines) == 2
    assert lines[0].startswith('p ')  # padded
    assert lines[1].startswith('prov')
