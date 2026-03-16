"""Vectra blueprint for the local mock portal."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag
from flask import Blueprint, redirect, request, url_for
from werkzeug.wrappers import Response

from mockserver.providers._html import render_mock_html

BASE_PATH = "/vectra"
LOGIN_PATH = f"{BASE_PATH}/"
LOGIN_POST_PATH = f"{BASE_PATH}/mock-login"
HOME_PATH = f"{BASE_PATH}/mock-home"
INVOICES_PATH = f"{BASE_PATH}/mock-invoices"
TWO_FACTOR_PATH = f"{BASE_PATH}/mock-2fa"
LOGOUT_PATH = f"{BASE_PATH}/mock-logout"

CONTENT_DIR = Path(__file__).resolve().parent / "content"
LOGIN_HTML = CONTENT_DIR / "login.html"
HOME_HTML = CONTENT_DIR / "home.html"

bp = Blueprint("vectra", __name__)

LOGIN_SOUP = BeautifulSoup(LOGIN_HTML.read_text(encoding="utf-8"), "html.parser")
HOME_SOUP = BeautifulSoup(HOME_HTML.read_text(encoding="utf-8"), "html.parser")

DEFAULT_INVOICES = (
    {"number": "FV/03/2026/001", "issued": "10.03.2026", "amount": "9,99 zł", "due_date": "20.03.2026"},
)
MULTI_INVOICES = (
    {"number": "FV/03/2026/001", "issued": "10.03.2026", "amount": "4,99 zł", "due_date": "20.03.2026"},
    {"number": "FV/03/2026/002", "issued": "10.03.2026", "amount": "5,00 zł", "due_date": "22.03.2026"},
)
TOTAL_AMOUNT = "9,99 zł"
ZERO_AMOUNT = "0,00 zł"


@bp.get(BASE_PATH)
@bp.get(LOGIN_PATH)
def vectra_login() -> str:
    """Render the Vectra login page for the selected scenario."""
    return _render_login_page(scenario=request.args.get("scenario", "ok"))


@bp.post(LOGIN_POST_PATH)
def vectra_mock_login() -> Response:
    """Validate mock credentials and redirect to the selected post-login scenario."""
    scenario = request.args.get("scenario", "ok")
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if scenario == "error" or not username or not password:
        return redirect(url_for("vectra.vectra_login", scenario="error"))
    if scenario == "2fa":
        return redirect(url_for("vectra.vectra_two_factor", scenario=scenario))
    return redirect(url_for("vectra.vectra_home", scenario=scenario))


@bp.get(HOME_PATH)
def vectra_home() -> str:
    """Render the post-login Vectra dashboard."""
    return _render_home_page(scenario=request.args.get("scenario", "ok"))


@bp.get(INVOICES_PATH)
def vectra_invoices() -> str:
    """Render the invoices table used by the provider to sum unpaid bills."""
    return _render_invoices_page(scenario=request.args.get("scenario", "ok"))


@bp.get(TWO_FACTOR_PATH)
def vectra_two_factor() -> str:
    """Render a simple 2FA prompt used by the headless login failure path."""
    return _render_two_factor_page()


@bp.get(LOGOUT_PATH)
def vectra_logout() -> Response:
    """Return the browser to the login page."""
    return redirect(url_for("vectra.vectra_login"))


@bp.get("/assets/<path:_asset_path>")
@bp.get("/webres/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/assets/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/webres/<path:_asset_path>")
def vectra_asset(_asset_path: str) -> Response:
    """Return a tiny placeholder payload for archived Vectra asset URLs."""
    if _asset_path.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
        return Response(b"", mimetype="image/png")
    if _asset_path.endswith((".css", ".js", ".json", ".map", ".woff", ".woff2", ".ttf", ".pdf")):
        return Response("", mimetype="text/plain")
    return Response("", mimetype="application/octet-stream")


def _clone_soup(source: BeautifulSoup) -> BeautifulSoup:
    """Return a fresh soup instance to avoid mutating the shared HTML template."""
    return BeautifulSoup(str(source), "html.parser")


def _remove_dynamic_content(soup: BeautifulSoup) -> None:
    """Drop archived scripts and overlays so the mock page stays static."""
    for element in soup.find_all(["script", "iframe", "noscript", "style"]):
        element.decompose()
    for selector in (
        "#g-recaptcha-response",
        "#cookiescript_injected",
        "#cookiescript_injected_wrapper",
        "#usercom-widget",
        "#ue_popups",
        ".snackbar-queue",
        ".fab-container",
        ".grecaptcha-badge",
    ):
        for element in soup.select(selector):
            element.decompose()


def _append_helper_script(soup: BeautifulSoup, script_content: str) -> None:
    """Append inline JavaScript used to adapt a captured page to mock behavior."""
    body = soup.body
    assert body is not None
    tag = soup.new_tag("script")
    tag.string = script_content
    body.append(tag)


def _rewrite_asset_paths(soup: BeautifulSoup) -> None:
    """Rewrite archived absolute asset URLs so they resolve through the mock."""
    for tag in soup.find_all(src=True):
        if not isinstance(tag, Tag):
            continue
        src = tag.get("src")
        if isinstance(src, str) and src.startswith("/assets/"):
            tag["src"] = f"{BASE_PATH}{src}"
        elif isinstance(src, str) and src.startswith("/webres/"):
            tag["src"] = f"{BASE_PATH}{src}"
    for tag in soup.find_all(href=True):
        if not isinstance(tag, Tag):
            continue
        href = tag.get("href")
        if isinstance(href, str) and href.startswith("/assets/"):
            tag["href"] = f"{BASE_PATH}{href}"
        elif isinstance(href, str) and href.startswith("/webres/"):
            tag["href"] = f"{BASE_PATH}{href}"


def _render_login_page(*, scenario: str) -> str:
    """Prepare the captured two-stage login page for mock use."""
    soup = _clone_soup(LOGIN_SOUP)
    _remove_dynamic_content(soup)
    _rewrite_asset_paths(soup)

    username_input = soup.select_one('input[name="username"]')
    password_input = soup.select_one('input[name="password"]')
    if isinstance(password_input, Tag):
        password_wrapper = password_input.find_parent(class_="v-input")
        if isinstance(password_wrapper, Tag):
            password_wrapper["style"] = "display: none;"

    continue_button = None
    for button in soup.find_all("button"):
        if "Kontynuuj" in " ".join(button.stripped_strings):
            continue_button = button
            break
    if isinstance(continue_button, Tag):
        continue_button["type"] = "button"
        continue_button.attrs.pop("disabled", None)
        continue_button["id"] = "vectra-continue"

    error_box = soup.select_one(".v-messages__message")
    if isinstance(error_box, Tag):
        error_box.string = "Nieprawidłowy login lub hasło" if scenario == "error" else ""

    if isinstance(username_input, Tag):
        username_wrapper = username_input.find_parent(class_="v-input")
        if isinstance(username_wrapper, Tag):
            form = soup.new_tag(
                "form",
                attrs={"id": "vectra-login-form", "method": "post", "action": f"{LOGIN_POST_PATH}?scenario={scenario}"},
            )
            username_wrapper.wrap(form)
            live_form = soup.select_one("#vectra-login-form")
            if isinstance(live_form, Tag):
                if isinstance(password_input, Tag):
                    wrapper = password_input.find_parent(class_="v-input")
                    if isinstance(wrapper, Tag):
                        live_form.append(wrapper.extract())
                if isinstance(continue_button, Tag):
                    live_form.append(continue_button.extract())

    cookie_button = soup.find(id="cookiescript_accept")
    if cookie_button is None:
        body = soup.body
        assert body is not None
        cookie_button = soup.new_tag(
            "button",
            attrs={
                "id": "cookiescript_accept",
                "type": "button",
                "style": "position:fixed; right:16px; bottom:16px; z-index:1000;",
            },
        )
        cookie_button.string = "Rozumiem"
        body.append(cookie_button)

    _append_helper_script(
        soup,
        """
        document.title = 'Vectra mock - login';
        const username = document.querySelector('input[name="username"]');
        const password = document.querySelector('input[name="password"]');
        const passwordWrapper = password?.closest('.v-input');
        const form = document.getElementById('vectra-login-form');
        const continueButton = document.getElementById('vectra-continue');
        const showPassword = () => {
          if (passwordWrapper) {
            passwordWrapper.style.display = '';
          }
          continueButton?.setAttribute('type', 'submit');
          password?.focus();
        };
        username?.addEventListener('keydown', event => {
          if (event.key === 'Enter') {
            event.preventDefault();
            showPassword();
          }
        });
        continueButton?.addEventListener('click', event => {
          if (passwordWrapper?.style.display === 'none') {
            event.preventDefault();
            showPassword();
          }
        });
        password?.addEventListener('keydown', event => {
          if (event.key === 'Enter') {
            event.preventDefault();
            form?.requestSubmit();
          }
        });
        document.getElementById('cookiescript_accept')?.addEventListener('click', event => {
          event.preventDefault();
          event.currentTarget.remove();
        });
        username?.focus();
        """,
    )
    return render_mock_html(soup)


def _render_home_page(*, scenario: str) -> str:
    """Prepare the captured dashboard page with mock payment data."""
    soup = _clone_soup(HOME_SOUP)
    _remove_dynamic_content(soup)
    _rewrite_asset_paths(soup)
    _configure_user_menu(soup)
    _configure_total(soup, amount=_scenario_total(scenario))
    _configure_invoices_link(soup, scenario=scenario)
    _remove_invoice_table(soup)
    if scenario == "timeout":
        dashboard = soup.select_one("div.main-page.dashboard")
        if isinstance(dashboard, Tag):
            dashboard.decompose()
    return render_mock_html(soup)


def _render_invoices_page(*, scenario: str) -> str:
    """Prepare the dashboard page with an unpaid-invoices table."""
    soup = _clone_soup(HOME_SOUP)
    _remove_dynamic_content(soup)
    _rewrite_asset_paths(soup)
    _configure_user_menu(soup)
    _configure_total(soup, amount=_scenario_total(scenario))
    _configure_invoices_link(soup, scenario=scenario)
    _configure_invoice_table(soup, scenario=scenario)
    return render_mock_html(soup)


def _render_two_factor_page() -> str:
    """Return a minimal page that triggers the provider's 2FA handling path."""
    return """
<!doctype html>
<html lang="pl">
<head><meta charset="utf-8"><title>Vectra mock - 2FA</title></head>
<body>
  <h3>Wpisz kod weryfikacyjny</h3>
  <p>To jest mock scenariusza 2FA.</p>
</body>
</html>
"""


