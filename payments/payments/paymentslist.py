""" Collected payments list """
import operator
import re

from payments.payments.payment import Payment


class PaymentsList:
    """
        List of collected payments
    """

    def __init__(self, payments: list[Payment]) -> None:
        self.payments: list[Payment] = payments

    def copy(self) -> 'PaymentsList':
        return PaymentsList(self.payments.copy())

    def sort(self,
             sort_key: str | None = None,
             reverse: bool = False) -> 'PaymentsList':
        """
        Sorts collected payments
        :param sort_key: sort key or None if no sorting should be performed
        :param reverse: reverse sort order
        :return PaymentsManager self object for pipelining
        """
        if sort_key:
            return PaymentsList(sorted(self.payments,
                                       key=lambda p: getattr(p, sort_key),
                                       reverse=reverse))
        return self.copy()

    def where(self,
              filter_string: str | None = None) -> 'PaymentsList':
        """
        Filters collected payments by provided criteria
        :param filter_string:
        :return PaymentsManager self object for pipelining
        """
        if filter_string:
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


