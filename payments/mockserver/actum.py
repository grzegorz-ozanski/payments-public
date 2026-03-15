"""Actum blueprint for the local mock portal."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup
from flask import Blueprint, Response, redirect, request, url_for

BASE_PATH = "/content/InetObsKontr"
CONTENT_DIR = Path(__file__).resolve().parents[1] / "content" / "actum"
LOGIN_HTML = CONTENT_DIR / "login.html"
PAYMENTS_HTML = CONTENT_DIR / "payments.html"

bp = Blueprint("actum", __name__)

LOGIN_SOUP = BeautifulSoup(LOGIN_HTML.read_text(encoding="utf-8"), "html.parser")
PAYMENTS_SOUP = BeautifulSoup(PAYMENTS_HTML.read_text(encoding="utf-8"), "html.parser")


@bp.get("/")
def root() -> Response:
    return redirect(url_for("actum.actum_login"))


@bp.get(f"{BASE_PATH}/")
def actum_index() -> Response:
    return redirect(url_for("actum.actum_login"))


@bp.get(f"{BASE_PATH}/LoginPage")
def actum_login() -> str:
    scenario = request.args.get("scenario", "ok")
    return _render_login_page(scenario=scenario)


@bp.post(f"{BASE_PATH}/mock-login")
def actum_mock_login() -> Response:
    scenario = request.args.get("scenario", "ok")
    username = request.form.get("nazwaUzytkownika", "")
    password = request.form.get("haslo", "")

    if scenario == "error":
        return redirect(url_for("actum.actum_login", scenario="error", _anchor="mainbox"))

    if not username or not password:
        return redirect(url_for("actum.actum_login", scenario="error", _anchor="mainbox"))

    return redirect(url_for("actum.actum_home", scenario=scenario))


@bp.get(f"{BASE_PATH}/home")
def actum_home() -> str:
    scenario = request.args.get("scenario", "ok")
    return _render_home_page(scenario=scenario)


@bp.get(f"{BASE_PATH}/mock-logout")
def actum_mock_logout() -> Response:
    return redirect(url_for("actum.actum_login"))


def _remove_external_scripts(soup: BeautifulSoup) -> None:
    for script in soup.find_all("script", src=True):
        script.decompose()


def _append_helper_script(soup: BeautifulSoup, script_content: str) -> None:
    body = soup.body
    assert body is not None
    tag = soup.new_tag("script")
    tag.string = script_content
    body.append(tag)


def _clone_soup(source: BeautifulSoup) -> BeautifulSoup:
    return BeautifulSoup(str(source), "html.parser")


def _render_login_page(*, scenario: str) -> str:
    soup = _clone_soup(LOGIN_SOUP)
    _remove_external_scripts(soup)

    form = soup.select_one("form.login-form")
    if form is not None:
        form["method"] = "post"
        form["action"] = f"{BASE_PATH}/mock-login?scenario={scenario}"

    password_input = soup.select_one('[aria-labelledby="haslo"]')
    if password_input is not None:
        password_input["name"] = "haslo"

    login_button = soup.select_one("button.login-btn")
    if login_button is not None:
        login_button["type"] = "submit"

    msg_boxes = soup.select("div.msg-box.basic.fail.redBg")
    message = "Invalid credentials" if scenario == "error" else ""
    for index, box in enumerate(msg_boxes):
        box.string = message if index == 0 else ""

    _append_helper_script(
        soup,
        """
        document.title = 'Actum mock - login';
        const userInput = document.querySelector('[aria-labelledby="login"]');
        if (userInput) {
          userInput.focus();
        }
        """,
    )
    return str(soup)


def _render_home_page(*, scenario: str) -> str:
    soup = _clone_soup(PAYMENTS_SOUP)
    _remove_external_scripts(soup)

    logout_button = soup.select_one("button.wcag.bg.navTxtColor")
    if logout_button is not None:
        logout_button["type"] = "button"
        logout_button["onclick"] = f"window.location.assign('{BASE_PATH}/mock-logout');"

    if scenario == "no_overdue":
        amount = soup.select_one("span.home-amount")
        if amount is not None:
            amount.decompose()

        due_date = soup.select_one("span.home-info")
        if due_date is not None:
            due_date.decompose()

        header = soup.select_one("h2.home-header")
        if header is not None:
            replacement = soup.new_tag(
                "span",
                attrs={
                    "class": "home-header nopayments greenColor greenIconBefore ng-star-inserted",
                },
            )
            replacement.string = "No outstanding payments"
            header.replace_with(replacement)

    if scenario == "timeout":
        amount = soup.select_one("span.home-amount")
        if amount is not None:
            amount.decompose()

    _append_helper_script(
        soup,
        """
        document.title = 'Actum mock - home';
        """,
    )
    return str(soup)