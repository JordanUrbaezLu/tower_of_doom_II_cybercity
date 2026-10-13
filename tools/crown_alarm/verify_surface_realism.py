"""Verify the atlas pass against its original meshes and the native bindings.

Use --staged before installation. This verifies UV edits without weakening the
existing exact compiled-LOD checks; run those after the parent's FULL build.
"""
import argparse, hashlib, json, math, pathlib, re, sys
from PIL import Image
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(pathlib.Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
p=argparse.ArgumentParser();p.add_argument('--staged',action='store_true');args=p.parse_args()
BASE=ROOT/'tmp/alarm_realism/baseline'
TARGET=ROOT/'tmp/alarm_realism/staged' if args.staged else ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
    m=xmodel.Model();m.LoadFile_Bin(str(p),split_meshes=True);return m
def geometry(m):
    # UV is the only excluded attribute. Any unrequested mesh/material/pivot/
    # normal/weight/face-order change fails this structural comparison.
    return {'bones':[(b.name,b.offset,b.matrix,b.parent) for b in m.bones],
        'materials':[v.name for v in m.materials],
        'meshes':[{'name':v.name,'verts':[(x.offset,x.weights) for x in v.verts],
            'faces':[(f.mesh_id,f.material_id,[(c.vertex,c.normal,c.color) for c in f.indices]) for f in v.faces]} for v in m.meshes]}
result={}
for family in ('crown_alarm','alarm_button'):
    archived=ROOT/'art'/family/'realism_before'
    BASE=archived if archived.exists() else ROOT/'tmp/alarm_realism/baseline'
    art=TARGET/'art'/family;m=json.loads((art/'manifest.json').read_text());old=json.loads((BASE/'art'/family/'manifest.json').read_text())
    assert m.get('surface_realism'),family
    assert m['gdt_sha256']==sha(TARGET/'source_data'/('tod_'+family+'.gdt'))
    defs=(TARGET/'source_data'/('tod_'+family+'.gdt')).read_text()
    expected=(BASE/'source_data'/('tod_'+family+'.gdt')).read_text()
    if family=='crown_alarm':
        expected,n=re.subn(r'("mtl_tod_alarm_lens" \( "material.gdf" \)\s*\{.*?"materialType" ")lit_emissive_transparent(")',r'\1lit_emissive_transparent_advanced\2',expected,flags=re.S)
        assert n==1
        repair=m.get('lens_repair')
        if repair is not None:
            # The reviewed clear-glass pass changes only the advanced lens's
            # dielectric tint and valid scalar specularMask binding. Preserve
            # the original strict comparison
            # for historical assets without this exact repair revision.
            assert isinstance(repair,dict) and repair.get('revision')=='2026-10-01 clear glass'
            assert repair.get('native_playtested') is False
            expected,n=re.subn(r'("mtl_tod_alarm_lens" \( "material.gdf" \)\s*\{.*?"specColorTint" ")[^"\n]*(")',
                lambda match:match.group(1)+'.220916 .220916 .220916 1'+match.group(2),expected,flags=re.S)
            assert n==1,'Expected exactly one repaired native lens tint'
            expected,n=re.subn(r'("mtl_tod_alarm_lens" \( "material.gdf" \)\s*\{.*?"specColorMap" ")[^"\n]*(")',
                lambda match:match.group(1)+'$black_specular'+match.group(2),expected,flags=re.S)
            assert n==1,'Expected exactly one repaired native lens scalar mask'
    assert defs==expected,'Unexpected native material/state/light edit'
    blocks={name:dict(re.findall(r'"([^"\n]+)" "([^"\n]*)"',body)) for name,kind,body in re.findall(r'"([^"\n]+)" \( "([^"\n]+).gdf" \)\s*\{(.*?)\n\t\}',defs,re.S)}
    total=0;changed_uv=0
    for row in m['models']:
        orig=load(BASE/row['file']);current=load(TARGET/row['file'])
        assert geometry(orig)==geometry(current),row['file']
        assert sha(TARGET/row['file'])==row['sha256']
        assert sum(len(x.faces) for x in current.meshes)==row['triangles']
        for a,b in zip(orig.meshes,current.meshes):
            for f,g in zip(a.faces,b.faces):
                for u,v in zip(f.indices,g.indices):
                    assert all(math.isfinite(x) and -.00001<=x<=1.00001 for x in v.uv)
                    changed_uv+=u.uv!=v.uv
                    total+=1
        for mat in current.materials:
            for key in ('colorMap','colorMap00','cosinePowerMap','normalMap','specColorMap'):
                if family=='crown_alarm' and mat.name=='mtl_tod_alarm_lens' and key=='specColorMap' and m.get('lens_repair'):
                    assert blocks[mat.name][key]=='$black_specular','Glass requires its valid stock nonmetal mask'
                    continue
                assert blocks[mat.name][key] in blocks,(mat.name,key)
    assert changed_uv>0
    maps=[]
    for name,digest in m['textures'].items():
        path=TARGET/'model_export'/('tod_'+family)/'_images'/name
        assert sha(path)==digest,name
        pix=np.asarray(Image.open(path));h,w=pix.shape[:2]
        assert w==h and w in (512,1024,2048),name
        if 'lamp_' not in name:
            assert pix[:,:,:3].std()>0,name
            if name.endswith('_n.png'):
                assert int(pix[:,:,2].min())>=250,(name,'excessive surface relief')
        maps.append({'image':name,'size':w,'sha256':digest})
    for key in ('pivot_z','turn_seconds','fixture_count','light_profile','variants','cap_z','console_z','stand_radius','height'):
        if key in old:assert m[key]==old[key],(family,key)
    result[family]={'lod_files':len(m['models']),'corners':total,'changed_uv_corners':changed_uv,'geometry_identical':True,
        'native_material_roles_preserved':True,'lens_gloss_spec_shader_enabled':family=='crown_alarm','maps':maps,'native_visual_verified':False}
    (art/'realism_review'/'source_validation.json').write_text(json.dumps(result[family],indent=2)+'\n')
print('ALARM_SURFACE_REALISM_PASS',json.dumps({k:{x:y for x,y in v.items() if x!='maps'} for k,v in result.items()}))
