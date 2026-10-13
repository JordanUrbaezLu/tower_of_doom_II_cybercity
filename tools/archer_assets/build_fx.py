"""Bounded native first pass from recovered T7 tomahawk effects, not new FX art."""
from pathlib import Path
import json,re,sys,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/bo6_extraction'))
from build_bo6_ice_fx import blocks,block_name,child_refs,gate_by_distance,rescale
SOURCE=ROOT/'source_library/archer_equipment/t7_tomahawk_fx'
OUT=ROOT/'share/raw/fx/tod/archer';OUT.mkdir(parents=True,exist_ok=True)
report=[]
for name in ('trail','impact','charge','trail_charged'):
    src=SOURCE/('fx_tomahawk_'+name+'.efx');text=src.read_text();parts=[];stats=[]
    for b in blocks(text):
        # Recovered dynamic-light stubs have no verified renderer definition.
        # Keep the actual sprite/arc art, omit lights and large smoke/decal layers.
        if 'dynamicLight' in b:continue
        if name=='impact' and any(k in b for k in ('gfx_fxt_smk','gfx_crater','gfx_fxt_light_flare')):continue
        assert not child_refs(b),(name,block_name(b))
        b=b.replace('gfx_fxt_fx_emp_ring_wave','mtl_tod_archer_charge_ring')
        b=gate_by_distance(b,56)
        if name in ('trail','trail_charged'):
            b=re.sub(r'(spawnLooping )([\d.]+) ([\d.]+);',lambda m:m[1]+str(max(35,int(float(m[2]))))+' '+m[3]+';',b)
        elif name=='impact':
            b=re.sub(r'(spawnOneShot )([\d.]+) ([\d.]+);',lambda m:m[1]+str(min(8,int(float(m[2]))))+' '+m[3]+';',b)
        stats.append({'source_element':block_name(b),'interval':re.search(r'spawnLooping ([^;]+)',b)[1],'life_ms':re.search(r'lifeSpanMsec ([^;]+)',b)[1]})
        parts.append(b)
    dest=OUT/('fx_tod_archer_'+name+'.efx');dest.write_text(text[:text.index('{')]+'\n'+'\n'.join(parts)+'\n')
    report.append({'source':src.relative_to(ROOT).as_posix(),'file':dest.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'elements':stats,'dynamic_lights':0})
(ROOT/'art/archer_assets/engine_kit/fx_manifest.json').write_text(json.dumps({'provenance':'T7 Assets V2.8 recovered tomahawk emitters; bounded native composition, stock texture first pass','effects':report,'native_tested':False},indent=2))
print('ARCHER_FX',[(r['file'],len(r['elements'])) for r in report])
