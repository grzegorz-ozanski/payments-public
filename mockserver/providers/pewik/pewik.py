"""PEWiK blueprint for the local mock portal."""

from __future__ import annotations

from pathlib import Path
from typing import cast
from urllib.parse import urlencode

from bs4 import BeautifulSoup, Tag
from flask import Blueprint, redirect, request, url_for
from werkzeug.wrappers import Response

from mockserver.providers._html import render_mock_html

BASE_PATH = "/pewik"
LOGIN_PATH = f"{BASE_PATH}/login"
FACTURES_PATH = f"{BASE_PATH}/trust/faktury"
BALANCES_PATH = f"{BASE_PATH}/trust/saldawpl"
MESSAGES_PATH = f"{BASE_PATH}/trust/wiadomosci"
LOGOUT_PATH = f"{BASE_PATH}/mock-logout"
DEFAULT_LOCATION = "Sezamowa 21, Gdynia"
DEFAULT_DUE_DATE = "2026-01-16"
DEFAULT_AMOUNT = "28,09"
CONTENT_DIR = Path(__file__).resolve().parent / "content"
LOGIN_HTML = CONTENT_DIR / "login.html"
PAYMENTS_HTML = CONTENT_DIR / "payments.html"

bp = Blueprint("pewik", __name__)

LOGIN_SOUP = BeautifulSoup(LOGIN_HTML.read_text(encoding="utf-8"), "html.parser")
PAYMENTS_SOUP = BeautifulSoup(PAYMENTS_HTML.read_text(encoding="utf-8"), "html.parser")


@bp.get("/")
@bp.get(BASE_PATH)
def root() -> Response:
    """Redirect the mock root to the PEWiK login page."""
    return redirect(url_for("pewik.pewik_login"))


@bp.get(LOGIN_PATH)
def pewik_login() -> str:
    """Render the login page variant selected by the optional scenario query param."""
    scenario = request.args.get("scenario", "ok")
    return _render_login_page(scenario=scenario)


@bp.post(f"{BASE_PATH}/mock-login")
@bp.post("/mock-login")
def pewik_mock_login() -> Response:
    """Validate mock credentials and redirect either to balances or back to login page."""
    scenario = request.args.get("scenario", "ok")
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if scenario == "error" or not username or not password:
        return redirect(url_for("pewik.pewik_login", scenario="error"))

    return redirect(url_for("pewik.pewik_balances", scenario=scenario))


@bp.get(FACTURES_PATH)
def pewik_factures() -> str:
    """Render the post-login page with the invoices tab active."""
    scenario = request.args.get("scenario", "ok")
    location = request.args.get("location", DEFAULT_LOCATION)
    return _render_home_page(scenario=scenario, location=location, active_tab="invoices")


@bp.get(BALANCES_PATH)
def pewik_balances() -> str:
    """Render the post-login page with balances visible for the selected location."""
    scenario = request.args.get("scenario", "ok")
    location = request.args.get("location", DEFAULT_LOCATION)
    return _render_home_page(scenario=scenario, location=location, active_tab="balances")


@bp.get(MESSAGES_PATH)
def pewik_messages() -> str:
    """Render the captured landing page shown immediately after login."""
    scenario = request.args.get("scenario", "ok")
    location = request.args.get("location", DEFAULT_LOCATION)
    return _render_home_page(scenario=scenario, location=location, active_tab="messages")


@bp.get(LOGOUT_PATH)
@bp.post(f"{BASE_PATH}/logout")
@bp.post("/logout")
def pewik_logout() -> Response:
    """Simulate logout by returning the browser to the login page."""
    return redirect(url_for("pewik.pewik_login"))


@bp.get("/img/<path:_asset_path>")
@bp.get("/js/<path:_asset_path>")
@bp.get("/css/<path:_asset_path>")
@bp.get("/webjars/<path:_asset_path>")
@bp.get("/media/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/img/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/js/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/css/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/webjars/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/media/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/public/<path:_asset_path>")
def pewik_asset(_asset_path: str) -> Response:
    """Return a tiny placeholder payload for archived PEWiK asset URLs."""
    return _placeholder_asset_response(_asset_path)


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


def _placeholder_asset_response(asset_path: str) -> Response:
    """Return an empty response with a rough content type matching the requested asset."""
    if asset_path.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
        return Response(b"", mimetype="image/png")
    if asset_path.endswith((".css", ".js", ".json", ".map", ".webmanifest", ".pdf")):
        return Response("", mimetype="text/plain")
    return Response("", mimetype="application/octet-stream")


