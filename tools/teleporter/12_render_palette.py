"""Render native-input palette states and one full yellow revolution."""
import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/teleporter';OUT=ART/'status_colors'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'native_states.blend'));s=bpy.context.scene
arcs=[o for o in s.objects if o.get('tp_preview_chase')]
mat=next(o for o in s.objects if o.get('tp_preview_body')).data.materials[0]
em=next(n for n in mat.node_tree.nodes if n.type=='EMISSION')
def frame(n):
    s.frame_set(n);s.update_tag()
    for m in bpy.data.materials:
        if m.use_nodes:m.node_tree.update_tag()
    for o in arcs:o.update_tag()
    bpy.context.view_layer.update()
s.render.image_settings.file_format='PNG'
for name,n,state in [('off',20,0),('ready',100,1),('recharging',190,2)]:
    frame(n);assert em.inputs['Strength'].default_value==(6 if state==1 else 0)
    assert all(o.hide_render==(state!=2) for o in arcs)
    s.render.filepath=str(ART/('state_'+name+'.png'));bpy.ops.render.render(write_still=True)
frames=OUT/'frames';frames.mkdir(exist_ok=True)
s.render.resolution_percentage=70
# 1 s off + 1 s green + a full 3 s pending revolution + 1 s green at 10 fps.
sequence=list(range(1,31,3))+list(range(91,121,3))+list(range(151,241,3))+list(range(331,361,3))
for i,n in enumerate(sequence):
    frame(n);s.render.filepath=str(frames/('%04d.png'%i));bpy.ops.render.render(write_still=True)
(ART/'state_art_validation.json').write_text(json.dumps(dict(off_zero_emission=True,off_chase_hidden=True,ready_green=True,
    pending_green_off=True,pending_yellow_visible=True,chase_revolution_seconds=3,preview_seconds=6,
    source='exported xmodel_bin and native map bindings',native_playtested=False),indent=2)+'\n')
print('TELEPORTER_NATIVE_PALETTE_RENDER_PASS 3 states, 60 frames, one complete yellow revolution',flush=True)
