"""MCP: preview-only correction to the installed transparent lens shader.

The actual packed transparent-advanced shaders consume color/normal/gloss and
a scalar specular mask with the native sRGB tint. The old alpha-test sample was
not a dependency of the alarm's techset. Nothing in model_export, source_data,
gameplay, FX or lighting is written. Other materials are untouched.
"""
import bpy, pathlib, json, re, sys, importlib, hashlib, shutil
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import surface_realism
importlib.reload(surface_realism)
ART=ROOT/'art/crown_alarm';REVIEW=ART/'realism_review'
gdt=ROOT/'source_data/tod_crown_alarm.gdt'
definitions={n:dict(re.findall(r'"([^"\n]+)" "([^"\n]*)"',body)) for n,kind,body in re.findall(r'"([^"\n]+)" \( "([^"\n]+).gdf" \)\s*\{(.*?)\n\t\}',gdt.read_text(),re.S)}
f=definitions['mtl_tod_alarm_lens'];assert f['materialType']=='lit_emissive_transparent_advanced'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native={str(p.relative_to(ROOT)):sha(p) for folder in [ROOT/'model_export/tod_crown_alarm',ROOT/'source_data'] for p in folder.rglob('*') if p.is_file() and (folder.name!='source_data' or p.name=='tod_crown_alarm.gdt')}
for master in [ART/'crown_alarm.blend',ART/'visibility_review/high_fixture.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(master))
    mat=bpy.data.materials['mtl_tod_alarm_lens']
    surface_realism.bind_material(mat,f,ROOT/'model_export/tod_crown_alarm/_images')
    scene=bpy.context.scene
    scene['lens_native_channels']='colorMap + normalMap + cosinePowerMap + $black_specular scalar nonmetal mask=0; F0=.04 and diffuse factor=1. Gray32 is thermalHeatmap. Full-color lens_s is an unbound source artifact.'
    bpy.ops.wm.save_as_mainfile(filepath=str(master))
    if master.name!='crown_alarm.blend':continue
    scene.frame_set(1)
    surface_realism.render_review(scene,REVIEW,'crown_alarm','after')
    cam=scene.camera;cam.location=(72,-84,48)
    cam.rotation_euler=(Vector((0,0,11))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=60
    surface_realism.render_review(scene,REVIEW,'crown_alarm','detail')
    changed=[]
    for ob in scene.objects:
        if ob.type!='MESH':continue
        for slot in ob.material_slots:
            if slot.material and slot.material.name=='mtl_tod_alarm_lamp_off':
                changed.append(slot);slot.material=bpy.data.materials['mtl_tod_alarm_lamp_on']
    surface_realism.render_review(scene,REVIEW,'crown_alarm','on_detail')
    # Do not save the temporary macro camera or on-state over the editable master.
for rel,digest in native.items():assert sha(ROOT/rel)==digest,'Preview correction changed a native input: '+rel
# The audit captures the actual techset dependency block and all six packed
# pixel shaders. Prefer the published evidence, with the isolated staging
# location available while this repair is under review.
audit_path=ROOT/'art/crown_alarm/lens_review/native_shader_audit.json'
if not audit_path.exists():audit_path=ROOT/'tmp/alarm_lens_repair/native_shader_audit.json'
audit=json.loads(audit_path.read_text())
primary=next(p for p in audit['packed_pixel_shaders'] if p['name']==audit['primary_packed_shader'])
src=audit_path.parent/(primary['name']+'.txt')
if not src.exists():src=ROOT/primary['disassembly_path']
assert sha(src)==primary['disassembly_sha256'],'Packed lens shader evidence is stale'
assert primary['discard_instructions']==0,'Lens evidence contains an alpha-test variant'
assert not audit['obsolete_prior_sample']['is_dependency_of_native_lens_techset']
evidence=REVIEW/(primary['name']+'.txt');shutil.copyfile(src,evidence)
report={'native_material':'mtl_tod_alarm_lens','native_shader':'lit_emissive_transparent_advanced','compiled_techset':audit['native_techset'],
        'packed_shader':primary['name'],
        'consumed_images':['i_tod_alarm_lens_c','i_tod_alarm_lens_n','i_tod_alarm_lens_g','$black_specular'],
        'unused_source_image':'i_tod_alarm_lens_s','bound_specular_mask':f['specColorMap'],
        'specular_mask_linear':surface_realism.native_lens_mask(f),
        'specular_formula':'F0=mix(0.04,sRGB-to-linear specColorTint,scalar_mask); black mask=0',
        'diffuse_factor':1-surface_realism.native_lens_mask(f),
        'specColorTint':f['specColorTint'],'effective_f0':surface_realism.native_lens_f0(f),
        'alpha_formula':'colorMap alpha * vertex alpha; lens emission zero',
        'evidence':evidence.name,'evidence_sha256':sha(evidence),
        'shader_audit_sha256':sha(audit_path),
        'native_inputs_unchanged':True,'other_materials_unchanged':True,'native_visual_verified':False,
        'renders':{name:sha(REVIEW/(name+'.png')) for name in ['before','after','detail','on_detail']}}
(REVIEW/'lens_native_channels.json').write_text(json.dumps(report,indent=2)+'\n')
print('NATIVE_LENS_PREVIEW_CORRECTED',json.dumps(report))
