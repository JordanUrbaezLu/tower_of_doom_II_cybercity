"""Render the MCP-authored scene in a separate Cycles process, keep paired AOV."""
import json
import pathlib
import shutil
import sys
import time
import bpy
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.modules.pop('pass_config', None)  # fresh pass paths even in the reused MCP studio
from pass_config import STAGE, sha, source_hashes
author = json.loads((STAGE / 'author.json').read_text(encoding='utf-8'))
assert author['source_hashes'] == source_hashes(), 'Authoring sources changed; regenerate the master before rendering'
assert sha(pathlib.Path(bpy.data.filepath)) == author['blend_sha256'], 'Master differs from the saved authoring receipt'
for name, expected in author['art_inputs'].items():
    assert sha(pathlib.Path(name)) == expected, 'Authored image changed: ' + name
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
width = int(args[0]) if args else 4096
samples = int(args[1]) if len(args)>1 else 96
assert width in (2048, 4096, 8192) and samples > 0
sc = bpy.context.scene
out = ROOT/'tmp/sky_dealer'/('raw_%d.exr'%width)
sc.render.resolution_x=width; sc.render.resolution_y=width//2
sc.cycles.samples=samples
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX'; prefs.get_devices()
for d in prefs.devices:
    d.use=d.type=='OPTIX'
sc.cycles.device='GPU'
sc.render.filepath=str(out)
for node in sc.node_tree.nodes:
    if node.type=='OUTPUT_FILE':
        node.base_path=str(out.parent)
        node.file_slots[0].path=out.stem+'.signmask_'
start=time.time()
bpy.ops.render.render(write_still=True)
candidates=list(out.parent.glob(out.stem+'.signmask_*.exr'))
assert len(candidates)==1, candidates
mask=out.with_suffix('.sign.exr')
candidates[0].replace(mask)
receipt={'blend':bpy.data.filepath,'raw':str(out),'mask':str(mask),'width':width,'samples':samples,'seconds':time.time()-start}
receipt.update(blend_sha256=author['blend_sha256'], raw_sha256=sha(out), mask_sha256=sha(mask),
               source_hashes=author['source_hashes'], renderer_sha256=sha(pathlib.Path(__file__)))
receipt['art_inputs'] = author['art_inputs']
if author.get('title_report'):
    title = pathlib.Path(author['title_report']['path'])
    assert sha(title) == author['title_report']['sha256'], 'Title report changed since authoring'
    if title != out.with_suffix('.title.json'):
        shutil.copyfile(title, out.with_suffix('.title.json'))
    receipt['title_report_sha256'] = author['title_report']['sha256']
out.with_suffix('.render.json').write_text(json.dumps(receipt,indent=2))
print('CONSISTENCY_RENDER_DONE',json.dumps(receipt),flush=True)
