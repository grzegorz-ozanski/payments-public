"""
    All supported providers
"""
from .actum import Actum
from .energa import Energa
from .multimedia import Multimedia
from .nordhome import Nordhome
from .opec import Opec
from .pewik import Pewik
from .pgnig import Pgnig
from .provider import Provider
from .vectra import Vectra

__all__ = [
    'Provider',
    'Actum',
    'Energa',
    'Multimedia',
    'Nordhome',
    'Opec',
    'Pgnig',
    'Pewik',
    'Vectra'
]


def all_lower() -> list[str]:
    """
    Returns the list of all supported providers
    """
    return [name.lower() for name in __all__ if name != 'Provider']
