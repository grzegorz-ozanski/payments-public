"""
    Dumps credentials into .env file
"""

import argparse

import keyring

import providers


def parse_args() -> argparse.Namespace:
    """
    Parse program arguments
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(description='Prepare an .env file to be used e.g. in GitHub Secrets')
    parser.add_argument('-o', '--output', default='.env', help='output env file')

    return parser.parse_args()


def main() -> None:
    """
    Main function
    """
    args = parse_args()
    with open(args.output, "w") as file:
        for provider in [provider.lower() for provider in providers.__all__ if provider.lower() != 'providerslist']:
            for cred in ('username', 'password'):
                print(f'{provider.upper()}_{cred.upper()}={keyring.get_password(provider, cred)}', file=file)


if __name__ == '__main__':
    main()
