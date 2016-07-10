from utils import defs
from . import skl

__all__ = [
    'SCHEMA',
]

SCHEMA = defs.Simple({
    0x1100: ('motion', skl.CSMotion())
})
