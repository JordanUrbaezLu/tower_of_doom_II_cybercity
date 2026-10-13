"""Left-side service bay, three blinking letters, localized sparks and mask breath.

Apply after 07_dark_direction.py. Mutations run in the live Blender MCP studio.
"""
from pathlib import Path
PRESERVE_SHOP_MATERIALS=True
exec(compile(Path(__file__).with_name('studio.py').read_text(),str(Path(__file__).with_name('studio.py')),'exec'))
if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
scene.frame_set(1)
for name in ('SHOP | 07 LEFT SERVICE BAY','SHOP | 08 ELECTRICAL FX - preview only'):
    old=bpy.data.collections.get(name)
    if old:
        for ob in list(old.objects):bpy.data.objects.remove(ob,do_unlink=True)
        bpy.data.collections.remove(old)
left=bpy.data.collections.new('SHOP | 07 LEFT SERVICE BAY');scene.collection.children.link(left)
fx=bpy.data.collections.new('SHOP | 08 ELECTRICAL FX - preview only');scene.collection.children.link(fx)
random.seed(92426)

def curves(owner):
    anim=owner.animation_data
    if not anim or not anim.action:return []
    result=[]
    for layer in anim.action.layers:
        for strip in layer.strips:
            for slot in anim.action.slots:
                bag=strip.channelbag(slot)
                if bag:result.extend(bag.fcurves)
    return result
def interpolation(owner,kind):
    for fc in curves(owner):
        for k in fc.keyframe_points:
            k.interpolation=kind
            if kind=='BEZIER':k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'
def principled(m):return next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
def emission_keys(m,keys,mode='CONSTANT'):
    m.node_tree.animation_data_clear()
    p=principled(m)
    for f,v in keys:
        p.inputs['Emission Strength'].default_value=v;p.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
    interpolation(m.node_tree,mode)
def pulse(m,lo,hi,period=180,phase=0):
    keys=[(f,lo+(hi-lo)*(.5+.5*math.cos(math.tau*(f-1+phase)/period))) for f in range(1,182,15)]
    emission_keys(m,keys,'BEZIER');return keys

# All letters light up. Preserve the approved rhythm and add only E as letter three.
old=json.loads((OUT/'neon_timing.json').read_text())
keys={k:old['animated_emission'][k] for k in ('T','H')}
keys['E']=[(1,5.5),(53,5.5),(54,0),(56,0),(57,5.5),(59,.5),(61,5.5),(112,5.5),(113,0),(116,0),(117,5.5),(119,.5),(121,5.5),(181,5.5)]
for letter in 'ITEMSHOP':
    m=bpy.data.materials['SHOP / neon letter '+letter]
    color=(.48,.008,.012) if letter in 'ITEM' else (.60,.012,.006)
    p=principled(m);m.diffuse_color=(*color,1)
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Emission Color'].default_value=(*color,1)
    m.node_tree.animation_data_clear();p.inputs['Emission Strength'].default_value=5.5
    if letter in keys:
        if keys[letter][-1][0]!=181:keys[letter].append([181,5.5])
        emission_keys(m,keys[letter])
for ob in bpy.data.collections['SHOP | 06 NEON SIGN - individual letters'].objects:
    if 'neon_letter' in ob:ob['neon_dead']=False;ob['neon_flickers']=ob['neon_letter'] in keys
scene['shop_sign_dead_letters']='';scene['shop_sign_flicker']='T,E,H; all letters functional'
(OUT/'neon_timing.json').write_text(json.dumps({'fps':30,'frames':180,'dead_letters':[],'animated_emission':keys,'native_integrated':False},indent=2))

