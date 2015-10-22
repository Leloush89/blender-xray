import bpy
from collections import namedtuple
import io
import math
import mathutils
import os.path
import random
from .xray_io import ChunkedReader, PackedReader
from .xray_io import ChunkedWriter, PackedWriter


class Context:
    def __init__(self, as_camera_animation):
        self.as_camera_animation = as_camera_animation


class Behaviour:
    RESET = 0
    CONSTANT = 1
    REPEAT = 2
    OSCILLATE = 3
    OFFSET_REPEAT = 4
    LINEAR = 5

    @staticmethod
    def value_to_name(cls, value):
        for n in dir(cls):
            if getattr(cls, n) == value:
                return n


class Shape:
    TCB = 0  # Kochanek-Bartels
    HERMITE = 1
    BEZIER_1D = 2  # obsolete, equivalent to HERMITE
    LINEAR = 3
    STEPPED = 4
    BEZIER_2D = 5


__ImpTcb = namedtuple('__ImpTcb', 't c b')
__ImpBez = namedtuple('__ImpBez', 'lx ly rx ry')
__ImpData = namedtuple('__ImpData', 'sh tcb bez')


def import_envelope(fc, pr, koef=mathutils.Vector((1, 1)), warn=print):
    bb = pr.getf('BB')

    if bb[0] != bb[1]:
        warn('different behaviours: ' + Behaviour.value_to_name(bb[0]) + '-' + Behaviour.value_to_name(bb[1]))
        bb[1] = bb[0]
    if bb[0] == Behaviour.CONSTANT:
        fc.extrapolation = 'CONSTANT'
    elif bb[0] == Behaviour.LINEAR:
        fc.extrapolation = 'LINEAR'
    else:
        bb = (Behaviour.CONSTANT, Behaviour.CONSTANT)
        warn(Behaviour.value_to_name(bb[0]) + '-behaviour not supported, replaced with CONSTANT')
        fc.extrapolation = 'CONSTANT'

    fckf = fc.keyframe_points
    data = []
    rq = lambda: pr.getf('H')[0] / 1024 - 32
    sh = 0
    for j in range(pr.getf('H')[0]):
        v, t, sh = pr.getf('ffB')
        kf = fckf.insert(t * koef.x, v * koef.y)
        tcb, bez = None, None
        if sh != 4:
            tcb = __ImpTcb(rq(), rq(), rq())
            bez = __ImpBez(rq(), rq(), rq(), rq())
        data.append(__ImpData(sh, tcb, bez))
    data.append(__ImpData(sh, None, None))

    def fo(k0p, k0, k1, di, i):
        if di.sh == Shape.TCB:
            a = (1 - di.tcb.t) * (1 + di.tcb.c) * (1 + di.tcb.b)
            b = (1 - di.tcb.t) * (1 - di.tcb.c) * (1 - di.tcb.b)
            d = k1[i] - k0[i]
            if k0p:
                t = (k1.x - k0.x) / (k1.x - k0p.x)
                return t * (a * (k0[i] - k0p[i]) + b * d)
            return b * d
        elif di.sh == Shape.LINE:
            d = k1.y - k0.y
            if k0p:
                t = (k1.x - k0.x) / (k1.x - k0p.x)
                return t * (k0.y - k0p.y + d)
            return d
        elif (di.sh == Shape.BEZIER_1D) or (di.sh == Shape.HERMITE):
            out = di.bez.ly
            if k0p:
                out *= (k1.x - k0.x) / (k1.x - k0p.x)
            return out
        elif di.sh == Shape.BEZIER_2D:
            out = di.bez.ry * (k1.x - k0.x)
            if math.fabs(di.bez.rx) > 1e-5:
                out /= di.bez.rx
            else:
                out *= 1e+5
            return out
        elif di.sh == Shape.STEPPED:
            return 0
        else:
            warn('unknown shape: ' + str(di.sh))

    def fi(k0, k1, k1n, di, i):
        if di.sh == Shape.TCB:
            a = (1 - di.tcb.t) * (1 - di.tcb.c) * (1 + di.tcb.b)
            b = (1 - di.tcb.t) * (1 + di.tcb.c) * (1 - di.tcb.b)
            d = k1[i] - k0[i]
            if k1n:
                t = (k1.x - k0.x) / (k1n.x - k0.x)
                return t * (b * (k1n[i] - k1[i]) + a * d)
            return a * d
        elif di.sh == Shape.LINE:
            d = k1.y - k0.y
            if k1n:
                t = (k1.x - k0.x) / (k1n.x - k0.x)
                return t * (k1n.y - k1.y + d)
            return d
        elif (di.sh == Shape.BEZIER_1D) or (di.sh == Shape.HERMITE):
            inp = di.bez.lx
            if k1n:
                inp *= (k1.x - k0.x) / (k1n.x - k0.x)
            return inp
        elif di.sh == Shape.BEZIER_2D:
            inp = di.bez.ly * (k1.x - k0.x)
            if math.fabs(di.bez.lx) > 1e-5:
                inp /= di.bez.lx
            else:
                inp *= 1e+5
            return inp
        elif di.sh == Shape.STEPPED:
            return 0
        else:
            warn('unknown shape: ' + str(di.sh))

    i, h = 0, len(fckf) - 1
    for i in range(h):
        kf0, kf1 = fckf[i], fckf[i + 1]
        kf0.handle_left_type = 'FREE'
        kf1.handle_right_type = 'FREE'
        d0, d1 = data[i], data[i + 1]
        if (d1.sh == Shape.TCB) or (d1.sh == Shape.HERMITE) or (d1.sh == Shape.BEZIER_1D):
            print(d0, d1)
            kf0.interpolation = 'BEZIER'
            outx = fo(None if i == 0 else fckf[i - 1].co, kf0.co, kf1.co, d0, 0)
            outy = fo(None if i == 0 else fckf[i - 1].co, kf0.co, kf1.co, d0, 1)
            inpx = fi(kf0.co, kf1.co, fckf[i + 2].co if i < (h - 1) else None, d1, 0)
            inpy = fi(kf0.co, kf1.co, fckf[i + 2].co if i < (h - 1) else None, d1, 1)
            print(outx, outy, inpx, inpy)
            kf0.handle_right = kf0.co + mathutils.Vector((outx, outy))
            kf1.handle_left = kf1.co - mathutils.Vector((inpx, inpy))
            # warn('todo' + str(d1))
        elif d1.sh == Shape.LINEAR:
            kf0.interpolation = 'LINEAR'
            warn('todo' + str(d1))
        elif d1.sh == Shape.STEPPED:
            kf0.interpolation = 'CONSTANT'
            warn('todo' + str(d1))
        elif d1.sh == Shape.BEZIER_2D:
            kf0.interpolation = 'BEZIER'
            kf0.handle_right = kf0.co + mathutils.Vector((d0.bez.rx * koef.x, d0.bez.ry * koef.y))
            kf1.handle_left = kf1.co + mathutils.Vector((d1.bez.lx * koef.x, d1.bez.ly * koef.y))


