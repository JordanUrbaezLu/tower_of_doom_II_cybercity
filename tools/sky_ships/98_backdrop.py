"""Studio backdrop = OUR ACTUAL IN-GAME SKY (source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr), so a
ship is judged against the busy magenta/indigo nebula and neon city it will really fly in front of, not
against black. Strength is solved from the image's own mean so the backdrop lands near the in-game look
(docs/sky_preview/sky3d_ingame_*.png). Also makes the PLAYER VIEW camera: the reveal framing (ship ~9,000
units away, ~27 degrees up, hfov ~80) that session 61's first-jump camera uses."""
import bpy, math, pathlib
import numpy as np
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXR = ROOT / 'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr'
scene = bpy.context.scene
world = scene.world
nt = world.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
img = bpy.data.images.get('SKY backdrop') or bpy.data.images.load(str(EXR))
img.name = 'SKY backdrop'
# Solve the strength from a small copy (reading 8192x4096 floats here would stall the studio).
probe = img.copy()
probe.scale(256, 128)
px = np.empty(256 * 128 * 4, dtype=np.float32)
probe.pixels.foreach_get(px)
bpy.data.images.remove(probe)
lum = (0.2126 * px[0::4] + 0.7152 * px[1::4] + 0.0722 * px[2::4])
mean = float(lum.mean())
strength = 0.30 / max(mean, 1e-9)
coord = nt.nodes.new('ShaderNodeTexCoord')
mapn = nt.nodes.new('ShaderNodeMapping')
env = nt.nodes.new('ShaderNodeTexEnvironment')
env.image = img
bg = nt.nodes.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = strength
out = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(coord.outputs['Generated'], mapn.inputs['Vector'])
nt.links.new(mapn.outputs['Vector'], env.inputs['Vector'])
nt.links.new(env.outputs['Color'], bg.inputs['Color'])
nt.links.new(bg.outputs['Background'], out.inputs['Surface'])

# The player-view camera, aimed at whichever ship sits at the studio origin.
cam = bpy.data.objects.get('PLAYER VIEW')
if cam is None:
    cd = bpy.data.cameras.new('PLAYER VIEW')
    cam = bpy.data.objects.new('PLAYER VIEW', cd)
    scene.collection.objects.link(cam)
cam['sky_group'] = 'studio'
cam.data.lens_unit = 'FOV'
cam.data.angle = math.radians(80.7)
cam.data.clip_start = 50
cam.data.clip_end = 2.0e6
cam.location = (-2500, -9000, -4600)
cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
print('SKY_BACKDROP mean_lum %.6g strength %.1f' % (mean, strength))
