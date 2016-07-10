import argparse
import io
import os.path
import sys
from tkinter import Tk, ttk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def main():
    from utils import defs
    sfmts = ','.join(defs.find_available_formats())
    parser = argparse.ArgumentParser(description='Displays contents of {}-files as treeview'.format(sfmts))
    parser.add_argument('file', help='{}-file'.format(sfmts))
    args = parser.parse_args()
    sch = defs.find_schema(args.file)

    root = Tk()
    root.title('dump-gui')

    tree = ttk.Treeview(root)
    tree['columns'] = ('val',)
    tree.column('val', width=100)
    tree.heading('#0', text='Property')
    tree.heading('val', text='Value')
    ysb = ttk.Scrollbar(root, orient='vertical', command=tree.yview)
    tree.configure(yscroll=ysb.set)

    with io.open(args.file, mode='rb') as f:
        class SinkImpl(defs.Sink):
            def __init__(self, nid, isarray):
                self._nid = nid
                self._isarray = isarray
                self._count = 0

            def val(self, name, value):
                self._ins(self._prep_name(name), value)

            def sub(self, name, kind):
                nid = self._ins(self._prep_name(name))
                r = SinkImpl(nid, kind == defs.Sink.SubKind.ARRAY)
                return r

            def warn(self, msg):
                self._ins('!WARN', str(msg))

            def _prep_name(self, name):
                if name is None:
                    assert self._isarray or (self._nid == '')
                    name = '[%d]' % self._count
                return name

            def _ins(self, text, value=None):
                c = self._count
                r = tree.insert(
                    self._nid, c
                    , text=text, values=(() if value is None else (value,)),
                    open=self._nid == ''
                )
                self._count = c + 1
                return r

        snk = SinkImpl('', False)
        sch.read_raw(os.path.basename(args.file), snk, f.read())

    tree.pack(side='left', fill='both', expand=True)
    ysb.pack(side='right', fill='y')
    root.mainloop()


if __name__ == '__main__':
    main()
