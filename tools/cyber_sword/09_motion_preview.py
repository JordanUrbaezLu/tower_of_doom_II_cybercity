"""Small exported-mesh motion preview; native engine brightness remains a user test."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/cyber_sword';OUT=ART/'motion_frames';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ART/'native_preview.blend'))
scene=bpy.context.scene;scene.render.resolution_percentage=50;scene.cycles.samples=12
mat=bpy.data.materials['Native approximation | mtl_tod_cyber_sword']
em=next(n for n in mat.node_tree.nodes if n.type=='EMISSION')
for frame in range(24):
    strength=0 if frame<5 or frame>=20 else min(1,(frame-4)/3)
    em.inputs[1].default_value=12*strength
    scene.render.filepath=str(OUT/f'{frame:03}.png')
    bpy.ops.render.render(write_still=True)
print('CYBER_SWORD_MOTION_DONE',flush=True)