def _configure_total(soup: BeautifulSoup, *, amount: str) -> None:
    """Set the total balance value expected by the provider."""
    total = soup.select_one("div.left-column h3")
    if isinstance(total, Tag):
        total.string = amount


def _scenario_total(scenario: str) -> str:
    """Return the dashboard total for the selected mock scenario."""
    if scenario == "no_overdue":
        return ZERO_AMOUNT
    return TOTAL_AMOUNT


def _scenario_invoices(scenario: str) -> tuple[dict[str, str], ...]:
    """Return invoice rows matching the selected mock scenario."""
    if scenario == "multi":
        return MULTI_INVOICES
    return DEFAULT_INVOICES


def _configure_invoices_link(soup: BeautifulSoup, *, scenario: str) -> None:
    """Point the invoices CTA at the mock invoices page."""
    for candidate in soup.find_all("a"):
        if "Zobacz faktury" in " ".join(candidate.stripped_strings):
            candidate["href"] = f"{INVOICES_PATH}?scenario={scenario}"
            break


def _configure_user_menu(soup: BeautifulSoup) -> None:
    """Expose a stable avatar menu with a logout action."""
    avatar_button = None
    for button in soup.find_all("button"):
        if button.select_one("span.ico-avatar") is not None:
            avatar_button = button
            break
    if not isinstance(avatar_button, Tag):
        nav = soup.select_one(".user-account-navigation")
        if not isinstance(nav, Tag):
            return
        avatar_button = soup.new_tag(
            "button",
            attrs={"class": "button-icon-circle", "type": "button", "style": "position: relative;"},
        )
        avatar_icon = soup.new_tag(
            "span",
            attrs={"class": "ico-avatar", "style": "display:inline-block; width:26px; height:26px;"},
        )
        avatar_button.append(avatar_icon)
        nav.append(avatar_button)

    avatar_button.clear()
    avatar_icon = soup.new_tag(
        "span",
        attrs={"class": "ico-avatar", "style": "display:inline-block; width:26px; height:26px;"},
    )
    avatar_button.append(avatar_icon)

    existing = soup.select_one("#vectra-logout-menu")
    if existing is not None:
        existing.decompose()

    menu = soup.new_tag(
        "div",
        attrs={
            "id": "vectra-logout-menu",
            "style": "display:block; position:absolute; right:1rem; top:4rem; background:#fff; padding:0.75rem 1rem; border:1px solid #d9d9d9; border-radius:0.5rem; z-index:1000;",
        },
    )
    logout = soup.new_tag("a", attrs={"href": LOGOUT_PATH})
    label = soup.new_tag("span")
    label.string = "Wyloguj się"
    logout.append(label)
    menu.append(logout)
    avatar_button.parent.append(menu)


