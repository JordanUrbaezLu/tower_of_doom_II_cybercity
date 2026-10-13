"""Inspect evaluated power/animation/pose, then resume the visible studio without resaving."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'art/partner_shop';scene=bpy.context.scene
if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
def emission(m):
    value=m.node_tree.nodes.get('Electrical timeline');gate=m.node_tree.nodes.get('Shop master power')
    fault=m.node_tree.nodes.get('Shared electrical fault')
    return value.outputs[0].default_value*gate.inputs[1].default_value*(fault.inputs[1].default_value if fault else 1) if value and gate else 0
def power(value,frame):
    scene['shop_powered']=value;scene.update_tag()
    for m in bpy.data.materials:
        if m.get('shop_emissive'):m.node_tree.update_tag()
    for ob in scene.objects:ob.update_tag()
    scene.frame_set(frame);bpy.context.view_layer.update()
# The sign is read from the master (18_black_market_sign.py): BLACK MARKET, C/E/T blink.
TEXT=scene.get('shop_sign_text','ITEM SHOP');BLINK=scene.get('shop_sign_blink','TEH')
sign_mats=sorted({m.name[len('SHOP / '):] for ob in scene.objects if ob.get('neon_letter') for m in ob.data.materials if m})
power(1,1);letters={name:[] for name in sign_mats};mask=[];angles=[];samples=[]
affected=['neon letter '+c for c in BLINK]+['mask slow red breath','mask weak wire breath','left red energy core','counter canister red pulse','existing tall core red pulse']+['left core scan '+str(i) for i in range(4)]
for frame in range(1,182):
    scene.frame_set(frame);bpy.context.view_layer.update()
    for c in letters:letters[c].append(round(emission(bpy.data.materials['SHOP / '+c]),5))
    mask.append(round(emission(bpy.data.materials['SHOP / mask slow red breath']),5))
    values=[emission(bpy.data.materials['SHOP / '+m]) for m in affected]
    expected=scene['shop_fault_bus']>0.5
    assert all((v>1e-7)==(True if name.startswith('mask ') else expected) for name,v in zip(affected,values)),(frame,values,expected)
    angles.append(math.degrees(bpy.data.objects['Pressure | wheel pivot'].rotation_euler.y))
    samples.append({'frame':frame,'bus':scene['shop_fault_bus'],'emission':dict(zip(affected,values)),'valve_degrees':angles[-1]})
assert sorted(c for c,v in letters.items() if len(set(v))>1)==sorted('neon letter '+c for c in BLINK),letters.keys()
assert all(max(v)>5 and v[0]==v[-1] for v in letters.values())
assert mask[0]==mask[-1] and min(mask)<.1 and max(mask)>3
assert min(mask)>0.07,'The mask must breathe independently without fault blackouts'
assert abs(max(angles)-100)<.001 and abs(min(angles))<.001
assert len({tuple(letters['neon letter '+c]) for c in BLINK})==1,'the blinking letters share one fault timeline'
(OUT/'electrical_evaluated.json').write_text(json.dumps(samples,indent=2))
power(0,45)
visible_mats={m for ob in scene.objects if ob.type in ('MESH','CURVE','FONT') and not ob.hide_render for m in ob.data.materials if m and m.get('shop_emissive')}
assert all(abs(emission(m))<1e-7 for m in visible_mats),[(m.name,emission(m)) for m in visible_mats if abs(emission(m))>1e-7]
vendor=bpy.data.collections['SHOP | 04 MERCHANT - active only']
assert all(o.hide_render for o in vendor.objects if o.type in ('MESH','CURVE','FONT'))
assert abs(bpy.data.objects['Pressure | wheel pivot'].rotation_euler.y)<1e-7
assert abs(bpy.data.objects['Pressure | gauge pivot'].rotation_euler.y)<1e-7
power(1,1);deps=bpy.context.evaluated_depsgraph_get()
def bounds(obs):
    pts=[]
    for ob in obs:
        if ob.type not in ('MESH','CURVE','FONT'):continue
        ev=ob.evaluated_get(deps);me=ev.to_mesh();pts.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
    return [[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]
hands=bounds([o for o in vendor.objects if o.name.startswith('Merchant | lowered glove')]);person=bounds(vendor.objects)
assert hands[1][2]<42,hands;assert person[1][2]<78 and abs(person[0][2]-11.9)<.15,person
manifest=OUT/'engine_kit/install_manifest.json'
exported=manifest.exists() and json.loads(manifest.read_text())['master_sha256']==hashlib.sha256((OUT/'partner_shop.blend').read_bytes()).hexdigest()
report={'revision':3,'blender':bpy.app.version_string,'sign_text':TEXT,'dead_letters':[],'blinking_letters':list(BLINK),'steady_letters':sorted({c for c in TEXT.replace(' ','') if c not in BLINK}),'sign_materials':sign_mats,'mask_range':[min(mask),max(mask)],'mask_independent_of_faults':True,'shared_power_faults_checked':True,'valve_travel_degrees':max(angles)-min(angles),'hands_bounds':hands,'vendor_bounds':person,'off_emission_zero':True,'off_vendor_absent':True,'off_pressure_at_rest':True,'loop_seams':True,'native_exported':exported,'native_playtested':False,'game_launched':False}
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
scene.render.engine='BLENDER_EEVEE';scene.sync_mode='FRAME_DROP';scene.camera=bpy.data.objects['01 HERO - three-quarter']
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.shading.type='RENDERED';s.overlay.show_overlays=False;s.clip_end=5000
            s.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion();s.region_3d.view_location=(0,-2,61);s.region_3d.view_distance=305
if bpy.context.screen and not bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_play()
print('LIVE_VALIDATED',json.dumps(report))
