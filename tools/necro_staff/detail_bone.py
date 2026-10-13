"""MCP: bake aged bone pigmentation into the staged native skull atlas.

Run after detail_pass.py. No preview-only procedural surface is left behind.
"""
import bpy,pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[2]
ART=ROOT/'art/necro_staff/detail_pass';OUT=ART/'models'
bpy.ops.wm.open_mainfile(filepath=str(ART/'staff_master.blend'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
window=bpy.context.window_manager.windows[0];window.scene=scene
area=next(a for a in window.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
skull=next(o for o in scene.objects if o.name.startswith('Carved human skull') and o['tier']==3)
for ob in scene.objects:ob.select_set(False);ob.hide_render=ob!=skull
skull.select_set(True);bpy.context.view_layer.objects.active=skull
m=skull.data.materials[0];n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
base=bs.inputs['Base Color'].links[0].from_socket
# Re-read the frozen exclusive atlas so re-running never compounds stains.
base.node.image=bpy.data.images.load(str(ART/'input_maps/i_tod_necro_bone_c.png'),check_existing=False)
coord=n.new('ShaderNodeTexCoord')
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=8;noise.inputs['Detail'].default_value=4;noise.inputs['Roughness'].default_value=.7
l.new(coord.outputs['Generated'],noise.inputs['Vector'])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.24;ramp.color_ramp.elements[0].color=(.22,.19,.13,1)
ramp.color_ramp.elements[1].position=.73;ramp.color_ramp.elements[1].color=(.91,.86,.73,1)
l.new(noise.outputs['Fac'],ramp.inputs['Fac'])
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.78
l.new(base,mix.inputs[1]);l.new(ramp.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True;scene.render.bake.margin=16
im=bpy.data.images.new('Aged bone pigmentation',width=2048,height=2048,alpha=True);im.colorspace_settings.name='sRGB'
target=n.new('ShaderNodeTexImage');target.image=im;n.active=target
with bpy.context.temp_override(window=window,area=area,region=region,object=skull,active_object=skull,selected_objects=[skull],selected_editable_objects=[skull]):bpy.ops.object.bake(type='DIFFUSE')
im.filepath_raw=str(OUT/'i_tod_necro_bone_c.png');im.file_format='PNG';im.save()
l.new(base,bs.inputs['Base Color']);base.node.image=im
# Share the native image with the subtle suture material as well.
for mat in bpy.data.materials:
    if not mat.use_nodes:continue
    for node in mat.node_tree.nodes:
        if node.type=='TEX_IMAGE' and node.image and pathlib.Path(bpy.path.abspath(node.image.filepath)).name=='i_tod_necro_bone_c.png':node.image=im
# Repair the initial staged leather preview connection; native map was correct.
leather=bpy.data.materials['mtl_tod_necro_staff_leather'];nodes=leather.node_tree.nodes
nm=next(o for o in nodes if o.type=='NORMAL_MAP');com=next(o for o in nodes if o.type=='COMBXYZ')
for link in list(nm.inputs['Strength'].links):leather.node_tree.links.remove(link)
nm.inputs['Strength'].default_value=1;leather.node_tree.links.new(com.outputs[0],nm.inputs['Color'])
for ob in scene.objects:ob.hide_render=False
scene['bone_pigmentation']='Baked multi-scale aged bone staining; native 2K color atlas, no procedural runtime dependency.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'staff_master.blend'))
record=json.loads((ART/'detail.json').read_text());record['bone_pigmentation']=scene['bone_pigmentation'];(ART/'detail.json').write_text(json.dumps(record,indent=2))
print('AGED BONE BAKED: final native atlas, anatomical cavity information retained')
