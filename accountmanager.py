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

    def sort_key(self, account_name: str) -> int:
        try:
            # TODO restrict bact to '=='
            return [account for account in self.accounts if account.name in account_name][0].key
        except IndexError:
            return 0
