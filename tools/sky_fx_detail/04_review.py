"""MCP preview of exact staged sprite textures, with editable phase animation.
This is a texture/layer preview, not a claim of BO3 depth, bloom or exposure parity.
"""
import bpy, math, pathlib, json
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'tmp/sky_fx_detail/staged'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'sky_detail.blend'))
scene=bpy.context.scene
for col in scene.collection.children:
    col.hide_render=True
    col.hide_viewport=True
col=bpy.data.collections.new('NATIVE TEXTURE LAYER PREVIEW')
scene.collection.children.link(col)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
scene.cycles.preview_samples=12
scene.render.film_transparent=False
scene.render.use_compositing=False
scene.world.use_nodes=True
w=scene.world.node_tree
w.nodes.clear()
bg=w.nodes.new('ShaderNodeBackground');bg.inputs[0].default_value=(.009,.012,.025,1)
bg.inputs[1].default_value=1
wo=w.nodes.new('ShaderNodeOutputWorld');w.links.new(bg.outputs[0],wo.inputs[0])
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0

def plane(name,image,tint,scale,position,strength):
    bpy.ops.mesh.primitive_plane_add(size=2,location=position)
    obj=bpy.context.object;obj.name=name
    for c in list(obj.users_collection):c.objects.unlink(obj)
    col.objects.link(obj)
    obj.rotation_euler=(math.pi/2,0,0)
    obj.scale=scale
    m=bpy.data.materials.new(name+' - exact export texture')
    m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    out=n.new('ShaderNodeOutputMaterial')
    im=n.new('ShaderNodeTexImage');im.image=bpy.data.images.load(str(OUT/(image+'.png')),check_existing=True)
    im.extension='REPEAT' if 'meteor' in image else 'CLIP'
    multiply=n.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1;multiply.inputs[2].default_value=(*tint,1)
    emit=n.new('ShaderNodeEmission');emit.inputs[1].default_value=strength
    trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
    l.new(im.outputs['Color'],multiply.inputs[1]);l.new(multiply.outputs[0],emit.inputs[0])
    l.new(im.outputs['Alpha'],mix.inputs[0]);l.new(trans.outputs[0],mix.inputs[1]);l.new(emit.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0])
    obj.data.materials.append(m)
    return obj

void=plane('Absorbing aperture','i_tod_sky_rift_void',(0,0,0),(.53,.53,1),(-.6,-.03,.1),0)
fibre=plane('Broken cyan violet orbital filaments','i_tod_sky_rift_fibre',(.52,.46,1),(1.45,1.45,1),(-.6,0,.1),1.3)
dust=plane('Faint accretion wisps','i_tod_sky_rift_dust',(.24,.48,1),(1.67,1.67,1),(-.6,.02,.1),.6)
meteor=plane('Ion wake - three lengths use the same native map','i_tod_sky_meteor_wake',(.62,.8,1),(1.1,.20,1),(1.35,-.08,-1.25),1.6)
meteor.rotation_euler.y=-.25
for ob in (fibre,dust,void):
    base=ob.scale.copy()
    for frame,k in ((1,.06),(12,.6),(20,1),(33,1),(42,.7),(49,.04)):
        ob.scale=base*k;ob.keyframe_insert(data_path='scale',frame=frame)
    if ob!=void:
        ob.rotation_euler.y=0;ob.keyframe_insert(data_path='rotation_euler',frame=1)
        ob.rotation_euler.y=.8 if ob==fibre else -.45;ob.keyframe_insert(data_path='rotation_euler',frame=49)

cam=scene.camera
cam.hide_set(False);cam.hide_render=False
cam.location=(.15,-8,.15)
cam.rotation_euler=(Vector((.15,0,.15))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=5.2
scene.render.resolution_x=960;scene.render.resolution_y=640
scene.frame_start=1;scene.frame_end=49;scene.render.fps=24
scene['preview_limit']='Exact exported image alpha/color and layer shapes; approximate native tint. BO3 exposure, lens distortion, stock lightning, OIT and bloom require user playtest.'
scene.frame_set(25)
scene.render.filepath=str(OUT/'detail_preview.png')
bpy.ops.render.render(write_still=True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active
            sp.shading.type='RENDERED';sp.shading.use_scene_world_render=True;sp.shading.use_scene_lights_render=True
            sp.overlay.show_overlays=False
            sp.region_3d.view_perspective='CAMERA'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'sky_detail_preview.blend'))
print('SKY DETAIL PREVIEW READY - exact textures / native exposure unverified')
