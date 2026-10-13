"""Save final production render settings on the reviewed MCP-authored master."""
import pathlib
import json
import sys
import bpy
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pass_config import STAGE, sha, source_hashes
author=json.loads((STAGE/'author.json').read_text(encoding='utf-8'))
assert author['source_hashes']==source_hashes(), 'Authoring sources changed; regenerate the master first'
sc=bpy.context.scene
sc.render.resolution_x=8192
sc.render.resolution_y=4096
sc.cycles.samples=160
sc.render.filepath=str(ROOT/'tmp/sky_simplify/raw_8192.exr')
for node in sc.node_tree.nodes:
    if node.type=='OUTPUT_FILE':
        node.base_path=str(ROOT/'tmp/sky_simplify')
        node.file_slots[0].path='raw_8192.signmask_'
sc['sky_art_direction']='v9 reduced visual density; authored hero station and title, preserved game camera anchors'
sc['preview_note']='Authoring W units. See simplify_preview.blend for the finished exported sky; native BO3 exposure remains user-verified.'
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'tmp/sky_simplify/simplify.blend'))
author['blend_sha256']=sha(STAGE/'simplify.blend')
author['render_settings']={'width':8192,'height':4096,'samples':160}
(STAGE/'author.json').write_text(json.dumps(author,indent=2)+'\n',encoding='utf-8')
print('FINAL_MASTER_SAVED',len(sc.objects),sum(len(o.data.polygons) for o in sc.objects if o.type=='MESH'))
