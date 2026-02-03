"""
    Human-like mouse move using B-spline curves
"""
import random
import time

import numpy as np
import scipy.interpolate as si
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webelement import WebElement

from browser import Browser, setup_logging

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


def _ensure_not_constant_axis(points: np.ndarray, axis: int, start: list[int], end: list[int]) -> np.ndarray:
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

    divisor = random.choice((2, 3, 4))  # take a mid, third or quarter point
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


def move_from_to(browser: Browser,
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
    points = _ensure_not_constant_axis(points, axis=0, start=start, end=end)
    points = _ensure_not_constant_axis(points, axis=1, start=start, end=end)
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