def _render_login_page(*, scenario: str) -> str:
    """Prepare the captured login page HTML so Selenium can submit the mock form."""
    soup = _clone_soup(LOGIN_SOUP)
    _remove_external_scripts(soup)

    form = soup.select_one("form")
    if form is not None:
        form["method"] = "post"
        form["action"] = f"{BASE_PATH}/mock-login?scenario={scenario}"

    error_box = soup.select_one("div.login-info")
    if error_box is not None:
        error_box.string = "Invalid credentials" if scenario == "error" else ""

    header = soup.select_one("div.card-header")
    if header is not None and scenario == "error":
        existing = header.select_one("div.error")
        if existing is None:
            error = soup.new_tag("div", attrs={"class": "error"})
            error.string = "Nieprawidlowy login lub haslo"
            header.append(error)

    _append_helper_script(
        soup,
        """
        document.title = 'PEWiK mock - login';
        const userInput = document.getElementById('username');
        if (userInput) {
          userInput.focus();
        }
        const cookiesClose = document.getElementById('cookiesClose');
        if (cookiesClose) {
          cookiesClose.addEventListener('click', event => {
            event.preventDefault();
            document.querySelector('.panel-cookies')?.remove();
          });
        }
        """,
    )
    return render_mock_html(soup)


def _render_home_page(*, scenario: str, location: str, active_tab: str) -> str:
    """Prepare the captured post-login page and inject the controls required by the provider."""
    soup = _clone_soup(PAYMENTS_SOUP)
    _remove_external_scripts(soup)

    _configure_cookies_panel(soup)
    _configure_logout_button(soup)
    _configure_tabs(soup, scenario=scenario, location=location, active_tab=active_tab)
    _configure_location_panel(soup, scenario=scenario, location=location)
    _configure_balance_table(soup, scenario=scenario)

    _append_helper_script(
        soup,
        """
        document.title = 'PEWiK mock - home';
        const locationArrow = document.querySelector('.select2-arrow');
        const locationResults = document.querySelector('.select2-results');
        if (locationArrow && locationResults) {
          const toggleResults = event => {
            event.preventDefault();
            const isHidden = locationResults.style.display === 'none';
            locationResults.style.display = isHidden ? 'block' : 'none';
          };
          locationArrow.addEventListener('click', toggleResults);
          locationArrow.addEventListener('keydown', event => {
            if (event.key === 'Enter' || event.key === ' ') {
              toggleResults(event);
            }
          });
        }
        const cookiesClose = document.getElementById('cookiesClose');
        if (cookiesClose) {
          cookiesClose.addEventListener('click', event => {
            event.preventDefault();
            document.querySelector('.panel-cookies')?.remove();
          });
        }
        """,
    )
    return render_mock_html(soup)


def _configure_logout_button(soup: BeautifulSoup) -> None:
    """Turn the archived logout control into a simple local redirect."""
    logout_button = soup.select_one("button.btn-wyloguj")
    if logout_button is not None:
        logout_button["type"] = "button"
        logout_button["onclick"] = f"window.location.assign('{LOGOUT_PATH}');"


def _configure_tabs(soup: BeautifulSoup, *, scenario: str, location: str, active_tab: str) -> None:
    """Point the invoices and balances tabs to mock routes instead of the real portal."""
    for link in soup.select("a"):
        text = link.get_text(strip=True)
        if text == "Faktury i salda":
            link["href"] = _route_with_params(FACTURES_PATH, scenario=scenario, location=location)
            link.attrs.pop("data-toggle", None)
            parent = link.parent
            if parent is not None:
                dropdown = parent.select_one("ul.dropdown-menu")
                if dropdown is not None:
                    dropdown["style"] = "display: block;"
        elif text == "Faktury":
            link["href"] = _route_with_params(FACTURES_PATH, scenario=scenario, location=location)
            _set_active_tab(link, active_tab == "invoices")
        elif text == "Salda":
            link["href"] = _route_with_params(BALANCES_PATH, scenario=scenario, location=location)
            _set_active_tab(link, active_tab == "balances")


