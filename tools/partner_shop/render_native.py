"""Render the exact reduced geometry and baked maps outside the live MCP master."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/partner_shop';KIT=ART/'engine_kit';IMG=ROOT/'model_export/tod_shop/_images'
bpy.ops.wm.open_mainfile(filepath=str(ART/'partner_shop.blend'));scene=bpy.context.scene
for o in list(scene.objects):
    if o.get('shop_native_group') or o.type=='EMPTY':bpy.data.objects.remove(o,do_unlink=True)
manifest=json.loads((KIT/'source_manifest.json').read_text());materials={}
for group in ('body','vendor','glow'):
    m=bpy.data.materials.new('Native '+group);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    tex={}
    for suffix in ('c','n','g','e'):
        im=bpy.data.images.load(str(IMG/('i_tod_shop_'+group+'_'+suffix+'.png')));im.colorspace_settings.name='Non-Color' if suffix in ('n','g') else 'sRGB'
        node=n.new('ShaderNodeTexImage');node.image=im;tex[suffix]=node
    l.new(tex['c'].outputs[0],p.inputs['Base Color']);l.new(tex['e'].outputs[0],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=6
    inv=n.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;l.new(tex['g'].outputs[0],inv.inputs[1]);l.new(inv.outputs[0],p.inputs['Roughness'])
    sep=n.new('ShaderNodeSeparateColor');comb=n.new('ShaderNodeCombineColor');flip=n.new('ShaderNodeMath');flip.operation='SUBTRACT';flip.inputs[0].default_value=1
    l.new(tex['n'].outputs[0],sep.inputs[0]);l.new(sep.outputs[0],comb.inputs[0]);l.new(sep.outputs[2],comb.inputs[2]);l.new(sep.outputs[1],flip.inputs[1]);l.new(flip.outputs[0],comb.inputs[1])
    nm=n.new('ShaderNodeNormalMap');l.new(comb.outputs[0],nm.inputs['Color']);l.new(nm.outputs[0],p.inputs['Normal']);p.inputs['Metallic'].default_value=0 if group=='vendor' else .55
    materials[group]=m
native={}
for g,mat in manifest['groups'].items():
    if g in ('arc','spark'):continue
    d=json.loads((KIT/(g+'_lod0.json')).read_text());me=bpy.data.meshes.new(g)
    me.from_pydata(d['verts'],[],[[f[i]['v'] for i in (0,2,1)] for f in d['faces']]);me.update();uv=me.uv_layers.new();normals=[]
    for poly,f in zip(me.polygons,d['faces']):
        poly.use_smooth=True
        for li,i in zip(poly.loop_indices,(0,2,1)):uv.data[li].uv=(f[i]['uv'][0],1-f[i]['uv'][1]);normals.append(f[i]['n'])
    me.normals_split_custom_set(normals);ob=bpy.data.objects.new('Native '+g,me);scene.collection.objects.link(ob);ob.location=manifest['pivots'].get(g,(0,0,0));me.materials.append(materials[mat.removeprefix('mtl_tod_shop_')]);native[g]=ob
scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=1280;scene.render.resolution_y=1080;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.camera=bpy.data.objects['01 HERO - three-quarter']
scene.render.filepath=str(ART/'native_baked.png');bpy.ops.render.render(write_still=True)
materials['glow'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=0
native['vendor'].hide_render=True;native['mask'].hide_render=True
scene['shop_powered']=0;scene.frame_set(1);scene.render.filepath=str(ART/'native_baked_off.png');bpy.ops.render.render(write_still=True)
print('NATIVE_PREVIEW_OK',flush=True)