def _import(fpath, cr, cx):
    for (cid, data) in cr:
        if cid == 0x1100:
            pr = PackedReader(data)
            name = pr.gets()
            fr = pr.getf('II')
            fps, ver = pr.getf('fH')
            # print(fps)
            if ver != 5:
                raise Exception('unsupported anm version: ' + str(ver))
            if not name:
                name = os.path.basename(fpath)
            bpy_obj = bpy.data.objects.new(name, None)
            bpy_obj.rotation_mode = 'ZXY'
            if cx.as_camera_animation:
                bpy_cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
                bpy_cam.parent = bpy_obj
                bpy_cam.rotation_euler = (math.pi / 2, 0, 0)
                bpy.context.scene.objects.link(bpy_cam)
            else:
                bpy_obj.empty_draw_type = 'SPHERE'
            bpy_obj.empty_draw_size = 0.5
            bpy.context.scene.objects.link(bpy_obj)
            a = bpy.data.actions.new(name=name)
            bpy_obj.animation_data_create().action = a
            fcs = (
                a.fcurves.new('location', 0, name),
                a.fcurves.new('location', 1, name),
                a.fcurves.new('location', 2, name),
                a.fcurves.new('rotation_euler', 0, name),
                a.fcurves.new('rotation_euler', 1, name),
                a.fcurves.new('rotation_euler', 2, name)
            )

            for i in range(6):
                fc = fcs[(0, 2, 1, 5, 3, 4)[i]]
                kv = (1, 1, 1, -1, 1, 1)[i]
                import_envelope(fc, pr, koef=mathutils.Vector((fps, kv)))


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        _import(fpath, ChunkedReader(f.read()), cx)


def _export(bpy_obj, cw, cx):
    pw = PackedWriter()
    pw.puts('')
    bpy_act = bpy_obj.animation_data.action
    fr = bpy_act.frame_range
    fr = (0, 300)
    pw.putf('II', int(fr[0]), int(fr[1]))
    fps = 30
    pw.putf('fH', fps, 5)

    mq = lambda v: int((max(min(v, 32), -32) + 32) * 65536) // 64
    rnd = lambda: random.random() * 2.0 - 1.0
    for i in range(6):
        fc = bpy_act.fcurves[(0, 2, 1, 5, 3, 4)[i]]
        kv = (1, 1, 1, -1, 1, 1)[i]
        pw.putf('BB', 1, 1)

        if i == 2:
            pw.putf('H', 5)
            for _ in range(5):
                pw.putf('ffB', rnd() * 2 - 1, _ * 2, Shape.TCB)
                pw.putf('HHH', mq(rnd()), mq(rnd()), mq(rnd()))
                pw.putf('HHHH', 32768, 32768, 32768, 32768)
        elif i == 0:
            pw.putf('H', 2)
            pw.putf('ffB', -10, 0, Shape.LINEAR)
            pw.putf('HHH', 32768, 32768, 32768)
            pw.putf('HHHH', 32768, 32768, 32768, 32768)
            pw.putf('ffB', 10, 10, Shape.LINEAR)
            pw.putf('HHH', 32768, 32768, 32768)
            pw.putf('HHHH', 32768, 32768, 32768, 32768)
        else:
            pw.putf('H', 1)
            pw.putf('ffB', 0, 0, Shape.STEPPED)
        # fckf = fc.keyframe_points
        # pw.putf('H', len(fckf))
        # for p in fckf:
        #     pw.putf('ffB', p.co.y / kv, p.co.x / fps, 5)
        #     pw.putf('HHH', 32768, 32768, 32768)
        #     dl, dr = p.handle_left - p.co, p.handle_right - p.co
        #     pw.putf('HHHH', *map(mq, (dl.x / fps, dl.y, dr.x / fps, dr.y)))
    cw.put(0x1100, pw)


def export_file(bpy_obj, fpath, cx):
    with io.open(fpath, 'wb') as f:
        cw = ChunkedWriter()
        _export(bpy_obj, cw, cx)
        f.write(cw.data)
