"""Assemble actual native source meshes and baked kit through Blender MCP."""
import bpy,pathlib,sys,json,math,hashlib
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/cybercity_materials'
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(pathlib.Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
from art_cohesion.native_preview import fullspec,fields,DESCRIPTION
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
scene=bpy.context.scene;scene['preview_limit']=DESCRIPTION;scene['units']='Native BO3 units; texture repeats every 128 units'
scene['layout']='Authoring comparison scene, not the game layout; native pilot is west crown shop bay'
mats={};hashes={}
def native_mat(file,name,folder):
    mat=fullspec(ROOT/'source_data'/file,name,ROOT/'model_export'/folder/'_images');mat.use_fake_user=True;mats[name]=mat;return mat
for kind in ('floor','wall','ceiling','trim'):native_mat('tod_surface.gdt','tod_cc_'+kind,'tod_surface')
for name in ('body','vendor','glow','glow_off'):native_mat('tod_shop.gdt','mtl_tod_shop_'+name,'tod_shop')
native_mat('tod_teleporter.gdt','mtl_tod_teleporter','tod_teleporter')
native_mat('tod_teleporter_states.gdt','mtl_tod_tp_off','tod_teleporter')
native_mat('tod_heavenly_altar.gdt','mtl_tod_altar','tod_heavenly_altar')

def emission(name,path=None,color=(1,1,1,1),strength=1,alpha=False):
    mat=bpy.data.materials.new(name);mat.use_nodes=True;n,l=mat.node_tree.nodes,mat.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');e=n.new('ShaderNodeEmission');e.inputs[0].default_value=color;e.inputs[1].default_value=strength
    if path:
        tx=n.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(path),check_existing=True);l.new(tx.outputs[0],e.inputs[0])
    surface=e.outputs[0]
    if alpha:
        tr=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');l.new(tx.outputs['Alpha'],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(surface,mix.inputs[2]);surface=mix.outputs[0]
    l.new(surface,out.inputs[0]);mats[name]=mat;return mat
portal=fields(ROOT/'source_data/chaos_pack_a_punch.gdt','i_chaos_pap_background_c','image')
emission('chaos_pap_background',pathlib.Path('C:/BO3Tools/TOD2Cybercity')/portal['baseImage'].replace('\\','/'))
emission('mtl_tod_altar_wings',ROOT/'model_export/tod_heavenly_altar/_images/i_tod_altar_wings_c.png',strength=3,alpha=True)
for i in range(3):
    f=fields(ROOT/'source_data/tod_teleporter_states.gdt','mtl_tod_tp_charge_'+str(i));emission('mtl_tod_tp_charge_'+str(i),color=tuple(float(x) for x in f['colorTint1'].split()),strength=float(f['scaleRGB']))

def binary(path,loc=(0,0,0),tag=''):
    hashes[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    model=xmodel.Model();model.LoadFile_Bin(str(path),split_meshes=True);made=[]
    for src in model.meshes:
        me=bpy.data.meshes.new(src.name);me.from_pydata([v.offset for v in src.verts],[],[[f.indices[i].vertex for i in (0,2,1)] for f in src.faces]);me.update()
        for m in model.materials:
            assert m.name in mats,m.name;me.materials.append(mats[m.name])
        uv=me.uv_layers.new();normals=[]
        for p,f in zip(me.polygons,src.faces):
            p.material_index=f.material_id;p.use_smooth=True
            for li,i in zip(p.loop_indices,(0,2,1)):
                c=f.indices[i];uv.data[li].uv=(c.uv[0],1-c.uv[1]);normals.append(c.normal)
        me.normals_split_custom_set(normals);ob=bpy.data.objects.new(tag+' | '+src.name,me);scene.collection.objects.link(ob);ob.location=loc;ob['review_group']=tag;made.append(ob)
    return made
shop=json.loads((ROOT/'art/partner_shop/engine_kit/install_manifest.json').read_text())
for r in shop['models']:
    g=r['group']
    if r['lod']!=0 or g in ('arc','spark'):continue
    pivot=shop['pivots'].get(g,[0,0,0]);binary(ROOT/r['file'],(-200+pivot[0],pivot[1],pivot[2]),'shop_'+g)
binary(ROOT/'model_export/tod_teleporter/tod_teleporter_lod0.xmodel_bin',(45,-90,13),'teleporter')
for ob in binary(ROOT/'model_export/tod_teleporter/tod_tp_recharge_lod0.xmodel_bin',(45,-90,13),'recharge'):ob.hide_render=True
binary(ROOT/'model_export/tod_heavenly_altar/tod_heavenly_altar_lod0.xmodel_bin',(240,0,0),'altar')

def plane(name,verts,uvs,material):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[(0,1,2,3)]);me.update();layer=me.uv_layers.new()
    for li,uv in enumerate(uvs):layer.data[li].uv=uv
    me.materials.append(mats[material]);ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob);return ob
plane('Baked deck 128-unit repeat',[(-400,-250,0),(380,-250,0),(380,100,0),(-400,100,0)],[(0,0),(780/128,0),(780/128,350/128),(0,350/128)],'tod_cc_floor')
plane('Baked wall 128-unit repeat',[(-400,100,0),(-400,100,256),(380,100,256),(380,100,0)],[(0,0),(0,2),(780/128,2),(780/128,0)],'tod_cc_wall')
plane('Machined wall border',[(-400,99.5,224),(-400,99.5,256),(380,99.5,256),(380,99.5,224)],[(0,0),(0,.25),(780/128,.25),(780/128,0)],'tod_cc_trim')

world=bpy.data.worlds.new('Shared neutral studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.17,.2,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35
def aim(ob,point):ob.rotation_euler=(Vector(point)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Broad key',(-200,-220,450),1600000,320),('Common fill',(350,-160,240),950000,260),('Edge light',(-120,170,310),1100000,230)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;ob=bpy.data.objects.new(name,d);scene.collection.objects.link(ob);ob.location=loc;aim(ob,(0,0,50))
data=bpy.data.cameras.new('Shared comparison camera');cam=bpy.data.objects.new('Shared comparison camera',data);scene.collection.objects.link(cam);scene.camera=cam;cam.location=(540,-1100,550);aim(cam,(-5,0,90));data.type='ORTHO';data.ortho_scale=950;data.clip_end=5000
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'native_comparison.blend'))
(ART/'review_manifest.json').write_text(json.dumps({'preview_limit':DESCRIPTION,'native_mesh_hashes':hashes,'original_portal':'static first layer only','game_launched':False},indent=2))
print('SHARED_NATIVE_REVIEW_SCENE_SAVED',len(hashes),'source binaries',flush=True)
