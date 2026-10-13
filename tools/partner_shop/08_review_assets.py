"""Render current design and exact flicker states; save editable state and evidence."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'art/partner_shop'
scene=bpy.context.scene;assert scene.get('tod2_shop_studio')
stage=bpy.data.collections['SHOP | 90 STUDIO - exclude from export']
vendor=bpy.data.collections['SHOP | 04 MERCHANT - active only']
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.image_settings.file_format='PNG'
scene.frame_set(1)
def cam(name,loc,target,lens=60):
    ob=bpy.data.objects.get(name)
    if ob is None:
        ob=bpy.data.objects.new(name,bpy.data.cameras.new(name));stage.objects.link(ob)
    ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.lens=lens;ob.data.clip_end=5000
    return ob
def render(camera,file,w,h):
    scene.camera=camera;scene.render.resolution_x=w;scene.render.resolution_y=h
    scene.render.filepath=str(OUT/file);bpy.ops.render.render(write_still=True)
hero=bpy.data.objects['01 HERO - three-quarter']
render(hero,'hero.png',1440,1200)
render(bpy.data.objects['02 PLAYER - service window'],'player_view.png',1440,1100)
merchant=cam('04 MERCHANT - close view',(25,-142,65),(0,-3,60),80)
render(merchant,'merchant.png',1100,1100)
render(bpy.data.objects['03 REAR - service hardware'],'rear.png',1200,1100)

# Render each distinct sign state once, then preserve its exact 30-fps event durations.
# Only emission changes, so reusing an identical state's still is lossless for this view.
signcam=cam('05 SIGN - flicker review',(0,-205,105),(0,-57,105),60)
signcam.data.type='ORTHO';signcam.data.ortho_scale=119
timing=json.loads((OUT/'neon_timing.json').read_text())
frames=sorted({1,181}|{f for rows in timing['animated_emission'].values() for f,v in rows})
dest=OUT/'sign_frames';dest.mkdir(exist_ok=True)
states={};clips=[]
scene.cycles.samples=12
for frame,end in zip(frames,frames[1:]):
    scene.frame_set(frame)
    state=tuple(round(next(n for n in bpy.data.materials['SHOP / neon letter '+letter].node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Emission Strength'].default_value,3) for letter in ('T','H'))
    if state not in states:
        file='sign_frames/state_%02d.png'%len(states)
        render(signcam,file,1000,320);states[state]=file
    clips.append((states[state],(end-frame)/30))
concat=['ffconcat version 1.0']
for file,duration in clips:
    concat+=['file '+file,'duration %.9f'%duration]
concat+=['file '+clips[-1][0]]
(OUT/'sign_animation.ffconcat').write_text('\n'.join(concat)+'\n',encoding='utf-8')

# Describe actual evaluated geometry and enforce the user-visible pose / separation.
scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
def bounds(objects):
    pts=[]
    for o in objects:
        if o.type in ('MESH','CURVE','FONT'):
            ev=o.evaluated_get(deps);pts.extend(ev.matrix_world@Vector(p) for p in ev.bound_box)
    return {'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]}
groups={}
for c in bpy.data.collections:
    if c.name.startswith('SHOP |') and not c.name.startswith(('SHOP | 90','SHOP | 91')):
        tri=0
        for ob in c.objects:
            if ob.type in ('MESH','CURVE','FONT'):
                ev=ob.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);ev.to_mesh_clear()
        groups[c.name]={'objects':len(c.objects),'evaluated_triangles':tri,'bounds':bounds(c.objects)}
hands=[o for o in vendor.objects if o.name.startswith('Merchant | lowered glove')]
hand_bounds=bounds(hands)
assert hand_bounds['max'][2]<42,'Hands must remain below the counter'
assert len(hands)==2
vendor_bounds=bounds(vendor.objects)
assert abs(vendor_bounds['min'][2]-11.9)<.15,'Merchant feet must rest on the interior deck'
assert vendor_bounds['max'][2]<78,'Merchant must sit comfortably below the window header'
assert scene['shop_sign_text']=='ITEM SHOP'
assert len(states)>2,'Flicker evaluation did not change states'
validation={'stage':'editable Blender art, not native integration','blender':bpy.app.version_string,'mcp_port':9881,'collections':groups,'hand_bounds':hand_bounds,'hands_below_counter':True,'sign_states':len(states),'sign_seconds':sum(t for f,t in clips),'dead_letters':['E','O'],'flicker_letters':['T','H'],'native_build':False,'game_launched':False}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
scene.camera=hero;scene.cycles.samples=24
scene.render.resolution_x=1440;scene.render.resolution_y=1200
scene.render.filepath=str(OUT/'hero.png')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.shading.type='RENDERED';s.overlay.show_overlays=False
            s.region_3d.view_rotation=hero.rotation_euler.to_quaternion();s.region_3d.view_location=(0,-2,61);s.region_3d.view_distance=305
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
print(json.dumps({'images':['hero.png','player_view.png','merchant.png','rear.png'],'sign_states':len(states),'pose_check':'hands below counter','master':str(OUT/'partner_shop.blend')}))
