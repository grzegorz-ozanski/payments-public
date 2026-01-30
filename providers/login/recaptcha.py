"""
    Module for a simple page with both username and password inputs visible when the page is opened
"""
import random
import string
import time
from argparse import Namespace

from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from browser import Browser, Locator, setup_logging
from providers.login.base import BaseLogin
from credentials.credentials import Credentials
import numpy as np
import scipy.interpolate as si

log = setup_logging(__name__)

def _get_element_coords(element: WebElement) -> list[int]:
    """
    Return web element coordinates as a list of floats
    :param element: WebElement to get coordinates from
    :return: list[element x coord, element y coord]
    """
    rect = element.rect
    return [rect['x'], rect['y']]

def _calculate_offset(end: list[int], start: list[int]) -> list[int]:
    """
    Calculate an offset between two points
    :param end: End point coordinates list[x, y]
    :param start: Start point coordinates list[x, y]
    :return: list[x offset, y offset]
    """
    return list(map(lambda x: x[0] - x[1], zip(end, start)))

def ensure_not_constant_axis(points: np.ndarray, axis: int, start: list[int], end: list[int]) -> np.ndarray:
    """
    If points[:, axis] are all identical, replace points with [start, mid, end]
    where mid introduces some variation.

    :param points: points array
    :param axis: 0 for x, 1 for y
    :param start: start point coordinates
    :param end: end point coordinates
    :return: points array with distortion introduced if necessary
    """
    vals = points[:, axis]
    if not np.all(vals == vals[0]):
        return points

    divisor = random.choice((2, 3, 4)) # take a mid, third or quarter point
    delta = random.uniform(50, 250)

    new_points = [start]
    if axis == 0:
        # X constant -> perturb X a bit, and tweak Y based on existing point(s)
        new_points.append([points[0, 0] + delta, points[1, 1] / divisor])
        mid_count = random.choice((1, 2))
        if mid_count == 2:
            new_points.append([points[0, 0] - delta, points[1, 1] / divisor])
    else:
        # Y constant -> perturb Y a bit, and tweak X based on existing point(s)
        new_points.append([points[1, 0] / divisor, points[0, 1] + delta])
        mid_count = random.choice((1, 2))
        if mid_count == 2:
            new_points.append([points[1, 0] / divisor, points[0, 1] - delta])
    new_points.append(end)
    return np.array(new_points, dtype=float)

def _move_from_to(browser: Browser,
                  start_element: WebElement,
                  end_element: WebElement,
                  steps: int = 10) -> None:
    """
    Move mouse pointer from one web element to another using interpolated B-spline curve
    :param browser: Browser object
    :param start_element: Web element to start from
    :param end_element: Web element to go to
    :param steps: Number of poins of an interpolated B-spline curve which would join both web elements
    """
    start = [0, 0]
    # We will be using relative mouse movement
    end = _calculate_offset(_get_element_coords(end_element), _get_element_coords(start_element))
    points = np.array([start, end])
    points = ensure_not_constant_axis(points, axis=0, start=start, end=end)
    points = ensure_not_constant_axis(points, axis=1, start=start, end=end)
    x = points[:, 0]
    y = points[:, 1]
    t = np.arange(len(points))
    ipl_t = np.linspace(t[0], t[-1], steps)

    # Generate B-spline points for X and Y
    dx = np.diff(np.rint(si.splev(ipl_t, si.splrep(t, x, k=1))).astype(int))
    dy = np.diff(np.rint(si.splev(ipl_t, si.splrep(t, y, k=1))).astype(int))
    action = ActionChains(browser)
    start_coords = _get_element_coords(start_element)
    end_coords = _get_element_coords(end_element)
    log.trace('Start point: (%d, %d), end point: (%d, %d)',
              start_coords[0], start_coords[1],
              end_coords[0], end_coords[1])
    action.move_to_element(start_element).perform()
    for mouse_x, mouse_y in zip(dx, dy):
        start_coords[0], start_coords[1] = start_coords[0] + mouse_x, start_coords[1] + mouse_y
        log.trace('Mouse moved by (%d, %d), current location: (%d, %d)',
                  mouse_x, mouse_y,
                  start_coords[0], start_coords[1])
        action.move_by_offset(mouse_x, mouse_y).perform()
        time.sleep(random.uniform(0.01, 0.05))
    log.trace('Mismatch: (%d, %d)' % (end_coords[0] - start_coords[0], end_coords[1] - start_coords[1]))


