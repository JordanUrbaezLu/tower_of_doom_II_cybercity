"""Run through Blender MCP. Preserve source models; export native rigid hooks."""
import bpy, sys, json, math, shutil
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'art/archer_assets'
LIB = ROOT / 'source_library/archer_equipment/apex_grapple'
OUT = ROOT / 'model_export/tod_archer'
for p in (ART, ART/'engine_kit', ART/'preview', OUT/'_images'):
    p.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT/'tools'))
from cyber_reference_one.native_geometry import clean
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
for image in list(bpy.data.images):
    if image.source=='FILE':bpy.data.images.remove(image)
bpy.ops.preferences.addon_enable(module='io_scene_cast')
scene = bpy.context.scene
scene.name = 'Archer equipment | Apex source and BO3 presentation'
scene.unit_settings.system='NONE'
scene['source_units']='Apex source units; BO3 inches, no upscaling of source textures'
scene['native_tested']=False

def material(name, folder, prefix):
    mat = bpy.data.materials.new(name); mat.use_nodes=True
    n=mat.node_tree.nodes; l=mat.node_tree.links
    shader=n.get('Principled BSDF')
    shader.inputs['Metallic'].default_value=.65
    record={}
    for suffix,target,channel in [('col','Base Color','Color'),('spc','Specular IOR Level','Color'),('gls','Roughness','Color'),('nml','Normal','Color')]:
        path=next(folder.rglob(prefix+'_'+suffix+'.png'))
        copy=OUT/'_images'/('i_tod_archer_'+name+'_'+suffix+'.png')
        shutil.copy2(path,copy)
        image=bpy.data.images.load(str(copy),check_existing=True)
        if suffix!='col':image.colorspace_settings.name='Non-Color'
        if suffix=='nml':
            # Apex's BC5 exports store XY in RG and zero B. Reconstruct +Z;
            # preserve native DirectX Y in the BO3 file, flip only for Blender.
            pixels=np.array(image.pixels[:],dtype=np.float32).reshape(-1,4)
            xy=pixels[:,:2]*2-1
            pixels[:,2]=np.sqrt(np.maximum(0,1-np.sum(xy*xy,axis=1)))*.5+.5
            pixels[:,3]=1
            image.pixels.foreach_set(pixels.ravel());image.filepath_raw=str(copy);image.file_format='PNG';image.save()
        tex=n.new('ShaderNodeTexImage');tex.image=image
        if suffix=='nml':
            sep=n.new('ShaderNodeSeparateColor');comb=n.new('ShaderNodeCombineColor');inv=n.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1
            l.new(tex.outputs['Color'],sep.inputs[0]);l.new(sep.outputs[0],comb.inputs[0]);l.new(sep.outputs[1],inv.inputs[1]);l.new(inv.outputs[0],comb.inputs[1]);l.new(sep.outputs[2],comb.inputs[2])
            normal=n.new('ShaderNodeNormalMap');l.new(comb.outputs[0],normal.inputs['Color']);l.new(normal.outputs['Normal'],shader.inputs[target])
        elif suffix=='gls':
            invert=n.new('ShaderNodeMath');invert.operation='SUBTRACT';invert.inputs[0].default_value=1
            l.new(tex.outputs['Color'],invert.inputs[1]);l.new(invert.outputs[0],shader.inputs[target])
        elif suffix=='col':l.new(tex.outputs[channel],shader.inputs[target])
        record[suffix]={'file':copy.relative_to(ROOT).as_posix(),'size':list(image.size)}
    return mat,record

