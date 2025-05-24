"""
    Main application entry point
"""
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
    """
    Parses command-line arguments and returns a Namespace object containing
    the parsed arguments and their values. The parser provides options for
    verbosity, headless mode, trace logging, provider selection, and output
    file specification, among others. This function is designed to be
    flexible and robust for handling various runtime configurations.

    :raises SystemExit: If the command-line arguments are invalid or the
        `-h`/`--help` flag is provided.
    :return: A Namespace object containing parsed arguments and their values.
    :rtype: Namespace
    """
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Enable verbose mode')
    parser.add_argument('-l', '--headless', default=None, type=str_to_bool, help='Toggle headless browser')
    parser.add_argument('-t', '--trace', default=False, action='store_true', help='Save trace logs')
    parser.add_argument('-p', '--provider', help='Run for single provider only')
    parser.add_argument('-o', '--output', help='Store retrieved payments in output file')

    return parser.parse_args()


def main() -> None:
    """
    This function serves as the main entry point for the application. It initializes
    the runtime environment, parses command-line arguments, configures logging and
    debugging settings, processes payment collections via specified providers, and
    outputs the results to either the console or a file if an output file is specified.
    The execution is tracked for timing and provides feedback throughout its workflow.

    :return: None
    """
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
