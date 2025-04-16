class Account:
    next_key: int = 0

    def __init__(self, name: str):
        self.name = name
        self.key = Account.next_key
        Account.next_key += 1
