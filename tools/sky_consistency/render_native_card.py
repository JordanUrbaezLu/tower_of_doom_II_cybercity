"""Render the MCP-authored card material bake; preserve strict source provenance."""
import json
import pathlib
import shutil
import sys
import time
import bpy
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pass_config import STAGE, REVIEW, sha, source_hashes
r = json.loads((STAGE / 'native_card_author.json').read_text(encoding='utf-8'))
assert r['sky_source_hashes'] == source_hashes(), 'Source drift before card material bake'
assert sha(ROOT / r['blend']) == r['blend_sha256']
assert sha(ROOT / r['source_png']) == r['source_png_sha256']
sc = bpy.data.scenes['Native sign material bake']
bpy.context.window.scene = sc
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == 'OPTIX'
sc.cycles.device = 'GPU'
t = time.time()
bpy.ops.render.render(write_still=True)
assert r['sky_source_hashes'] == source_hashes(), 'Source drift during card material bake'
out = ROOT / r['output']
asset = ROOT / 'art/sky3d/sign/v11_native_lit.png'
shutil.copyfile(out, asset)
r.update(output_sha256=sha(out), generated_asset=asset.relative_to(ROOT).as_posix(),
         generated_asset_sha256=sha(asset), renderer_sha256=sha(pathlib.Path(__file__)), seconds=time.time()-t,
         alpha_note='Derived visibility alpha includes foreground and ground holdouts; immutable source painting preserved.')
(REVIEW / 'native_card_art.json').write_text(json.dumps(r, indent=2)+'\n', encoding='utf-8')
print('NATIVE_CARD_BAKED', r['output_sha256'])
