"""
    Authentication flow strategies
"""
from .base import BaseLogin
from .one_stage import OneStageLogin
from .two_stage import TwoStageLogin
from .recaptcha import RecaptchaLogin

__all__ = [
    'BaseLogin',
    'OneStageLogin',
    'TwoStageLogin',
    'RecaptchaLogin'
]
