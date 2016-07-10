import argparse
import io
import json
import os.path
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def main():
    from utils import defs
    sfmts = ','.join(defs.find_available_formats())
    parser = argparse.ArgumentParser(description='Converts contents of {}-files to JSON-like text'.format(sfmts))
    parser.add_argument('--strict', action='store_true', dest='strict', help='Generate strict-json file')
    parser.add_argument('file', help='{}-file'.format(sfmts))
    args = parser.parse_args()
    sch = defs.find_schema(args.file)
    with io.open(args.file, mode='rb') as f:
        firstmsg = True

        def printnn(msg):
            sys.stdout.write(msg)

        def printfnn(msg):
            nonlocal firstmsg
            if firstmsg:
                firstmsg = False
            else:
                sys.stdout.write('\n')
            printnn(msg)

        class SinkImpl(defs.Sink):
            _TAB = '  '

            def __init__(self, offset=0, isarray=False):
                self._offset = offset
                self._offs_v = self._TAB * offset
                self._offs_e = self._TAB * max(0, offset - 1)
                self._pending = None
                self._isarray = isarray
                self._ndcomma = False
                self._lsissub = False
                self._finishd = False

            def val(self, name, value):
                self.complete()
                self.finprev()
                if isinstance(value, str):
                    value = json.dumps(value)
                else:
                    value = str(value)
                printfnn(self._offs_v + self._prep_name(name) + value)
                self._ndcomma = True
                self._lsissub = False

            def sub(self, name, kind):
                assert kind is not None
                self.complete()
                fp = self.finprev()
                braces = {
                    defs.Sink.SubKind.OBJECT: ('{', '}'),
                    defs.Sink.SubKind.ARRAY: ('[', ']'),
                }[kind]
                if self._isarray:
                    if fp:
                        printnn(' ')
                    printnn(braces[0])
                else:
                    printfnn(self._offs_v + self._prep_name(name) + braces[0])
                r = SinkImpl(self._offset + (0 if self._isarray else 1), isarray=braces[0] == '[')
                self._pending = (r, braces[1])
                self._lsissub = True
                return r

            def finprev(self):
                if self._ndcomma:
                    printnn(',')
                    self._ndcomma = False
                    return True
                return False

            def complete(self):
                p = self._pending
                if p:
                    p[0].finish()
                    printnn(p[1])
                    self._pending = None
                    self._ndcomma = True

            def finish(self):
                self.complete()
                if not self._lsissub or not self._isarray:
                    printfnn(self._offs_e)
                self._finishd = True

            def warn(self, msg):
                self.complete()
                printfnn(self._offs_v + '!WARN: ' + str(msg))

            def _prep_name(self, name):
                if name is None:
                    assert self._isarray or (self._offset == 0)
                    return ''
                if args.strict:
                    name = json.dumps(name)
                return name + ': '

        snk = SinkImpl()
        sch.read_raw(None, snk, f.read())
        snk.complete()
        printfnn('')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
