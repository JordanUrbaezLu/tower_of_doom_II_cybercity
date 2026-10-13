"""MCP-authored editable weapon effect study on the actual Dealer and exported clips.

Review only: never saves over the shipping master. Eevee contact frames and a
keyed warning/discharge scene, with native radius/timing and restrained bloom.
"""
import importlib.util
import math
import pathlib
import json
import os
import bpy
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/dealer_combat/review'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/dealer_boss/dealer_boss.blend'))
exec(compile(pathlib.Path(__file__).with_name('studio.py').read_text(), 'studio.py', 'exec'))
from process_guard import check
check(strict=True)
spec = importlib.util.spec_from_file_location('dc_anim', pathlib.Path(__file__).with_name('anim_preview.py'))
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
A.rest_pose(RIG)
bpy.context.view_layer.update()
os.environ['TOD_DEALER_MASTER_OUT'] = str(OUT/'weapon_study.blend')
exec(compile(pathlib.Path(__file__).with_name('11_weapons.py').read_text(), '11_weapons.py', 'exec'))
del os.environ['TOD_DEALER_MASTER_OUT']
CLIPS = ROOT/'tmp/dealer_combat_stage/xanim_export/tod_dealer'
native = json.loads((CLIPS/'combat_clips.json').read_text())

fx = bpy.data.collections.new('DEALER COMBAT | editable warning and discharge')
scene.collection.children.link(fx)


def emissive(name, color, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Emission Color'].default_value = (*color, 1)
    p.inputs['Emission Strength'].default_value = strength
    p.inputs['Roughness'].default_value = .4
    return mat


red = emissive('DC | oxblood warning', (1, .055, .035), 2)
gold = emissive('DC | discharge core', (1, .45, .1), 3)


def line(name, coords, radius, mat):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = radius
    curve.bevel_resolution = 1
    s = curve.splines.new('POLY')
    s.points.add(len(coords)-1)
    for p, co in zip(s.points, coords):
        p.co = (*co, 1)
    ob = bpy.data.objects.new(name, curve)
    fx.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


ring = []
center = Vector((210, 50, 3))
for i in range(24):
    a = i*math.tau/24
    p = center + Vector((100*math.cos(a), 100*math.sin(a), 0))
    ring.append(line('Warning | bead %02d' % i, [p, p+Vector((0,0,3))], 1.5, red))
arcs = []
for j in range(6):
    a = j*math.tau/6
    coords = [center+Vector((k*14*math.cos(a), k*14*math.sin(a), 7+math.sin(k*2+j)*4)) for k in range(7)]
    arcs.append(line('Discharge | filament %d' % j, coords, .55, gold))
for ob in arcs:
    for frame, size in ((1,.001),(53,.001),(54,1),(67,.001)):
        ob.scale = (size,)*3
        ob.keyframe_insert('scale', frame=frame)
    if ob.animation_data:
        for fc in ob.animation_data.action.fcurves:
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'

camdata = bpy.data.cameras.new('DC | player-height camera')
cam = bpy.data.objects.new('DC | player-height camera', camdata)
fx.objects.link(cam)
cam.location = (365,-280,70)
cam.rotation_euler = (Vector((135,30,38))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.lens = 28
scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 960
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 90
scene.render.image_settings.file_format = 'PNG'
scene.use_nodes = False # no bloom: judge the surface and footprint first

poses = [('shock_warning','tod_dealer_c_shock','dg2',1,15),
         ('shock_release','tod_dealer_c_shock','dg2',1,57),
         ('burst_warning','tod_dealer_c_burst','dingo',2,15),
         ('burst_fire','tod_dealer_c_burst','dingo',2,43)]
measure = {}
for name, clip, weapon, state, frame in poses:
    check(strict=True)
    review_state(state)
    for ob in scene.objects:
        if ob.get('weapon') or ob.name.startswith('Scythe |'):
            hide = ob.get('weapon') != weapon
            ob.hide_viewport = hide; ob.hide_render = hide; ob.hide_set(hide)
    scene.frame_set(frame)
    A.pose_frame(RIG, CLIPS/(clip+'.xanim_bin'), frame)
    bpy.context.view_layer.update()
    tag = RIG.matrix_world @ RIG.pose.bones['tag_weapon_right'].matrix
    muzzle = tag @ Vector(native['weapon_muzzles'][weapon])
    accents = []
    if name == 'shock_warning':
        coords = [tag @ Vector((33+3*math.sin(k),3*math.cos(k),3+3*math.sin(k))) for k in range(12)]
        accents.append(line('Charge | measured DG-2 coils', coords, .4, gold))
    if name == 'burst_fire':
        accents.append(line('Muzzle | measured Dingo flash', [muzzle,muzzle+Vector((8,0,0))],1.2,gold))
        aim = center+Vector((0,0,37))
        accents.append(line('Tracer | locked target', [muzzle.lerp(aim,.45),muzzle.lerp(aim,.60)],.3,gold))
    for ob in arcs:
        ob.hide_render = name != 'shock_release'
    scene.render.filepath = str(OUT / (name+'.png'))
    bpy.ops.render.render(write_still=True)
    measure[name] = dict(clip=clip, weapon=weapon, frame=frame,
                        clip_sha256=native['clips'][clip]['sha256'], weapon_tag=list(tag.translation), muzzle=list(muzzle))
    for ob in accents: bpy.data.objects.remove(ob,do_unlink=True)
scene.frame_set(15)
A.pose_frame(RIG, CLIPS/'tod_dealer_c_burst.xanim_bin', 15)
for ob in arcs: ob.hide_render=True; ob.hide_viewport=True
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.shading.type = 'RENDERED'
            space.shading.use_scene_lights_render = True
            space.shading.use_scene_world_render = True
            space.region_3d.view_perspective = 'CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'dealer_combat.blend'))
(OUT/'review.json').write_text(json.dumps(dict(native_radius=100, tell_seconds=1.8, fps=30,
    bloom=False, preview_only=True, poses=measure), indent=2))
print('DEALER COMBAT REVIEW: actual rig, actual clips, editable 100-unit warning and keyed discharge; native playback untested')
