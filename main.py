import platform
from dataclasses import dataclass, field

import providers
import logging
from browser import Browser
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
    browser_options: list[str] = field(default_factory=list)
    save_trace_logs: bool = False
    output_file: str = ''


def parse_args() -> Options:
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='verbose')
    parser.add_argument('-l', '--headless', choices=['TRUE', 'FALSE'], nargs='?', help='headless browser')
    parser.add_argument('-c', '--chromedriver', help='chromedriver URL')
    parser.add_argument('-t', '--trace', default=False, action='store_true', help='trace logs')
    parser.add_argument('-o', '--output', help='output file')

    args = parser.parse_args()

    options = Options()

    running_under_debugger = sys.gettrace() is not None
    if args.verbose:
        options.verbose = args.verbose
    else:
        options.verbose = running_under_debugger
    if args.headless is not None:
        value = args.headless.strip().lower()
        if value == 'true':
            headless = True
        elif value == 'false':
            headless = False
        else:
            raise Exception(f"Unrecognized bool value for '--headless': {value}")
    else:
        headless = not running_under_debugger

    chromedriver = None
    if args.chromedriver is not None:
        chromedriver = args.chromedriver

    options.browser_options = ["disable-gpu", "disable-webgl", "window-size=1200,1100",
                               "log-level=3", "no-sandbox", "disable-dev-shm-usage", "enable-unsafe-swiftshader",
                               ]

    if headless:
        options.browser_options.append("headless")

    if not options.verbose:
        logging.disable(logging.CRITICAL)

    if chromedriver is None:
        system = platform.system()
        if system == 'Darwin':  # running on macOS
            options.url = "***REMOVED***"
        elif system == 'Windows' or system == 'Linux':
            chromedriver_root = pathlib.Path(__file__).parent.joinpath('chromedriver').resolve(True)
            options.url = f"{chromedriver_root.joinpath('chromedriver')}"
            options.binary_location = str(chromedriver_root.joinpath("chrome").joinpath("chrome"))
            if system == 'Windows':
                options.url += ".exe"
                options.binary_location += ".exe"
        else:
            raise NotImplementedError(f"'{system}' is not supported.")
    else:
        options.url = chromedriver

    options.save_trace_logs = args.trace
    options.output_file = args.output
    return options

def main():
    begin_time = datetime.datetime.now()
    print(f"Starting at {datetime.datetime.now()}")


    hodowlana = Location('Hodowlana')
    bryla = Location('Bryla')
    sezamowa = Location('Sezamowa')

    providers_list = providers.ProvidersList(
                providers.Pgnig(sezamowa),
                providers.Energa(hodowlana, bryla, sezamowa),
                providers.Actum(hodowlana),
                providers.Multimedia({'90': hodowlana, '77': sezamowa}),
                providers.Pewik(sezamowa),
                providers.Opec(sezamowa),
                providers.Nordhome(bryla)
            )

    options = parse_args()
    browser = Browser(chrome_path=options.url,
                      options=options.browser_options,
                      chrome_binary_location=options.binary_location,
                      save_trace_logs=options.save_trace_logs)
    payments = PaymentsManager(browser, providers_list, options.verbose)
    payments.collect()
    payments.print()
    if options.output_file:
        payments.write(options.output_file)

    end_time = datetime.datetime.now()
    print("Finished at %s" % end_time)
    print("Took %s " % (end_time - begin_time))


if __name__ == '__main__':
    main()
