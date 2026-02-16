"""
    Main application entry point
"""
import argparse
import ctypes
import datetime
import logging
import os
import sys
from argparse import Namespace
from enum import StrEnum
from functools import cache
from typing import Sequence

from str_to_bool import str_to_bool

from payments import providers
from browser import BrowserOptions, setup_logging
from payments.lookuplist import LookupList
from payments.payments import PaymentsManager, Payment

log = setup_logging(__name__)


class DebugFlags(StrEnum):
    """
    Application debugging flags
    """
    BROWSER_PROFILE = 'bp'
    MULTIMEDIA_LOGIN = 'ml'


@cache
def is_debugger_active() -> bool:
    """
    Return True if a debugger is currently attached.
    """
    return sys.gettrace() is not None or 'VSCODE_DEBUGPY_ADAPTER_ENDPOINTS' in os.environ


def is_elevated() -> bool:
    """
    Returns True if current process has admin/root privileges.
    Cross-platform:
      - Windows: checks token membership in Administrators group.
      - POSIX: checks effective UID == 0.
    """
    if sys.platform == "win32":
        try:
            # noinspection PyUnresolvedReferences
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError, ValueError, TypeError, ctypes.ArgumentError):
            # Conservative fallback: if we can't tell, assume not elevated
            return False
    else:
        # Linux/macOS/*BSD
        geteuid = getattr(os, "geteuid", None)
        if geteuid is None:
            # Very unusual POSIX env without geteuid; fallback to uid if available
            getuid = getattr(os, "getuid", None)
            return bool(getuid and getuid() == 0)
        return bool(geteuid() == 0)


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
        )
    )

    parser.add_argument('-c', '--clear-profile-on-exit', default=False, action='store_true',
                        help='Clear browser user profile on exit')
    parser.add_argument('-l', '--headless', default=None, type=str_to_bool,
                        help='Toggle headless browser mode (default: auto)')
    parser.add_argument('-d', '--debug',
                        help='Comma-separated list of debug flags (implicates verbose mode)'
                             f'({DebugFlags.BROWSER_PROFILE}: browser profile creation debugging, '
                             f'{DebugFlags.MULTIMEDIA_LOGIN}: Multimedia provider login debugging)', )
    parser.add_argument('-o', '--output',
                        help='Write retrieved payments to output file (UTF-8)')
    parser.add_argument('-p', '--provider', default='',
                        help='Run for single provider only', choices=providers.all_lower())
    parser.add_argument('--persistent-profile-dir', default='',
                        help='Persisten browser profile directory location (default: user temp directory)')
    parser.add_argument('-t', '--trace', default=False, action='store_true',
                        help='Enable trace logging for browser actions')
    parser.add_argument('-r', '--reverse', default=False, action='store_true',
                        help='Sort in reverse order')
    parser.add_argument('-s', '--sort', default=None,
                        help='Sort payments by the provided key', choices=Payment.SORT_KEYS)
    parser.add_argument('-f', '--filter', default=None,
                        help=f'Filter (<=, <, =, !=, >, >=) by provided keys ({Payment.SORT_KEYS})')
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
                log.error('Unrecognized debug flag: %s', flag)
                parser.print_help()
                exit(1)

    return args


def main() -> int:
    """
    This function serves as the main entry point for the application. It initializes
    the runtime environment, parses command-line arguments, configures logging and
    debugging settings, processes payment collections via specified providers, and
    outputs the results to either the console or a file if an output file is specified.
    The execution is tracked for timing and provides feedback throughout its workflow.

    :return: exit code
    """
    if os.getenv('RUNNER_VERSION') and is_elevated():
        raise SystemExit('Covardly refusing to run with elevated privileges (admin/root)'
                         ' in GitHub runner environment')
    begin_time = datetime.datetime.now()
    print(f'Starting at {datetime.datetime.now()}')

    args = parse_args()

    # If -v/--verbose argument was provided, use it to toggle verbosity;
    # otherwise, be turn verbosity on when running under the debugger, and off when otherwise
    verbose = args.verbose if args.verbose else is_debugger_active()

    # Turn off logging if verbosity is off
    if not verbose:
        logging.disable(logging.CRITICAL)

    log.debug('Called with arguments: %s', args)
    # If -l/--headless argument was provided, use it to set headless mode on/off;
    # otherwise, use headed browser when running under the debugger and headless one when otherwise
    headless = args.headless if args.headless is not None else not is_debugger_active()

    def browser_options() -> BrowserOptions:
        """
        Browser options factory
        """
        return BrowserOptions(__file__,
                              headless,
                              args.trace,
                              args.chrome_path,
                              not args.clear_profile_on_exit,
                              args.persistent_profile_dir,
                              renderer_timeout=30)

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
        providers.Opec(sezamowa),
        providers.Nordhome(bryla),
        providers.Vectra(sezamowa)
    )

    selected_providers: providers.Provider | Sequence[providers.Provider]
    if args_provider := args.provider.lower():
        selected_providers = providers_list[args_provider]
        if not selected_providers:
            print(f'ERROR: No providers can be found for provided argument "{args_provider}"')
    else:
        selected_providers = providers_list['']
    payments = PaymentsManager(selected_providers)
    output = payments.collect(browser_options)
    if args.sort:
        output = output.sort(args.sort, args.reverse)
    if args.filter:
        output = output.where(args.filter)
    print(output)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as stream:
            print(output, file=stream)

    end_time = datetime.datetime.now()
    print('Finished at %s' % end_time)
    print('Took %s ' % (end_time - begin_time))
    return 0


if __name__ == '__main__':
    main()