def _configure_location_panel(soup: BeautifulSoup, *, scenario: str, location: str) -> None:
    """Populate the customer selector with one stable mock location visible to Selenium."""
    container = soup.select_one("div.select2-container")
    if container is not None:
        classes = [value for value in _class_values(container) if value != "select2-container-disabled"]
        container["class"] = " ".join(classes)
        container["style"] = "display: inline-block; width: 100%; max-width: 38rem;"

    choice = soup.select_one("a.select2-choice")
    if choice is not None:
        choice["href"] = "#"
        choice["style"] = (
            "display: flex; align-items: stretch; justify-content: space-between; "
            "min-height: 3rem; border: 1px solid #bfc7cf; background: #fff;"
        )

    chosen = soup.select_one("span.select2-chosen")
    if chosen is not None:
        chosen["style"] = "display: block; flex: 1; padding: 0.5rem 0.75rem;"
        chosen.clear()
        wrapper = soup.new_tag("div", attrs={"class": "v-panel-podmiotow-format-selection"})
        wrapper.extend(
            [
                _text_div(soup, "Klient:"),
                _span_div(soup, "OZANSKI GRZEGORZ"),
                _text_div(soup, "Kod nabywcy:"),
                _span_div(soup, "281441"),
                _text_div(soup, "Adres:"),
                _span_div(soup, location),
            ]
        )
        chosen.append(wrapper)

    arrow = soup.select_one("span.select2-arrow")
    if arrow is not None:
        arrow["style"] = (
            "display: inline-flex; width: 2.75rem; min-width: 2.75rem; height: auto; "
            "align-items: center; justify-content: center; cursor: pointer; "
            "border-left: 1px solid #bfc7cf; background: #f3f5f7;"
        )
        arrow["role"] = "button"
        arrow["tabindex"] = "0"
        # noinspection PyUnnecessaryCast
        icon = cast(Tag | None, arrow.find("b"))
        if icon is not None:
            icon.string = "v"
            icon["style"] = "display: inline-block; font-weight: 700; line-height: 1;"

    results = soup.select_one("ul.select2-results")
    if results is not None:
        results["style"] = (
            "display: block; position: static; margin: 0.25rem 0 0; padding: 0; "
            "list-style: none; border: 1px solid #bfc7cf; background: #fff;"
        )
        results.clear()
        item = soup.new_tag("li")
        link = soup.new_tag(
            "a",
            attrs={
                "class": "select2-result",
                "href": _route_with_params(BALANCES_PATH, scenario=scenario, location=location),
                "style": "display: block; padding: 0.5rem 0.75rem;",
            },
        )
        link.string = location
        item.append(link)
        results.append(item)


def _configure_balance_table(soup: BeautifulSoup, *, scenario: str) -> None:
    """Insert a minimal balances table matching the selectors used by the provider."""
    container = soup.select_one("div.col-md-9")
    if container is None:
        return

    existing = soup.select_one("#saldaWplatyWykaz")
    if existing is not None:
        existing.decompose()

    if scenario == "timeout":
        return

    table = soup.new_tag("table", attrs={"id": "saldaWplatyWykaz", "class": "table table-brs"})
    tbody = soup.new_tag("tbody")
    table.append(tbody)

    if scenario == "no_overdue":
        row = soup.new_tag("tr")
        cell = soup.new_tag("td")
        cell.string = "Brak sald"
        row.append(cell)
        tbody.append(row)
    else:
        row = soup.new_tag("tr")
        values = ["", "", "", DEFAULT_DUE_DATE, "", DEFAULT_AMOUNT]
        for value in values:
            cell = soup.new_tag("td")
            cell.string = value
            row.append(cell)
        tbody.append(row)

    container.append(table)


def _configure_cookies_panel(soup: BeautifulSoup) -> None:
    """Keep the cookies banner visible and clickable for the provider flow."""
    cookies_panel = soup.select_one("div.panel-cookies")
    if cookies_panel is None:
        return

    cookies_panel["style"] = (
        "position: fixed; left: 1rem; right: 1rem; bottom: 1rem; z-index: 1000; "
        "display: block; padding: 0; background: #fff; border: 1px solid #bfc7cf; "
        "box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);"
    )

    close_link = cookies_panel.select_one("#cookiesClose")
    if close_link is not None:
        close_link["href"] = "#"
        close_link["role"] = "button"
        close_link["style"] = (
            "display: inline-block; padding: 0.5rem 0.75rem; cursor: pointer; "
            "background: #198754; color: #fff; text-decoration: none; border-radius: 0.25rem;"
        )


def _route_with_params(path: str, *, scenario: str, location: str) -> str:
    """Build a simple local URL preserving scenario and selected location."""
    return f"{path}?{urlencode({'scenario': scenario, 'location': location})}"


def _set_active_tab(link: Tag, is_active: bool) -> None:
    """Mark a tab item as active when the rendered page represents that section."""
    parent = link.parent
    if parent is None:
        return
    classes = [value for value in _class_values(parent) if value != "active"]
    if is_active:
        classes.append("active")
    if classes:
        parent["class"] = " ".join(classes)
    elif "class" in parent.attrs:
        del parent["class"]


def _class_values(tag: Tag) -> list[str]:
    """Return class attribute values normalized to a plain list of strings."""
    class_attr = tag.get("class")
    if class_attr is None:
        return []
    if isinstance(class_attr, str):
        return class_attr.split()
    return [value for value in class_attr if isinstance(value, str)]


def _text_div(soup: BeautifulSoup, text: str) -> Tag:
    """Create a simple div with plain text content."""
    div = soup.new_tag("div")
    div.string = text
    return div


def _span_div(soup: BeautifulSoup, text: str) -> Tag:
    """Create a div containing a nested span, matching the captured selector structure."""
    div = soup.new_tag("div")
    span = soup.new_tag("span")
    span.string = text
    div.append(span)
    return div
