from __future__ import annotations

import html
import os
import re
from collections import defaultdict
from pathlib import Path

SEPARATOR_RE = re.compile(r'^\*{5,}\s*$')  # '*****' (i więcej), sama linia
NAME_RE = re.compile(r'^Processing service\s+(.+?)\.\.\.\s*$')
HTML_HEADER = """<!DOCTYPE html>
<html>
  <head>
    <style>
      /* Ukrycie trójkąta <summary> */
      summary {
        list-style: none;
        cursor: pointer;
      }

      summary::-webkit-details-marker {
        display: none;
      }
      .log {
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas,
                     "Liberation Mono", monospace;
        font-size: 16px;
        white-space: pre;   /* domyślnie, ale jasno */
      }
    </style>
  </head>
<body>
"""
HTML_FOOTER = """</body>
</html>"""

def parse_log(path: str | Path) -> dict[str, str]:
    out: dict[str, str] = {}

    first_separator_found = False
    current_name: str | None = None
    current_lines: list[str] = []
    separators_count = 0

    def flush() -> None:
        nonlocal current_name, current_lines
        if current_name is not None:
            out[current_name] = '<br/>'.join(current_lines)
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

            # Count all separators but flush only on even ones (those indicate the start of a new block);
            # odd separators are just headers closings
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
    out: dict[str, list[str]] = defaultdict(list)

    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f.readlines():
            line = line.rstrip()
            if not line:
                continue

            provider = line.split(maxsplit=1)[0]
            out[provider].append(line)

    return {k: '\n'.join(v) for k, v in out.items()}

def encode(string: str) -> str:
    return html.escape(string)

def html_output(env_variable_name: str,
                output_file: Path | str,
                html_log_file: Path | str) -> None:
    log_file = os.environ.get(env_variable_name)
    if log_file is None:
        return
    logs = parse_log(log_file)
    output = parse_output(output_file)

    with open(html_log_file, 'w') as f:
        f.write(HTML_HEADER)
        for provider in output.keys():
            f.write(f'''<details>
                <summary class="log">{encode(output[provider])}</summary>
                <code>{logs[provider]}</code>
            </details>''')
        f.write(HTML_FOOTER)

if __name__ == '__main__':
    html_output('BROWSER_LOG_FILENAME', 'run/log.txt', 'log.html')
