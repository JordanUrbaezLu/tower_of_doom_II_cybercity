import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/cyber_sword'
bpy.ops.wm.open_mainfile(filepath=str(ART/'native_preview.blend'))
scene=bpy.context.scene;scene.cycles.samples=16
mat=bpy.data.materials['Native approximation | mtl_tod_cyber_sword']
for n in mat.node_tree.nodes:
    if n.type=='NORMAL_MAP':
        for link in list(n.inputs['Color'].links):mat.node_tree.links.remove(link)
        n.inputs['Color'].default_value=(.5,.5,1,1)
scene.render.filepath=str(ART/'normal_diagnostic.png');bpy.ops.render.render(write_still=True)
