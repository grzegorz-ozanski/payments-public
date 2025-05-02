import platform
from dataclasses import dataclass, field
from typing import List

import providers
import logging
from browser import Browser, setup_logging
from payments import PaymentsManager
from locations import Location
import sys
import datetime
import pathlib
import argparse


@dataclass
class Options:
    verbose: bool = False
    url: str = ''
    binary_location: str = ''
    browser_options: List[str] = field(default_factory=list)
    save_trace_logs: bool = False


def parse_args() -> Options:
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='verbose')
    parser.add_argument('-l', '--headless', choices=['TRUE', 'FALSE'], nargs='?', help='headless browser')
    parser.add_argument('-c', '--chromedriver', help='chromedriver URL')
    parser.add_argument('-t', '--trace', default=False, action='store_true', help='trace logs')

    args = parser.parse_args()

    options = Options()

    if args.verbose:
        options.verbose = args.verbose
    else:
        options.verbose = sys.gettrace() is not None
    headless = True
    if args.headless is not None:
        value = args.headless.strip().lower()
        if value == 'true':
            headless = True
        elif value == 'false':
            headless = False
        else:
            raise Exception(f"Unrecognized bool value for '--headless': {value}")

    chromedriver = None
    if args.chromedriver is not None:
        chromedriver = args.chromedriver

    options.browser_options = ["disable-gpu", "window-size=1200,1100",
                               "log-level=3", "no-sandbox", "disable-dev-shm-usage", "enable-unsafe-swiftshader",
                               ]

    if headless:
        options.browser_options.append("headless")
    _ = setup_logging(__name__, 'DEBUG')

    if not options.verbose:
        logging.disable(logging.CRITICAL)

    if chromedriver is None:
        system = platform.system()
        if system == 'Darwin':  # running on macOS
            options.url = "file://***REMOVED***"
        elif system == 'Windows' or system == 'Linux':
            chromedriver_root = pathlib.Path(__file__).parent.joinpath('chromedriver').resolve(True)
            options.url = f"file://{chromedriver_root.joinpath('chromedriver')}"
            if system == 'Windows':
                options.url += ".exe"
                options.binary_location = str(chromedriver_root.joinpath("chrome").joinpath("chrome.exe"))
        else:
            raise NotImplementedError(f"'{system}' is not supported.")
    else:
        options.url = chromedriver

    options.save_trace_logs = args.trace
    return options

def main():
    begin_time = datetime.datetime.now()
    print(f"Starting at {datetime.datetime.now()}")


    hodowlana = Location('Hodowlana')
    bryla = Location('Bryla')
    sezamowa = Location('Sezamowa')

    providers_list = [
                providers.Pgnig(sezamowa),                                # 0
                providers.Energa(hodowlana, bryla, sezamowa),    # 1
                providers.Actum(hodowlana),                               # 2
                providers.Multimedia({'90': hodowlana, '77': sezamowa}),  # 3
                providers.Pewik(sezamowa),                                # 4
                providers.Opec(sezamowa),                                 # 5
                providers.Nordhome(bryla)                                 # 6
            ]

    options = parse_args()
    browser = Browser(url=options.url,
                      options=options.browser_options,
                      binary_location=options.binary_location,
                      save_trace_logs=options.save_trace_logs)
    payments = PaymentsManager(browser, providers_list, options.verbose)
    payments.collect()
    payments.print()

    end_time = datetime.datetime.now()
    print("Finished at %s" % end_time)
    print("Took %s " % (end_time - begin_time))


if __name__ == '__main__':
    main()
