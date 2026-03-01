"""
    Application entrypoint unittests
"""

import argparse
import sys
import tempfile
from unittest.mock import patch, MagicMock

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from payments import main


def setup_args(monkeypatch: MonkeyPatch, output: str = '') -> None:
    """
    Setup test environment for main() function
    :param output: output file name
    :param monkeypatch:
    """
    monkeypatch.setattr('sys.argv', ['prog'])
    monkeypatch.setattr(main, 'parse_args', lambda: argparse.Namespace(
        clear_profile_on_exit=False,
        chrome_path=None,
        headless=True,
        output=output,
        persistent_profile_dir='',
        provider='',
        trace=False,
        verbose=False,
        sort=None,
        filter=None,
        json=None,
        print_json=False
    ))
    monkeypatch.setattr(main, 'is_debugger_active', lambda: False)


def test_parse_args_defaults(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(sys, 'argv', ['prog'])
    args = main.parse_args()
    assert args.verbose is False
    assert args.trace is False
    assert args.provider == ''


def test_main_prints_output(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
    setup_args(monkeypatch)
    with (patch('payments.main.PaymentsManager') as mock_mgr_cls,
          patch('payments.main.LookupList') as mock_lookup):
        dummy_mgr = MagicMock()
        dummy_mgr.collect.return_value = 'TEST_OUTPUT'
        mock_mgr_cls.return_value = dummy_mgr
        mock_lookup.return_value.__getitem__.return_value = ['provider']

        main.main()
        out = capsys.readouterr().out
        assert 'TEST_OUTPUT' in out


def test_main_writes_to_file(monkeypatch: MonkeyPatch) -> None:
    dummy_file = tempfile.NamedTemporaryFile(delete=False)
    dummy_path = dummy_file.name
    dummy_file.close()
    setup_args(monkeypatch, dummy_path)

    with (patch('payments.main.PaymentsManager') as mock_mgr_cls,
          patch('payments.main.LookupList') as mock_lookup):
        mgr = MagicMock()
        mgr.collect.return_value = 'WYNIK'
        mock_mgr_cls.return_value = mgr
        mock_lookup.return_value.__getitem__.return_value = ['provider']

        main.main()

    with open(dummy_path, encoding='utf-8') as f:
        assert f.read().strip() == 'WYNIK'