records=[]
for asset,folder,prefix in [('hook','projectile_grapple_hook_anchor_bolt','grapple_gun'),('pathfinder_prop','pathfinder_grapplehook','pathfinder_prop_grapplehook')]:
    source=LIB/'assets/mdl'/folder/(folder+'_LOD0.cast')
    existing=set(bpy.data.objects)
    bpy.ops.import_scene.cast(filepath=str(source),import_skin=True,import_ik=False,import_constraints=False)
    imported=[o for o in bpy.data.objects if o not in existing]
    meshes=[o for o in imported if o.type=='MESH']
    mat,textures=material(asset,source.parent,prefix)
    for ob in meshes:ob.data.materials.clear();ob.data.materials.append(mat)
    # Export evaluated bind-pose geometry, maintaining imported winding/normals.
    d={'verts':[],'faces':[],'material':'mtl_tod_archer_'+asset}
    for ob in meshes:
        me=ob.data;me.calc_loop_triangles();start=len(d['verts'])
        d['verts'] += [list(ob.matrix_world@v.co) for v in me.vertices]
        nm=ob.matrix_world.to_3x3().inverted().transposed()
        for tri in me.loop_triangles:
            face=[]
            for li in (tri.loops[0],tri.loops[2],tri.loops[1]):
                uv=me.uv_layers.active.data[li].uv
                face.append({'v':start+me.loops[li].vertex_index,'n':list((nm@me.corner_normals[li].vector).normalized()),'uv':[uv[0],1-uv[1]]})
            d['faces'].append(face)
    clean(d)
    (ART/'engine_kit'/(asset+'.json')).write_text(json.dumps(d,separators=(',',':')))
    collection=bpy.data.collections.new('SOURCE | '+asset);scene.collection.children.link(collection)
    for ob in imported:
        for old in list(ob.users_collection):old.objects.unlink(ob)
        collection.objects.link(ob)
        ob['source_file']=source.relative_to(ROOT).as_posix()
    records.append({'asset':asset,'source':source.relative_to(ROOT).as_posix(),'textures':textures,'triangles':len(d['faces']),'removed_slivers':d['native_slivers_removed']})

# Preserve the native cable texture; shader conversion is explicit in install_native.
cable=next((LIB/'standalone_materials/extract_models').rglob('grapple_col.png'))
shutil.copy2(cable,OUT/'_images/i_tod_archer_cable.png')
# Studio presentation and hook silhouette icon use the actual projectile model.
for ob in bpy.data.collections['SOURCE | pathfinder_prop'].objects:ob.hide_render=True
hook=[o for o in bpy.data.collections['SOURCE | hook'].objects if o.type=='MESH'][0]
bounds=[hook.matrix_world@Vector(c) for c in hook.bound_box]
center=sum(bounds,Vector())/8
scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.threads_mode='FIXED';scene.render.threads=8
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast' if 'Medium High Contrast' in [i.name for i in scene.view_settings.bl_rna.properties['look'].enum_items] else 'None'
world=bpy.data.worlds.new('Neutral studio');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.18,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.35
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Key',center+Vector((5,-15,20)),24000,18),('Rim',center+Vector((-8,9,8)),18000,12)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc;aim(ob,center)
data=bpy.data.cameras.new('Asset camera');camera=bpy.data.objects.new('Asset camera',data);scene.collection.objects.link(camera)
camera.location=center+Vector((22,-32,20));aim(camera,center);data.type='ORTHO';data.ortho_scale=25;scene.camera=camera
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.filepath=str(ART/'preview/grapple_hook.png');bpy.ops.render.render(write_still=True)
# A clean 512px silhouette remains readable inside the 46x32 equipment tile.
iconmat=bpy.data.materials.new('HUD white silhouette');iconmat.use_nodes=True
nodes=iconmat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');iconmat.node_tree.links.new(em.outputs[0],out.inputs[0])
scene.view_layers[0].material_override=iconmat
scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.filepath=str(ROOT/'art/archer/review/i_tod_archer_hook_hud.png')   # R5: a review render (the HUD tile is i_tod_h2_ab_hook);bpy.ops.render.render(write_still=True)
scene.view_layers[0].material_override=None
scene.render.resolution_x=1024;scene.render.resolution_y=1024
(ART/'engine_kit/source_manifest.json').write_text(json.dumps({'models':records,'cable_source':cable.relative_to(ROOT).as_posix(),'native_tested':False},indent=2))
for image in bpy.data.images:
    if image.source=='FILE':image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'archer_equipment.blend'))
print('ARCHER_MCP_STAGED',json.dumps(records))
