"""Wire last: activate only after final native portrait + matched review checks pass.

--check validates prerequisites without changing files. No Blender, sync or build.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/dealer_presence';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run([sys.executable,'-B','tools/dealer_presence/verify.py','--prerequisites'],cwd=ROOT,check=True)
if '--check' in sys.argv:
    print('DEALER_WIRING_PREREQUISITES_OK');raise SystemExit(0)
from process_guard import check
check()
generator=ROOT/'tools/gen_tower_map.js';zone=ROOT/'zone_source/zm_tod2_cybercity.zone';build=ROOT/'tools/build_map.ps1';sync=ROOT/'tools/sync_to_modtools.ps1'
block="""// BEGIN DEALER PRESENCE: three small fixed panels on existing opaque walls.
// No collision, lights, entity spawns or runtime animation. Shared native
// geometry and matched Blender reviews: tools/dealer_presence/layout.js.
require('./dealer_presence/layout').emit({worldBrushes,guid,CM,TOP2,CORE,LAP_RISE,FLIGHT_RISE});
// END DEALER PRESENCE
"""
anchor="decalSouthWall('power decal hall POWER',   DECAL_POWER, -540, 1480);   // the switch is at 1613"
g=generator.read_bytes().decode('utf-8');z=zone.read_bytes().decode('utf-8');b=build.read_bytes().decode('utf-8');s=sync.read_bytes().decode('utf-8')
gnl='\r\n' if '\r\n' in g else '\n';znl='\r\n' if '\r\n' in z else '\n';bnl='\r\n' if '\r\n' in b else '\n';snl='\r\n' if '\r\n' in s else '\n'
sync_anchor=r'    Copy-Tree (Join-Path $RepoRoot "model_export\tod_shop") (Join-Path $ModTools "model_export\tod_shop") "item shop models and baked textures" $false'
sync_row=r'    Copy-Tree (Join-Path $RepoRoot "model_export\tod_dealer_presence") (Join-Path $ModTools "model_export\tod_dealer_presence") "Dealer surveillance portrait texture" $false'
build_anchor='    if ($LASTEXITCODE -ne 0) { Die "Lucky sources contract failed - see tools/lucky/test_lucky.js output (docs/197)." }'
build_block='''    # BEGIN DEALER PRESENCE SOURCE GATE: reviewed native wall panels.
    & python -B (Join-Path $PSScriptRoot "dealer_presence/verify.py") --check
    if ($LASTEXITCODE -ne 0) { Die "Dealer wall panels failed source/material/preview validation - see tools/dealer_presence/verify.py." }
    # END DEALER PRESENCE SOURCE GATE'''.replace('\n',bnl)
native_block=block.replace('\n',gnl)
assert g.count(anchor)==1,'Generator anchor changed; inspect current layout before wiring'
assert 'material,mtl_tod_dealer_surveillance' not in z,'World patches own wc material variant'
before={p.relative_to(ROOT).as_posix():sha(p) for p in (generator,zone,build,sync)}
backup=ROOT/'tmp/dealer_presence_wiring'/str(time.time_ns());backup.mkdir(parents=True)
for p in (generator,zone,build,sync,ROOT/'map_source/zm/zm_tod2_cybercity.map'):
    (backup/p.name).write_bytes(p.read_bytes())
if 'BEGIN DEALER PRESENCE' in g:
    assert native_block.strip() in g,'Existing Dealer block differs from owned insertion'
else:
    assert "require('./dealer_presence/layout').emit(" not in g
    g=g.replace(anchor,anchor+gnl+gnl+native_block.rstrip(),1)
if 'image,i_tod_dealer_surveillance' not in z:
    if not z.endswith(znl):z+=znl
    z+=znl+'// Dealer presence: three static existing-wall panels, canonical native portrait.'+znl+'image,i_tod_dealer_surveillance'+znl
if 'BEGIN DEALER PRESENCE SOURCE GATE' in b:
    assert build_block in b,'Existing Dealer source gate differs from owned insertion'
else:
    assert b.count(build_anchor)==1,'Build gate anchor changed; inspect before wiring'
    assert 'dealer_presence/verify.py' not in b,'Existing Dealer gate needs review'
    b=b.replace(build_anchor,build_anchor+bnl+build_block,1)
if 'model_export\\tod_dealer_presence' in s:
    assert s.splitlines().count(sync_row)==1,'Existing Dealer sync row differs from owned insertion'
else:
    assert s.count(sync_anchor)==1,'Sync allowlist anchor changed; inspect before wiring'
    s=s.replace(sync_anchor,sync_anchor+snl+sync_row,1)
generator.write_bytes(g.encode('utf-8'));zone.write_bytes(z.encode('utf-8'));build.write_bytes(b.encode('utf-8'));sync.write_bytes(s.encode('utf-8'))
subprocess.run(['node','tools/gen_tower_map.js'],cwd=ROOT,check=True)
status=json.loads((ART/'status.json').read_text(encoding='utf-8'));status.update(wired=True,state='reviewed_ready_for_guarded_full_build',reason='Final portrait, source provenance and matched reviews passed; actual map regenerated.',wired_ns=time.time_ns())
(ART/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,'-B','tools/dealer_presence/verify.py','--check'],cwd=ROOT,check=True)
(ART/'wiring.json').write_text(json.dumps({'schema':1,'before':before,'before_copies':backup.relative_to(ROOT).as_posix(),'after':{p.relative_to(ROOT).as_posix():sha(p) for p in (generator,zone,build,sync,ROOT/'map_source/zm/zm_tod2_cybercity.map')},'native_build_run':False},indent=2)+'\n',encoding='utf-8')
print('DEALER_PRESENCE_WIRED: three reviewed panels ready for root guarded full build; no build or native launch run')
