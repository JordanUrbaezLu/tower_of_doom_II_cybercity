"""Blender MCP: bake an exclusive skull atlas, retaining anatomy and adding pores.

Run after author.py, before export_preview.py. Original BO3 color/normal inputs
remain bound to their source UV; the new 2K atlas is a real resample plus authored
surface detail, not a claim that enlargement alone improves the original art.
"""
import bpy, pathlib, json
ROOT=pathlib.Path(__file__).resolve().parents[2]
ART=ROOT/'art/necro_staff'; OUT=ROOT/'model_export/tod_necro_staff'
bpy.ops.wm.open_mainfile(filepath=str(ART/'staff_master.blend'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
window=bpy.context.window_manager.windows[0];window.scene=scene
area=next(a for a in window.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
scene.cycles.bake_type='DIFFUSE';scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False
scene.render.bake.use_pass_color=True;scene.render.bake.margin=16
skulls=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('Carved human skull')]
assert len(skulls)==2
ob=next(o for o in skulls if o['tier']==3)
for o in scene.objects:o.select_set(False);o.hide_render=o!=ob
ob.select_set(True);bpy.context.view_layer.objects.active=ob
old=ob.data.uv_layers.active;old.name='SourceBoneUV'
hero=ob.data.uv_layers.new(name='HeroSkullUV');ob.data.uv_layers.active=hero
with bpy.context.temp_override(window=window,area=area,region=region,object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025)
    bpy.ops.object.mode_set(mode='OBJECT')
old=ob.data.uv_layers['SourceBoneUV'];hero=ob.data.uv_layers['HeroSkullUV']
ob.data.uv_layers.active=hero;hero.active_render=True
m=ob.data.materials[0];n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map=old.name
for node in list(n):
    if node.type=='TEX_IMAGE':l.new(uvnode.outputs['UV'],node.inputs['Vector'])
    if node.type=='NORMAL_MAP':node.uv_map=old.name
base=bs.inputs['Base Color'].links[0].from_socket
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=2.2;ao.samples=16
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.48
l.new(base,mix.inputs[1]);l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=3;noise.inputs['Roughness'].default_value=.72
coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],noise.inputs['Vector'])
original_normal=bs.inputs['Normal'].links[0].from_socket
bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.30;bump.inputs['Distance'].default_value=.035
l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(original_normal,bump.inputs['Normal']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
saved={}
for key,kind in [('c','DIFFUSE'),('n','NORMAL')]:
    im=bpy.data.images.new('Hero skull '+key,width=2048,height=2048,alpha=True)
    im.colorspace_settings.name='sRGB' if key=='c' else 'Non-Color'
    target=n.new('ShaderNodeTexImage');target.image=im;n.active=target
    if kind=='NORMAL':
        scene.render.bake.normal_space='TANGENT';scene.render.bake.normal_r='POS_X';scene.render.bake.normal_g='NEG_Y';scene.render.bake.normal_b='POS_Z'
    with bpy.context.temp_override(window=window,area=area,region=region,object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):
        bpy.ops.object.bake(type=kind)
    im.filepath_raw=str(OUT/('i_tod_necro_bone_'+key+'.png'));im.file_format='PNG';im.save()
    saved[key]=im
# Both tiers share precisely the same anatomy and now the exclusive skull UVs.
for other in skulls:
    if other==ob:continue
    assert len(other.data.loops)==len(ob.data.loops)
    other.data.uv_layers.active.name='SourceBoneUV'
    dest=other.data.uv_layers.new(name='HeroSkullUV')
    for src,dst in zip(hero.data,dest.data):dst.uv=src.uv
    other.data.uv_layers.active=dest;dest.active_render=True
# Restore a native-equivalent preview using only baked maps, no preview-only AO.
for node in list(n):
    if node.type=='TEX_IMAGE' and node.image and node.image.name.startswith('i_tod_necro_bone_'):
        key=node.image.name.rsplit('_',1)[-1]
        if key in saved:node.image=saved[key]
        for link in list(node.inputs['Vector'].links):l.remove(link)
    if node.type=='NORMAL_MAP':node.uv_map='HeroSkullUV'
l.new(base,bs.inputs['Base Color']);l.new(original_normal,bs.inputs['Normal'])
for other in scene.objects:other.hide_render=False
scene['bone_atlas']='Exclusive 2048 UV layout; original bone color/normal resampled, AO and procedural pores baked through Cycles.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'staff_master.blend'))
(ART/'bone_bake.json').write_text(json.dumps({'resolution':2048,'uv':'HeroSkullUV','source_uv':'SourceBoneUV','ao_distance':2.2,'normal_y':'DirectX','native_visual_verified':False},indent=2))
record=json.loads((ART/'authoring.json').read_text())
record['bone_maps']='Exclusive 2048 atlas baked from original BO3 color/normal maps, authored pores and cavity shading; HeroSkullUV'
(ART/'authoring.json').write_text(json.dumps(record,indent=2))
print('NECRO_BONE_BAKED: exclusive 2K atlas, cavities and fine pores; both tiers share matching UVs')
