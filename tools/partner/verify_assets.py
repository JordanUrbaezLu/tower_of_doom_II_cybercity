"""Validate partner binary geometry, dependencies, finishes and native asset ledger.

W2A (2026-10-05) contract, on top of the geometry / dependency checks: no companion samples a missing or a flat map
(the Protector's 4x4 blue enamel swatch and the Talon / Cerberus's 35 unfound maps are the negative controls: run
with --root on a tree holding the pre-W2A outputs and this FAILS), the Civil Protector wears the donor's gold, and
every map-owned image carries the semantic its slot's techset reads (a mismatch links an EMPTY material).
"""
from pathlib import Path
import argparse, hashlib, json, re, sys, csv
p=argparse.ArgumentParser();p.add_argument('--ledger',type=Path)
p.add_argument('--root',type=Path,help='validate this tree instead of the repo (negative controls, scratch overlays)')
args=p.parse_args()
ROOT=(args.root or Path(__file__).resolve().parents[2]).resolve()
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
manifest=json.loads((ROOT/'model_export/tod_partner/manifest.json').read_text())
zone=(ROOT/'zone_source/tod_partners.zpkg').read_text()
gdt=(ROOT/'source_data/tod_partners.gdt').read_text()
assert len(manifest['models'])==12
for entry in manifest['models']:
    src=ROOT/entry['file'];assert hashlib.sha256(src.read_bytes()).hexdigest()==entry['sha256'],src
    assert 'xmodel,'+entry['asset'] in zone,entry['asset']
    m=xmodel.Model();m.LoadFile_Bin(str(src),split_meshes=True)
    assert m.meshes and m.bones
    for mi,me in enumerate(m.meshes):
        assert me.verts and me.faces
        for f in me.faces:
            assert f.mesh_id==mi,(entry['asset'],mi,f.mesh_id)
            assert 0<=f.material_id<len(m.materials)
            assert len(f.indices)==3
            assert all(0<=c.vertex<len(me.verts) for c in f.indices)
        for v in me.verts:assert all(0<=b<len(m.bones) for b,w in v.weights)
    if '_part' in entry['asset'][len('tod_partner_'):]:
        assert max(hi-lo for lo,hi in entry['bounds'])<=34.001,entry['asset']
    if entry['asset']=='tod_partner_protector':
        assert len(m.bones)>100,'animated Protector rig lost'
    for mat in m.materials:
        if mat.name.startswith(('mtl_tod_partner_','mtl_tod_ptn_')):assert '"'+mat.name+'" ( "material.gdf" )' in gdt,mat.name
        if mat.name.startswith('mtl_tod_ptn_'):assert len(mat.name)<32,mat.name
    if entry['asset']!='tod_partner_protector' and not entry['asset'].startswith('tod_partner_protector_'):
        # Talon / R.A.P.S. / Cerberus wear their real T7 materials, never the old flat swatches.
        assert all(mat.name.startswith('mtl_tod_ptn_') for mat in m.materials),(entry['asset'],[x.name for x in m.materials])
# Every real-material image reference resolves: our PNG (x4, <=1024) or a stock image with its file.
from PIL import Image
import sqlite3
blocks=dict(re.findall(r'\t"([^"]+)" \( "material\.gdf" \)\n\t\{\n(.*?)\n\t\}',gdt,re.S))
images=dict(re.findall(r'\t"([^"]+)" \( "image\.gdf" \)\n\t\{\n(.*?)\n\t\}',gdt,re.S))
MT=Path('C:/BO3Tools/TOD2Cybercity')
db=sqlite3.connect((MT/'gdtdb/gdt.db').as_uri()+'?mode=ro',uri=True);db.execute('pragma writable_schema=ON')
def norm(p):return re.sub(r'[\\/]+','/',p)
for name,body in images.items():
    if not name.startswith('i_tod_ptn_'):continue
    base=dict(re.findall(r'\t\t"([^"]*)" "(.*)"',body))['baseImage']
    png=ROOT/norm(base);assert png.exists(),base
    w,h=Image.open(png).size;assert w%4==0 and h%4==0 and max(w,h)<=1024,(name,w,h)
