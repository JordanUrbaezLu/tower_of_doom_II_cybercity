"""Check original recipes, unchanged rig/geometry, actual texture files and all weapon forms."""
from pathlib import Path
import sys,re,json,hashlib,argparse,csv
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from inspect_expected_roster import blocks
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import xmodel,asset,native_path
from restore_fire_bow import SOURCE,DEST,TEXTURE,SUFFIXES,outputs,DONOR
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ledger',type=Path);args=ap.parse_args()
    for p,data in outputs().items():assert p.read_bytes()==data,('stale',p)
    source=blocks(SOURCE);made=blocks(DEST);images={};meshes={}
    for suffix in SUFFIXES:
        orig=source['mtl_wpn_t7_zmb_bow_rune'+suffix]['fields']
        new=made['mtl_tod_fire_bow_rune'+suffix]['fields']
        expected={k:('i_tod_fire_bow_lava' if v=='i_t7_camo_zod_pap_e3' else v) for k,v in orig.items()}
        assert new==expected,('Changed original shader recipe',suffix)
        assert new['materialType']=='lit_emissive_scroll_3layer_plus'
        assert new['colorMap02'].endswith('_e') and new['colorMap00']!=new['colorMap']
        for key in ['colorMap','colorMap00','colorMap01','colorMap02','normalMap','cosinePowerMap','occMap']:
            name=new[key]
            fields=made[name]['fields'] if name in made else asset('image',name)
            p=ROOT/fields['baseImage'].replace('\\','/') if name in made else native_path('',fields['baseImage'])
            assert p.is_file(),(name,p)
            images[name]={'file':str(p),'sha256':sha(p)}
    for kind in ['view','world','projectile']:
        f=made['tod_fire_bow_rune_'+kind]['fields']
        old=asset('xmodel','hb_fire_bow_rune_'+kind)
        a=xmodel.Model();b=xmodel.Model()
        path=native_path('model_export',f['filename'])
        a.LoadFile_Bin(str(path),split_meshes=True)
        b.LoadFile_Bin(str(native_path('model_export',old['filename'])),split_meshes=True)
        assert [(x.name,x.parent,x.offset,x.matrix) for x in a.bones]==[(x.name,x.parent,x.offset,x.matrix) for x in b.bones],kind
        assert [[(v.offset,v.weights) for v in m.verts] for m in a.meshes]==[[(v.offset,v.weights) for v in m.verts] for m in b.meshes],kind
        assert [len(m.faces) for m in a.meshes]==[len(m.faces) for m in b.meshes],kind
        assert all(not m.name.startswith('mtl_hb_fire_bow') for m in a.materials)
        if kind=='view':assert {'tag_rune_rock_lower_fx_01','tag_rune_rock_upper_fx_01'}<={x.name for x in a.bones}
        meshes[kind]={'file':str(path),'sha256':sha(path),'triangles':sum(len(m.faces) for m in a.meshes),'bones':len(a.bones)}
    weapons=blocks(ROOT/'source_data/tod_weapon_twins.gdt')
    names=[]
    for name,v in weapons.items():
        if not name.startswith('cc_fire_bow'):continue
        names.append(name);f=v['fields']
        for k,suffix in [('gunModel','view'),('worldModel','world'),('projectileModel','projectile')]:assert f[k]=='tod_fire_bow_rune_'+suffix,(name,k)
        assert f['viewPersistentEffectSet']=='weapon_elemental_rune_zm_1p_persist'
    assert len(names)==40,(len(names),'Fire Bow forms: DEADEYE d0..d3 x QUICK DRAW s0..s4 x base/up (9 levels 2026-09-28); (2026-09-28; 24 on 2026-09-27 class pass 4; was 8)')
    for p in DONOR.rglob('*.efx'):
        assert p.read_bytes()==(Path('C:/BO3Tools/TOD2Cybercity')/p.relative_to(DONOR)).read_bytes(),('Original persistent FX changed',p)
    if args.ledger:
        with args.ledger.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        packed={r['name'].split('|')[0] for r in rows}
        required=['tod_fire_bow_rune_'+k for k in meshes]+['mc/mtl_tod_fire_bow_rune'+s for s in SUFFIXES]+['i_tod_fire_bow_lava']
        assert set(required)<=packed,('Missing compiled assets',set(required)-packed)
    out=ROOT/'art/fire_bow';out.mkdir(exist_ok=True)
    (out/'source_receipt.json').write_text(json.dumps({'source_gdt':str(SOURCE.relative_to(ROOT)),'source_sha256':sha(SOURCE),'output_sha256':sha(DEST),'images':images,'models':meshes,'weapons':sorted(names),'native_compiled':bool(args.ledger),'native_visual_verified':False},indent=2))
    print('FIRE BOW: four original material recipes, 21 image bindings, unchanged rigs/vertices, 40 weapon forms and original persistent FX verified; native visual review pending.')
if __name__=='__main__':main()