# Actual left wall is -X, seen by a player approaching the counter from -Y.
before=set(scene.objects)
box('Left | recessed service-bay housing',(-72,3,48),(10,69,64),black,left,1.4)
box('Left | oxblood panel backing',(-77.5,4,49),(1.2,63,57),paint,left,1)
for y in (-26,32):
    box('Left | flanged mounting rail',(-79,y,49),(3,3,62),steel,left,.4)
    for z in (22,47,77):cylinder('Left | rail captive bolt',(-81,y,z),.65,.5,brass,left,(-1,0,0),vertices=6,bevel=.08)
for z in (20,79):box('Left | edge carrier',(-78,3,z),(3,62,3),iron,left,.5)
# Layered regulator on the rear half, separated from the canister silhouette.
box('Left | regulator plinth',(-81,17,44),(8,27,34),iron,left,1)
box('Left | regulator face gasket',(-85.2,17,44),(1,24,31),rubber,left,.8)
box('Left | regulator armored cover',(-86.2,17,44),(1.6,22,28),paint,left,.8)
for z in range(35,55,3):box('Left | heat exchanger fin',(-89,17,z),(5,19,1.15),steel,left,.18)
for y in (9,25):
    for z in (33,55):cylinder('Left | regulator cover screw',(-87.4,y,z),.52,.5,brass,left,(-1,0,0),vertices=6,bevel=.06)
box('Left | junction box',(-81,19,69),(8,23,13),black,left,.9)
for y in (11,19,27):
    cylinder('Left | cable socket',(-86,y,69),1.5,1.2,brass,left,(-1,0,0),vertices=20)
    tube('Left | armored power feed',[(-87,y,69),(-93,y,65),(-94,y,58),(-89,y,54)],.55,rubber,left)
# Small labels follow the side face; their orientation is readable from -X.
text('CAPACITOR / 07',(-88,17,58),1.6,ink,left,rot=(math.pi/2,0,-math.pi/2))
text('HIGH VOLTAGE',(-78.4,-2,81.3),1.9,ink,left,rot=(math.pi/2,0,-math.pi/2))

# New left energy canister: red core, perforated cage, ceramic ends, copper feed.
coremat=material('left red energy core',(.43,.002,.006),.08,.3,2.8,False)
ringmat=material('left energy scan rings',(.6,.01,.003),.1,.3,2.2,False)
for z in (30,68):
    box('Left | canister mounting saddle',(-80,-17,z),(13,16,5),iron,left,.8)
    cylinder('Left | canister end casting',(-84,-18,z),6.1,4.5,steel,left)
    cylinder('Left | end brass locking ring',(-84,-18,z+.9),6.35,.8,brass,left)
    cylinder('Left | ceramic end insulator',(-84,-18,z-1),4.9,3,black,left)
cylinder('Left | luminous canister core',(-84,-18,49),4.35,33,coremat,left)
for a in (0,math.pi/2,math.pi,math.pi*1.5):
    x=-84+5.2*math.sin(a);y=-18+5.2*math.cos(a)
    beam('Left | protective cage rail',(x,y,32),(x,y,66),.48,iron,left)
for z in (37,49,61):cylinder('Left | split retention band',(-84,-18,z),5.6,1.0,black,left)
scanmats=[]
for idx,z in enumerate((36,44,52,60)):
    m=material('left core scan '+str(idx),(.65,.012,.003),.08,.35,2,False);scanmats.append(m)
    cylinder('Left | red scan band '+str(idx),(-84,-18,z),4.43,.8,m,left)
    pulse(m,.15,3.0,90,idx*18)
pulse(coremat,1.05,3.3,90,15)
tube('Left | copper high-pressure return',[(-84,-18,71),(-84,-18,77),(-93,-13,82),(-97,-6,75),(-97,-6,26),(-90,-11,22),(-81,-16,26)],.95,copper,left)
for z in (31,50,70):
    cylinder('Left | pressure compression coupling',(-97,-6,z),1.45,2.5,brass,left,vertices=6)
    box('Left | pressure tube wall saddle',(-91,-6,z),(12,3,2),iron,left,.25)
