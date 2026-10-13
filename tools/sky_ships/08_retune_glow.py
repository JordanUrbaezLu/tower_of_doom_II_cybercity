"""Re-apply sky_lib.EMIT to every sky material in the studio (native scaleRGB + viewport emission) without
rebuilding the ships. Then re-run 06_export.py + install.py."""
import bpy, sys, importlib, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib
importlib.reload(sky_lib)
EMIT = sky_lib.EMIT
def kind_of(label):
    if label.startswith('engine_'): return 'engine'
    if label.startswith('nav_'): return 'nav'
    if label.startswith('neon_'): return 'neon'
    if label.startswith('cargo_'): return 'container'
    return {'windows': 'window', 'hangar': 'hangar', 'glass': 'glass'}.get(label)
done = {}
for m in bpy.data.materials:
    if not m.name.startswith('mtl_tod_sky_') or 'bo3' not in m:
        continue
    d = json.loads(m['bo3'])
    k = kind_of(m.name[len('mtl_tod_sky_'):])
    if d['kind'] != 'glow' or k is None:
        continue
    d['scaleRGB'] = EMIT[k]
    m['bo3'] = json.dumps(d)
    bs = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bs.inputs['Emission Strength'].default_value = EMIT[k] * 0.6 * 0.3     # the studio view stays readable
    done[m.name] = EMIT[k]
print('SKY_GLOW_RETUNED', json.dumps(done))
