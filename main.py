import platform

import services
import logging
from log import setup_logging
from browser import Browser
from payments import Payments
import sys
import datetime
import pathlib
import argparse


def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-v', '--verbose', default=None, action='store_true', help='verbose')
    parser.add_argument('-l', '--headless', choices=['TRUE', 'FALSE'], nargs='?', help='headless browser')
    parser.add_argument('-c', '--chromedriver', help='chromedriver URL')

    args = parser.parse_args()

    print(args)
    begin_time = datetime.datetime.now()
    print("Starting at %s" % datetime.datetime.now())

    if args.verbose is not None:
        verbose = args.verbose
    else:
        verbose = sys.gettrace() is not None
    if args.headless is not None:
        value = "-l=FALSE".split('=')[1].strip().lower()
        if value == 'true':
            headless = True
        elif value == 'false':
            headless = False
        else:
            raise Exception(f"Unrecognized bool value for '--headless': {value}")
    else:
        headless = not verbose

    chromedriver = None
    if args.chromedriver is not None:
         chromedriver = args.chromedriver

    params = {"options": ["disable-gpu", "window-size=1200,1100"]}

    if headless:
        params["options"].append("headless")
    log = setup_logging(__name__, 'DEBUG')

    if not verbose:
        logging.disable(logging.CRITICAL)

    if chromedriver is None:
        system = platform.system()
        if system == 'Darwin':  # running on macOS
            params["url"] = "file://***REMOVED***"
        elif system == 'Windows' or system == 'Linux':
            chromedriver_root = pathlib.Path(__file__).parent.joinpath('chromedriver').resolve(True)
            params["url"] = f"file://{chromedriver_root.joinpath('chromedriver')}"
            if system == 'Windows':
                params["url"] += ".exe"
                params["binary_location"] = str(chromedriver_root.joinpath("chrome").joinpath("chrome.exe"))
        else:
            raise NotImplementedError(f"'{system}' is not supported.")
    else:
        params["url"] = chromedriver

    items = [
                # services.Pgnig("FILTERED_SERVICE_LOGIN"),
                # services.Energa("FILTERED_SERVICE_LOGIN"),
                services.Actum("FILTERED_SERVICE_LOGIN"),
                # services.Multimedia("FILTERED_SERVICE_LOGIN"),
                # services.Pewik("FILTERED_SERVICE_LOGIN"),
                # services.Opec('FILTERED_SERVICE_LOGIN')
                # services.Nordhome('FILTERED_SERVICE_LOGIN')
            ]

    Payments(Browser(**params), items, verbose).collect()

    end_time = datetime.datetime.now()
    print("Finished at %s" % end_time)
    print("Took %s " % (end_time - begin_time))


if __name__ == '__main__':
    main()
