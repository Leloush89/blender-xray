from utils import defs
from . import skl

__all__ = [
    'SCHEMA',
]

SCHEMA = defs.Array('I', skl.CSMotion())
