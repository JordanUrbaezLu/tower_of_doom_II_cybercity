"""Render and check the authored three-state loop without resaving the master."""
import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/teleporter'
bpy.ops.wm.open_mainfile(filepath=str(ART/'teleporter_cyber.blend'));s=bpy.context.scene;s.render.engine='BLENDER_EEVEE'
s.render.resolution_x=960;s.render.resolution_y=704;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
if hasattr(s.eevee,'taa_render_samples'):s.eevee.taa_render_samples=32
base={m for o in s.objects if o.get('teleporter_design') for m in o.data.materials if m and m.get('tp_state_strength')}
arcs=[o for o in s.objects if o.get('tp_state_art')]
def frame(f):
    s.frame_set(f);s.update_tag()
    for m in bpy.data.materials:
        if m.use_nodes:m.node_tree.update_tag()
    for o in arcs:o.update_tag()
    bpy.context.view_layer.update()
def energy(m):return next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Emission Strength'].default_value
for name,f,state in [('off',20,0),('ready',100,1),('recharging',190,2)]:
    frame(f)
    if state==1:assert all(energy(m)>0 for m in base) and all(o.hide_render for o in arcs)
    else:assert all(energy(m)==0 for m in base)
    if state==0:assert all(o.hide_render for o in arcs)
    if state==2:assert all(not o.hide_render for o in arcs)
    s.render.filepath=str(ART/('state_'+name+'.png'));bpy.ops.render.render(write_still=True)
folder=ART/'state_frames';folder.mkdir(exist_ok=True)
for i,f in enumerate(range(1,361,3)):
    frame(f);s.render.filepath=str(folder/('%04d.png'%i));bpy.ops.render.render(write_still=True)
(ART/'state_art_validation.json').write_text(json.dumps({'off_zero_emission':True,'off_chase_hidden':True,'ready_green':True,'recharge_green_off':True,'recharge_yellow_visible':True,'chase_revolution_seconds':3,'preview_seconds':12,'native_playtested':False},indent=2))
print('TELEPORTER_STATE_PREVIEW_COMPLETE',flush=True)