def _input_delay(low: float = 0.05, high: float = 0.2) -> float:
    """
    Generates a random input delay from a specified range

    :param low: Lower bound of the range
    :param high: Upper bound of the range
    :return: Generated random value
    """
    return random.uniform(low, high)


def _input_with_error(control: WebElement, text: str, error_rate: float) -> None:
    """
    Clear the input field and type the given text, introducing human-like errors at a specified rate
    :param control: input field to be cleared
    :param text: text to be typed
    :param error_rate: Value from range [0, 1] determing how ofted a "mistake" should happen during input
    """
    time.sleep(0.5)
    if control.get_attribute('value') != '':
        # Clear the input first if already contains any value
        control.send_keys(Keys.CONTROL, 'a')
        time.sleep(_input_delay())
        if random.random() < 0.5:
            control.send_keys(Keys.DELETE)
        else:
            control.send_keys(Keys.BACKSPACE)
    for char in text:
        control.send_keys(char)
        if random.random() < error_rate:
            log.debug('Wrong char entered on purpose')
            # Generate random incorrect inputs
            control.send_keys(random.choice(string.ascii_letters))
            time.sleep(random.uniform(0.5, 2))
            control.send_keys(Keys.BACKSPACE)
        time.sleep(_input_delay())


class RecaptchaLogin(BaseLogin):
    """
    Log into a page that has both username and password inputs visible at the moment of opening.
    Try to be non-deterministic not to alert reCAPTCHA v3.
    """
    def __init__(self,
                 service_name:str,
                 user_input: Locator,
                 password_input: Locator,
                 credentials: Credentials):
        super().__init__(service_name, user_input, password_input, credentials)
        self.login_button : Locator | None = None
        self.error_treshold = Namespace(user=random.uniform(0.01, 0.2),
                                        password=random.uniform(0.01, 0.1))
        self.login_button_treshold = random.uniform(0.01, 0.4)
        self.tab_key_treshold = random.uniform(0.01, 0.4)

    def input_username(self, browser: Browser, username_input_box: WebElement, username: str) -> None:
        """
        Input the username for the service to the input box provided, emulating some inperfections
        :param browser: Browser object
        :param username_input_box: Username input box
        :param username: username
        """
        browser.click_page_element_with_retry_using_js(username_input_box, self.user_input_selector)
        time.sleep(0.5)
        _input_with_error(username_input_box, username, self.error_treshold.user)

    def input_password(self, password_input_box: WebElement, password: str) -> None:
        """
        Input the password for the service to the input box provided, emulating some inperfections
        :param password_input_box:
        :param password: password
        """
        _input_with_error(password_input_box, password, self.error_treshold.password)
        time.sleep(0.5)

    def execute(self, browser: Browser) -> None:
        if self.login_button is None:
            raise RuntimeError('Login button locator must be set before executing reCAPTCHA login strategy')
        username_input = self.find_username_input(browser)
        assert username_input is not None

        password_input = self.find_password_input(browser)
        assert password_input is not None

        username_value, password_value = self.get_credentials()
        self.input_username(browser, username_input, username_value)
        log.web_trace("username-input")
        _move_from_to(browser, username_input, password_input)
        if random.random() < self.tab_key_treshold:
            log.debug('Using <TAB> to move to password input')
            password_input.send_keys(Keys.TAB)
        else:
            log.debug('Using mouse to move to password input')
            browser.click_page_element_with_retry_using_js(password_input, self.user_input_selector)

        self.input_password(password_input, password_value)
        log.web_trace("password-input")
        if random.random() < self.login_button_treshold:
            log.debug('Using <ENTER> to submit a form')
            password_input.send_keys(Keys.ENTER)
        else:
            log.debug('Using mouse to submit a form')
            browser.find_page_element(self.login_button).click()
