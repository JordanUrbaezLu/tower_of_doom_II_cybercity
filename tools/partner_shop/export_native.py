"""Bake the live MCP master into native parts, power-off shell and distance LODs.

Background Blender only. The editable master is never replaced by the export.
"""
import bpy,bmesh,sys,json,hashlib,math,runpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/partner_shop';OUT=ROOT/'model_export/tod_shop';IMG=OUT/'_images';KIT=ART/'engine_kit'
for p in (OUT,IMG,KIT):p.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tools'));import cyber_material_bake as BAKE
from cyber_reference_one.native_geometry import clean
BAKE.EMISSION_SCALE=6
master=ART/'partner_shop.blend';digest=hashlib.sha256(master.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(master));scene=bpy.context.scene;scene['shop_powered']=1;scene.frame_set(1);bpy.context.view_layer.update()
scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.threads_mode='FIXED';scene.render.threads=8
try:
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
    for d in pref.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.render.bake.margin=5;scene.render.bake.use_selected_to_active=False;scene.render.bake.normal_g='NEG_Y'
GROUPS=['solid','vendor','valve','needle','steady','mask','letter_t','letter_e','letter_c','core_left','core_counter','core_right','scan_0','scan_1','scan_2','scan_3','arc','spark']
parts={g:[] for g in GROUPS};pivots={'valve':[90,-32,47],'needle':[73,-36.55,74]}
deps=bpy.context.evaluated_depsgraph_get()
for src in list(scene.objects):
    group=src.get('shop_native_group')
    if group not in parts:continue
    ev=src.evaluated_get(deps);me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=deps)
    ob=bpy.data.objects.new('Native '+src.name,me);scene.collection.objects.link(ob);ob.matrix_world=src.matrix_world.copy();ob['group']=group
    attr=me.attributes.new('shop_generated','FLOAT_VECTOR','POINT')
    lo=[min(v.co[i] for v in me.vertices) for i in range(3)];hi=[max(v.co[i] for v in me.vertices) for i in range(3)]
    attr.data.foreach_set('vector',[(v.co[i]-lo[i])/(hi[i]-lo[i]) if hi[i]-lo[i]>1e-8 else .5 for v in me.vertices for i in range(3)])
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
    parts[group].append(ob)
# The native arc and fleck are the authored Blender effect geometry, rebased to contact.
for kind in ('arc','spark'):
    src=next(o for o in scene.objects if o.get('fx_kind')==kind and o.get('fx_event')=='sign T')
    scene.frame_set(src.get('fx_frame',20));deps=bpy.context.evaluated_depsgraph_get();ev=src.evaluated_get(deps)
    me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=deps)
    ob=bpy.data.objects.new('Native effect '+kind,me);scene.collection.objects.link(ob)
    ob.matrix_world=src.matrix_world.copy();ob.matrix_world.translation=(0,0,0);ob['group']=kind;parts[kind].append(ob)
scene.frame_set(1)
keep={o for objects in parts.values() for o in objects}
for ob in list(scene.objects):
    if ob not in keep:bpy.data.objects.remove(ob,do_unlink=True)
for m in {m for o in keep for m in o.data.materials if m}:
    a=m.node_tree.nodes.new('ShaderNodeAttribute');a.attribute_name='shop_generated'
    for n in list(m.node_tree.nodes):
        if n.type in ('TEX_NOISE','TEX_VORONOI','TEX_WAVE') and not n.inputs['Vector'].is_linked:m.node_tree.links.new(a.outputs['Vector'],n.inputs['Vector'])
def select(ob):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
def join(objects,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=name
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);return ob
def reduce(ob,limit):
    select(ob);ob.data.calc_loop_triangles();before=len(ob.data.loop_triangles)
    if before>limit:
        mod=ob.modifiers.new('Native surface budget','DECIMATE');mod.ratio=limit/before;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
    print('SHOP_REDUCE',ob.name,before,len(ob.data.polygons),flush=True)
def bake(ob,name,size):
    select(ob);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1,island_margin=.0008,margin_method='FRACTION',area_weight=.4);bpy.ops.object.mode_set(mode='OBJECT')
    mats=list(ob.data.materials)
    for suffix in ('n','c','s','g','e'):
        im=bpy.data.images.new('i_tod_shop_'+name+'_'+suffix,width=size,height=size,alpha=False);im.colorspace_settings.name='Non-Color' if suffix in ('n','g') else 'sRGB'
        for m in mats:
            node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;m.node_tree.nodes.active=node
            if suffix!='n':BAKE.wire_channel(m,suffix)
        bpy.ops.object.bake(type='NORMAL' if suffix=='n' else 'EMIT',normal_space='TANGENT')
        im.filepath_raw=str(IMG/(im.name+'.png'));im.file_format='PNG';im.save();print('SHOP_BAKED',name,suffix,flush=True)
def geometry(ob,group,material,pivot=(0,0,0),face_group=None):
    me=ob.data;me.calc_loop_triangles();data={'bone':'tag_origin','material':material,'verts':[list(ob.matrix_world@v.co-Vector(pivot)) for v in me.vertices],'faces':[]}
    nm=ob.matrix_world.to_3x3().inverted().transposed()
    for tri in me.loop_triangles:
        if face_group is not None and me.attributes['native_part'].data[tri.polygon_index].value!=face_group:continue
        corners=[]
        for li in (tri.loops[0],tri.loops[2],tri.loops[1]):
            n=(nm@me.corner_normals[li].vector).normalized()
            if n.length_squared<.9:n=(nm@tri.normal).normalized()
            uv=me.uv_layers.active.data[li].uv;corners.append({'v':me.loops[li].vertex_index,'n':list(n),'uv':[uv[0],1-uv[1]]})
        data['faces'].append(corners)
    clean(data,min_altitude=.001);used=sorted({c['v'] for f in data['faces'] for c in f});remap={v:i for i,v in enumerate(used)}
    data['verts']=[data['verts'][v] for v in used]
    for face in data['faces']:
        for c in face:c['v']=remap[c['v']]
    (KIT/(group+'_lod0.json')).write_text(json.dumps(data,separators=(',',':')))
    return len(data['faces'])
