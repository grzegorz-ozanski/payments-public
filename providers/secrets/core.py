"""
    Credentials module
"""
from os import environ
import keyring


class Secret:
    """
    Retrieve credential from environment or system keyring.

    Priority: environment variable > keyring service.
    """
    def __init__(self, service_name: str, name: str, env_upper: bool = True):
        self.keyring_service = service_name
        self.keyring = name
        self.environ = f'{service_name}_{name}'
        if env_upper:
            self.environ = self.environ.upper()

    def get(self) -> str | None:
        """Return the credential value or raise if not found."""
        if value := environ.get(self.environ):
            return value
        value = keyring.get_password(self.keyring_service, self.keyring)
        if value and value.strip():
            return value.strip()
        raise RuntimeError(f'"{self.keyring}" not found in env {self.environ} '
                           f'or keyring service {self.keyring_service}!')


class Secrets:
    """
    Stores credentials values (username and password) described by tags provided.
    """
    def __init__(self, name: str, username_tag: str, password_tag: str):
        self.username = Secret(name, username_tag)
        self.password = Secret(name, password_tag)
