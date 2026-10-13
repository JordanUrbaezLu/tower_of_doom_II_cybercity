"""Live MCP revision: common electrical faults, readable mechanics and a harsher mask."""
from pathlib import Path
import shutil
PRESERVE_SHOP_MATERIALS=True
exec(compile(Path(__file__).with_name('studio.py').read_text(),str(Path(__file__).with_name('studio.py')),'exec'))
if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
backup=OUT/'checkpoints/20260924_before_shared_fault.blend';backup.parent.mkdir(exist_ok=True)
if not backup.exists():shutil.copy2(OUT/'partner_shop.blend',backup)
scene['shop_powered']=1;scene.frame_set(1)

def curves(owner):
    a=owner.animation_data.action if owner.animation_data else None
    return [] if not a else [fc for layer in a.layers for strip in layer.strips for slot in a.slots if (bag:=strip.channelbag(slot)) for fc in bag.fcurves]
def interpolation(owner,mode):
    for fc in curves(owner):
        for k in fc.keyframe_points:k.interpolation=mode
def variable(driver,name,path):
    v=driver.variables.new();v.name=name;v.type='SINGLE_PROP';v.targets[0].id_type='SCENE';v.targets[0].id=scene;v.targets[0].data_path=path
def hide_off(ob):
    for prop in ('hide_render','hide_viewport'):
        d=ob.driver_add(prop).driver;d.expression='power < 0.5';variable(d,'power','["shop_powered"]')
def parent_original(ob):
    # Geometry is defined in the original, pre-shortening merchant coordinates.
    root=bpy.data.objects['MERCHANT_ROOT | active-only separate model']
    from mathutils import Matrix
    ob.parent=root;ob.matrix_parent_inverse=Matrix.Identity(4)
    ob.location.z-=11.9
    hide_off(ob)

# All failing loads lose and regain power on the same frame. Healthy letters stay lit.
bus=[(1,1),(31,0),(34,1),(36,0),(40,1),(91,0),(95,1),(98,0),(103,1),(151,0),(154,1),(157,0),(162,1),(181,1)]
scene['shop_fault_bus']=1.0
for f,v in bus:scene['shop_fault_bus']=v;scene.keyframe_insert('["shop_fault_bus"]',frame=f)
for fc in curves(scene):
    if fc.data_path=='["shop_fault_bus"]':
        for k in fc.keyframe_points:k.interpolation='CONSTANT'
scene.id_properties_ui('shop_fault_bus').update(min=0,max=1,description='Shared T/E/H and capacitor power fault; mask breathes independently.')
affected=['neon letter '+c for c in 'TEH']+['mask slow red breath','mask weak wire breath','left red energy core','counter canister red pulse','existing tall core red pulse','left energy scan rings']+['left core scan '+str(i) for i in range(4)]
for suffix in affected:
    m=bpy.data.materials['SHOP / '+suffix];nt=m.node_tree
    gate=nt.nodes.get('Shared electrical fault') or nt.nodes.new('ShaderNodeMath');gate.name='Shared electrical fault';gate.operation='MULTIPLY'
    nt.links.new(nt.nodes['Electrical timeline'].outputs[0],gate.inputs[0]);nt.links.new(gate.outputs[0],nt.nodes['Shop master power'].inputs[0])
    try:gate.inputs[1].driver_remove('default_value')
    except TypeError:pass
    d=gate.inputs[1].driver_add('default_value').driver;d.expression='bus';variable(d,'bus','["shop_fault_bus"]')
    # Exact analytic pulse in preview and game, avoiding approximated Bezier samples.
    nt.animation_data_clear();value=nt.nodes['Electrical timeline'].outputs[0]
    if suffix.startswith('neon letter'):value.default_value=5.5
    else:
        lo,hi,period,offset={
            'mask slow red breath':(.08,3.1,180,0),'mask weak wire breath':(.015,.5,180,0),
            'left red energy core':(1.05,3.3,90,0),'counter canister red pulse':(.45,2.5,90,0),
            'existing tall core red pulse':(1.15,3.1,90,0),'left energy scan rings':(.7,2.2,90,0),
        }.get(suffix,(.15,3,90,18*int(suffix[-1]) if suffix[-1].isdigit() else 0))
        d=value.driver_add('default_value').driver;d.expression=f'{lo}+{hi-lo}*(0.5+0.5*cos((frame-1+{offset})*2*pi/{period}))'
    # animation_data_clear above removes node drivers too; restore both power gates.
    for node,name,path in [('Shop master power','power','["shop_powered"]'),('Shared electrical fault','bus','["shop_fault_bus"]')]:
        d=nt.nodes[node].inputs[1].driver_add('default_value').driver
        d.expression='1' if name=='bus' and suffix.startswith('mask ') else name
        if d.expression!='1':variable(d,name,path)
for ob in scene.objects:
    if ob.type in ('MESH','CURVE') and any(m and m.name=='SHOP / left energy scan rings' for m in ob.data.materials):ob['shop_native_group']='core_left'

