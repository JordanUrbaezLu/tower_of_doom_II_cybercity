"""THE WAR DAMAGE KIT (docs/205): resolve every stock Treyarch prop the pass uses.

Reads each prop's LOD xmodel_bin files from the stock Mod Tools model_export
(read-only), measures the real LOD0 mesh (never the _col collision file) and
writes art/war_damage/kit.json: the files per LOD, the material names, the
triangle counts and the LOD0 bounds. build_clusters.py and layout.js read it;
nothing here is guessed from a name.

Usage: python tools/war_damage/probe_kit.py
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel  # noqa: E402

STOCK = pathlib.Path(r'C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130\model_export')

# role -> stock models. Roles are what layout.js asks for; every one must resolve.
KIT = {
    'pile':      ['p7_debris_concrete_rubble_pile_03'],
    'scatter':   ['p7_debris_concrete_rubble_scattered_01'],
    'chunk':     ['p7_debris_concrete_rubble_sm_00', 'p7_debris_concrete_rubble_sm_03', 'p7_debris_concrete_rubble_sm_07'],
    'slab':      ['p7_debris_concrete_rubble_lg_03_no_metal', 'p7_debris_concrete_rubble_med_01_no_metal'],
    'rebar':     ['p7_rebar_straight_32_01', 'p7_rebar_straight_32_02'],
    'rebar_grid':['p7_rebar_patch_64x64_01', 'p7_rebar_patch_64x64_02'],
    'rebar_col': ['p7_rebar_column_128'],
    'scrap':     ['p7_fxp_debris_metal_scrap_01', 'p7_fxp_debris_metal_scrap_02'],
    'beam':      ['p7_zm_der_gantry_beam_01'],
    'cable':     ['p7_wires_electrical_rubber_02', 'p7_wires_electrical_rubber_03', 'p7_wires_electrical_rubber_04'],
    'fixture':   ['p7_light_fixture_led_ceiling_01_dmg'],
    'glass':     ['p7_debris_glass_shards_01', 'p7_debris_glass_shards_03'],
}

def lod_files(name):
    """-> {lod index: path} for name_lodN.xmodel_bin (case-insensitive), any folder."""
    out = {}
    pat = re.compile(re.escape(name) + r'_lod(\d)\.xmodel_bin$', re.I)
    for p in STOCK.rglob(name + '_lod*'):
        m = pat.search(p.name)
        if m:
            out[int(m.group(1))] = p
    return dict(sorted(out.items()))

def measure(path):
    m = xmodel.Model()
    m.LoadFile_Bin(str(path), split_meshes=True)
    pts = [v.offset for me in m.meshes for v in me.verts]
    return {
        'bones': len(m.bones),
        'materials': [mt.name for mt in m.materials],
        'triangles': sum(len(me.faces) for me in m.meshes),
        'min': [round(min(p[i] for p in pts), 2) for i in range(3)],
        'max': [round(max(p[i] for p in pts), 2) for i in range(3)],
    }

kit, missing = {}, []
for role, names in KIT.items():
    for name in names:
        files = lod_files(name)
        if 0 not in files:
            missing.append(name)
            continue
        info = measure(files[0])
        info['lods'] = {str(k): p.relative_to(STOCK).as_posix() for k, p in files.items()}
        info['lod_triangles'] = {str(k): measure(p)['triangles'] for k, p in files.items()}
        info['role'] = role
        kit[name] = info
        print(f"{role:10s} {name:44s} lods={list(files)} tris={info['lod_triangles']} "
              f"size={[round(b - a, 1) for a, b in zip(info['min'], info['max'])]} mats={info['materials']}")

out = ROOT / 'art/war_damage/kit.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'stock_root': str(STOCK), 'props': kit, 'missing': missing}, indent=2) + '\n')
print('KIT', len(kit), 'props resolved;', 'MISSING: ' + ', '.join(missing) if missing else 'none missing')
roles_without = [r for r, names in KIT.items() if not any(n in kit for n in names)]
if roles_without:
    print('FAIL roles with no usable prop:', roles_without)
    sys.exit(1)