tube('Left | sign power conduit',[(-83,23,77),(-80,27,89),(-69,15,96),(-62,-26,98),(-46,-51,101)],.65,rubber,left)
for y in (-2,22):
    box('Left | ceramic fuse pedestal',(-84,y,25),(10,7,8),black,left,.7)
    cylinder('Left | exposed fuse cap',(-90,y,25),2.4,2,steel,left,(-1,0,0))
    cylinder('Left | fuse indicator',(-91.2,y,25),1.4,.4,ringmat,left,(-1,0,0),bevel=.1)
for ob in set(scene.objects)-before:
    for c in list(ob.users_collection):c.objects.unlink(ob)
    left.objects.link(ob)

# The existing small left-counter canister and tall right-side core also breathe.
counterpulse=material('counter canister red pulse',(.49,.003,.006),.1,.32,2,False)
pulse(counterpulse,.45,2.5,90,30)
for ob in stock.objects:
    if ob.name.startswith('Forearm status slot'):ob.data.materials.clear();ob.data.materials.append(counterpulse)
rightpulse=material('existing tall core red pulse',(.46,.004,.009),.1,.28,2.5,False)
pulse(rightpulse,1.15,3.1,90,0)
for ob in active.objects:
    if ob.name.startswith('Violet chamber inner lens'):ob.data.materials.clear();ob.data.materials.append(rightpulse)

# Eyes and mouth pulse together over six seconds; deliberately damaged wires stay weaker.
maskpulse=material('mask slow red breath',(.56,.0015,.005),.05,.35,2.8,False)
weakmask=material('mask weak wire breath',(.19,.0007,.002),.03,.4,.45,False)
maskkeys=pulse(maskpulse,.08,3.1,180);pulse(weakmask,.015,.5,180)
for ob in vendor.objects:
    if ob.type not in ('MESH','CURVE'):continue
    mats=ob.data.materials
    for idx,m in enumerate(mats):
        if m and m.name in ('SHOP / mask cyan electroluminescent wire','SHOP / mask slow red breath'):mats[idx]=maskpulse
        elif m and m.name in ('SHOP / mask failing red eye','SHOP / mask weak wire breath'):mats[idx]=weakmask

# Sparse electrical arcs and flying flecks, separate preview collection.
spark=material('hot amber-red spark',(.85,.19,.025),0,.3,7,False)
arc=material('red electrical filament',(.8,.025,.005),0,.25,6,False)
events=[('sign T',(-30.75,-62,110.5),20),('sign H',(20.25,-62,105),40),('sign E',(-23,-62,105),54),
        ('sign T',(-30.75,-62,110.5),79),('sign E',(-23,-62,105),113),('sign H',(20.25,-62,105),157),
        ('left core',(-87,-22,65),30),('left core',(-88,-21,33),120),
        ('counter left',(-41,-39,51.5),92),('right core',(79,-27,62),145)]
def keyscale(ob,keys):
    for f,v in keys:ob.scale=(v,v,v);ob.keyframe_insert('scale',frame=f)
    interpolation(ob,'CONSTANT')