# A deliberate 100-degree travel with a unique rim stripe makes the turn readable.
wheel=bpy.data.objects['Pressure | wheel pivot'];gauge=bpy.data.objects['Pressure | gauge pivot']
wheel.animation_data.drivers[0].driver.expression='power * (50*pi/180*(1-cos((frame-1)*2*pi/90)))'
gauge.animation_data.drivers[0].driver.expression='power * (24*pi/180*sin((frame-1)*2*pi/90)+3.5*pi/180*sin((frame-1)*2*pi/9))'
for ob in list(scene.objects):
    if ob.get('shop_revision_2'):bpy.data.objects.remove(ob,do_unlink=True)
scene.frame_set(1);bpy.context.view_layer.update()
stripe=material('valve worn ivory index',(.38,.32,.19),.2,.65)
ob=tube('Pressure | moving rim index',[(88.9,-32.66,52.3),(90,-32.68,52.4),(91.1,-32.66,52.3)],.25,stripe,detail)
mw=ob.matrix_world.copy();ob.parent=wheel;ob.matrix_world=mw;ob['shop_native_group']='valve';ob['shop_native_pivot']=[90,-32,47];ob['shop_revision_2']=True
ob=mesh('Pressure | fixed travel pointer',[(89.1,-32.5,56),(90.9,-32.5,56),(90,-32.5,54.2)],[(0,1,2)],brass,detail)
sol=ob.modifiers.new('Pointer plate thickness','SOLIDIFY');sol.thickness=.35;ob['shop_native_group']='solid';ob['shop_revision_2']=True

# Keep the reference's X eyes, but compress and cant them inward under armored brows.
for ob in list(vendor.objects):
    if ob.name.startswith(('Merchant | cyan X eye','Merchant | cyan grin arc','Merchant | grin stitched crossbar','Merchant | cheek smile hook')):bpy.data.objects.remove(ob,do_unlink=True)
led=bpy.data.materials['SHOP / mask slow red breath'];weak=bpy.data.materials['SHOP / mask weak wire breath'];maskmat=bpy.data.materials['SHOP / black molded face mask']
def face_y(x,z):return -8.05-2.05*math.sqrt(max(.04,1-(x/6.0)**2-((z-71.1)/8.25)**2))
def wire(name,coords,r=.11,mat=led):
    depth=.60 if any(term in name for term in ('grin','tooth','corner')) else .28
    ob=tube('Merchant | menace '+name,[(x,face_y(x,z)-depth,z) for x,z in coords],r,mat,vendor)
    for sp in ob.data.splines:
        for p in sp.bezier_points:p.handle_left_type='VECTOR';p.handle_right_type='VECTOR'
    ob['shop_revision_2']=True;ob['shop_native_group']='mask';parent_original(ob);return ob
def plate(name,coords,depth=.35):
    verts=[(x,face_y(x,z)-depth,z) for x,z in coords]
    ob=mesh('Merchant | menace '+name,verts,[tuple(range(len(verts)))],maskmat,vendor,.06)
    sol=ob.modifiers.new('Forged shell plate','SOLIDIFY');sol.thickness=.18
    ob['shop_revision_2']=True;ob['shop_native_group']='vendor';parent_original(ob)
for s in (-1,1):
    # Outer corners higher than inner corners: a lowered, confrontational expression.
    wire('slanted X long',[(s*4.0,76.0),(s*2.65,74.75),(s*1.2,73.6)],.145)
    wire('slanted X cut',[(s*4.0,73.9),(s*2.65,74.75),(s*1.5,75.45)],.105,weak if s==1 else led)
    plate('overhanging brow',[(s*.85,75.8),(s*4.55,77.6),(s*4.35,76.5),(s*1.05,75.0)],.47)
    plate('hollow cheek',[(s*1.45,70.5),(s*4.5,72.8),(s*4.8,70.0),(s*3.3,67.5),(s*2.1,68.3)],.33)
plate('split nose bridge',[(-.65,75.5),(0,77.1),(.6,75.5),(.95,71.1),(0,70.1),(-.85,71.25)],.5)
# Broken angular seam and exposed uneven teeth replace the broad, friendly U smile.
wire('jagged grin seam',[(-4.55,69.8),(-3.8,68.7),(-2.6,68.3),(-1.3,67.35),(-.2,67.65),(1,67.2),(2.2,68.0),(3.6,68.35),(4.55,70.3)],.125)
for i,(x,z,h) in enumerate([(-3.8,68.7,1.4),(-2.95,68.5,2.1),(-2.05,67.95,1.55),(-1.2,67.35,2.15),(-.3,67.65,1.25),(.65,67.35,1.85),(1.55,67.6,1.4),(2.5,68.1,2.35),(3.4,68.3,1.45)]):
    wire('uneven tooth '+str(i),[(x-.17,z+.65),(x+.04,z-h),(x+.33,z+.32)],.075 if i%3 else .095)
wire('left scar',[(-4.35,72.6),(-4.0,71.7),(-4.3,71.15)],.052,weak)
wire('right torn corner',[(4.3,69.95),(4.7,71.0),(4.4,71.4)],.07)

