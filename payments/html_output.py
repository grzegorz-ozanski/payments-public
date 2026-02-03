"""
    Combines payment script output and browser trace logs into a single HTML file.
"""
from __future__ import annotations

import argparse
import html
import re
from collections import defaultdict
from pathlib import Path

SEPARATOR_RE = re.compile(r'^\*{5,}\s*$')  # '*****' (i więcej), sama linia
NAME_RE = re.compile(r'^Processing service\s+(.+?)\.\.\.\s*$')
HTML_HEADER = '''<!DOCTYPE html>
<html>
  <head/>
  <body>
'''
HTML_FOOTER = '''\
  </body>
</html>
'''


def parse_log(path: str | Path) -> dict[str, str]:
    """
    Convert large monolithic browser log file into a dictionary of per-provider chunks
    :param path: log file path
    :return: dictionary where keys are provider names and values are part of the browser log relevant to each provider
    """
    out: dict[str, str] = {}

    first_separator_found = False
    current_name: str | None = None
    current_lines: list[str] = []
    separators_count = 0

    def flush() -> None:
        """
        Helper function to store accumulated lines in an output dictionary under the proper key
        (currently processed provider)
        """
        nonlocal current_name, current_lines
        if current_name is not None:
            out[current_name] = '\n'.join(current_lines)
        current_name = None
        current_lines = []

    with open(path, encoding='utf-8', errors='replace') as f:
        it = iter(f)

        for line in it:
            line = line.rstrip('\n')

            # Discard everything before first separator
            if not first_separator_found:
                if SEPARATOR_RE.match(line):
                    first_separator_found = True
                else:
                    continue

            # Count all separators but flush only on even ones, indicating the start of a new provider data, while
            # odd separators are just the ending of the header
            if SEPARATOR_RE.match(line):
                separators_count += 1
                if separators_count % 2 == 1:
                    flush()
            m = NAME_RE.match(line)
            if m:
                current_name = m.group(1).strip()

            current_lines.append(line)

    flush()
    return out


def parse_output(path: str | Path) -> dict[str, str]:
    """
    Converts payment output data into a dictionary of per-provider chunks
    :param path: payment output file path
    :return: dictionary where keys are provider names and values are the respective payment values
    """
    # We need list of strings as each provider may have more than one line
    out: dict[str, list[str]] = defaultdict(list)

    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f.readlines():
            line = line.rstrip()
            if not line:
                continue

            provider = line.split(maxsplit=1)[0]
            out[provider].append(line)

    return {k: '\n'.join(v) for k, v in out.items()}


def encode(string: str, replace_newline: bool = False) -> str:
    """
    Encodes string for proper HTML representation
    :param string: string to be converted
    :param replace_newline: True if new line character should be replaced by <br/> tag
    :return: encoded string
    """
    result = html.escape(string)
    return result.replace('\n', '<br/>') if replace_newline else result


def html_output(log_file: Path | str,
                output_file: Path | str,
                html_file: Path | str,
                add_header: bool = True) -> None:
    """
    Generates HTML code of <details>-<summary> tags, where <summary> contains the payment value for the provider,
    and <details> a part of browser's logs relevant for this provider
    :param log_file: browser log file
    :param output_file: payments output file
    :param html_file: output HTML file
    :param add_header: True if the whole HTML document should be generated,
    False if only the internal <details>-<summary>
    """
    log_file_path = Path(log_file)
    html_file_path = Path(html_file)
    output_file_path = Path(output_file)
    logs = parse_log(log_file_path)
    output = parse_output(output_file_path)

    with open(html_file_path, 'w', encoding='utf-8') as f:
        if add_header:
            f.write(HTML_HEADER)
        for provider in output.keys():
            # For proper display in GitHub workflow summary it's essential that
            # <details> tag starts at column 0
            f.write(f'''\
<details>
    <summary>{encode(output[provider], True)}</summary>
    <pre>{logs[provider]}</pre>
</details>''')
        if add_header:
            f.write(HTML_FOOTER)


def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments and returns a Namespace object containing
    the parsed arguments and their values.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Combines payment script output and trace logs into a single HTML file."
        )
    )

    parser.add_argument('-H', '--html-file', required=True, type=Path,
                        help='target HTML file path')
    parser.add_argument('-l', '--log-file', required=True, type=Path,
                        help='log file path')
    parser.add_argument('-o', '--output-file', required=True, type=Path,
                        help='payments output file path')
    parser.add_argument('-n', '--no-header', required=False, action='store_true', default=False,
                        help='do not add HTML header (for embedding in GitHub workflow summary)')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    html_output(args.log_file, args.output_file, args.html_file, not args.no_header)
