import argparse
import datetime
import logging
import os
import sys
from argparse import Namespace

from str_to_bool import str_to_bool

import providers
from browser import Browser, BrowserOptions, setup_logging
from payments import PaymentsManager
from lookuplist import LookupList

log = setup_logging(__name__)


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='verbose')
    parser.add_argument('-l', '--headless', default=None, type=str_to_bool, help='headless browser')
    parser.add_argument('-t', '--trace', default=False, action='store_true', help='trace logs')
    parser.add_argument('-p', '--provider', help='single provider')
    parser.add_argument('-o', '--output', help='output file')

    return parser.parse_args()


def main() -> None:
    begin_time = datetime.datetime.now()
    print(f"Starting at {datetime.datetime.now()}")

    args = parse_args()
    log.debug(f'Called with arguments: {args}')
    running_under_debugger = sys.gettrace() is not None or "VSCODE_DEBUGPY_ADAPTER_ENDPOINTS" in os.environ

    # If -v/--verbose argument was provided, use it to toggle verbosity;
    # otherwise, be turn verbosity on when running under the debugger, and off when otherwise
    verbose = args.verbose if args.verbose else running_under_debugger

    # If -l/--headless argument was provided, use it to set headless mode on/off;
    # otherwise, use headed browser when running under the debugger and headless one when otherwise
    headless = args.headless if args.headless is not None else not running_under_debugger

    options = BrowserOptions(__file__, headless, args.trace)

    # Turn off logging if verbosity is off
    if not verbose:
        logging.disable(logging.CRITICAL)

    hodowlana = 'Hodowlana'
    bryla = 'Bryla'
    sezamowa = 'Sezamowa'

    providers_list = LookupList(
        providers.Pgnig(sezamowa),
        providers.Energa(hodowlana, bryla, sezamowa),
        providers.Actum(hodowlana),
        providers.Multimedia({'90': hodowlana, '77': sezamowa}),
        providers.Pewik(sezamowa),
        providers.Opec(sezamowa),
        providers.Nordhome(bryla)
    )

    payments = PaymentsManager(providers_list[args.provider if args.provider else ''])
    output = payments.collect_payments(Browser(options))
    # payments.collect_fake_payments(r'.github\data\test_output.txt')
    print(output)
    if args.output:
        with open(args.output, 'w', encoding="utf-8") as stream:
            print(output, file=stream)

    end_time = datetime.datetime.now()
    print("Finished at %s" % end_time)
    print("Took %s " % (end_time - begin_time))


if __name__ == '__main__':
    main()