# Larger bespoke arcs + ballistic flecks. Three fault clusters; right core sparks each time.
fx=bpy.data.collections['SHOP | 08 ELECTRICAL FX - preview only']
for ob in list(fx.objects):bpy.data.objects.remove(ob,do_unlink=True)
spark=bpy.data.materials['SHOP / hot amber-red spark'];arc=bpy.data.materials['SHOP / red electrical filament']
events=[('sign T',(-30.75,-62,110.5),31),('left core',(-89,-23,65),31),('right core',(79,-27,62),31),
        ('sign E',(-23,-62,105),91),('left core',(-89,-23,34),91),('right core',(81,-27,36),91),('counter left',(-41,-39,51.5),91),
        ('sign H',(20.25,-62,105),151),('left core',(-89,-23,65),151),('right core',(79,-27,62),151)]
random.seed(92427)
for ei,(name,org,start) in enumerate(events):
    origin=Vector(org);pts=[]
    for j in range(7):
        t=j/6;pts.append(tuple(Vector((t*7.0+random.uniform(-1.1,1.1),-1.2-abs(math.sin(t*math.pi))*1.3,-t*4.8+random.uniform(-1.2,1.2)))))
    ob=tube('FX | '+name+' large contact arc',pts,.15,arc,fx);ob.location=origin
    ob['fx_kind']='arc';ob['fx_event']=name;ob['fx_frame']=start
    for f,v in [(1,0),(start-1,0),(start,1),(start+2,0),(start+3,.8),(start+4,0),(181,0)]:ob.scale=(v,)*3;ob.keyframe_insert('scale',frame=f)
    interpolation(ob,'CONSTANT');hide_off(ob)
    for j in range(5):
        size=random.uniform(.26,.46)
        ob=mesh('FX | '+name+' large spark '+str(j),[(-size,0,0),(size,0,0),(0,0,size*4.5),(0,size,0)],[(0,1,2),(0,3,1),(1,3,2),(2,3,0)],spark,fx)
        ob['fx_kind']='spark';ob['fx_event']=name;ob['fx_frame']=start
        born=start;life=9;velocity=Vector((random.uniform(-24,24),random.uniform(-18,-6),random.uniform(2,16)))
        for f in (1,born-1):ob.location=origin;ob.scale=(0,)*3;ob.keyframe_insert('location',frame=f);ob.keyframe_insert('scale',frame=f)
        for age in range(life+1):
            t=age/30;ob.location=origin+velocity*t+Vector((0,0,-42*t*t));scale=(1-age/life)**.55 if age<life else 0
            ob.scale=(scale,)*3;ob.keyframe_insert('location',frame=born+age);ob.keyframe_insert('scale',frame=born+age)
        ob.scale=(0,)*3;ob.keyframe_insert('scale',frame=181);interpolation(ob,'LINEAR');hide_off(ob)

sign={c:[(f,v*5.5) for f,v in bus] for c in 'TEH'}
report={'revision':2,'fps':30,'frames':180,'seconds':6,'dead_letters':[],'blinking_letters':['T','E','H'],
        'steady_letters':['I','M','S','O','P'],'shared_fault_frames':[31,36,91,98,151,157],
        'mask_period_seconds':6,'mask_independent_of_faults':True,'canister_period_seconds':3,'canister_phase_offsets':[0,0,0],
        'spark_events':10,'simultaneous_events_max':4,'particles_per_event':6,'max_live_particles':24,
        'native_lifetime_ms_max':310,'new_flashing_dynamic_lights':0,'valve_travel_degrees':100,'gauge_swing_degrees':24,
        'fx_objects':len(fx.objects),'native_integrated':False,'native_playtested':False}
(OUT/'electrical_timing.json').write_text(json.dumps({'sign':sign,'power_bus':bus,'events':events,'report':report},indent=2))
(OUT/'neon_timing.json').write_text(json.dumps({'fps':30,'frames':180,'dead_letters':[],'animated_emission':sign,'shared_power_bus':True},indent=2))
(OUT/'electrical_validation.json').write_text(json.dumps(report,indent=2))
groups={}
for ob in scene.objects:
    if 'shop_native_group' in ob:groups.setdefault(ob['shop_native_group'],[]).append(ob.name)
(OUT/'native_groups.json').write_text(json.dumps(groups,indent=2))
scene['shop_electrical_revision']='2: synchronized T/E/H and capacitor faults; independent slow mask breath; large sparks both sides; 100-degree indexed valve'
scene['shop_pressure_animation']='100-degree valve travel every three seconds; indexed rim; gauge +/-24 degrees with 3.5-degree chatter; true OFF rests.'
scene['shop_mask_direction']='Slanted red X eyes under angular brows, armored hollow cheeks, jagged seam with uneven pointed teeth; unchanged hands-down pose'
scene.frame_set(1);scene.update_tag();bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
scene.render.engine='BLENDER_EEVEE'
if bpy.context.screen and not bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_play()
print('SHOP_REVISION_2',json.dumps(report))
