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
from lookuplist import LookupList
from payments import PaymentsManager

log = setup_logging(__name__)


def is_debugger_active() -> bool:
    """
    Return True if a debugger is currently attached.
    """
    return sys.gettrace() is not None or "VSCODE_DEBUGPY_ADAPTER_ENDPOINTS" in os.environ


def parse_args() -> Namespace:
    """
    Parses command-line arguments and returns a Namespace object containing
    the parsed arguments and their values.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Automatically collects payment information from supported providers' web portals "
            "using browser automation (Selenium). Supports headless mode, trace logging, "
            "and output to file."
        ),
        epilog=f"Available providers: {', '.join(providers.__all__)}"
    )

    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help='Enable verbose mode (show debug logs)')
    parser.add_argument('-l', '--headless', default=None, type=str_to_bool,
                        help='Toggle headless browser mode (default: auto)')
    parser.add_argument('-t', '--trace', default=False, action='store_true',
                        help='Enable trace logging for browser actions')
    parser.add_argument('-p', '--provider', default='',
                        help='Run for single provider only (name must match one from the list)')
    parser.add_argument('-o', '--output',
                        help='Write retrieved payments to output file (UTF-8)')

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
    running_under_debugger = is_debugger_active()

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

    if args.trace and not verbose:
        print("ℹ️ Trace enabled, but verbose mode is off — no logs will be shown on console")

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

    payments = PaymentsManager(providers_list[args.provider.lower() or 'energa'])
    payments.collect_payments(Browser(options))
    output = payments.to_string()
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
