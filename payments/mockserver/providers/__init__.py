"""
    Mock providers module
"""
from .actum.actum import bp as actum_bp
from .nordhome.nordhome import bp as nordhome_bp
from .opec.opec import bp as opec_bp
from .pewik.pewik import bp as pewik_bp
__all__ = [
    'actum_bp',
    'nordhome_bp',
    'opec_bp',
    'pewik_bp',
]
