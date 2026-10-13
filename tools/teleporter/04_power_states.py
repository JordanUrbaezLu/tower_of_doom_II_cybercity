"""MCP art pass: dark, green ready, and a yellow circular pending chase."""
import bpy,json,math,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'art/teleporter'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'teleporter_cyber.blend'));scene=bpy.context.scene
palette_spec=json.loads((ROOT/'tools/teleporter/state_palette.json').read_text())
assert sum(bool(o.get('teleporter_design')) for o in scene.objects)==446
if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
backup=OUT/'checkpoints/before_power_states.blend';backup.parent.mkdir(exist_ok=True)
if not backup.exists():shutil.copyfile(OUT/'teleporter_cyber.blend',backup)
scene['teleporter_state']=1;scene['teleporter_preview_auto']=1
scene.id_properties_ui('teleporter_state').update(min=0,max=2,description='0 OFF / 1 READY green / 2 PENDING yellow chase. Disable preview_auto for manual control.')
scene.id_properties_ui('teleporter_preview_auto').update(min=0,max=1,description='Automatically demonstrate all three states over twelve seconds.')
scene.render.fps=30;scene.frame_start=1;scene.frame_end=360
mode='(state if auto < 0.5 else (0 if frame <= 60 else (1 if frame <= 150 or frame > 330 else 2)))'
def drive(owner,prop,expression,index=None):
    try:owner.driver_remove(prop) if index is None else owner.driver_remove(prop,index)
    except TypeError:pass
    fc=owner.driver_add(prop) if index is None else owner.driver_add(prop,index)
    d=fc.driver;d.type='SCRIPTED';d.expression=expression
    for name,path in [('state','teleporter_state'),('auto','teleporter_preview_auto')]:
        v=d.variables.new();v.name=name;v.type='SINGLE_PROP';v.targets[0].id_type='SCENE';v.targets[0].id=scene;v.targets[0].data_path='["'+path+'"]'
materials={m for o in scene.objects if o.get('teleporter_design') for m in o.data.materials if m}
for m in materials:
    if not m.use_nodes:continue
    p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if not p:continue
    strength=m.get('tp_state_strength',p.inputs['Emission Strength'].default_value)
    if strength<=0:continue
    m['tp_state_strength']=strength;p.inputs['Emission Color'].default_value=(*palette_spec['ready_linear'],1)
    p.inputs['Base Color'].default_value=(.008,.008,.011,1)
    drive(p.inputs['Emission Strength'],'default_value',str(strength)+'*('+mode+' == 1)')
col=bpy.data.collections.get('04 STATES | yellow recharge chase')
if col:
    for ob in list(col.objects):bpy.data.objects.remove(ob,do_unlink=True)
else:col=bpy.data.collections.new('04 STATES | yellow recharge chase');scene.collection.children.link(col)
root=bpy.data.objects.new('Recharge | circular chase pivot',None);col.objects.link(root)
drive(root,'rotation_euler','(frame-151)*2*pi/90',2)
palette=[]
for i,strength in enumerate((5.5,2.3,.75)):
    m=bpy.data.materials.get('TP state | yellow '+str(i)) or bpy.data.materials.new('TP state | yellow '+str(i));m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.08,.028,.002,1);p.inputs['Roughness'].default_value=.35
    p.inputs['Emission Color'].default_value=(*palette_spec['pending_linear'],1)
    drive(p.inputs['Emission Strength'],'default_value',str(strength)+'*('+mode+' == 2)')
    m['tp_state_strength']=strength;palette.append(m)
for i in range(18):
    curve=bpy.data.curves.new('Recharge arc '+str(i),'CURVE');curve.dimensions='3D';curve.bevel_depth=.25;curve.bevel_resolution=2;curve.resolution_u=1
    spl=curve.splines.new('POLY');spl.points.add(4)
    for j,pt in enumerate(spl.points):
        a=math.radians(-i*5+j);pt.co=(73.05*math.cos(a),73.05*math.sin(a),8.5,1)
    ob=bpy.data.objects.new('Recharge | segment %02d'%i,curve);col.objects.link(ob);ob.parent=root;curve.materials.append(palette[i//6]);ob['tp_state_art']=True;ob['tp_state_band']=i//6
    drive(ob,'hide_render',mode+' != 2');drive(ob,'hide_viewport',mode+' != 2')
scene['teleporter_state_contract']='OFF: zero emission, no chase. READY: green strips. PENDING: green off, yellow quarter-circle chase; one turn / 3 seconds.'
scene.frame_set(190);bpy.context.view_layer.update();scene.render.engine='BLENDER_EEVEE';scene.sync_mode='FRAME_DROP'
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.shading.type='RENDERED';area.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'teleporter_cyber.blend'))
if bpy.context.screen and not bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_play()
(OUT/'states_brief.md').write_text('''# Teleporter status art\n\nUser correction, September 26: OFF has no device lights; READY is green; PENDING is an animated yellow chase. No pink. The accepted metal finish stays intact.\n\nMaster: teleporter_cyber.blend, MCP port 9879. Original 446 parts and baked body retained. Eighteen yellow arc segments form a quarter-circle chase rotating once every three seconds, with three brightness bands. Manual scene teleporter_state: 0 off, 1 ready, 2 pending; teleporter_preview_auto=0 enables manual control.\n\nNative: same seven body LODs, green and zero-emission material twins, one 1,152-triangle yellow indicator while powered but pending (destination lock, cooldown or upgrade pause). Explicit shutdown and no power are dark. Ready FX is green; charge overlay yellow; release overlay green. Stock teleport bursts retain their original electricity. Triggers, 0.8-second travel charge and 60-second cooldown are preserved. No additional particles or dynamic lights.\n\nBlender proves authored shape/timing; BO3 appearance and runtime output require the user playtest. Read docs/162_lighting/03_glow_and_perks.md; untested shader/light claims remain untested.\n''')
print('TELEPORTER_STATES_AUTHORED',len(materials),'retained materials; 18 chase segments; 3-second revolution')
