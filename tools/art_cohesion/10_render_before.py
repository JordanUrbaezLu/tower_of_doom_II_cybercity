"""Reconstruct the pre-refactor materials on the identical review geometry.

Preview only: does not alter the map, native inputs, or the finished master.
The saved baseline already includes the user's separate blackout change.
"""
import bpy, pathlib, sys, json, hashlib, datetime
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
ART=ROOT/'art/cybercity_materials'
sys.path.insert(0,str(ROOT/'tools/art_cohesion'))
from crown_views import VIEWS
from native_preview import fields, fullspec
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
master=ART/'crown_complete.blend'; master_sha=sha(master)
legacy=ROOT/'source_data/tod_materials.gdt'
snapshot=json.loads((ART/'build_inputs.json').read_text())
assert sha(legacy)==snapshot['inputs']['source_data/tod_materials.gdt'], 'Legacy material definitions changed since the recorded baseline'
before={r['label']:r for r in json.loads((ART/'crown_before_refactor.json').read_text())['rows']}
current=json.loads((ART/'crown_inventory.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(master));scene=bpy.context.scene
origin=Vector((0,8608,19392))
def signature(face):return tuple(round(x,5) for x in [*face['n'],face['d']])
legacy_fields={};mats={}
def old_material(name):
    if name in mats:return mats[name]
    f=fields(legacy,name);legacy_fields[name]=f
    # These exact pre-refactor blackout materials have no texture-dependent
    # diffuse, specular, normal, mirror or emission component.
    assert f['colorMap']=='$white_diffuse' and not f['normalMap']
    for key in ('scaleRGB','specMapEnable','specAmount','glossRangeMin','glossRangeMax','reflectionProbeAmount'):
        assert float(f[key])==0,(name,key,f[key])
    assert all(float(v)==0 for v in f['specColorTint'].split()[:3])
    c=[float(v) for v in f['colorTint'].split()[:3]]
    c=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c]
    mat=bpy.data.materials.new('Before native blackout | '+name);mat.use_nodes=True
    mat['native_fields']=json.dumps(f);n=mat.node_tree.nodes;n.clear()
    d=n.new('ShaderNodeBsdfDiffuse');d.inputs['Color'].default_value=(*c,1)
    out=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(d.outputs[0],out.inputs['Surface'])
    mats[name]=mat;return mat
changed=0
for row in current['rows']:
    ob=bpy.data.objects.get(row['label']);assert ob and ob.get('native_architecture'),row['label']
    assert len(ob.data.polygons)==len(row['faces'])
    old=before[row['label']]
    mapping={signature(f):f['mat'] for f in old['faces']}
    assigned=[]
    for face in row['faces']:
        # The initial local test bay split these two original solids. Restore
        # their recorded original family across the now-whole floor/wall.
        if row['label']=='crown hall floor':name='tod_black_dark_blue_tinted'
        elif row['label']=='crown wall W':name='tod_black_purple'
        else:name=mapping[signature(face)]
        assert name.startswith('tod_black_'),(row['label'],name)
        assigned.append(name)
    ob.data.materials.clear();slots=list(dict.fromkeys(assigned))
    for name in slots:ob.data.materials.append(old_material(name))
    for poly,name in zip(ob.data.polygons,assigned):poly.material_index=slots.index(name)
    changed+=1
assert changed==803

# Restore the recorded original prop finishes, using the SAME approximation
# as the after preview. Preview GDT is isolated in art/, never installed.
profiles=json.loads((ART/'finish_before.json').read_text())
gdt=ART/'before_preview_finishes.gdt';blocks=[]
for native,folder in [('mtl_tod_teleporter','tod_teleporter'),('mtl_tod_altar','tod_heavenly_altar')]:
    f=fields(ROOT/'source_data'/(folder+'.gdt'),native);f.update(profiles[native])
    blocks.append('\t"'+native+'" ( "material.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+v+'"\n' for k,v in f.items())+'\t}\n')
gdt.write_text('{\n'+''.join(blocks)+'}\n')
restored={name:fullspec(gdt,name,ROOT/'model_export'/folder/'_images') for name,folder in [('mtl_tod_teleporter','tod_teleporter'),('mtl_tod_altar','tod_heavenly_altar')]}
for ob in scene.objects:
    if ob.type!='MESH' or ob.get('native_architecture'):continue
    for slot in ob.material_slots:
        if not slot.material:continue
        native=slot.material.name.split(' | ')[-1].split('.')[0]
        if native in restored:slot.material=restored[native]

scene['comparison_baseline']='Reconstructed pre-refactor blackout materials; identical geometry, studio lights, exposure and camera parameters'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'crown_before_review.blend'))
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.cycles.seed=0
views=[]
for name,loc,target,kind,value,w,h in VIEWS:
    cam=scene.camera;cam.location=Vector(loc)-origin;cam.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler();cam.data.type=kind
    if kind=='ORTHO':cam.data.ortho_scale=value
    else:cam.data.lens=value
    scene.render.resolution_x=w;scene.render.resolution_y=h
    output=ART/(name+'_before.png');scene.render.filepath=str(output)
    bpy.ops.render.render(write_still=True)
    views.append({'name':name,'location':loc,'target':target,'type':kind,'lens_or_scale':value,'dimensions':[w,h],'before_sha256':sha(output),'after_sha256':sha(ART/(name+'.png'))})
    print('BEFORE_RENDER_SAVED',name,flush=True)
assert sha(master)==master_sha,'Finished master was modified'
(ART/'before_after_manifest.json').write_text(json.dumps({'created':datetime.datetime.now().isoformat(),'baseline':'immediately before material refactor, including blackout settings','baseline_assignments_sha256':sha(ART/'crown_before_refactor.json'),'legacy_gdt_sha256':sha(legacy),'master_sha256':master_sha,'architecture_count':changed,'geometry_unchanged':True,'same_lights_and_exposure':True,'preview_only':True,'game_screenshot':False,'restored_whole_solid_roles':{'crown hall floor':'tod_black_dark_blue_tinted','crown wall W':'tod_black_purple'},'legacy_material_fields':legacy_fields,'views':views},indent=2)+'\n')
print('BEFORE_AFTER_PREVIEW_COMPLETE',len(views),'matched views',flush=True)
