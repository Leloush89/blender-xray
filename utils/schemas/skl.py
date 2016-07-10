from utils import defs

__all__ = [
    'SCHEMA',
    'CSMotion',
]


class CSMotion(defs.Struct):
    _HEADER = defs.Struct.simple((
        ('name', 'S'),
        ('range', (
            ('start', 'I'),
            ('end', 'I'),
        )),
        ('fps', 'f'),
    ))

    class _ShapeKey(defs.Struct):
        _HEADER = defs.Struct.simple((
            ('value', 'f'),
            ('time', 'f'),
        ))

        class _Q16(defs.Def):
            def read(self, name, sink, pr):
                sink.val(name, pr.getf('H')[0] * 64 / 65536 - 32)

        _ADVANCED = defs.Struct.simple((
            ('tension', _Q16()),
            ('continuity', _Q16()),
            ('bias', _Q16()),
            ('params', [4, _Q16()]),
        ))

        def __init__(self):
            super().__init__(self._HEADER)

        def _read_packed(self, sink, pr):
            super()._read_packed(sink, pr)
            sh = pr.getf('B')[0]
            sink.val('shape', sh)
            if sh != 4:
                defs.Struct.read_structure(sink, pr, self._ADVANCED)

    _ENVS = defs.Simple([6, (
        ('behaviours', [2, 'B']),
        ('keys', ['H', _ShapeKey()]),
    )])
    _DATA_V = {
        5: defs.Struct.simple((
            ('envelopes', _ENVS),
        )),
        6: defs.Struct.simple((
            ('flags', 'B'),
            ('bonepart', 'H'),
            ('speed', 'f'),
            ('accrue', 'f'),
            ('falloff', 'f'),
            ('power', 'f'),
            ('bmotions', ['H', (
                ('bone', 'S'),
                ('flags', 'B'),
                ('envelopes', _ENVS),
            )]),
        )),
    }

    _MARKS = defs.Simple(['I', (
        ('name', 'S'),
        ('intervals', ['I', [2, 'f']]),
    )])

    def __init__(self):
        super().__init__(self._HEADER)

    def _read_packed(self, sink, pr):
        super()._read_packed(sink, pr)
        ver = pr.getf('H')[0]
        sink.val('version', ver)
        d = self._DATA_V.get(min(ver, 6), self)
        if d is self:
            raise Exception('unsupported version: {}'.format(ver))
        defs.Struct.read_structure(sink, pr, d)
        if ver >= 7:
            self._MARKS.read('marks', sink, pr)


SCHEMA = defs.Simple({
    0x1200: ('motion', CSMotion())
})