for ei,(name,origin,start) in enumerate(events):
    origin=Vector(origin)
    # Each arc flickers two or three frames, bridging a contact rather than the whole prop.
    pts=[]
    for j in range(7):
        t=j/6;pts.append(tuple(origin+Vector((t*3.2+random.uniform(-.55,.55),-.6-abs(math.sin(t*math.pi))*.65,-t*2.2+random.uniform(-.6,.6)))))
    ob=tube('FX | '+name+' short contact arc',pts,.08,arc,fx)
    # Move curve coordinates into a contact-local frame so zero scale hides them at the source.
    for sp in ob.data.splines:
        for p in sp.bezier_points:
            p.co-=origin;p.handle_left-=origin;p.handle_right-=origin
    ob.location=origin;ob['fx_kind']='arc';ob['fx_event']=name
    keyscale(ob,[(1,0),(start-1,0),(start,1),(start+2,0),(start+3,.7),(start+4,0),(181,0)])
    for j in range(5 if name.startswith('sign') else 4):
        # A small tapered hot metal streak travels a short ballistic path and extinguishes.
        size=random.uniform(.12,.24)
        verts=[(-size,0,0),(size,0,0),(0,0,size*4),(0,size,0)]
        ob=mesh('FX | '+name+' spark '+str(j),verts,[(0,1,2),(0,3,1),(1,3,2),(2,3,0)],spark,fx)
        born=start+j%2;life=random.randint(6,11)
        velocity=Vector((random.uniform(-12,12),random.uniform(-9,-3),random.uniform(1,8)))
        for f in (1,born-1):
            ob.location=origin;ob.scale=(0,)*3;ob.keyframe_insert('location',frame=f);ob.keyframe_insert('scale',frame=f)
        for age in range(life+1):
            t=age/30;ob.location=origin+velocity*t+Vector((0,0,-42*t*t))
            scale=(1-age/life)**.55 if age<life else 0
            ob.scale=(scale,)*3;ob.keyframe_insert('location',frame=born+age);ob.keyframe_insert('scale',frame=born+age)
        ob.scale=(0,)*3;ob.keyframe_insert('scale',frame=181);interpolation(ob,'LINEAR')
        ob['fx_kind']='spark';ob['fx_event']=name

# Preview camera favors the newly detailed left wall while preserving sign/face visibility.
hero=bpy.data.objects['01 HERO - three-quarter']
hero.location=(-225,-340,128);hero.rotation_euler=(Vector((-3,-2,61))-hero.location).to_track_quat('-Z','Y').to_euler();hero.data.lens=48
scene.camera=hero;scene.frame_start=1;scene.frame_end=180;scene.render.fps=30
scene['shop_electrical_revision']='all letters work; T/E/H blink; left bay; local sparks; mask slow pulse'
scene['shop_fx_native_status']='Blender-authored preview curves/meshes only, native BO3 FX integration pending'
scene.frame_set(1);bpy.context.view_layer.update()

# Sweep the actual animated data rather than inferring behavior from authored key lists.
letters={c:[] for c in 'ITEMSHOP'};maskvalues=[];counts=[]
for f in range(1,182):
    scene.frame_set(f)
    for c in letters:letters[c].append(round(principled(bpy.data.materials['SHOP / neon letter '+c]).inputs['Emission Strength'].default_value,5))
    maskvalues.append(round(principled(maskpulse).inputs['Emission Strength'].default_value,5))
    counts.append(sum(max(o.scale)>.001 for o in fx.objects))
blinking=sorted(c for c,values in letters.items() if len(set(values))>1)
assert blinking==['E','H','T'],blinking
assert all(max(values)>5 for values in letters.values())
assert all(min(values)>5 for c,values in letters.items() if c not in blinking)
assert all(values[0]==values[-1] for values in letters.values())
assert maskvalues[0]==maskvalues[-1] and min(maskvalues)<.1 and max(maskvalues)>3
assert counts[0]==counts[-1]==0
report={'fps':30,'frames':180,'seconds':6,'dead_letters':[],'blinking_letters':blinking,'steady_letters':sorted(set(letters)-set(blinking)),
        'mask_emission_range':[min(maskvalues),max(maskvalues)],'mask_period_seconds':6,'canister_period_seconds':3,
        'spark_events':len(events),'fx_objects':len(fx.objects),'max_simultaneously_visible_fx_objects':max(counts),
        'new_flashing_dynamic_lights':0,'left_detail_objects':len(left.objects),'native_integrated':False,'loop_seam_checked':True}
(OUT/'electrical_validation.json').write_text(json.dumps(report,indent=2))
(OUT/'electrical_timing.json').write_text(json.dumps({'sign':keys,'mask':maskkeys,'events':events,'report':report},indent=2))
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
print(json.dumps(report))
