"""
    Convert payments JSON output into padded text output.
"""
import argparse
import json
import logging
from typing import Any, TypeAlias, cast

from payments.payments.payment import Payment
from payments.payments.paymentslist import PaymentsList

logging.getLogger('payments.payments.payment').setLevel(logging.INFO)

JsonDict: TypeAlias = dict[str, Any]

class UpdatedData:
    """
    JSON files with updated payments data.
    """
    def __init__(self, names: list[str]) -> None:
        self.names = names
        self.data: list[JsonDict]  = []

    def _load(self) -> None:
        for filename in self.names:
            with open(filename, encoding='utf-8') as stream:
                self.data.append(cast(JsonDict, json.load(stream)))

    def get_item(self, provider: str, location: str) -> JsonDict:
        """
        Gets the updated data item for the given provider and location.
        :param provider: provider name
        :param location: location
        :return: JSON item for the given provider and location
        """
        if not self.data:
            self._load()
        for json_data in self.data:
            if provider_data := json_data.get(provider):
                for item in provider_data.get('payments', []):
                    if item.get('location', '') == location:
                        return cast(JsonDict, item)
        raise RuntimeError(f'Cannot find updated data for provider {provider}, location {location} '
                           f'in files {self.names}!')


def parse_args() -> argparse.Namespace:
    """
    Parses command line arguments.
    :return: Namespace containing parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description='Convert payments JSON output into text formatted like PaymentsList.__str__.'
    )
    parser.add_argument('-i', '--input', required=True, nargs='*', help='Input JSON file path')
    parser.add_argument('-o', '--output', required=False, help='Output text file path')
    return parser.parse_args()

def main() -> int:
    """
    Main program function.
    :return: status code
    """
    args = parse_args()

    with open(args.input[0], encoding='utf-8') as stream:
        data = json.load(stream)

    updated_data = UpdatedData(args.input[1:])
    payments: list[Payment] = []
    provider_timings: dict[str, float] = {}

    for provider, provider_data in data.items():
        provider_timings[provider] = float(provider_data.get('time', 0) or 0)
        for item in provider_data.get('payments', []):
            location = item.get('location', '')
            if item.get('status', '') == 'failed':
                item = updated_data.get_item(provider, location)
            payments.append(
                Payment(
                    provider=provider,
                    location=location,
                    due_date=item.get('due_date', ''),
                    amount=item.get('amount', ''),
                    comment=item.get('comment', '')
                )
            )

    output = f'{PaymentsList(payments, provider_timings)}\n'

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as stream:
            stream.write(output)
    else:
        print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
