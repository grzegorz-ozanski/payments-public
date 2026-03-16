"""Shared HTML helpers for mock providers."""

from __future__ import annotations

from bs4 import BeautifulSoup

MOJIBAKE_REPLACEMENTS = (
    ("\u00c4\u2026", "\u0105"),
    ("\u00c4\u201e", "\u0104"),
    ("\u00c4\u2021", "\u0107"),
    ("\u00c4\u2020", "\u0106"),
    ("\u00c4\u2122", "\u0119"),
    ("\u00c4\u02dc", "\u0118"),
    ("\u0139\u201a", "\u0142"),
    ("\u0139\u017d", "\u0141"),
    ("\u00c5\u201e", "\u0144"),
    ("\u00c5\u0192", "\u0143"),
    ("\u00c3\u00b3", "\u00f3"),
    ("\u00c3\u201c", "\u00d3"),
    ("\u0139\u203a", "\u015b"),
    ("\u0139\u0160", "\u015a"),
    ("\u00c5\u00ba", "\u017a"),
    ("\u00c5\u00b9", "\u0179"),
    ("\u0139\u00bc", "\u017c"),
    ("\u0139\u00bb", "\u017b"),
    ("\u0139\u0081", "\u0141"),
    ("\u0102\u201c", "\u00d3"),
)


def render_mock_html(soup: BeautifulSoup) -> str:
    """Serialize mock HTML and normalize common mojibake left in archived captures."""
    html = str(soup)
    for broken, fixed in MOJIBAKE_REPLACEMENTS:
        html = html.replace(broken, fixed)
    return html
