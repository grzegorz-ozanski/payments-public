"""
    Mock providers module
"""
from .actum.actum import bp as actum_bp
from .multimedia.multimedia import bp as multimedia_bp
from .nordhome.nordhome import bp as nordhome_bp
from .opec.opec import bp as opec_bp
from .pgnig.pgnig import bp as pgnig_bp
from .pewik.pewik import bp as pewik_bp
__all__ = [
    'actum_bp',
    'multimedia_bp',
    'nordhome_bp',
    'opec_bp',
    'pgnig_bp',
    'pewik_bp',
]
