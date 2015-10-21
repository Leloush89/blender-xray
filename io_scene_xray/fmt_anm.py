import bpy
import io
import math
import mathutils
import os.path
from .xray_io import ChunkedReader, PackedReader
from .xray_io import ChunkedWriter, PackedWriter


class Context:
    def __init__(self, as_camera_animation):
        self.as_camera_animation = as_camera_animation


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

            def update_kf_r(kp, kc, kn, tcb):
                a = (1 - tcb[0]) * (1 + tcb[1]) * (1 + tcb[2])
                b = (1 - tcb[0]) * (1 - tcb[1]) * (1 - tcb[2])
                dx, dy = kn.co.x - kc.co.x, kn.co.y - kc.co.y
                tx, ty = 0, 0
                # print(a, b, dx, dy)
                if kp:
                    t = (kn.co.x - kc.co.x) / (kn.co.x - kp.co.x)
                    tx = t * (a * (kc.co.x - kp.co.x) + b * dx)
                    ty = t * (a * (kc.co.y - kp.co.y) + b * dy)
                else:
                    tx = b * dx
                    ty = b * dy
                kc.handle_right = kc.co + mathutils.Vector((tx, ty))
                # print(kc.co, kc.handle_right, sh, tcb, pp, tx, ty)

            def update_kf_l(kp, kc, kn, tcb):
                a = (1 - tcb[0]) * (1 - tcb[1]) * (1 + tcb[2])
                b = (1 - tcb[0]) * (1 + tcb[1]) * (1 - tcb[2])
                dx, dy = kc.co.x - kp.co.x, kc.co.y - kp.co.y
                tx, ty = 0, 0
                # print(a, b, dx, dy)
                if kn:
                    t = (kc.co.x - kp.co.x) / (kn.co.x - kp.co.x)
                    tx = t * (b * (kn.co.x - kc.co.x) + a * dx)
                    ty = t * (b * (kn.co.y - kc.co.y) + a * dy)
                else:
                    tx = a * dx
                    ty = a * dy
                kc.handle_left = kc.co - mathutils.Vector((tx, ty))
                # print(kc.co, kc.handle_left, sh, tcb, pp, tx, ty)

            for i in range(6):
                fc = fcs[(0, 2, 1, 5, 3, 4)[i]]
                kv = (1, 1, 1, -1, 1, 1)[i]
                bb = pr.getf('BB')
                fckf = fc.keyframe_points
                ppkf, pkf, sh, tcb, pp = None, None, None, None, None
                tcbs, pps = [], []
                for j in range(pr.getf('H')[0]):
                    v, t, sh = pr.getf('ffB')
                    # print(v, t, sh)
                    kf = fckf.insert(t * fps, v * kv)
                    kf.handle_left_type = 'FREE'
                    kf.handle_right_type = 'FREE'
                    if sh != 4:
                        tcb = tuple((x * 64 / 65536 - 32) for x in pr.getf('HHH'))
                        pp = tuple((x * 64 / 65536 - 32) for x in pr.getf('HHHH'))
                    tcbs.append(tcb)
                    pps.append(pp)
                    psh = sh
                    ppkf = pkf
                    pkf = kf
                h = len(fckf) - 1
                for i in range(h):
                    update_kf_r(fckf[i - 1] if i > 0 else None, fckf[i], fckf[i + 1], tcbs[i])
                    update_kf_l(fckf[i], fckf[i + 1], fckf[i + 2] if i < (h - 1) else None, tcbs[i + 1])


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        _import(fpath, ChunkedReader(f.read()), cx)


def _export(bpy_obj, cw, cx):
    pw = PackedWriter()
    pw.puts('')
    bpy_act = bpy_obj.animation_data.action
    fr = bpy_act.frame_range
    pw.putf('II', int(fr[0]), int(fr[1]))
    fps = 30
    pw.putf('fH', fps, 5)

    for i in range(6):
        fc = bpy_act.fcurves[(0, 2, 1, 5, 3, 4)[i]]
        kv = (1, 1, 1, -1, 1, 1)[i]
        pw.putf('BB', 1, 1)
        fckf = fc.keyframe_points
        pw.putf('H', len(fckf))
        print(i)
        for p in fckf:
            pw.putf('ffB', p.co.y / kv, p.co.x / fps, 5)
            pw.putf('HHH', 32768, 32768, 32768)
            dl, dr = p.handle_left - p.co, p.handle_right - p.co
            print(dl, dr)
            pw.putf('HHHH', *tuple(((int(max(min(x, 32), -32)) + 32) * 65536 // 64) for x in [dl.x/fps, dl.y, dr.x/fps, dr.y]))
    cw.put(0x1100, pw)


def export_file(bpy_obj, fpath, cx):
    with io.open(fpath, 'wb') as f:
        cw = ChunkedWriter()
        _export(bpy_obj, cw, cx)
        f.write(cw.data)
