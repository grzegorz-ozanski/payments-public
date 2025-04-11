import platform
from dataclasses import dataclass, field
from typing import List

import services
import logging
from log import setup_logging
from browser import Browser
from paymentsmanager import PaymentsManager
from accountmanager import AccountsManager
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


def parse_args() -> Options:
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-v', '--verbose', default=None, action='store_true', help='verbose')
    parser.add_argument('-l', '--headless', choices=['TRUE', 'FALSE'], nargs='?', help='headless browser')
    parser.add_argument('-c', '--chromedriver', help='chromedriver URL')

    args = parser.parse_args()

    print(args)
    options = Options()

    if args.verbose is not None:
        options.verbose = args.verbose
    else:
        options.verbose = sys.gettrace() is not None
    if args.headless is not None:
        value = "-l=FALSE".split('=')[1].strip().lower()
        if value == 'true':
            headless = True
        elif value == 'false':
            headless = False
        else:
            raise Exception(f"Unrecognized bool value for '--headless': {value}")
    else:
        headless = not options.verbose

    chromedriver = None
    if args.chromedriver is not None:
        chromedriver = args.chromedriver

    options.browser_options = ["disable-gpu", "window-size=1200,1100"]

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

    return options

def main():
    begin_time = datetime.datetime.now()
    print("Starting at %s" % datetime.datetime.now())


    accounts = AccountsManager().add('Hodowlana').add('Bryla').add('Sezamowa')
    items = [
                services.Pgnig("FILTERED_SERVICE_LOGIN"),   # 0 - fixed
                services.Energa("FILTERED_SERVICE_LOGIN"),  # 1
                services.Actum("FILTERED_SERVICE_LOGIN"),               # 2 - fixed
                services.Multimedia("FILTERED_SERVICE_LOGIN"),        # 3 - fixed
                services.Pewik("FILTERED_SERVICE_LOGIN"),   # 4 - fixed
                services.Opec('FILTERED_SERVICE_LOGIN'),              # 5 - fixed
                services.Nordhome('FILTERED_SERVICE_LOGIN')             # 6 - fixed
            ]

    options = parse_args()
    browser = Browser(url=options.url,
                      options=options.browser_options,
                      binary_location=options.binary_location)
    payments = PaymentsManager(browser, [items[0], items[3]], accounts, options.verbose)
    payments.collect()
    payments.print()

    end_time = datetime.datetime.now()
    print("Finished at %s" % end_time)
    print("Took %s " % (end_time - begin_time))


if __name__ == '__main__':
    main()
