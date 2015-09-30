import bpy
import io
import math
import os.path
from .xray_io import ChunkedReader, PackedReader


class ImportContext:
    def __init__(self, camera_animation):
        self.camera_animation = camera_animation


def _import(fpath, cr, cx):
    for (cid, data) in cr:
        if cid == 0x1100:
            pr = PackedReader(data)
            name = pr.gets()
            fr = pr.getf('II')
            fps, ver = pr.getf('fH')
            if ver != 5:
                raise Exception('unsupported anm version: ' + str(ver))
            if not name:
                name = os.path.basename(fpath)
            bpy_obj = bpy.data.objects.new(name, None)
            bpy_obj.rotation_mode = 'ZXY'
            if cx.camera_animation:
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
                pr.getf('BB')
                for _3 in range(pr.getf('H')[0]):
                    v, t, shape = pr.getf('ffB')
                    fc.keyframe_points.insert(t * fps, v * kv)
                    if shape != 4:
                        t, c, b = pr.getf('HHH')
                        pp = pr.getf('HHHH')


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        _import(fpath, ChunkedReader(f.read()), cx)
