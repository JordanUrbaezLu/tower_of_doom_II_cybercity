"""Save final production render settings on the reviewed MCP-authored master."""
import pathlib
import bpy
ROOT=pathlib.Path(__file__).resolve().parents[2]
sc=bpy.context.scene
sc.render.resolution_x=8192
sc.render.resolution_y=4096
sc.cycles.samples=160
sc.render.filepath=str(ROOT/'tmp/sky_cohesion/raw_8192.exr')
for node in sc.node_tree.nodes:
    if node.type=='OUTPUT_FILE':
        node.base_path=str(ROOT/'tmp/sky_cohesion')
        node.file_slots[0].path='raw_8192.signmask_'
sc['sky_art_direction']='Dark cosmic cybercity; v8 authored monument and four lower-city forms'
sc['preview_note']='Authoring W units. See sky_preview.blend for the finished exported sky; native BO3 exposure remains user-verified.'
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'tmp/sky_cohesion/cohesion.blend'))
print('FINAL_MASTER_SAVED',len(sc.objects),sum(len(o.data.polygons) for o in sc.objects if o.type=='MESH'))