refs=0
for name,body in blocks.items():
    if not name.startswith('mtl_tod_ptn_'):continue
    for k,v in re.findall(r'\t\t"([^"]*)" "(.*)"',body):
        if not re.search(r'(Map\d*|heatmap|flickerLookupMap)$',k) or not v or v.startswith('$'):continue
        refs+=1
        if v in images:continue
        r=db.execute('select baseImage from image where _name=?',(v,)).fetchone()
        assert r and r[0] and (MT/norm(r[0])).exists(),('unresolved image',name,k,v)
assert refs>200,refs
assert '"team" "allies"' in gdt
assert '"defaultGoalRadius" "48"' in gdt
# ---- W2A: complete, real, correctly-typed maps on every companion ------------------------------------------------
import numpy as np
assert not manifest.get('not_in_pack'),('a companion material samples a map no source holds',sorted(manifest['not_in_pack']))
ifields={n:dict(re.findall(r'\t\t"([^"]*)" "(.*)"',b)) for n,b in images.items()}
flat=[]
for name,f in ifields.items():
    if not name.startswith(('i_tod_ptn_','i_tod_partner_')):continue
    a=np.asarray(Image.open(ROOT/norm(f['baseImage'])).convert('RGB'),np.float32)
    if a.reshape(-1,3).std(0).max()<2.0:flat.append(name)      # a uniform swatch, not a texture
assert not flat,('flat swatch images',flat)
assert 'mtl_tod_partner_enamel' not in blocks,'the retired blue enamel swatch material is back'
prot=xmodel.Model();prot.LoadFile_Bin(str(ROOT/'model_export/tod_partner/tod_partner_protector.xmodel_bin'),split_meshes=True)
cols=[d[0] for d in db.execute('select * from material limit 0').description]
for mat in prot.materials:
    if mat.name.startswith('mtl_tod_ptn_pro_'):
        assert mat.name in blocks,mat.name
        continue
    assert not mat.name.startswith('mtl_tod_partner_'),('Protector swatch material',mat.name)
    row=db.execute('select * from material where _name=?',(mat.name,)).fetchone()
    assert row,('Protector material neither map-owned nor stock',mat.name)
    for k,v in zip(cols,row):
        if isinstance(v,str) and v and not v.startswith('$') and re.search(r'Map\d*$',k):
            r=db.execute('select baseImage from image where _name=?',(v,)).fetchone()
            assert r and r[0] and (MT/norm(r[0])).exists(),('stock Protector material samples a missing map',mat.name,k,v)
gold=[e for e in manifest['materials']['protector'] if re.search(r'_(upper|leg|limbs|foot)_gold$',e['original'])]
assert len(gold)==4,('the four gold shells',[e['original'] for e in gold])
for e in gold:
    want=db.execute('select specColorTint,colorMap from material where _name=?',(e['original'],)).fetchone()
    got=dict(re.findall(r'\t\t"([^"]*)" "(.*)"',blocks[e['material']]))
    assert (got.get('specColorTint'),got.get('colorMap'))==tuple(want),('not the donor gold finish',e['original'],want)
    for k in ('normalMap','cosinePowerMap','specColorMap'):
        assert got.get(k,'').startswith('i_'),('gold shell without a real/authored map',e['material'],k,got.get(k))
# Slot semantics: what every stock material of the same techset puts in that slot (>=5 samples, >=80% agree).
usage={}
for name,body in blocks.items():
    if not name.startswith('mtl_tod_ptn_'):continue
    f=dict(re.findall(r'\t\t"([^"]*)" "(.*)"',body));mt=f.get('materialType','')
    for k,v in f.items():
        if v not in ifields or not re.search(r'Map\d*$',k):continue
        if (mt,k) not in usage:
            try:rows_=db.execute('select i.semantic,count(*) from material m join image i on i._name=m.'+k+
                                 ' where m.materialType=? and m.'+k+" like 'i_%' group by i.semantic",(mt,)).fetchall()
            except sqlite3.OperationalError:rows_=[]
            tot=sum(c for s_,c in rows_);top=max(rows_,key=lambda r:r[1]) if rows_ else None
            usage[(mt,k)]=top[0] if top and tot>=5 and top[1]>=0.8*tot else None
        want=usage[(mt,k)]
        assert want is None or ifields[v].get('semantic')==want,('slot semantic mismatch (an EMPTY material at link)',name,mt,k,v,ifields[v].get('semantic'),want)
