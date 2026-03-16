"""OPEC blueprint for the local mock portal."""

from __future__ import annotations

from pathlib import Path
from werkzeug.wrappers import Response

from bs4 import BeautifulSoup, Tag
from flask import Blueprint, redirect, request, url_for

from mockserver.providers._html import render_mock_html

BASE_PATH = "/opec"
LOGIN_PATH = f"{BASE_PATH}/"
LOGIN_POST_PATH = f"{BASE_PATH}/Account/LogOn"
HOME_PATH = f"{BASE_PATH}/mock-home"
MONTH_PATH = f"{BASE_PATH}/mock-month"
LOGOUT_PATH = f"{BASE_PATH}/mock-logout"
ASSET_BASE_PATH = BASE_PATH
DEFAULT_AMOUNT = "2 224,08"
MATCH_DUE_DATE = "2026-03-15"
MATCH_MONTH = "2026-02"
CONTENT_DIR = Path(__file__).resolve().parent / "content"
LOGIN_HTML = CONTENT_DIR / "login.html"
HOME_HTML = CONTENT_DIR / "home.html"
MONTH_HTML = CONTENT_DIR / "month.html"

bp = Blueprint("opec", __name__)

LOGIN_SOUP = BeautifulSoup(LOGIN_HTML.read_text(encoding="utf-8"), "html.parser")
HOME_SOUP = BeautifulSoup(HOME_HTML.read_text(encoding="utf-8"), "html.parser")
MONTH_SOUP = BeautifulSoup(MONTH_HTML.read_text(encoding="utf-8"), "html.parser")


@bp.get("/")
def root() -> str | Response:
    """Render the OPEC login page at the mock root."""
    return _render_login_page(scenario=request.args.get("scenario", "ok"))


@bp.get(BASE_PATH)
@bp.get(LOGIN_PATH)
def opec_login() -> str:
    """Render the login page variant selected by the optional scenario query param."""
    return _render_login_page(scenario=request.args.get("scenario", "ok"))


@bp.post(LOGIN_POST_PATH)
def opec_mock_login() -> Response:
    """Validate mock credentials and redirect either to the home page or error state."""
    scenario = request.args.get("scenario", "ok")
    username = request.form.get("UserName", "")
    password = request.form.get("Password", "")

    if scenario == "error" or not username or not password:
        return redirect(url_for("opec.opec_login", scenario="error"))

    return redirect(url_for("opec.opec_home", scenario=scenario))


@bp.get(HOME_PATH)
def opec_home() -> str:
    """Render the account card page with amount and months history."""
    return _render_home_page(scenario=request.args.get("scenario", "ok"))


@bp.get(MONTH_PATH)
def opec_month() -> str:
    """Render a single month financial operations page."""
    return _render_month_page(scenario=request.args.get("scenario", "ok"))


@bp.get(LOGOUT_PATH)
def opec_logout() -> Response:
    """Simulate logout by returning the browser to the login page."""
    return redirect(url_for("opec.opec_login"))


@bp.get(f"{ASSET_BASE_PATH}/<path:_asset_path>")
def opec_asset(_asset_path: str) -> Response:
    """Return a tiny placeholder payload for archived OPEC asset URLs."""
    if _asset_path.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
        return Response(b"", mimetype="image/png")
    if _asset_path.endswith((".css", ".js")):
        return Response("", mimetype="text/plain")
    return Response("", mimetype="application/octet-stream")


def _remove_external_scripts(soup: BeautifulSoup) -> None:
    """Strip original external scripts so the archived HTML stays static inside the mock."""
    for script in soup.find_all("script", src=True):
        script.decompose()


def _append_helper_script(soup: BeautifulSoup, script_content: str) -> None:
    """Append inline JavaScript used to adapt a captured page to mock-server behavior."""
    body = soup.body
    assert body is not None
    tag = soup.new_tag("script")
    tag.string = script_content
    body.append(tag)


def _clone_soup(source: BeautifulSoup) -> BeautifulSoup:
    """Return a fresh soup instance to avoid mutating the shared HTML template."""
    return BeautifulSoup(str(source), "html.parser")


def _render_login_page(*, scenario: str) -> str:
    """Prepare the captured login page HTML so Selenium can submit the mock form."""
    soup = _clone_soup(LOGIN_SOUP)
    _remove_external_scripts(soup)

    form = soup.select_one("form")
    if form is not None:
        form["method"] = "post"
        form["action"] = f"{LOGIN_POST_PATH}?scenario={scenario}"

    summary = soup.select_one("div.validation-summary-valid, div.validation-summary-errors")
    if summary is not None and scenario == "error":
        summary["class"] = "validation-summary-errors"
        items = summary.select("li")
        if items:
            items[0]["style"] = ""
            items[0].string = "Nieprawidlowy login lub haslo"

    _append_helper_script(
        soup,
        """
        document.title = 'OPEC mock - login';
        document.getElementById('UserName')?.focus();
        """,
    )
    return render_mock_html(soup)