def _remove_invoice_table(soup: BeautifulSoup) -> None:
    """Drop any existing invoice table so the dashboard stays lightweight."""
    for table in soup.select("table.vectra-complex-table"):
        table.decompose()


def _configure_invoice_table(soup: BeautifulSoup, *, scenario: str) -> None:
    """Insert an invoice table matching the selectors and column order used by the provider."""
    _remove_invoice_table(soup)

    target = soup.select_one("div.left-column")
    if not isinstance(target, Tag):
        return

    if scenario == "no_overdue":
        note = soup.new_tag("div", attrs={"class": "vectra-mock-note"})
        note.string = "Brak faktur do zapłaty"
        target.append(note)
        return
    if scenario == "timeout":
        return

    wrapper = soup.new_tag("div", attrs={"class": "vectra-mock-invoices", "style": "margin-top:1.5rem;"})
    table = soup.new_tag("table", attrs={"class": "vectra-complex-table", "style": "width:100%; border-collapse:collapse;"})
    tbody = soup.new_tag("tbody")
    table.append(tbody)
    wrapper.append(table)
    target.append(wrapper)

    for invoice in _scenario_invoices(scenario):
        row = soup.new_tag("tr")
        cells = (
            invoice["number"],
            "Internet",
            "Opłata abonamentowa",
            invoice["issued"],
            invoice["amount"],
            invoice["due_date"],
        )
        for value in cells:
            cell = soup.new_tag("td")
            cell.string = value
            row.append(cell)
        tbody.append(row)
