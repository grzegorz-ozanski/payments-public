from dataclasses import dataclass, field
from typing import List

@dataclass
class Account:
    name: str
    key: int


@dataclass
class AccountsManager:
    accounts: List[Account] = field(default_factory=list)

    def add(self, account_name: str):
        self.accounts.append(Account(account_name, len(self.accounts) + 1))
        return self

    def get(self, account_name: str) -> Account | None:
        try:
            # TODO restrict bact to '=='
            return [account for account in self.accounts if account.name in account_name][0]
        except IndexError:
            return None

    def sort_key(self, account_name: str) -> int:
        try:
            # TODO restrict bact to '=='
            return self.get(account_name).key
        except IndexError:
            return 0
