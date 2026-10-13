"""Source gate: native dimensions, current art/preview provenance and real wall support."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,math
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/dealer_presence';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prerequisites='--prerequisites' in sys.argv
status=json.loads((ART/'status.json').read_text(encoding='utf-8'))
generator=(ROOT/'tools/gen_tower_map.js').read_text(encoding='utf-8-sig')
zone=(ROOT/'zone_source/zm_tod2_cybercity.zone').read_text(encoding='utf-8-sig')
maptext=(ROOT/'map_source/zm/zm_tod2_cybercity.map').read_text(encoding='utf-8-sig')
if not status['wired'] and not prerequisites:
    assert "require('./dealer_presence/layout').emit(" not in generator
    assert 'i_tod_dealer_surveillance' not in zone and 'mtl_tod_dealer_surveillance' not in zone
    assert 'dealer presence ' not in maptext and 'mtl_tod_dealer_surveillance' not in maptext
    assert not (ROOT/'source_data/tod_dealer_presence.gdt').exists(),'Unused Dealer staging GDT must stay out of converter scanning'
    assert not (ROOT/'model_export/tod_dealer_presence/_images/i_tod_dealer_surveillance.png').exists()
    print('DEALER_PRESENCE_PENDING_OK: authored placements preserved; runtime wiring absent; staging files excluded from conversion')
    raise SystemExit(0)
receipt=json.loads((ART/'install.json').read_text());portrait=json.loads((ART/'portrait.json').read_text());preview=json.loads((ART/'preview.json').read_text())
assert receipt['portrait_receipt_sha256']==sha(ART/'portrait.json')
assert portrait['author_script_sha256']==sha(Path(__file__).with_name('author_portrait.py'))
for p,h in portrait['sources'].items():assert sha(ROOT/p)==h,('Canonical Dealer source changed',p)
for pkey,hkey in [('source','source_sha256'),('installed_image','installed_image_sha256'),('gdt','gdt_sha256')]:assert sha(ROOT/receipt[pkey])==receipt[hkey],pkey
png=(ROOT/receipt['installed_image']).read_bytes();assert png[:8]==b'\x89PNG\r\n\x1a\n'
assert struct.unpack('>II',png[16:24])==(1024,1024),'Mipped native Dealer image must be 1024 POT'
gdt=(ROOT/receipt['gdt']).read_text();assert gdt.startswith('{')
assert '"scaleRGB" ".65"' in gdt and '"materialType" "lit_emissive"' in gdt
assert '"noMipMaps" "1"' not in gdt,'Portrait requires normal mipmaps for distance'
assert sha(ART/'geometry.json')==preview['geometry_sha256']
assert sha(ROOT/receipt['gdt'])==preview['gdt_sha256']
assert sha(ROOT/receipt['installed_image'])==preview['source_image_sha256']
assert sha(Path(__file__).with_name('preview.py'))==preview['preview_script_sha256']
assert sha(Path(__file__).with_name('layout.js'))==preview['layout_script_sha256']
assert sha(ART/'context.json')==preview['context_sha256']
for p,h in preview['native_preview_sources'].items():assert sha(ROOT/p)==h,('Reviewed native material source changed',p)
assert len(preview['images'])==7
for name,digest in preview['images'].items():assert sha(ART/name)==digest,('Review image changed',name)
fresh=json.loads(subprocess.check_output(['node','-e',"console.log(JSON.stringify(require('./tools/dealer_presence/layout').geometry()))"],cwd=ROOT,text=True))
stored=json.loads((ART/'geometry.json').read_text());assert fresh==stored,'Panel layout changed without authoring review'
assert len(fresh['placements'])==3 and fresh['triangles']==84 and not fresh['collision']
assert fresh['entities']==fresh['lights']==fresh['runtime_threads']==0
for p in fresh['placements']:
    q=next(q for q in fresh['quads'] if q['id']==p['id'] and q['part']=='canonical dealer portrait')
    a=[q['verts'][1][i]-q['verts'][0][i] for i in range(3)];b=[q['verts'][3][i]-q['verts'][0][i] for i in range(3)]
    cross=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    assert sum(cross[i]*p['normal'][i] for i in range(3))>0,'Portrait winding faces into wall'
    assert q['uv']==[[0,0],[1,0],[1,1],[0,1]],'Portrait UV orientation changed'
subprocess.run(['node','tools/dealer_presence/inventory.js','--check'],cwd=ROOT,check=True)
if not prerequisites:
    sync_row=r'    Copy-Tree (Join-Path $RepoRoot "model_export\tod_dealer_presence") (Join-Path $ModTools "model_export\tod_dealer_presence") "Dealer surveillance portrait texture" $false'
    assert (ROOT/'tools/sync_to_modtools.ps1').read_text(encoding='utf-8-sig').splitlines().count(sync_row)==1,'Dealer portrait folder must be copied to the private tools root by guarded sync'
    assert (ROOT/'tools/build_map.ps1').read_text(encoding='utf-8-sig').count('dealer_presence/verify.py") --check')==1,'Dealer source gate must run in guarded builds'
    assert generator.count("require('./dealer_presence/layout').emit(")==1
    assert 'material,mtl_tod_dealer_surveillance' not in zone,'World patches own the wc material variant; do not zone a bare material'
    assert 'image,i_tod_dealer_surveillance' in zone
    assert maptext.count('mtl_tod_dealer_surveillance')==3,'Regenerate map for three panel faces'
    assert maptext.count('dealer presence ')==42,'Native map must contain exactly 42 collision-free panel patches'
print('DEALER_PRESENCE_SOURCE_OK: 3 canonical portrait panels; 1024 POT+mips; 84 triangles; real supports; reviewed native maps; no collision/entities/lights')
