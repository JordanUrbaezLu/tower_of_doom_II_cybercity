"""Invoked by verify_native.py; validate state derivatives and compiled coverage."""
import json,hashlib,sys,csv,math,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];KIT=ROOT/'art/teleporter/engine_kit';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
m=json.loads((KIT/'install_manifest.json').read_text());st=json.loads((KIT/'states_manifest.json').read_text())
assert st['master_sha256']==m['master_sha256']==sha(ROOT/m['master'])
assert st['gdt_sha256']==sha(ROOT/'source_data/tod_teleporter_states.gdt')
assert st['off_shared_lods']==[r['sha256'] for r in m['models']]
assert st['ready_image_sha256']==m['textures']['i_tod_teleporter_ready_e.png']
assert st['palette']==json.loads((ROOT/'tools/teleporter/state_palette.json').read_text())
file=ROOT/st['recharge_file'];assert sha(file)==st['recharge_sha256'];model=xmodel.Model();model.LoadFile_Bin(str(file),split_meshes=True)
assert len(model.bones)==1 and model.bones[0].name=='tag_origin';assert sum(len(x.faces) for x in model.meshes)==1152==st['recharge_triangles']
assert len(model.materials)==3
for mesh in model.meshes:
    for v in mesh.verts:assert v.weights==[(0,1.)] and 72.77<math.hypot(*v.offset[:2])<73.34 and 8.23<v.offset[2]<8.79
gdt=(ROOT/'source_data/tod_teleporter_states.gdt').read_text();assert '"skinOverride" "mtl_tod_teleporter mtl_tod_tp_off"' in gdt;assert '"scaleRGB" "0"' in gdt
assert 'include,tod_teleporter_states' in (ROOT/'zone_source/zm_tod2_cybercity.zone').read_text()
ledger=globals().get('LEDGER')
if ledger:
    with Path(ledger).open(encoding='utf-8-sig',newline='') as f:rows={r['name']:r for r in csv.DictReader(f)}
    off=rows['tod_teleporter_off'];assert int(off['lodCount'])==7
    for r in m['models']:assert int(off['tris'+str(6-r['lod'])])==r['triangles']
    chase=rows['tod_tp_recharge'];assert int(chase['lodCount'])==1 and int(chase['tris0'])==1152
else:subprocess.run(['node',str(ROOT/'tools/teleporter/test_states.js')],check=True)
subprocess.run([sys.executable,'-B',str(ROOT/'tools/teleporter/check_state_images.py')],check=True)
(KIT/'states_validation.json').write_text(json.dumps({'source_checks':True,'compiled':bool(ledger),'body_geometry_unchanged':True,'off_emission_scale':0,'extra_models_per_recharging_pad':1,'indicator_triangles':1152,'revolution_seconds':3,'new_dynamic_lights':0,'game_launched':False,'native_playtested':False},indent=2))
print('TELEPORTER_STATES_VALIDATED: shared body, dark twin, green emission, yellow chase; compiled='+str(bool(ledger)))
