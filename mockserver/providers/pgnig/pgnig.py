"""PGNiG blueprint for the local mock portal."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag
from flask import Blueprint, redirect, request, url_for
from werkzeug.wrappers import Response

from mockserver.providers._html import render_mock_html

BASE_PATH = "/pgnig"
LOGIN_PATH = f"{BASE_PATH}/"
LOGIN_POST_PATH = f"{BASE_PATH}/mock-login"
HOME_PATH = f"{BASE_PATH}/mock-home"
INVOICES_PATH = f"{BASE_PATH}/faktury"
LOGOUT_PATH = f"{BASE_PATH}/mock-logout"
DEFAULT_LOCATION = "Sezamowa 21"
DEFAULT_DUE_DATE = "19-03-2026"
DEFAULT_AMOUNT = "23,96 z\u0142"
ALL_PAID_TEXT = "Faktury s\u0105 op\u0142acone"
PAY_CAPTION = "Zap\u0142a\u0107"
CONTENT_DIR = Path(__file__).resolve().parent / "content"
LOGIN_HTML = CONTENT_DIR / "login.html"
HOME_HTML = CONTENT_DIR / "home.html"
INVOICES_HTML = CONTENT_DIR / "invoices.html"

bp = Blueprint("pgnig", __name__)

LOGIN_SOUP = BeautifulSoup(LOGIN_HTML.read_text(encoding="utf-8"), "html.parser")
HOME_SOUP = BeautifulSoup(HOME_HTML.read_text(encoding="utf-8"), "html.parser")
INVOICES_SOUP = BeautifulSoup(INVOICES_HTML.read_text(encoding="utf-8"), "html.parser")


@bp.get(BASE_PATH)
@bp.get(LOGIN_PATH)
def pgnig_login() -> str:
    """Render the PGNiG login page variant selected by the optional scenario query param."""
    return _render_login_page(scenario=request.args.get("scenario", "ok"))


@bp.post(LOGIN_POST_PATH)
def pgnig_mock_login() -> Response:
    """Validate mock credentials and redirect either to the dashboard or error state."""
    scenario = request.args.get("scenario", "ok")
    username = request.form.get("identificator", "")
    password = request.form.get("accessPin", "")

    if scenario == "error" or not username or not password:
        return redirect(url_for("pgnig.pgnig_login", scenario="error"))

    return redirect(url_for("pgnig.pgnig_home", scenario=scenario))


@bp.get(HOME_PATH)
def pgnig_home() -> str:
    """Render the dashboard page with address data and the invoices menu entry."""
    return _render_home_page(
        scenario=request.args.get("scenario", "ok"),
        location=request.args.get("location", DEFAULT_LOCATION),
    )


@bp.get(INVOICES_PATH)
def pgnig_invoices() -> str:
    """Render the invoices list page used by the provider to collect unpaid payments."""
    return _render_invoices_page(
        scenario=request.args.get("scenario", "ok"),
        location=request.args.get("location", DEFAULT_LOCATION),
    )


@bp.get(LOGOUT_PATH)
def pgnig_logout() -> Response:
    """Simulate logout by returning the browser to the login page."""
    return redirect(url_for("pgnig.pgnig_login"))


@bp.get(f"{BASE_PATH}/<path:_asset_path>")
def pgnig_asset(_asset_path: str) -> Response:
    """Return a tiny placeholder payload for archived PGNiG asset URLs."""
    if _asset_path.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
        return Response(b"", mimetype="image/png")
    if _asset_path.endswith((".css", ".js", ".json", ".map", ".woff", ".woff2", ".ttf", ".manifest")):
        return Response("", mimetype="text/plain")
    return Response("", mimetype="application/octet-stream")


def _clone_soup(source: BeautifulSoup) -> BeautifulSoup:
    """Return a fresh soup instance to avoid mutating the shared HTML template."""
    return BeautifulSoup(str(source), "html.parser")


def _remove_dynamic_content(soup: BeautifulSoup) -> None:
    """Drop archived scripts and overlays so the mock page stays static and predictable."""
    for element in soup.find_all(["script", "iframe", "noscript", "df-messenger", "apple-pay-merchandising-modal"]):
        element.decompose()
    for selector in (
        "#CookiebotWidget",
        "#CookiebotWidgetUnderlay",
        "#app > div > span",
        ".pgnig-cx-widget",
        ".ModalContent",
        ".modal-mobile-app",
        ".listenerAutoLogout",
        ".ghost.hide",
    ):
        for element in soup.select(selector):
            element.decompose()


def _append_helper_script(soup: BeautifulSoup, script_content: str) -> None:
    """Append inline JavaScript used to adapt a captured page to mock-server behavior."""
    body = soup.body
    assert body is not None
    tag = soup.new_tag("script")
    tag.string = script_content
    body.append(tag)


def _render_login_page(*, scenario: str) -> str:
    """Prepare the captured login page HTML so Selenium can submit the mock form."""
    soup = _clone_soup(LOGIN_SOUP)
    _remove_dynamic_content(soup)

    form = soup.select_one('div[data-testid="login/form"] form')
    if form is not None:
        form["method"] = "post"
        form["action"] = f"{LOGIN_POST_PATH}?scenario={scenario}"

    reset_button = soup.find("button", string=lambda text: isinstance(text, str) and "Zresetuj" in text)
    if isinstance(reset_button, Tag):
        reset_button["class"] = "button reset-password-mock"

    back_button = soup.find("button", string=lambda text: isinstance(text, str) and "Wstecz" in text)
    if isinstance(back_button, Tag):
        back_button.decompose()

    if scenario == "error":
        title = soup.select_one("div.login-box h1.title")
        if title is not None:
            error = soup.new_tag("div", attrs={"class": "mock-error"})
            error.string = "Nieprawid\u0142owy login lub has\u0142o"
            title.insert_after(error)

    _append_helper_script(
        soup,
        """
        document.title = 'PGNiG mock - login';
        document.querySelector('[name="identificator"]')?.focus();
        """,
    )
    return render_mock_html(soup)


def _render_home_page(*, scenario: str, location: str) -> str:
    """Prepare the dashboard page with address details and the local invoices route."""
    soup = _clone_soup(HOME_SOUP)
    _remove_dynamic_content(soup)

    _configure_location(soup, location=location)
    _configure_invoices_link(soup, scenario=scenario, location=location)
    _configure_dashboard_status(soup, scenario=scenario)
    _ensure_logout_button(soup)

    _append_helper_script(
        soup,
        """
        document.title = 'PGNiG mock - home';
        """,
    )
    return render_mock_html(soup)


def _render_invoices_page(*, scenario: str, location: str) -> str:
    """Prepare the invoices page with one unpaid row or a scenario-specific empty state."""
    soup = _clone_soup(INVOICES_SOUP)
    _remove_dynamic_content(soup)

    _configure_location(soup, location=location)
    _configure_invoices_link(soup, scenario=scenario, location=location)
    _configure_invoice_rows(soup, scenario=scenario)
    _ensure_logout_button(soup)

    _append_helper_script(
        soup,
        """
        document.title = 'PGNiG mock - invoices';
        """,
    )
    return render_mock_html(soup)


def _configure_location(soup: BeautifulSoup, *, location: str) -> None:
    """Replace the captured address text with a stable mock location."""
    address = soup.select_one("div.reading-adress span")
    if isinstance(address, Tag):
        address.string = f" ul. {location}, 81-591 Gdynia "
        return

    anchor = soup.select_one("div.reading-box .small-12.large-12.columns")
    if not isinstance(anchor, Tag):
        return

    wrapper = soup.new_tag("div", attrs={"class": "reading-adress"})
    icon = soup.new_tag("i", attrs={"class": "icon-fire orange"})
    label = soup.new_tag("span")
    label.string = f" ul. {location}, 81-591 Gdynia "
    wrapper.append(icon)
    wrapper.append(label)

    submit_row = anchor.select_one("#reading_form")
    if isinstance(submit_row, Tag):
        submit_row.insert_before(wrapper)
    else:
        anchor.append(wrapper)


def _configure_invoices_link(soup: BeautifulSoup, *, scenario: str, location: str) -> None:
    """Point the invoices menu to the local mock route instead of the live portal."""
    for link in soup.select("a.menu-element"):
        if " ".join(link.stripped_strings) == "Faktury":
            link["href"] = f"{INVOICES_PATH}?scenario={scenario}&location={location}"


def _configure_dashboard_status(soup: BeautifulSoup, *, scenario: str) -> None:
    """Adjust the dashboard payment summary for success and no-overdue scenarios."""
    status = soup.select_one("div.last-invoice.blue")
    if not isinstance(status, Tag):
        return

    strong = status.find("strong")
    strong_tag = strong if isinstance(strong, Tag) else None
    if scenario == "no_overdue":
        if strong_tag is not None:
            strong_tag.string = ALL_PAID_TEXT
        status.clear()
        if strong_tag is not None:
            status.append(strong_tag)
        status.append("Brak p\u0142atno\u015bci do uregulowania")
        return

    if strong_tag is not None:
        strong_tag.string = "Zbli\u017caj\u0105ce si\u0119 p\u0142atno\u015bci"
    status.clear()
    if strong_tag is not None:
        status.append(strong_tag)
    status.append(soup.new_tag("br"))
    status.append(f"Kwota do zap\u0142aty: {DEFAULT_AMOUNT}")
    status.append(soup.new_tag("br"))


def _configure_invoice_rows(soup: BeautifulSoup, *, scenario: str) -> None:
    """Keep only the invoice rows relevant for the selected mock scenario."""
    table = soup.select_one('div[data-testid="invoice/list"]')
    if table is None:
        return

    rows = table.select("div.main-row-container")
    for row in rows:
        row_parent = row.parent
        if isinstance(row_parent, Tag):
            row_parent.decompose()

    if scenario == "timeout":
        return

    if scenario == "no_overdue":
        _append_paid_invoice_row(soup, table, due_date=DEFAULT_DUE_DATE, amount=DEFAULT_AMOUNT)
        return

    _append_unpaid_invoice_row(soup, table, due_date=DEFAULT_DUE_DATE, amount=DEFAULT_AMOUNT)
    _append_paid_invoice_row(soup, table, due_date="18-02-2026", amount="27,85 z\u0142")


def _append_unpaid_invoice_row(soup: BeautifulSoup, table: Tag, *, due_date: str, amount: str) -> None:
    """Insert a single payable invoice row matching the provider selectors."""
    wrapper = _build_invoice_wrapper(soup, due_date=due_date, amount=amount, button_label=PAY_CAPTION)
    table.append(wrapper)


def _append_paid_invoice_row(soup: BeautifulSoup, table: Tag, *, due_date: str, amount: str) -> None:
    """Insert a paid invoice row to keep the list structure close to the original trace."""
    wrapper = _build_invoice_wrapper(soup, due_date=due_date, amount=amount, button_label="Op\u0142acona", paid=True)
    table.append(wrapper)


def _build_invoice_wrapper(
    soup: BeautifulSoup,
    *,
    due_date: str,
    amount: str,
    button_label: str,
    paid: bool = False,
) -> Tag:
    """Create a minimal invoice row with the same column structure as the provider expects."""
    row = soup.new_tag("div", attrs={"class": "table-row agreemnet-row row row-clicked invoice_element outline-focus"})
    row.append(soup.new_tag("div", attrs={"class": "color-agreements"}))
    row.append(soup.new_tag("div", attrs={"class": "color-bg-agreements"}))

    container = soup.new_tag("div", attrs={"class": "width-100 p-16-0 main-row-container"})
    row.append(container)

    invoice_col = soup.new_tag("div", attrs={"class": "small-6 large-3 columns text-left"})
    number = soup.new_tag("div", attrs={"class": "invoice-number"})
    number.string = "P/2800888/0003/26"
    invoice_col.append(number)
    container.append(invoice_col)

    container.append(soup.new_tag("div", attrs={"class": "small-1 large-1 columns fs-20 hide-for-small-only"}))

    due_col = soup.new_tag("div", attrs={"class": "small-3 large-2 columns"})
    due_col.string = due_date
    container.append(due_col)

    amount_col = soup.new_tag("div", attrs={"class": "small-3 large-15 columns"})
    amount_span = soup.new_tag("span")
    amount_span.string = amount
    amount_col.append(amount_span)
    container.append(amount_col)

    usage_col = soup.new_tag("div", attrs={"class": "large-2 columns show-for-large"})
    usage_col.string = "24 kWh"
    container.append(usage_col)

    status_col = soup.new_tag("div", attrs={"class": "small-12 large-25 columns"})
    if paid:
        button = soup.new_tag("div", attrs={"class": "button expanded disable"})
    else:
        button = soup.new_tag("button", attrs={"class": "button expanded outline-focus", "type": "button"})
    button.string = button_label
    status_col.append(button)
    container.append(status_col)
    return row


def _ensure_logout_button(soup: BeautifulSoup) -> None:
    """Insert a simple logout control matching the default provider XPath."""
    menu = soup.select_one("ul.main-menu")
    if menu is None or menu.find(string=lambda text: isinstance(text, str) and "Wyloguj" in text):
        return

    item = soup.new_tag("li")
    button = soup.new_tag("button", attrs={"type": "button", "onclick": f"window.location.assign('{LOGOUT_PATH}');"})
    button.string = "Wyloguj"
    item.append(button)
    menu.append(item)
