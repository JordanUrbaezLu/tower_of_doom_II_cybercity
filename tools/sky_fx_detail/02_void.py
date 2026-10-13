"""MCP continuation: author the soft black occlusion aperture separately.

Black RGB with smoothly varying alpha is an absorbing surface for BO3's
premultiplied effect blend. It is not an emissive black additive sprite.
"""
import bpy, pathlib, json, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'tmp/sky_fx_detail/staged'
scene=bpy.context.scene
scene.render.dither_intensity=0
for c in scene.collection.children: c.hide_render=True
col=bpy.data.collections.new('Rift absorbing aperture')
scene.collection.children.link(col)
bpy.ops.mesh.primitive_plane_add(size=2)
o=bpy.context.object
o.name='Soft absorbing horizon - alpha falloff'
for c in list(o.users_collection): c.objects.unlink(o)
col.objects.link(o)
m=bpy.data.materials.new('Black RGB / soft alpha horizon')
m.use_nodes=True
n=m.node_tree.nodes
n.clear()
out=n.new('ShaderNodeOutputMaterial')
tex=n.new('ShaderNodeTexCoord')
dist=n.new('ShaderNodeVectorMath'); dist.operation='DISTANCE';dist.inputs[1].default_value=(.5,.5,0)
ramp=n.new('ShaderNodeMapRange')
ramp.interpolation_type='SMOOTHERSTEP'
ramp.inputs['From Min'].default_value=.36
ramp.inputs['From Max'].default_value=.46
ramp.inputs['To Min'].default_value=1
ramp.inputs['To Max'].default_value=0
mix=n.new('ShaderNodeMixShader')
t=n.new('ShaderNodeBsdfTransparent')
black=n.new('ShaderNodeEmission'); black.inputs['Color'].default_value=(0,0,0,1)
links=m.node_tree.links
links.new(tex.outputs['UV'],dist.inputs[0])
links.new(dist.outputs['Value'],ramp.inputs['Value'])
links.new(ramp.outputs['Result'],mix.inputs[0])
links.new(t.outputs[0],mix.inputs[1]);links.new(black.outputs[0],mix.inputs[2])
links.new(mix.outputs[0],out.inputs[0])
o.data.materials.append(m)
scene.frame_set(1)
scene.render.resolution_x=scene.render.resolution_y=512
scene.render.filepath=str(OUT/'i_tod_sky_rift_void.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'sky_detail.blend'))
manifest=json.loads((OUT/'manifest.json').read_text())
manifest['images']['i_tod_sky_rift_void.png']=hashlib.sha256((OUT/'i_tod_sky_rift_void.png').read_bytes()).hexdigest()
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('SKY DETAIL VOID STAGED')
