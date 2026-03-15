"""Multimedia blueprint for the local mock portal."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag
from flask import Blueprint, redirect, request, url_for
from werkzeug.wrappers import Response

from payments.mockserver.providers._html import render_mock_html

BASE_PATH = "/multimedia"
LOGIN_PATH = f"{BASE_PATH}/"
LOGIN_POST_PATH = f"{BASE_PATH}/mock-login"
HOME_PATH = f"{BASE_PATH}/mock-home"
LOGOUT_PATH = f"{BASE_PATH}/mock-logout"
DEFAULT_DUE_DATE = "31-03-2026"
DEFAULT_INVOICES = (
    ("90,00", "Hodowlana"),
    ("77,00", "Sezamowa"),
)
CONTENT_DIR = Path(__file__).resolve().parent / "content"
LOGIN_HTML = CONTENT_DIR / "login.html"
HOME_HTML = CONTENT_DIR / "home.html"

bp = Blueprint("multimedia", __name__)

LOGIN_SOUP = BeautifulSoup(LOGIN_HTML.read_text(encoding="utf-8"), "html.parser")
HOME_SOUP = BeautifulSoup(HOME_HTML.read_text(encoding="utf-8"), "html.parser")


@bp.get(BASE_PATH)
@bp.get(LOGIN_PATH)
def multimedia_login() -> str:
    """Render the Multimedia login page variant selected by the optional scenario query param."""
    return _render_login_page(scenario=request.args.get("scenario", "ok"))


@bp.post(LOGIN_POST_PATH)
def multimedia_mock_login() -> Response:
    """Validate mock credentials and redirect either to the dashboard or error state."""
    scenario = request.args.get("scenario", "ok")
    username = request.form.get("Login_SSO$UserName", "")
    password = request.form.get("Login_SSO$Password", "")

    if scenario == "error" or not username or not password:
        return redirect(url_for("multimedia.multimedia_login", scenario="error"))

    return redirect(url_for("multimedia.multimedia_home", scenario=scenario))


@bp.get(HOME_PATH)
def multimedia_home() -> str:
    """Render the invoice list page used by the provider to collect Multimedia payments."""
    return _render_home_page(scenario=request.args.get("scenario", "ok"))


@bp.get(LOGOUT_PATH)
def multimedia_logout() -> Response:
    """Simulate logout by returning the browser to the login page."""
    return redirect(url_for("multimedia.multimedia_login"))


@bp.get("/CSS/<path:_asset_path>")
@bp.get("/Content/<path:_asset_path>")
@bp.get("/Script/<path:_asset_path>")
@bp.get("/Scripts/<path:_asset_path>")
@bp.get("/TSPD/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/CSS/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/Content/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/Script/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/Scripts/<path:_asset_path>")
@bp.get(f"{BASE_PATH}/TSPD/<path:_asset_path>")
def multimedia_asset(_asset_path: str) -> Response:
    """Return a tiny placeholder payload for archived Multimedia asset URLs."""
    if _asset_path.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
        return Response(b"", mimetype="image/png")
    if _asset_path.endswith((".css", ".js", ".json", ".map", ".woff", ".woff2", ".ttf")):
        return Response("", mimetype="text/plain")
    return Response("", mimetype="application/octet-stream")


def _clone_soup(source: BeautifulSoup) -> BeautifulSoup:
    """Return a fresh soup instance to avoid mutating the shared HTML template."""
    return BeautifulSoup(str(source), "html.parser")


def _remove_dynamic_content(soup: BeautifulSoup) -> None:
    """Drop archived scripts and overlays so the mock page stays static and predictable."""
    for element in soup.find_all(["script", "iframe", "noscript", "apm_do_not_touch"]):
        element.decompose()
    for selector in (
        "#g-recaptcha-response",
        "#cookiescript_injected",
        "#cookiescript_injected_wrapper",
        ".grecaptcha-badge",
        ".footer-cookies",
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


def _class_values(tag: Tag) -> list[str]:
    """Return class attribute values normalized to a plain list of strings."""
    class_attr = tag.get("class")
    if class_attr is None:
        return []
    if isinstance(class_attr, str):
        return class_attr.split()
    return [value for value in class_attr if isinstance(value, str)]


def _render_login_page(*, scenario: str) -> str:
    """Prepare the captured login page HTML so Selenium can submit the mock form."""
    soup = _clone_soup(LOGIN_SOUP)
    _remove_dynamic_content(soup)

    form = soup.select_one("form#Form1")
    if form is not None:
        form["method"] = "post"
        form["action"] = f"{LOGIN_POST_PATH}?scenario={scenario}"

    login_button = soup.select_one("#LoginButton")
    if isinstance(login_button, Tag):
        login_button.name = "button"
        login_button["type"] = "submit"
        login_button["class"] = "btn-primary -w-100p -pos-rel"
        login_button.attrs.pop("href", None)

    spinner = soup.select_one("#LoginButton i.spinner")
    if spinner is not None:
        classes = [value for value in _class_values(spinner) if value != "loadingSpinner"]
        spinner["class"] = " ".join(classes)

    error_box = soup.select_one("span.logonFailureText")
    if error_box is None:
        target = soup.select_one(".panel-form-line-input")
        if target is not None:
            error_box = soup.new_tag("span", attrs={"class": "logonFailureText error"})
            target.append(error_box)
    if error_box is not None:
        error_box.string = "Nieprawidlowy login lub haslo" if scenario == "error" else ""

    _append_helper_script(
        soup,
        """
        document.title = 'Multimedia mock - login';
        document.getElementById('Login_SSO_UserName')?.focus();
        document.getElementById('cookiescript_accept')?.addEventListener('click', event => {
          event.preventDefault();
          document.getElementById('cookiescript_injected')?.remove();
          document.getElementById('cookiescript_injected_wrapper')?.remove();
        });
        """,
    )
    return render_mock_html(soup)


def _render_home_page(*, scenario: str) -> str:
    """Prepare the post-login page with either invoices or the all-paid state."""
    soup = _clone_soup(HOME_SOUP)
    _remove_dynamic_content(soup)

    _remove_login_panel(soup)
    _ensure_layout_container(soup)
    _configure_logout_button(soup)
    _configure_invoice_section(soup, scenario=scenario)

    _append_helper_script(
        soup,
        """
        document.title = 'Multimedia mock - home';
        document.getElementById('cookiescript_accept')?.addEventListener('click', event => {
          event.preventDefault();
          document.getElementById('cookiescript_injected')?.remove();
          document.getElementById('cookiescript_injected_wrapper')?.remove();
        });
        """,
    )
    return render_mock_html(soup)


def _remove_login_panel(soup: BeautifulSoup) -> None:
    """Remove login-only controls so the provider can treat the page as authenticated."""
    for selector in (
        "#Form1",
        "#LoginButton",
        "#Login_SSO_UserName",
        "#Login_SSO_Password",
    ):
        element = soup.select_one(selector)
        if element is not None:
            parent = element
            if selector == "#Form1":
                parent.decompose()
            else:
                element.decompose()


def _ensure_layout_container(soup: BeautifulSoup) -> Tag:
    """Return a stable content container for the mock invoice widgets."""
    wrapper = soup.select_one("body > div")
    if isinstance(wrapper, Tag):
        return wrapper
    body = soup.body
    assert body is not None
    wrapper = soup.new_tag("div", attrs={"class": "multimedia-mock"})
    body.append(wrapper)
    return wrapper


def _configure_logout_button(soup: BeautifulSoup) -> None:
    """Add a simple logout link matching the default provider XPath."""
    wrapper = _ensure_layout_container(soup)
    existing = soup.find(string=lambda text: isinstance(text, str) and "Wyloguj" in text)
    if existing is not None:
        return

    logout = soup.new_tag(
        "a",
        attrs={
            "href": LOGOUT_PATH,
            "class": "btn-primary",
            "style": "display:inline-block; margin:1rem 0; padding:0.75rem 1rem;",
        },
    )
    logout.string = "Wyloguj"
    wrapper.append(logout)


def _configure_invoice_section(soup: BeautifulSoup, *, scenario: str) -> None:
    """Insert invoice widgets matching the selectors used by the provider."""
    wrapper = _ensure_layout_container(soup)

    existing = soup.select_one(".multimedia-mock-payments")
    if existing is not None:
        existing.decompose()

    section = soup.new_tag("div", attrs={"class": "multimedia-mock-payments", "style": "padding: 1rem 0 2rem;"})
    wrapper.append(section)

    title = soup.new_tag("h2")
    title.string = "Twoje faktury"
    section.append(title)

    if scenario == "no_overdue":
        all_paid = soup.new_tag("div", attrs={"class": "clear"})
        label = soup.new_tag("span", attrs={"class": "-bold"})
        label.string = "Brak nieoplaconych faktur"
        all_paid.append(label)
        section.append(all_paid)
        return

    if scenario == "timeout":
        return

    for amount, location in DEFAULT_INVOICES:
        section.append(_build_invoice(soup, amount=amount, due_date=DEFAULT_DUE_DATE, location=location))


def _build_invoice(soup: BeautifulSoup, *, amount: str, due_date: str, location: str) -> Tag:
    """Create a minimal invoice card exposing the selectors used by the provider."""
    invoice = soup.new_tag(
        "div",
        attrs={
            "class": "invoiceInfo",
            "style": "margin: 1rem 0; padding: 1rem; border: 1px solid #d9d9d9; border-radius: 0.5rem;",
        },
    )

    location_box = soup.new_tag("div", attrs={"class": "adres"})
    location_box.string = location
    invoice.append(location_box)

    amount_box = soup.new_tag("div", attrs={"class": "kwota"})
    amount_box.string = amount
    invoice.append(amount_box)

    due_box = soup.new_tag("div", attrs={"class": "platnoscDo"})
    due_box.string = due_date
    invoice.append(due_box)
    return invoice
