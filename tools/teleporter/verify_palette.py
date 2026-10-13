"""Reject pink status art and prove the accepted body/finish did not change."""
import hashlib, json, re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art/teleporter/status_colors'
sys.path.insert(0,str(ROOT/'tools'))
from art_cohesion.native_preview import fields
from art_cohesion.profiles import PROFILES
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
palette=json.loads((ROOT/'tools/teleporter/state_palette.json').read_text())
assert palette['ready_linear'][1]==1 and max(palette['ready_linear'][::2])<.1
assert palette['pending_linear'][0]==1 and palette['pending_linear'][1]>=.8 and palette['pending_linear'][2]<.03
before=json.loads((OUT/'before.json').read_text(encoding='utf-8-sig'))
unchanged={rel:digest for rel,digest in before.items() if rel.startswith('model_export/') and not rel.endswith('i_tod_teleporter_ready_e.png')}
for rel,digest in unchanged.items():assert sha(ROOT/rel)==digest,('accepted body/texture changed',rel)
for file,name in [('tod_teleporter.gdt','mtl_tod_teleporter'),('tod_teleporter_states.gdt','mtl_tod_tp_off')]:
    f=fields(ROOT/'source_data'/file,name)
    for key,v in PROFILES['teleporter'].items():assert f[key]==v if isinstance(v,str) else float(f[key])==v,(name,key)
    assert float(f['scaleRGB'])==(0 if name.endswith('_off') else 6)
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
for band,strength in enumerate((5.5,2.3,.75)):
    f=fields(ROOT/'source_data/tod_teleporter_states.gdt','mtl_tod_tp_charge_'+str(band))
    tint=[linear(float(v)) for v in f['colorTint1'].split()[:3]]
    assert all(abs(a-b)<1e-6 for a,b in zip(tint,palette['pending_linear']))
    assert float(f['scaleRGB'])==strength and float(f['waterRoughness'])==0
for name,key in [('ready','ready_linear'),('charge_field','pending_linear'),('release_field','ready_linear')]:
    text=(ROOT/'share/raw/fx/tod/teleporter'/('fx_tod_tp_'+name+'.efx')).read_text()
    curves=re.findall(r'\bcolorGraph\s+1\s*(.*?);',text,re.S)
    assert len(curves)==(3 if name=='release_field' else 4)
    for curve in curves:
        rows=re.findall(r'^\s*[01]\s+([\d.e+-]+)\s+([\d.e+-]+)\s+([\d.e+-]+)\s*$',curve,re.M)
        assert len(rows)==4 and all([float(v) for v in r]==palette[key] for r in rows)
    assert 'gfx_debug_missing_fx' not in text
subprocess.run([sys.executable,'-B',str(ROOT/'tools/teleporter/generate_fx.py'),'--check'],check=True)
report=dict(palette=palette,accepted_geometry_and_maps_unchanged=unchanged,metal_finish_unchanged=True,
            all_status_effect_colors_checked=True,native_built=False,native_visual_verified=False)
(OUT/'source_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('TELEPORTER_PALETTE_PASS: green ready, yellow pending, zero off; accepted metal and all eight meshes unchanged')
