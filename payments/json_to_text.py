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

    def _get_item(self, provider: str, location: str | None = None) -> JsonDict | None:
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
                if location is None:
                    # noinspection PyUnnecessaryCast
                    return cast(JsonDict, provider_data)
                for item in provider_data.get('payments', []):
                    if item.get('location', '') == location:
                        return cast(JsonDict, item)
        if location is None:
            return None
        raise RuntimeError(f'Cannot find updated data for provider {provider}, location {location} '
                           f'in files {self.names}!')

    def get_provider(self, provider: str) -> JsonDict | None:
        """
        Get the updated data the given provider.
        :param provider: provider name
        :return: JSON item for the given provider
        """
        return self._get_item(provider)


    def get_provider_location(self, provider: str, location: str) -> JsonDict | None:
        """
        Get the updated data the given provider and location.
        :param provider: provider name
        :param location: location name
        :return: JSON item for the given provider and location
        """
        return self._get_item(provider, location)


def parse_args() -> argparse.Namespace:
    """
    Parses command line arguments.
    :return: Namespace containing parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description='Convert payments JSON output into text formatted like PaymentsList.__str__.'
    )
    parser.add_argument('-i', '--input', required=True,
                        help='Input JSON file path')
    parser.add_argument('-u', '--updated', required=False, nargs='+', default=[],
                        help='Path to the JSON files with updated data')
    parser.add_argument('-o', '--output', required=False,
                        help='Output text file path')
    parser.add_argument('-j', '--json-output', required=False,
                        help='Output merged JSON file path')
    return parser.parse_args()

def main() -> int:
    """
    Main program function.
    :return: status code
    """
    args = parse_args()

    with open(args.input, encoding='utf-8') as stream:
        data = cast(JsonDict,json.load(stream))

    updated_data = UpdatedData(args.updated)
    payments: list[Payment] = []

    for provider, provider_data in data.items():
        if updated_provider_data := updated_data.get_provider(provider):
            provider_data['time'] = updated_provider_data.get('time', provider_data.get('time', ''))

        for index, item in enumerate(provider_data.get('payments', [])):
            location = item.get('location', '')
            if args.updated and item.get('status', '') == 'failed':
                updated_item = updated_data.get_provider_location(provider, location)
                provider_data['payments'][index] = updated_item
                item = updated_item
            payments.append(
                Payment(
                    provider=provider,
                    location=location,
                    due_date=item.get('due_date', ''),
                    amount=item.get('amount', ''),
                    comment=item.get('comment', '')
                )
            )

    provider_timings = {
        provider: float(provider_data.get('time', 0) or 0)
        for provider, provider_data in data.items()
    }
    output = f'{PaymentsList(payments, provider_timings)}\n'

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as stream:
            stream.write(output)
    else:
        print(output)

    if args.json_output:
        with open(args.json_output, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
