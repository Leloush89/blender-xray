import enum
import importlib
import os
from io_scene_xray.xray_io import ChunkedReader, PackedReader


class Sink:
    class SubKind(enum.Enum):
        OBJECT = 0
        ARRAY = 1

    def val(self, name, value):
        pass

    def sub(self, name, kind=None):
        pass

    def warn(self, msg):
        pass


class Def:
    def read(self, name, sink, pr):
        pass

    def read_raw(self, name, sink, data):
        pr = PackedReader(data)
        self.read(name, sink, pr)
        rm = pr.remaining()
        if rm:
            mx = min(rm, 256)
            sink.warn('{} has {} byte(s) unparsed: {}'.format(name, rm, pr.getb(mx)))


class Value(Def):
    def __init__(self, fmt):
        self._format = fmt

    def read(self, name, sink, pr):
        fmt = self._format
        if fmt == 'S':
            v = pr.gets()
        else:
            v = pr.getf(fmt)
            if len(v) == 1:
                v = v[0]
        sink.val(name, v)


class Struct(Def):
    def __init__(self, structure):
        assert len(structure) != 0
        self._struct = structure

    def read(self, name, sink, pr):
        snk = sink.sub(name, kind=Sink.SubKind.OBJECT)
        self._read_packed(snk, pr)

    def _read_packed(self, sink, pr):
        Struct.read_structure(sink, pr, self._struct)

    @staticmethod
    def read_structure(sink, pr, structure):
        for e in structure:
            e[1].read(e[0], sink, pr)

    @staticmethod
    def simple(schema):
        return tuple((e if isinstance(e[1], Def) else (e[0], Simple(e[1]))) for e in schema)


class Array(Def):
    def __init__(self, length, structure):
        self._length = length
        self._struct = structure

    def read(self, name, sink, pr):
        snk = sink.sub(name, kind=Sink.SubKind.ARRAY)
        length = self._length
        if isinstance(length, str):
            length = pr.getf(length)[0]
        while length != 0:
            self._struct.read(None, snk, pr)
            length -= 1


class Chunked(Def):
    def __init__(self, schema):
        self._schema = schema

    def read(self, name, sink, pr):
        snk = sink.sub(name, kind=Sink.SubKind.OBJECT)
        for cid, cdata in ChunkedReader(pr.getb(pr.remaining())):
            s = self._schema.get(cid, self)
            if s is self:
                s = self._schema.get(None, self)
            if s is self:
                snk.warn('{} has unknown chunk {:#x}: {}'.format(name, cid, cdata[:256]))
                continue
            n = s[0]
            if n is None:
                n = str(cid)
            s[1].read_raw(n, snk, cdata)


# noinspection PyPep8Naming
def Simple(schema):
    t = type(schema)
    if t == tuple:
        return Struct(Struct.simple(schema))
    if t == list:
        return Array(schema[0], Simple(schema[1]))
    if t == dict:
        return Chunked({k: (v[0], Simple(v[1])) for k, v in schema.items()})
    if isinstance(schema, str):
        return Value(schema)
    return schema


def find_available_formats():
    from . import schemas
    formats = []
    for f in os.listdir(os.path.dirname(schemas.__file__)):
        if (f == '__init__.py') or not f.endswith('.py'):
            continue
        formats.append(f[:-3])
    formats.sort()
    return formats


def find_schema(file_name):
    ext = os.path.splitext(file_name)[-1]
    m = importlib.import_module('utils.schemas' + ext)
    return m.SCHEMA
