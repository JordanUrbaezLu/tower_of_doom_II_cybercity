"""Visible, rendered fleet studio using shipping maps/native gloss and the actual Cybercity EXR.

This is a native-material approximation: Blender does not reproduce BO3's BRDF,
probes, dynamic lighting or exposure. Saves a separate review .blend, never the master.
"""
import bpy, sys, pathlib, math, json
import numpy as np
from mathutils import Vector
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/art_cohesion'))
import native_preview
job_path=ROOT/'tmp/sky_realism/live_job.json'
job=json.loads(job_path.read_text()) if job_path.exists() else {}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/job.get('source_blend','art/sky_ships/sky_fleet.blend')))
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = -1
scene.use_nodes = False
scene.render.use_compositing = False
gdt = ROOT/job.get('gdt','source_data/tod_sky_ships.gdt')
gdt_text = gdt.read_text()
mats={m.name:native_preview.fullspec(gdt,m.name,ROOT/job['images'] if job.get('images') else None) for m in list(bpy.data.materials)
      if m.name.startswith('mtl_tod_sky_') and ('"'+m.name+'" ( "material.gdf" )') in gdt_text}
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        for slot in ob.material_slots:
            if slot.material and slot.material.name in mats: slot.material=mats[slot.material.name]
for c in bpy.data.collections:
    if c.name.startswith(('SHIP ', 'ROCK ')):
        c.hide_viewport = c.hide_render = c.name != 'SHIP dreadnought'
world = scene.world or bpy.data.worlds.new('Cybercity actual sky')
scene.world = world
world.use_nodes = True
n,l=world.node_tree.nodes,world.node_tree.links
n.clear()
env=n.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(str(ROOT/'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr'),check_existing=True)
probe=env.image.copy();probe.scale(256,128)
pixels=np.empty(256*128*4,dtype=np.float32);probe.pixels.foreach_get(pixels)
mean=float((pixels[0::4]*.2126+pixels[1::4]*.7152+pixels[2::4]*.0722).mean())
bpy.data.images.remove(probe)
bg=n.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.30/max(mean,1e-9)
out=n.new('ShaderNodeOutputWorld');l.new(env.outputs['Color'],bg.inputs['Color']);l.new(bg.outputs[0],out.inputs[0])
cam=bpy.data.objects.get('PLAYER VIEW') or bpy.data.objects.new('PLAYER VIEW',bpy.data.cameras.new('PLAYER VIEW'))
if not cam.users_collection:scene.collection.objects.link(cam)
cam.data.clip_start,cam.data.clip_end=20,2e6
cam.data.angle=math.radians(65)
col=bpy.data.collections['SHIP dreadnought']
target=Vector(col['offset'])
cam.location=target+Vector((4000,-11500,-4700))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
scene.camera=cam
scene['preview_limit']=native_preview.DESCRIPTION+'; actual Cybercity EXR, no BO3 exposure parity'
for win in bpy.context.window_manager.windows:
    for area in win.screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active
            sp.shading.type='RENDERED'
            sp.shading.use_scene_world_render=True
            sp.shading.use_scene_lights_render=True
            sp.shading.use_compositor='DISABLED'
            sp.clip_end=2e6
            sp.region_3d.view_perspective='CAMERA'
            sp.region_3d.view_camera_zoom=0
            sp.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/sky_ships/sky_fleet_realism_preview.blend'))
scene.render.filepath=str(ROOT/'art/sky_ships/review/realism/live_cybercity_preview.png')
bpy.ops.render.render(write_still=True)
print('FLEET_LIVE_PREVIEW_READY',scene['preview_limit'])
