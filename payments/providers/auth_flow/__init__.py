"""
    Authentication flow strategies
"""
from .base import BaseLogin
from .one_stage import OneStageLogin
from .recaptcha import RecaptchaLogin
from .two_stage import TwoStageLogin

__all__ = [
    'BaseLogin',
    'OneStageLogin',
    'TwoStageLogin',
    'RecaptchaLogin'
]
