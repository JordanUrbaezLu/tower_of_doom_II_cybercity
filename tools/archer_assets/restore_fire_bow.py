"""Restore the original rune bow material pipeline without changing donor assets.

The inherited HB models replaced four original materials with lit_emissive_advanced
and made their stone albedo the emission map (scale 3). Original material fields
are restored verbatim: three-layer shader, lava layers, masks, UV motion and HDR.
The donor archive contains its missing lava PNG but no image GDT for it. Register
that unchanged image privately, then skin original meshes with map-owned twins.
"""
from pathlib import Path
import re,hashlib,json,argparse
ROOT=Path(__file__).resolve().parents[2]
DONOR=ROOT/'source_library/fire_bow/original/hb21_elemental_bows_v1.0.0'
SOURCE=DONOR/'source_data/wpn_t7_zmb_bow.gdt'
DEST=ROOT/'source_data/tod_fire_bow.gdt'
TEXTURE=ROOT/'model_export/tod_fire_bow/i_tod_fire_bow_lava.png'
SUFFIXES=('', '_handle', '_rocks', '_missile')
def block(text,name):
    return re.search(r'\t"'+re.escape(name)+r'" \(.*?\n\t\}',text,re.S)[0]
def rename(b,old,new):return b.replace('"'+old+'"','"'+new+'"',1)
def field(b,key,value):
    b,n=re.subn(r'("'+re.escape(key)+r'" )"[^"\r\n]*"',lambda m:m[1]+'"'+value+'"',b,count=1)
    assert n==1,key
    return b
def outputs():
    text=SOURCE.read_text()
    image=rename(block(text,'i_wpn_t7_zmb_bow_rune_e'),'i_wpn_t7_zmb_bow_rune_e','i_tod_fire_bow_lava')
    image=field(image,'baseImage',TEXTURE.relative_to(ROOT).as_posix())
    image=field(image,'streamable','0')
    out=[image]
    skins=[]
    for suffix in SUFFIXES:
        old='mtl_wpn_t7_zmb_bow_rune'+suffix;new='mtl_tod_fire_bow_rune'+suffix
        b=rename(block(text,old),old,new)
        b=b.replace('"i_t7_camo_zod_pap_e3"','"i_tod_fire_bow_lava"')
        out.append(b);skins.append(old+' '+new)
    for kind in ['view','world','projectile']:
        old='wpn_t7_zmb_bow_rune_'+kind;new='tod_fire_bow_rune_'+kind
        b=rename(block(text,old),old,new)
        out.append(field(b,'skinOverride','\\r\\n'.join(skins)+'\\r\\n'))
    return {DEST:('{\n'+'\n'.join(out)+'\n}\n').encode(),
            TEXTURE:(DONOR/'model_export/black_ops_3/wpn_t7_zmb_bow/_images/i_t7_camo_zod_pap_e3.png').read_bytes()}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    for path,data in outputs().items():
        if args.check:assert path.exists() and path.read_bytes()==data,('stale',path)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print('FIRE BOW RESTORATION: original lava bytes, four original material recipes, three original mesh bindings '+('verified' if args.check else 'written'))
if __name__=='__main__':main()
