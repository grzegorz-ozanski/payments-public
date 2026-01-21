"""
    Main application entry point
"""
import argparse
import datetime
import logging
import os
import sys
from argparse import Namespace
from enum import StrEnum

from str_to_bool import str_to_bool

import providers
from browser import BrowserOptions, setup_logging
from lookuplist import LookupList
from payments import PaymentsManager

log = setup_logging(__name__)

class DebugFlags(StrEnum):
    """
    Application debugging flags
    """
    BROWSER_PROFILE = 'bp'
    MULTIMEDIA_LOGIN = 'ml'


def is_debugger_active() -> bool:
    """
    Return True if a debugger is currently attached.
    """
    return sys.gettrace() is not None or 'VSCODE_DEBUGPY_ADAPTER_ENDPOINTS' in os.environ


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

    parser.add_argument('-c', '--clear-profile-on-exit', default=False, action='store_true',
                        help='Clear browser user profile on exit')
    parser.add_argument('-l', '--headless', default=None, type=str_to_bool,
                        help='Toggle headless browser mode (default: auto)')
    parser.add_argument('-d', '--debug',
                        help='Comma-separated list of debug flags (implicates verbose mode)'
                             f'({DebugFlags.BROWSER_PROFILE}: browser profile creation debugging, '
                             f'{DebugFlags.MULTIMEDIA_LOGIN}: Multimedia provider login debugging)',)
    parser.add_argument('-o', '--output',
                        help='Write retrieved payments to output file (UTF-8)')
    parser.add_argument('-p', '--provider', default='',
                        help='Run for single provider only (name must match one from the list)')
    parser.add_argument('--persistent-profile-dir', default='',
                        help='Persisten browser profile directory location (default: user temp directory)')
    parser.add_argument('-t', '--trace', default=False, action='store_true',
                        help='Enable trace logging for browser actions')
    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help='Enable verbose mode (show debug logs)')
    parser.add_argument('--chrome-path',
                        help='Use provided Chrome binary instead of automatically downloading')

    args = parser.parse_args()
    if args.debug:
        args.verbose = True
        for flag in [f.strip() for f in args.debug.split(',')]:
            if flag == DebugFlags.BROWSER_PROFILE:
                os.environ['BROWSER_DEBUG_PROFILE'] = '1'
            elif flag == DebugFlags.MULTIMEDIA_LOGIN:
                os.environ['PAYMENTS_DEBUG_MULTIMEDIA_LOGIN'] = '1'
            else:
                log.error(f'Unrecognized debug flag: {flag}')
                parser.print_help()
                exit(1)

    return args


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
    print(f'Starting at {datetime.datetime.now()}')

    args = parse_args()
    running_under_debugger = is_debugger_active()

    # If -v/--verbose argument was provided, use it to toggle verbosity;
    # otherwise, be turn verbosity on when running under the debugger, and off when otherwise
    verbose = args.verbose if args.verbose else running_under_debugger

    # Turn off logging if verbosity is off
    if not verbose:
        logging.disable(logging.CRITICAL)

    log.debug(f'Called with arguments: {args}')
    # If -l/--headless argument was provided, use it to set headless mode on/off;
    # otherwise, use headed browser when running under the debugger and headless one when otherwise
    headless = args.headless if args.headless is not None else not running_under_debugger

    options = BrowserOptions(__file__,
                             headless,
                             args.trace,
                             args.chrome_path,
                             not args.clear_profile_on_exit,
                             args.persistent_profile_dir)

    if args.trace and not verbose:
        print('ℹ️ Trace enabled, but verbose mode is off — no logs will be shown on console')

    hodowlana = 'Hodowlana'
    bryla = 'Bryla'
    sezamowa = 'Sezamowa'

    providers_list = LookupList[providers.Provider](
        providers.Pgnig(sezamowa),
        providers.Energa(hodowlana, bryla, sezamowa),
        providers.Actum(hodowlana),
        providers.Multimedia({'90': hodowlana, '77': sezamowa}),
        providers.Pewik(sezamowa),
        providers.Opec2(sezamowa),
        providers.Nordhome(bryla),
        providers.Vectra(sezamowa)
    )

    payments = PaymentsManager(providers_list['' or args.provider.lower()])
    payments.collect_payments(options)
    output = payments.to_string()
    # payments.collect_fake_payments(r'.github\data\test_output.txt')
    print(output)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as stream:
            print(output, file=stream)

    end_time = datetime.datetime.now()
    print('Finished at %s' % end_time)
    print('Took %s ' % (end_time - begin_time))

if __name__ == '__main__':
    main()
