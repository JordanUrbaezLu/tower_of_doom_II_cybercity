"""Render matched 8K-angular-scale crops; never resave a source master.

Run only via review_quality.ps1 after the MCP-authored candidate is saved.
Before / after_old isolate architecture; after_old / after isolate sampling.
The fixed inspection exposure is approximate, not a native game screenshot.
"""
import json
import math
from pathlib import Path
import sys
import time
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from pass_config import STAGE, REVIEW, sha
from quality_profile import apply_quality, actual_quality, load_quality

case = sys.argv[sys.argv.index('--') + 1]
assert case in ('before', 'after_old', 'after')
master = REVIEW / 'before/tod2_sky.blend' if case == 'before' else STAGE / 'depth.blend'
assert Path(bpy.data.filepath).resolve() == master.resolve()
master_sha = sha(master)
if case != 'before':
    author = json.loads((STAGE / 'author.json').read_text(encoding='utf-8'))
    assert master_sha == author['blend_sha256'], 'Candidate master was not recorded by MCP authoring'
sc = bpy.context.scene
assert sc.camera.data.type == 'PANO'
source_quality = actual_quality(sc)
if case == 'before':
    assert source_quality['filter_width'] == 1.5
    assert source_quality['pixel_filter_type'] == 'BLACKMAN_HARRIS'
    assert source_quality['adaptive_threshold'] == .025
    assert source_quality['adaptive_min_samples'] == 16
    assert source_quality['use_adaptive_sampling']
apply_quality(sc, production=True)
if case in ('before', 'after_old'):
    sc.cycles.adaptive_threshold = .025
    sc.cycles.adaptive_min_samples = 16
    sc.cycles.filter_width = 1.5
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == 'OPTIX'
sc.cycles.device = 'GPU'
sc.cycles.seed = 73
sc.render.use_persistent_data = False
sc.render.resolution_percentage = 100
sc.render.use_border = sc.render.use_crop_to_border = True
# No compositor file-output node may overwrite the production sign AOV.
sc.use_nodes = False
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.render.image_settings.color_depth = '8'
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
gain = json.loads((Path(__file__).parent / 'finish_profile.json').read_text())['fixed_gain']
sc.view_settings.exposure = math.log2(gain * 10.0 / .0176)
sc.view_settings.gamma = 1.0
out = REVIEW / 'crops'
out.mkdir(exist_ok=True)
views = [('mid_city', 108, 140, -3, 15),
         ('outer_city', 45, 78, 0, 16),
         ('roofscape', -75, -43, -18, 2)]
images = {}
for name, az0, az1, el0, el1 in views:
    c0, c1 = math.floor((az0 / 360 + .5) * 8192), math.ceil((az1 / 360 + .5) * 8192)
    r0, r1 = math.floor((90 - el1) / 180 * 4096), math.ceil((90 - el0) / 180 * 4096)
    sc.render.border_min_x, sc.render.border_max_x = c0 / 8192, c1 / 8192
    sc.render.border_min_y, sc.render.border_max_y = (4096-r1) / 4096, (4096-r0) / 4096
    path = out / (case + '_' + name + '.png')
    sc.render.filepath = str(path)
    started = time.time()
    bpy.ops.render.render(write_still=True)
    images[name] = dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path),
                        bounds=[c0, c1, r0, r1], pixels=[c1-c0, r1-r0],
                        seconds=time.time()-started)
assert sha(master) == master_sha, 'Read-only source master changed during review'
report = dict(case=case, master=master.relative_to(ROOT).as_posix(), master_sha256=master_sha,
              source_quality=source_quality,
              script_sha256=sha(Path(__file__)), quality_profile=load_quality(),
              render_quality=actual_quality(sc), fixed_inspection_exposure=sc.view_settings.exposure,
              scene_camera='same saved equirectangular camera; crops are native 8192 pixel scale',
              images=images, master_resaved=False, native_visual_verified=False)
(out / (case + '.json')).write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print('DEPTH_QUALITY_CROPS_COMPLETE', case)