counts={};materials={}
# Bake wheel / needle along with the hut, preserving a face attribute for separation.
for idx,g in enumerate(('solid','valve','needle')):
    for ob in parts[g]:
        a=ob.data.attributes.new('native_part','INT','FACE');a.data.foreach_set('value',[idx]*len(ob.data.polygons))
solid=join(parts['solid']+parts['valve']+parts['needle'],'Hut and mechanical pieces');reduce(solid,95000);bake(solid,'body',4096)
for idx,g in enumerate(('solid','valve','needle')):
    counts[g]=geometry(solid,g,'mtl_tod_shop_body',pivots.get(g,(0,0,0)),idx);materials[g]='mtl_tod_shop_body'
vendor=join(parts['vendor'],'Merchant cloth and mask');reduce(vendor,26000);bake(vendor,'vendor',2048)
counts['vendor']=geometry(vendor,'vendor','mtl_tod_shop_vendor');materials['vendor']='mtl_tod_shop_vendor'
# Native glow palette preserves each tube's authored color and relative radiance.
glows=[g for g in GROUPS if g not in ('solid','vendor','valve','needle')]
palette=[];entries={}
for g in glows:
    for ob in parts[g]:
        for m in ob.data.materials:
            key=(g,m.name)
            if key in entries:continue
            p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');col=list(p.inputs['Emission Color'].default_value[:3]);base=list(p.inputs['Base Color'].default_value[:3])
            value=m.node_tree.nodes.get('Electrical timeline');strength=value.outputs[0].default_value if value else p.inputs['Emission Strength'].default_value
            if g=='mask':strength=.5 if 'weak' in m.name else 3.1
            elif g.startswith('letter'):strength=5.5
            elif g=='core_left':strength=2.2 if 'scan rings' in m.name else 3.3
            elif g=='core_counter':strength=2.5
            elif g=='core_right':strength=3.1
            elif g.startswith('scan'):strength=3
            entries[key]=len(palette);palette.append({'group':g,'material':m.name,'c':base,'e':[v*strength/6 for v in col],'s':[.06]*3,'g':[1-p.inputs['Roughness'].default_value]*3,'n':[.5,.5,1]})
(KIT/'palette_sources.json').write_text(json.dumps(palette,indent=2))
size=64;cell=8
for suffix in ('c','e','s','g','n'):
    pixels=[0.0]*(size*size*4)
    for i,entry in enumerate(palette):
        rgb=entry[suffix]
        # Generated byte-buffer images save their values directly. Encode the
        # three color channels once, matching the GDT's sRGB3chAlpha semantic.
        if suffix in ('c','e','s'):rgb=[12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055 for v in rgb]
        cx=(i%8)*cell;cy=(i//8)*cell
        for y in range(cy,cy+cell):
            for x in range(cx,cx+cell):pixels[(y*size+x)*4:(y*size+x)*4+4]=rgb+[1.0]
    im=bpy.data.images.new('i_tod_shop_glow_'+suffix,width=size,height=size,alpha=False);im.colorspace_settings.name='Non-Color' if suffix in ('n','g') else 'sRGB';im.pixels.foreach_set(pixels);im.filepath_raw=str(IMG/(im.name+'.png'));im.file_format='PNG';im.save()
for g in glows:
    for ob in parts[g]:
        uv=ob.data.uv_layers.new(name='Authored light palette')
        ob.data.uv_layers.active_index=len(ob.data.uv_layers)-1;uv.active_render=True
        for poly in ob.data.polygons:
            idx=entries[(g,ob.data.materials[poly.material_index].name)];co=((idx%8+.5)/8,(idx//8+.5)/8)
            # A small nondegenerate UV polygon stays within its constant-color
            # swatch and gives the native tangent generator a valid basis.
            for j,li in enumerate(poly.loop_indices):
                a=j*math.tau/len(poly.loop_indices);uv.data[li].uv=(co[0]+.02*math.cos(a),co[1]+.02*math.sin(a))
    ob=join(parts[g],'Native '+g);reduce(ob,12000 if g=='steady' else 5000 if g=='mask' else 2600)
    counts[g]=geometry(ob,g,'mtl_tod_shop_glow');materials[g]='mtl_tod_shop_glow'
(KIT/'lod_counts.json').write_text(json.dumps({'0':counts},indent=2))
runpy.run_path(str(ROOT/'tools/cyber_reference_one/reduce_game_lods.py'),run_name='__main__',init_globals={'CYBER_LOD_SOURCE':KIT,'CYBER_LOD_OUTPUT':KIT,'CYBER_LOD_AREA_FLOORS':{g:(0,.008,.04,.15,.5,1.2,2.5) if g=='solid' else (0,0,0,0,0,0,0) for g in counts}})
manifest={'master':master.relative_to(ROOT).as_posix(),'master_sha256':digest,'groups':materials,'pivots':pivots,'emission_scale':6,'textures':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in IMG.glob('*.png')},'lod_counts':json.loads((KIT/'lod_counts.json').read_text()),'off_state':'Combined hut plus physical neon/canister surfaces with emission disabled, no vendor or FX.'}
(KIT/'source_manifest.json').write_text(json.dumps(manifest,indent=2));print('SHOP_EXPORT_OK',counts,flush=True)
