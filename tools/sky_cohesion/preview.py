"""Open a lightweight Rendered viewport using the finished game sky texture.

Run only after saving/installing the authored master. This replaces this dedicated
studio's in-memory scene; the editable city remains in art/sky3d/tod2_sky.blend.
The existing display bracket is approximate, not an engine exposure verification.
"""
import json
import hashlib
import math
import pathlib
import bpy
ROOT=pathlib.Path(__file__).resolve().parents[2]
stats=json.loads((ROOT/'docs/sky_preview/sky3d_stats.json').read_text())
sc=bpy.context.scene
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob,do_unlink=True)
sc.name='Cybercity sky preview'
sc.use_nodes=False
sc.world=bpy.data.worlds.new('Finished Cybercity panorama')
sc.world.use_nodes=True
n=sc.world.node_tree.nodes;l=sc.world.node_tree.links;n.clear()
coord=n.new('ShaderNodeTexCoord')
sep=n.new('ShaderNodeSeparateXYZ');l.new(coord.outputs['Generated'],sep.inputs[0])
az=n.new('ShaderNodeMath');az.operation='ARCTAN2'
l.new(sep.outputs['X'],az.inputs[0]);l.new(sep.outputs['Y'],az.inputs[1])
u=n.new('ShaderNodeMath');u.operation='MULTIPLY_ADD';u.inputs[1].default_value=1/(2*math.pi);u.inputs[2].default_value=.5
l.new(az.outputs[0],u.inputs[0])
el=n.new('ShaderNodeMath');el.operation='ARCSINE';l.new(sep.outputs['Z'],el.inputs[0])
v=n.new('ShaderNodeMath');v.operation='MULTIPLY_ADD';v.inputs[1].default_value=1/math.pi;v.inputs[2].default_value=.5
l.new(el.outputs[0],v.inputs[0])
uv=n.new('ShaderNodeCombineXYZ');l.new(u.outputs[0],uv.inputs['X']);l.new(v.outputs[0],uv.inputs['Y'])
clamp=n.new('ShaderNodeClamp');clamp.inputs['Min'].default_value=.5/stats['size'][1];clamp.inputs['Max'].default_value=1-.5/stats['size'][1]
l.new(v.outputs[0],clamp.inputs['Value']);l.new(clamp.outputs[0],uv.inputs['Y'])
tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr'),check_existing=False)
tex.image.colorspace_settings.name='Non-Color'
tex.interpolation='Linear';tex.extension='REPEAT';l.new(uv.outputs[0],tex.inputs['Vector'])
scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=stats['display_mult']/stats['preview_gain']
l.new(tex.outputs['Color'],scale.inputs[0])
gamma=n.new('ShaderNodeGamma');gamma.inputs['Gamma'].default_value=1/2.2;l.new(scale.outputs['Vector'],gamma.inputs['Color'])
bg=n.new('ShaderNodeBackground');l.new(gamma.outputs['Color'],bg.inputs['Color']);bg.inputs['Strength'].default_value=1
out=n.new('ShaderNodeOutputWorld');l.new(bg.outputs[0],out.inputs[0])
camd=bpy.data.cameras.new('Title view');camd.type='PERSP';camd.sensor_fit='HORIZONTAL';camd.angle=math.radians(80.69094375281911)
cam=bpy.data.objects.new('Title view',camd);sc.collection.objects.link(cam)
cam.location=(0,0,0);cam.rotation_euler=(math.radians(103),0,-math.radians(stats['roll']));sc.camera=cam
sc.render.engine='BLENDER_EEVEE_NEXT'
sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
sc.render.film_transparent=False
sc.render.use_border=False;sc.render.use_crop_to_border=False
sc.view_settings.view_transform='Raw';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.view_settings.use_curve_mapping=False
sc['preview_note']='Finished native HDR panorama, approximate display bracket. BO3 bloom/exposure and native quality await user playtest.'
sc['editable_city_master']='art/sky3d/tod2_sky.blend'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.shading.type='RENDERED'
            sp.shading.use_scene_world_render=True;sp.shading.use_scene_lights_render=True
            sp.overlay.show_overlays=False;sp.lens=24
            sp.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
            sp.region_3d.view_location=(0,0,0);sp.region_3d.view_distance=1
            sp.region_3d.view_perspective='CAMERA'
            sp.region_3d.view_camera_zoom=28
bpy.context.workspace.name='CYBERCITY SKY PREVIEW'
bpy.data.orphans_purge(do_recursive=True)
path=ROOT/'art/sky3d/sky_preview.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path))
tex.image.filepath=bpy.path.relpath(tex.image.filepath)
bpy.ops.wm.save_as_mainfile(filepath=str(path))
receipt={'engine':sc.render.engine,'viewport':'RENDERED','scene_world':True,'scene_lights':True,
         'pitch_deg':13,'hfov_deg':math.degrees(camd.angle),'view_transform':sc.view_settings.view_transform,
         'shader_gamma':1/2.2,'display_scale':stats['display_mult']/stats['preview_gain'],
         'exr_sha256':hashlib.sha256((ROOT/'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr').read_bytes()).hexdigest(),
         'master':str(path),'native_visual_verified':False}
(ROOT/'art/sky3d/cohesion_review/preview.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('SKY_PREVIEW_READY',sc.render.engine,'RENDERED',path)
