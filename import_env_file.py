"""
    Imports credentials from .env file to keyring
"""

import argparse
import re

import keyring


def parse_args() -> argparse.Namespace:
    """
    Parse program arguments
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(description='Prepare an .env file to be used e.g. in GitHub Secrets')
    parser.add_argument('-i', '--input', default='.env', help='input env file')

    return parser.parse_args()


def main() -> None:
    """
    Main function
    """
    args = parse_args()
    with open(args.input) as file:
        for provider, cred, value in [re.split('[=_]', item) for item in file.readlines()]:
            keyring.set_password(provider.lower(), cred.lower(), value)


if __name__ == '__main__':
    main()
