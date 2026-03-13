""" Collected payments list """
import operator
import re
from functools import cache
from typing import Any

from payments.payments.payment import Payment


class PaymentsList:
    """
        List of collected payments
    """

    def __init__(self, payments: list[Payment], provider_timings: dict[str, float] | None = None) -> None:
        self.payments: list[Payment] = payments
        self.provider_timings = provider_timings

    def copy(self) -> 'PaymentsList':
        """
        Creates a copy of the object
        """
        return PaymentsList(self.payments.copy())

    def sort(self, sort_key: str, reverse: bool = False) -> 'PaymentsList':
        """
        Sorts collected payments
        :param sort_key: sort key or None if no sorting should be performed
        :param reverse: reverse sort order
        :return PaymentsManager self object for pipelining
        """
        return PaymentsList(sorted(self.payments,
                                   key=lambda p: getattr(p, sort_key),
                                   reverse=reverse))

    def where(self, filter_string: str) -> 'PaymentsList':
        """
        Filters collected payments by provided criteria
        :param filter_string:
        :return PaymentsManager self object for pipelining
        """
        ops = {
            "<": operator.lt,
            "<=": operator.le,
            ">": operator.gt,
            ">=": operator.ge,
            "==": operator.eq,
            "!=": operator.ne
        }
        m = re.match(rf'(\S+)\s*({"|".join(ops.keys())})\s*(\S+)', filter_string)
        if m:
            return PaymentsList(list(filter(lambda p: ops[m[2]](getattr(p, m[1]), m[3]),
                                            self.payments)))
        return self.copy()

    @cache
    def json(self) -> dict[str, Any]:
        """
        Converts payments list to JSON
        :return: payments list as JSON-serializable dict
        """
        result: dict[str, Any] = {}
        for payment in self.payments:
            if payment.provider not in result:
                result[payment.provider] = {
                    'payments': [],
                    'time': f'{self.provider_timings[payment.provider]:.2f}' if self.provider_timings else ''
                }
            result[payment.provider]['payments'].append({
                'location': payment.location,
                'amount': payment.amount.value,
                'due_date': payment.due_date.value.strftime('%d-%m-%Y'),
                'comment': payment.comment,
                'status': 'failure' if payment.amount.is_unknown() else 'success',
                'reason': ''
            })
        return result

    def __str__(self) -> str:
        """
        Export all payments to string, adding padding
        """
        max_len_provider = 0
        max_len_amount = 0
        max_len_location = 0

        for payment in self.payments:
            max_len_provider = max(max_len_provider, len(payment.provider))
            max_len_amount = max(max_len_amount, len(str(payment.amount)))
            max_len_location = max(max_len_location, len(payment.location))
        return '\n'.join([payment.to_padded_string([max_len_provider, max_len_amount, max_len_location])
                          for payment in self.payments])
