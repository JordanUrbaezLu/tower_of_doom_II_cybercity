"""Bake MCP-authored surface depth and materials for native brush surfaces."""
import bpy, pathlib, sys, hashlib, json, time
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/cybercity_materials'
OUT=ROOT/'model_export/tod_surface/_images';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ART/'cybercity_material_library.blend'))
sys.path.insert(0,str(ROOT/'tools'));import cyber_material_bake as BAKE
BAKE.EMISSION_SCALE=6
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.threads_mode='FIXED';scene.render.threads=4
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
# Physical source view, deliberately before replacing outputs with channel bakes.
scene.render.filepath=str(ART/'authored_tiles.png');bpy.ops.render.render(write_still=True)
scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=2;scene.render.bake.max_ray_distance=4
scene.render.bake.margin=0;scene.render.bake.normal_g='NEG_Y'
source_materials=[m for m in bpy.data.materials if m.name.startswith('CC |')]
records={}
for kind in ('floor','wall','ceiling','trim'):
    for o in scene.objects:o.hide_render=True;o.hide_set(True);o.select_set(False)
    high=list(bpy.data.collections['CC_TILE_'+kind].objects)
    for o in high:o.hide_render=False;o.hide_set(False);o.select_set(True)
    low=bpy.data.objects['CC receiver '+kind];low.hide_render=False;low.hide_set(False);low.select_set(True);bpy.context.view_layer.objects.active=low
    target=bpy.data.materials.new('Baked '+kind);target.use_nodes=True;low.data.materials.clear();low.data.materials.append(target)
    for material in source_materials:
        n,l=material.node_tree.nodes,material.node_tree.links
        l.new(n.get('Principled BSDF').outputs[0],n.get('Material Output').inputs['Surface'])
    for suffix in ('n','c','s','g','e'):
        im=bpy.data.images.new('i_tod_cc_'+kind+'_'+suffix,width=1024,height=1024,alpha=False)
        im.colorspace_settings.name='Non-Color' if suffix in ('n','g') else 'sRGB'
        node=target.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;target.node_tree.nodes.active=node
        if suffix!='n':
            for material in source_materials:BAKE.wire_channel(material,suffix)
        bpy.ops.object.bake(type='NORMAL' if suffix=='n' else 'EMIT',normal_space='TANGENT')
        dest=OUT/(im.name+'.png');im.filepath_raw=str(dest);im.file_format='PNG';im.save()
        records[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
        print('CC_TILE_BAKED',kind,suffix,flush=True)
manifest={'master':'art/cybercity_materials/cybercity_material_library.blend','master_sha256':hashlib.sha256((ART/'cybercity_material_library.blend').read_bytes()).hexdigest(),'tile_units':128,'tile_texels':1024,'normal_green':'DirectX negative Y','textures':records,'native_visual_approved':False}
(ART/'bake_manifest.json').write_text(json.dumps(manifest,indent=2))
print('CC_BAKE_COMPLETE',len(records),'maps',flush=True)
