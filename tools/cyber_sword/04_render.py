"""Render the MCP-authored dark/ready states without opening the game."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'art/cyber_sword'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'cyber_sword.blend'))
scene=bpy.context.scene
for name,frame in [('charging',1),('ready',60)]:
    scene.frame_set(frame);scene.update_tag();bpy.context.view_layer.update()
    print('RENDER_STATE',name,scene['cyber_charge'],bpy.data.materials['CS | cyan circuit'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value,flush=True)
    scene.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True);print('CYBER_SWORD_RENDERED',name,flush=True)
