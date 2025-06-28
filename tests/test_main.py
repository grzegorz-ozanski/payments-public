"""
    Application entrypoint unittests
"""

import argparse
import sys
import tempfile
from unittest.mock import patch, MagicMock

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

import main

def setup_args(monkeypatch: MonkeyPatch, output: str = ''):
    """
    Setup test environment for main() function
    :param output: output file name
    :param monkeypatch:
    """
    monkeypatch.setattr("sys.argv", ["prog"])
    monkeypatch.setattr(main, "parse_args", lambda: argparse.Namespace(
        verbose=False, headless=True, trace=False, provider='', output=output, chrome_path=None
    ))
    monkeypatch.setattr(main, "is_debugger_active", lambda: False)


def test_parse_args_defaults(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["prog"])
    args = main.parse_args()
    assert args.verbose is False
    assert args.trace is False
    assert args.provider == ''


def test_main_prints_output(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
    setup_args(monkeypatch)
    with patch("main.PaymentsManager") as mock_mgr_cls, patch("main.Browser"), patch("main.LookupList") as mock_lookup:
        dummy_mgr = MagicMock()
        dummy_mgr.to_string.return_value = "TEST_OUTPUT"
        mock_mgr_cls.return_value = dummy_mgr
        mock_lookup.return_value.__getitem__.return_value = ["provider"]

        main.main()
        out = capsys.readouterr().out
        assert "TEST_OUTPUT" in out


def test_main_writes_to_file(monkeypatch: MonkeyPatch) -> None:
    dummy_file = tempfile.NamedTemporaryFile(delete=False)
    dummy_path = dummy_file.name
    dummy_file.close()
    setup_args(monkeypatch, dummy_path)

    with patch("main.PaymentsManager") as mock_mgr_cls, patch("main.Browser"), patch("main.LookupList") as mock_lookup:
        mgr = MagicMock()
        mgr.to_string.return_value = "WYNIK"
        mock_mgr_cls.return_value = mgr
        mock_lookup.return_value.__getitem__.return_value = ["provider"]

        main.main()

    with open(dummy_path, encoding="utf-8") as f:
        assert f.read().strip() == "WYNIK"