def _render_home_page(*, scenario: str) -> str:
    """Prepare the object card page with amount and clickable history rows."""
    soup = _clone_soup(HOME_SOUP)
    _remove_external_scripts(soup)

    _configure_logout(soup)
    _configure_amount(soup, scenario=scenario)
    _configure_months_table(soup, scenario=scenario)

    _append_helper_script(
        soup,
        """
        document.title = 'OPEC mock - home';
        """,
    )
    return render_mock_html(soup)


def _render_month_page(*, scenario: str) -> str:
    """Prepare the month details page with a payments table matching the provider selectors."""
    soup = _clone_soup(MONTH_SOUP)
    _remove_external_scripts(soup)

    _configure_logout(soup)
    _configure_month_details(soup, scenario=scenario)

    _append_helper_script(
        soup,
        """
        document.title = 'OPEC mock - month';
        """,
    )
    return render_mock_html(soup)


def _configure_logout(soup: BeautifulSoup) -> None:
    """Turn the archived logout control into a simple local redirect."""
    logout_item = soup.find(lambda tag: isinstance(tag, Tag) and "Wyloguj" in " ".join(tag.stripped_strings))
    if isinstance(logout_item, Tag):
        logout_item["onclick"] = f"window.location.assign('{LOGOUT_PATH}');"
        logout_item["role"] = "button"
        logout_item["tabindex"] = "0"


def _configure_amount(soup: BeautifulSoup, *, scenario: str) -> None:
    """Adjust the total amount block for success and zero-balance scenarios."""
    amount = soup.select_one("sh-blok > div:nth-of-type(2) div.shh-flex-row > span.shf-s30")
    if amount is None:
        return
    amount.string = "0,00" if scenario == "no_overdue" else DEFAULT_AMOUNT


def _configure_months_table(soup: BeautifulSoup, *, scenario: str) -> None:
    """Keep the financial history table present and make month rows navigate to mock month details."""
    rows = soup.select("h2 + p + table.sh-table tbody tr.exe")
    if not rows:
        return

    for index, row in enumerate(rows):
        row["onclick"] = f"window.location.assign('{MONTH_PATH}?scenario={scenario}&index={index}');"
        row["onkeydown"] = (
            "if (event.key === 'Enter' || event.key === ' ') "
            f"{{ window.location.assign('{MONTH_PATH}?scenario={scenario}&index={index}'); }}"
        )

    if scenario == "timeout":
        amount_block = soup.select_one("sh-blok > div:nth-of-type(2)")
        if amount_block is not None:
            amount_block.decompose()

    if scenario == "no_overdue":
        first_row = rows[0]
        amount_cell = first_row.select_one('td[data-label="Obciążenia"], td[data-label="ObciÄ…ĹĽenia"]')
        if amount_cell is not None:
            amount_cell.string = "0,00"


def _configure_month_details(soup: BeautifulSoup, *, scenario: str) -> None:
    """Adjust the monthly payments table to either contain a matching due date or simulate missing data."""
    header = soup.select_one("h2")
    if header is not None:
        header.string = f"Zapisy finansowe w miesiacu {MATCH_MONTH}"

    table = soup.select_one("h2 + style + small + table, h2 + small + table, table.sh-table")
    if table is None:
        return

    rows = table.select("tbody tr")
    if len(rows) < 2:
        return

    charge_row = rows[-1]
    charge_date = charge_row.select_one('td[data-label="Data płatności"], td[data-label="Data pĹ‚atnoĹ›ci"]')
    charge_amount = charge_row.select_one('td[data-label="Obciążenia"], td[data-label="ObciÄ…ĹĽenia"]')
    payment_amount = charge_row.select_one('td[data-label="Wpłaty"], td[data-label="WpĹ‚aty"]')

    if charge_date is not None:
        charge_date.string = "" if scenario == "timeout" else MATCH_DUE_DATE
    if charge_amount is not None:
        charge_amount.string = "0,00" if scenario == "no_overdue" else DEFAULT_AMOUNT.replace("\u00a0", "")
    if payment_amount is not None:
        payment_amount.string = "0,00"

    back_button = soup.find(string=lambda text: isinstance(text, str) and "Karta obiektu" in text)
    if back_button is not None and isinstance(back_button.parent, Tag):
        back_button.parent["onclick"] = "window.history.back();"
