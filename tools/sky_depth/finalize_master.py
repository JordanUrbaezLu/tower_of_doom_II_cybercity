"""Save final production render settings on the reviewed MCP-authored master."""
import pathlib
import json
import sys
import bpy
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.modules.pop('pass_config', None)  # fresh pass paths even in the reused MCP studio
from pass_config import STAGE, sha, source_hashes
from quality_profile import PROFILE_PATH, load_quality, apply_quality
author=json.loads((STAGE/'author.json').read_text(encoding='utf-8'))
assert author['source_hashes']==source_hashes(), 'Authoring sources changed; regenerate the master first'
master=STAGE/'depth.blend'
assert pathlib.Path(bpy.data.filepath).resolve()==master.resolve(), 'Open the saved editable master before finalizing; the preview scene must never replace it'
assert sha(master)==author['blend_sha256'], 'Saved editable master differs from its authoring receipt'
sc=bpy.context.scene
sc.render.resolution_x=8192
sc.render.resolution_y=4096
sc.cycles.samples=160
render_quality=apply_quality(sc, production=True)
sc.render.filepath=str(ROOT/'tmp/sky_depth/raw_8192.exr')
for node in sc.node_tree.nodes:
    if node.type=='OUTPUT_FILE':
        node.base_path=str(ROOT/'tmp/sky_depth')
        node.file_slots[0].path='raw_8192.signmask_'
sc['sky_art_direction']='v13 readable mid/far architecture and depth; same Dealer title, restrained celestial detail and camera anchors'
sc['preview_note']='Authoring W units. See depth_preview.blend for the finished exported sky; native BO3 exposure remains user-verified.'
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'tmp/sky_depth/depth.blend'))
author['blend_sha256']=sha(STAGE/'depth.blend')
author['render_settings']={'width':8192,'height':4096,'samples':160}
author.update(quality_profile=load_quality(), quality_profile_sha256=sha(PROFILE_PATH),
              render_quality=render_quality)
(STAGE/'author.json').write_text(json.dumps(author,indent=2)+'\n',encoding='utf-8')
print('FINAL_MASTER_SAVED',len(sc.objects),sum(len(o.data.polygons) for o in sc.objects if o.type=='MESH'))