# LOCKSTEP: the HUD portrait shows the same Protector finish the world model wears (r1_comp_portraits.PROTECTOR_FINISH).
portrait=ROOT/'tools/artgen/packs/r1_comp_portraits.py'
if portrait.exists():
    pf=re.search(r"^PROTECTOR_FINISH\s*=\s*'(\w+)'",portrait.read_text(encoding='utf-8'),re.M)
    assert pf and pf.group(1)==manifest.get('protector_finish'),('portrait / world Protector finish differ',pf and pf.group(1),manifest.get('protector_finish'))
authored={name for name,src_ in manifest.get('images',{}).items() if 'companion_maps/authored/' in src_['from']}
for name in authored:assert (ROOT/manifest['images'][name]['from']).exists(),('authored source missing',name)
# Nothing real is dropped: the R.A.P.S. keeps every triangle (its rust-spots decal shell, 17% of the model, was dropped
# until W2A), and the Talon / Cerberus drop only stencil decals no source defines (their colour is unknown) plus the
# Cerberus's light covers, a coplanar twin of the base light strip that has no definition anywhere.
UNDEFINED_OK={'mtl_veh_t7_drone_amws_lite_covers_base'}
for short,log in manifest['materials'].items():
    for e in log:
        if 'DROPPED' not in e.get('result',''):continue
        assert short!='raps',('the R.A.P.S. dropped a material again',e['original'],e.get('triangles'))
        assert 'decal' in e['original'] or e['original'] in UNDEFINED_OK,('a non-decal material was dropped',short,e['original'])
assert sum(e.get('triangles',0) for e in manifest['materials']['raps'] if 'DROPPED' not in e.get('result',''))>=12000,'R.A.P.S. lost geometry'
if args.ledger:
    with args.ledger.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    names={(r['type'],r['name']) for r in rows}
    required=[('xmodel',m['asset']) for m in manifest['models']]+[('aitype','spawner_tod_partner'),('xmodel','p8_zm_crafting_table'),('xmodel','wm_t9_ak47_full')]
    for item in required:assert item in names,('not packed',item)
    geometry=args.ledger.with_name(args.ledger.stem+'_xmodel.csv')
    with geometry.open(encoding='utf-8-sig',newline='') as f:compiled={r['name']:r for r in csv.DictReader(f)}
    for entry in manifest['models']:
        row=compiled[entry['asset']]
        assert int(row['tris0'])==entry['triangles'],('native conversion lost geometry',entry['asset'])
    # every map-owned companion material linked WITH its texture table (a name-only row, ~41-49 B, is EMPTY)
    size={r['name']:int(r['resident'] or 0) for r in rows if r['type']=='material'}
    for name in blocks:
        if name.startswith('mtl_tod_ptn_'):
            assert size.get('mc/'+name,0)>100,('companion material linked empty or not at all',name,size.get('mc/'+name))
    # every AUTHORED map reached the fastfile (a pack map in a slot this techset never reads may be left out: warn only)
    packed={r['name'] for r in rows if r['type']=='image'}
    for name in ifields:
        if not name.startswith('i_tod_ptn_') or name in packed:continue
        assert name not in authored,('authored companion map not packed',name)
        print('PARTNER_ASSETS_WARN: pack map not in the fastfile (slot unread by its techset?):',name)
print('PARTNER_ASSETS_PASS: 12 model binaries, valid objects/triangles/weights, two bounded pieces each, Protector rig, ally aitype, real T7 materials on Talon/R.A.P.S./Cerberus ('+str(refs)+' image refs resolved); no missing or flat map, the gold Protector, the complete R.A.P.S., slot semantics agree'+('; native ledger verified' if args.ledger else ''))
