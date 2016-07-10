from utils import defs
from . import skl

__all__ = [
    'SCHEMA',
]

SCHEMA = defs.Simple({
    0x0810: ('version', 'H'),
    0x0812: ('params', (
        ('format', 'I'),
        ('flags', 'I'),
        ('border_color', 'I'),
        ('fade_color', 'I'),
        ('fade_amount', 'I'),
        ('mip_filter', 'I'),
        ('width', 'I'),
        ('height', 'I'),
    )),
    0x0813: ('type', 'I'),
    0x0814: ('texture_type', 'I'),
    0x0815: ('detail', (
        ('name', 'S'),
        ('scale', 'f'),
    )),
    0x0816: ('material', (
        ('id', 'I'),
        ('weight', 'f'),
    )),
    0x0817: ('bump', (
        ('height', 'f'),
        ('mode', 'I'),
        ('name', 'S'),
    )),
    0x0818: ('normal_map', 'S'),
    0x0819: ('fade_delay', 'B'),
})
