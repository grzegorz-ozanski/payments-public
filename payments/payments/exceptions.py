"""
    Program-wide exeptions
"""


class PaymentError(Exception):
    """
    Base class for any payment error
    """
    def __init__(self, message: str) -> None:
        self.reason = message
        super().__init__(message)
