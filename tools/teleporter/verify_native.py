"""Validate export tables, all distance levels, dependencies and shared placement."""
import sys,json,hashlib,math,re,csv,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/teleporter';STAGE=ART/'engine_kit'
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
parser=argparse.ArgumentParser();parser.add_argument('--compiled-ledger',type=Path);args=parser.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((STAGE/'install_manifest.json').read_text());assert sha(ROOT/m['master'])==m['master_sha256'];assert sha(ROOT/'source_data/tod_teleporter.gdt')==m['gdt_sha256']
sys.path.insert(0,str(ROOT/'tools'))
from art_cohesion.profiles import PROFILES
from art_cohesion.native_preview import fields
for file,name in [('tod_teleporter.gdt','mtl_tod_teleporter'),('tod_teleporter_states.gdt','mtl_tod_tp_off')]:
    f=fields(ROOT/'source_data'/file,name)
    # Omission silently inherits 0.1 in material.awi, shifting an atlas's glow.
    assert 'waterRoughness' in f and float(f['waterRoughness'])==0,(name,'surface glow depth must be explicit zero')
    for key,value in PROFILES['teleporter'].items():
        assert (f[key]==value if isinstance(value,str) else float(f[key])==value),(name,key,f[key],value)
    assert f['specColorMap']=='i_tod_teleporter_s' and f['specMapEnable']=='1'
    assert f['colorMap00']==('i_tod_teleporter_e' if name.endswith('_off') else 'i_tod_teleporter_ready_e')
    assert float(f['scaleRGB'])==(0 if name.endswith('_off') else 6)
for f,d in m['textures'].items():assert sha(ROOT/'model_export/tod_teleporter/_images'/f)==d,f
counts=[];bounds=[]
for r in m['models']:
    p=ROOT/r['file'];assert sha(p)==r['sha256'];model=xmodel.Model();model.LoadFile_Bin(str(p),split_meshes=True)
    assert len(model.bones)==1 and model.bones[0].name=='tag_origin';assert [mat.name for mat in model.materials]==['mtl_tod_teleporter']
    count=sum(len(mesh.faces) for mesh in model.meshes);assert count==r['triangles'];counts.append(count)
    coords=[]
    for i,mesh in enumerate(model.meshes):
        assert all(f.mesh_id==i and f.material_id==0 for f in mesh.faces)
        assert all(v.weights==[(0,1.)] and all(math.isfinite(x) for x in v.offset) for v in mesh.verts)
        assert all(.99<sum(x*x for x in c.normal)<1.01 and all(math.isfinite(x) for x in c.uv) for f in mesh.faces for c in f.indices)
        coords.extend(v.offset for v in mesh.verts)
    b=[[min(p[i] for p in coords) for i in range(3)],[max(p[i] for p in coords) for i in range(3)]];bounds.append(b)
    assert all(abs(p[0])<77.501 and abs(p[1])<77.501 and -14<p[2]<11 for p in coords),b
    assert b[1][0]>76 and b[0][0]<-76 and b[1][2]>8,b
assert counts[0]<=53000 and all(a>=b>0 for a,b in zip(counts,counts[1:])),counts
s=(ROOT/'scripts/zm/zm_tod2_cybercity/_tod_teleport.gsc').read_text(encoding='utf-8-sig');body=s.split('function spawn_der_teleporter(',1)[1].split('\nfunction ',1)[0]
assert body.count('Spawn( "script_model", origin )')==1 and 'SetModel( "tod_teleporter_off" )' in body
assert 'SetScale' not in body and 'TOD_TP_PAD_ZOFF' not in s
assert '#define TOD_TP_COOLDOWN_SEC   60' in s and '#define TOD_TP_CHARGE_SEC     0.8' in s
assert '#precache( "model", "tod_teleporter" );' in s
zone=(ROOT/'zone_source/zm_tod2_cybercity.zone').read_text(encoding='utf-8-sig');assert 'xmodel,tod_teleporter' in zone and 'xmodel,p7_zm_der_teleporter' not in zone
if args.compiled_ledger:
    with args.compiled_ledger.open(encoding='utf-8-sig',newline='') as f:rows={r['name']:r for r in csv.DictReader(f)}
    r=rows[m['asset']];assert int(r['lodCount'])==7
    for lod,count in enumerate(counts):assert int(r['tris'+str(6-lod)])==count,(lod,count,r['tris'+str(6-lod)])
report={'triangles':counts,'bounds':bounds,'source_checks':'passed','compiled_checked':bool(args.compiled_ledger),'game_launched':False,'native_visual_verified':False}
(STAGE/('compiled_validation.json' if args.compiled_ledger else 'source_validation.json')).write_text(json.dumps(report,indent=2)+'\n')
print('TELEPORTER_VALIDATED',json.dumps(report))
import runpy
runpy.run_path(str(ROOT/'tools/teleporter/verify_states.py'),init_globals={'LEDGER':args.compiled_ledger})
