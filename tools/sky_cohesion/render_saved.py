"""Render the MCP-authored scene in a separate Cycles process, keep paired AOV."""
import json
import pathlib
import sys
import time
import bpy
ROOT = pathlib.Path(__file__).resolve().parents[2]
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
width = int(args[0]) if args else 4096
samples = int(args[1]) if len(args)>1 else 96
sc = bpy.context.scene
out = ROOT/'tmp/sky_cohesion'/('raw_%d.exr'%width)
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
out.with_suffix('.render.json').write_text(json.dumps(receipt,indent=2))
print('COHESION_RENDER_DONE',json.dumps(receipt),flush=True)
