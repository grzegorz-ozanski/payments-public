"""Energa blueprint for the local mock portal."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag
from flask import Blueprint, redirect, request, url_for
from werkzeug.wrappers import Response

from payments.mockserver.providers._html import render_mock_html

BASE_PATH = "/energa"
LOGIN_PATH = f"{BASE_PATH}/"
LOGIN_POST_PATH = f"{BASE_PATH}/mock-login"
ACCOUNTS_PATH = f"{BASE_PATH}/mock-accounts"
DASHBOARD_PATH = f"{BASE_PATH}/mock-dashboard"
INVOICES_PATH = f"{BASE_PATH}/mock-invoices"
LOGOUT_PATH = f"{BASE_PATH}/mock-logout"
ASSET_PREFIX = "/ss"

CONTENT_DIR = Path(__file__).resolve().parent / "content"
LOGIN_HTML = CONTENT_DIR / "login.html"
ACCOUNTS_HTML = CONTENT_DIR / "accounts.html"
INVOICES_HTML = CONTENT_DIR / "invoices.html"

bp = Blueprint("energa", __name__)

LOGIN_SOUP = BeautifulSoup(LOGIN_HTML.read_text(encoding="utf-8"), "html.parser")
ACCOUNTS_SOUP = BeautifulSoup(ACCOUNTS_HTML.read_text(encoding="utf-8"), "html.parser")
INVOICES_SOUP = BeautifulSoup(INVOICES_HTML.read_text(encoding="utf-8"), "html.parser")

ACCOUNTS = (
    {
        "id": "3838990000",
        "location": "Bryla",
        "address": "Janki Bryla 8/A/14",
        "city": "81-577 Gdynia",
        "summary": "Brak należności 0,00 PLN",
        "amount": "0,00",
        "due_date": "13.03.2026",
        "invoice_number": "3838990000/FES/00012",
    },
    {
        "id": "9429890000",
        "location": "Hodowlana",
        "address": "Hodowlana 26/2",
        "city": "81-606 Gdynia",
        "summary": "Do zapłaty 348,86 PLN",
        "amount": "348,86",
        "due_date": "24.03.2026",
        "invoice_number": "9429890000/FES/00063",
    },
    {
        "id": "5607711551",
        "location": "Sezamowa",
        "address": "Sezamowa 21",
        "city": "81-591 Gdynia",
        "summary": "Brak należności 0,00 PLN",
        "amount": "0,00",
        "due_date": "13.03.2026",
        "invoice_number": "5607711551/FES/00021",
    },
)


@bp.get(BASE_PATH)
@bp.get(LOGIN_PATH)
def energa_login() -> str:
    """Render the Energa login page for the selected scenario."""
    return _render_login_page(scenario=request.args.get("scenario", "ok"))


@bp.post(LOGIN_POST_PATH)
def energa_mock_login() -> Response:
    """Validate mock credentials and continue to the mocked account list."""
    scenario = request.args.get("scenario", "ok")
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if scenario == "error" or not username or not password:
        return redirect(url_for("energa.energa_login", scenario="error"))
    return redirect(url_for("energa.energa_accounts", scenario=scenario))


@bp.get(ACCOUNTS_PATH)
def energa_accounts() -> str:
    """Render the mocked Energa account list."""
    return _render_accounts_page(scenario=request.args.get("scenario", "ok"))


@bp.get(DASHBOARD_PATH)
def energa_dashboard() -> str:
    """Render the mocked account dashboard used to read the balance."""
    scenario = request.args.get("scenario", "ok")
    account = _get_account(request.args.get("location"))
    return _render_dashboard_page(account, scenario=scenario)


@bp.get(INVOICES_PATH)
def energa_invoices() -> str:
    """Render the invoices view used to read due dates."""
    scenario = request.args.get("scenario", "ok")
    account = _get_account(request.args.get("location"))
    return _render_invoices_page(account, scenario=scenario)


@bp.get(LOGOUT_PATH)
def energa_logout() -> Response:
    """Return the browser to the login page."""
    return redirect(url_for("energa.energa_login"))


@bp.get(f"{ASSET_PREFIX}/<path:_asset_path>")
@bp.get(f"{BASE_PATH}{ASSET_PREFIX}/<path:_asset_path>")
def energa_asset(_asset_path: str) -> Response:
    """Return a tiny placeholder payload for archived Energa asset URLs."""
    if _asset_path.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
        return Response(b"", mimetype="image/png")
    if _asset_path.endswith((".css", ".js", ".json", ".map", ".woff", ".woff2", ".ttf")):
        return Response("", mimetype="text/plain")
    return Response("", mimetype="application/octet-stream")


def _clone_soup(source: BeautifulSoup) -> BeautifulSoup:
    """Return a fresh soup instance to avoid mutating the shared HTML template."""
    return BeautifulSoup(str(source), "html.parser")


def _get_account(location: str | None) -> dict[str, str]:
    """Resolve the selected account, defaulting to the first match."""
    if location:
        for account in ACCOUNTS:
            if account["location"] == location:
                return account
    return ACCOUNTS[0]


def _mock_url(path: str, *, scenario: str, location: str | None = None) -> str:
    """Build a mock URL preserving the current scenario and selected location."""
    query = [f"scenario={scenario}"]
    if location is not None:
        query.append(f"location={location}")
    return f"{path}?{'&'.join(query)}"


def _remove_dynamic_content(soup: BeautifulSoup) -> None:
    """Drop archived scripts, overlays and telemetry so the mock stays static."""
    for element in soup.find_all(["script", "iframe", "noscript"]):
        element.decompose()
    for selector in (
        ".Toastify",
        ".accessibility-panel",
        ".accessibility-reading-line__bar",
        ".index-page",
        ".popup__wrapper",
        ".grecaptcha-badge",
        "#CybotCookiebotDialog",
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
        src = tag.get("src")
        if isinstance(src, str) and src.startswith(ASSET_PREFIX):
            tag["src"] = f"{BASE_PATH}{src}"
    for tag in soup.find_all(href=True):
        href = tag.get("href")
        if isinstance(href, str) and href.startswith(ASSET_PREFIX):
            tag["href"] = f"{BASE_PATH}{href}"


def _configure_login_form(soup: BeautifulSoup, *, scenario: str) -> None:
    """Convert the captured login page into a working mock form."""
    switch_button = soup.select_one("#kc-switch-button")
    if isinstance(switch_button, Tag):
        switch_button["type"] = "button"
        switch_button["onclick"] = "document.getElementById('kc-form-login').style.opacity = '1';"

    form = soup.select_one("#kc-form-login")
    if isinstance(form, Tag):
        form["method"] = "post"
        form["action"] = _mock_url(LOGIN_POST_PATH, scenario=scenario)
        form["style"] = "opacity: 1; transform: none;"

    login_button = soup.select_one("#kc-login")
    if isinstance(login_button, Tag):
        login_button.attrs.pop("disabled", None)

    cookie_button = soup.find(id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
    if cookie_button is None:
        body = soup.body
        assert body is not None
        cookie_button = soup.new_tag(
            "button",
            attrs={
                "id": "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
                "type": "button",
                "style": "position:fixed; right:16px; bottom:16px; z-index:1000;",
            },
        )
        cookie_button.string = "Akceptuj cookies"
        body.append(cookie_button)

    error_box = soup.select_one("#input-error")
    if error_box is None and isinstance(form, Tag):
        error_box = soup.new_tag("span", attrs={"id": "input-error", "class": "input-wrapper__description error"})
        form.append(error_box)
    if isinstance(error_box, Tag):
        error_box.string = "Nieprawidłowy login lub hasło" if scenario == "error" else ""


def _configure_user_menu(soup: BeautifulSoup) -> None:
    """Ensure the user menu is visible and exposes a working logout entry."""
    menu = soup.select_one("button.hover-submenu")
    if isinstance(menu, Tag):
        menu["aria-expanded"] = "true"

    dropdown = soup.select_one("#dropdown-menu")
    if not isinstance(dropdown, Tag):
        header = soup.select_one(".right-wrapper")
        if not isinstance(header, Tag):
            return
        dropdown = soup.new_tag("div", attrs={"class": "submenu", "role": "menu", "id": "dropdown-menu"})
        header.append(dropdown)

    logout_link = None
    for candidate in dropdown.find_all("a"):
        if "Wyloguj" in candidate.get_text(" ", strip=True):
            logout_link = candidate
            break
    if not isinstance(logout_link, Tag):
        logout_link = soup.new_tag("a", attrs={"role": "menuitem", "class": "clickable"})
        dropdown.append(logout_link)
    logout_link["href"] = LOGOUT_PATH
    logout_link.clear()
    label = soup.new_tag("span", attrs={"class": "text es-text variant-body mlm"})
    label.string = "Wyloguj się"
    logout_link.append(label)


def _configure_account_labels(soup: BeautifulSoup, *, scenario: str) -> None:
    """Make account labels navigate directly to the mocked dashboard views."""
    labels = soup.select("label.radio-button__label")
    for label, account in zip(labels, ACCOUNTS, strict=False):
        label["style"] = "cursor:pointer;"
        label["onclick"] = f"window.location.href='{_mock_url(DASHBOARD_PATH, scenario=scenario, location=account['location'])}'"
        label["data-location"] = account["location"]

        card = label.find_parent(class_="invoice-profile")
        if not isinstance(card, Tag):
            continue
        summary = card.select_one(".item__summary")
        if isinstance(summary, Tag):
            if scenario == "no_overdue":
                summary.string = "Brak należności 0,00 PLN"
            elif scenario == "timeout":
                summary.string = "Ładowanie danych..."
            else:
                summary.string = account["summary"]


def _configure_navigation(soup: BeautifulSoup, *, scenario: str, location: str, active: str) -> None:
    """Point top-level navigation controls at mock views for the selected account."""
    accounts_button = None
    for button in soup.find_all(["button", "a"]):
        if "LISTA KONT" in button.get_text(" ", strip=True):
            accounts_button = button
            break
    if isinstance(accounts_button, Tag):
        accounts_button["onclick"] = f"window.location.href='{_mock_url(ACCOUNTS_PATH, scenario=scenario)}'"
        accounts_button["style"] = "cursor:pointer;"
        if accounts_button.name == "a":
            accounts_button["href"] = _mock_url(ACCOUNTS_PATH, scenario=scenario)

    dashboard_link = soup.select_one("#main-tab-dashboard")
    if isinstance(dashboard_link, Tag):
        dashboard_link["href"] = _mock_url(DASHBOARD_PATH, scenario=scenario, location=location)
        dashboard_link["aria-selected"] = "true" if active == "dashboard" else "false"

    invoices_link = soup.select_one("#main-tab-payments-unpaid")
    if isinstance(invoices_link, Tag):
        invoices_link["href"] = _mock_url(INVOICES_PATH, scenario=scenario, location=location)
        invoices_link["aria-selected"] = "true" if active == "invoices" else "false"

    invoices_subtab = soup.select_one("#tab-payments-unpaid")
    if isinstance(invoices_subtab, Tag):
        invoices_subtab["href"] = _mock_url(INVOICES_PATH, scenario=scenario, location=location)
        invoices_subtab["aria-selected"] = "true" if active == "invoices" else "false"


def _set_location_header(soup: BeautifulSoup, account: dict[str, str]) -> None:
    """Update the account header shown above tabs."""
    location_span = soup.select_one(".text.es-text.variant-body-bold.mlxs.mrm")
    if isinstance(location_span, Tag):
        location_span.clear()
        location_span.append(f"licznik {account['address']} ")
        location_span.append(soup.new_tag("span", attrs={"class": "break"}))
        location_span.append(account["city"])

    label_span = soup.find(string=lambda text: isinstance(text, str) and "Konto fakturowe" in text)
    if label_span is not None and label_span.parent is not None:
        label_span.replace_with(f"Konto fakturowe {account['id']}:")


def _configure_amount(soup: BeautifulSoup, *, amount: str) -> None:
    """Ensure the dashboard exposes the balance selector expected by the provider."""
    amount_box = soup.select_one(".h1.text.es-text.variant-balance")
    if not isinstance(amount_box, Tag):
        container = soup.select_one("#page-content")
        if not isinstance(container, Tag):
            return
        amount_box = soup.new_tag("span", attrs={"class": "h1 text es-text variant-balance"})
        container.insert(0, amount_box)
    amount_box.string = f"{amount} zł"


def _configure_invoices_table(soup: BeautifulSoup, *, account: dict[str, str], scenario: str) -> None:
    """Adjust the unpaid-invoices view to either show a due date or the all-paid state."""
    form = soup.select_one("form[novalidate]")
    if not isinstance(form, Tag):
        return

    for strong in form.select("strong"):
        if "wszystkie" in strong.get_text(" ", strip=True).lower():
            strong.decompose()

    table = form.select_one("table.side-by-side__table")
    if isinstance(table, Tag):
        if scenario == "no_overdue":
            table.decompose()
        else:
            due_cell = table.select_one('td[data-headerlabel="Termin płatności"] span')
            if isinstance(due_cell, Tag):
                due_cell.string = account["due_date"]
            invoice_no = table.select_one('td[data-headerlabel="Numer faktury"]')
            if isinstance(invoice_no, Tag):
                invoice_no.string = account["invoice_number"]
            invoice_amount = table.select_one('td[data-headerlabel="Kwota faktury"]')
            if isinstance(invoice_amount, Tag):
                invoice_amount.string = f"{account['amount']} zł"
            amount_due = table.select_one('td[data-headerlabel="Kwota do zapłaty"]')
            if isinstance(amount_due, Tag):
                amount_due.string = f"{account['amount']} zł"

    pay_button = form.select_one("button.button.primary")
    if isinstance(pay_button, Tag):
        if scenario == "no_overdue":
            pay_button.decompose()
        else:
            pay_button.string = "Zapłać teraz"

    if scenario == "no_overdue":
        info_box = soup.new_tag("div")
        row = soup.new_tag("div")
        text = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Wszystkie faktury zostały opłacone"
        text.append(strong)
        row.append(text)
        info_box.append(row)
        form.clear()
        form.append(info_box)


def _render_login_page(*, scenario: str) -> str:
    """Prepare the captured Energa login page for mock use."""
    soup = _clone_soup(LOGIN_SOUP)
    _remove_dynamic_content(soup)
    _rewrite_asset_paths(soup)
    _configure_login_form(soup, scenario=scenario)
    _append_helper_script(
        soup,
        """
        document.title = 'Energa mock - login';
        document.getElementById('username')?.focus();
        document.getElementById('CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll')?.addEventListener('click', event => {
          event.preventDefault();
          event.currentTarget.remove();
        });
        """,
    )
    return render_mock_html(soup)


def _render_accounts_page(*, scenario: str) -> str:
    """Prepare the captured account list page with mock navigation."""
    soup = _clone_soup(ACCOUNTS_SOUP)
    _remove_dynamic_content(soup)
    _rewrite_asset_paths(soup)
    _configure_user_menu(soup)
    if scenario != "timeout":
        _configure_account_labels(soup, scenario=scenario)
    else:
        for label in soup.select("label.radio-button__label"):
            label.decompose()
    _append_helper_script(soup, "document.title = 'Energa mock - accounts';")
    return render_mock_html(soup)


def _render_dashboard_page(account: dict[str, str], *, scenario: str) -> str:
    """Prepare the account dashboard page used to read the total balance."""
    soup = _clone_soup(INVOICES_SOUP)
    _remove_dynamic_content(soup)
    _rewrite_asset_paths(soup)
    _configure_user_menu(soup)
    _set_location_header(soup, account)
    _configure_navigation(soup, scenario=scenario, location=account["location"], active="dashboard")
    _configure_amount(soup, amount="0,00" if scenario == "no_overdue" else account["amount"])
    _append_helper_script(soup, "document.title = 'Energa mock - dashboard';")
    return render_mock_html(soup)


def _render_invoices_page(account: dict[str, str], *, scenario: str) -> str:
    """Prepare the captured invoices page with mock data for the selected account."""
    soup = _clone_soup(INVOICES_SOUP)
    _remove_dynamic_content(soup)
    _rewrite_asset_paths(soup)
    _configure_user_menu(soup)
    _set_location_header(soup, account)
    _configure_navigation(soup, scenario=scenario, location=account["location"], active="invoices")
    _configure_amount(soup, amount="0,00" if scenario == "no_overdue" else account["amount"])
    _configure_invoices_table(soup, account=account, scenario=scenario)
    _append_helper_script(soup, "document.title = 'Energa mock - invoices';")
    return render_mock_html(soup)
