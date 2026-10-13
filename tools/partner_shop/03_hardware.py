"""Authored mechanical detail, inventory, service fittings and rear construction."""
from pathlib import Path
exec(compile((Path(__file__).with_name('studio.py')).read_text(),str(Path(__file__).with_name('studio.py')),'exec'))
random.seed(2341)
# Own only this pass's additions so iteration is safe.
for ob in list(scene.objects):
    if ob.get('shop_detail_pass')==3:bpy.data.objects.remove(ob,do_unlink=True)
before=set(scene.objects)

# Bring the sign in front of the roof edge; frame it with a fabricated case.
if not scene.get('shop_sign_reseated'):
    for ob in detail.objects:
        if ob.location.y < -53 and ob.location.z > 94: ob.location.y -= 4
    for ob in active.objects:
        if ob.name.startswith('Sign violet'):ob.location.y-=4
    scene['shop_sign_reseated']=True
for x in (-42,42):
    beam('Sign rear standoff',(x,-48,104),(x,-58,104),.7,brass)
for x in (-62,62):
    for z in (28,54,79):
        plate('Column bolted armored strap',x,-43,z,8,6,iron)
        box('Column recessed index', (x,-44, z), (3,.3,.45),brass,detail,.1)
for x in (-67,67):
    for y in (-28,9,38):
        box('Side panel frame',(x,y,49),(1.2,2,64),steel,detail,.2)
    for z in (23,78):box('Side panel horizontal frame',(x,5,z),(1.2,73,1.5),steel,detail,.2)
    for y in (-25,15,34):
        for z in (25,76):bolt((x*1.015,y,z),((1 if x>0 else -1),0,0),.58)
    # Triangular external gussets tie column into canopy.
    for y in (-32,36):
        verts=[(x,y-6,85),(x,y+6,85),(x,y+6,94),(x+(.9 if x>0 else -.9),y-6,85),(x+(.9 if x>0 else -.9),y+6,85),(x+(.9 if x>0 else -.9),y+6,94)]
        mesh('Canopy reinforcing gusset',verts,[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)],brass,detail,.15)

# Side discharge assembly: shielded purple core with offset copper return pipe.
box('Discharge assembly mounting rail',(75,-20,48),(7,12,57),iron,detail,.7)
cylinder('Violet core chamber',(79,-22,49),4.2,28,black)
cylinder('Violet chamber inner lens',(79,-22,49),3.65,23,violet,col=active)
for z in (32,35,63,66):
    cylinder('Chamber end bell',(79,-22,z),5.6,2.3,steel)
    cylinder('Chamber end copper collar',(79,-22,z+.8),5.7,.55,brass)
for a in (0,math.pi/2,math.pi,math.pi*1.5):
    x=79+4.5*math.sin(a);y=-22+4.5*math.cos(a)
    beam('Core protective tie rod',(x,y,36),(x,y,62),.48,black)
for z in (39,49,59):
    cylinder('Core containment band',(79,-22,z),4.6,.8,iron)
    for a in (-.55,.55):
        bolt((79+4.6*math.sin(a),-22-4.6*math.cos(a),z),r=.38)
tube('Copper pressure return',[(79,-22,67),(80,-22,76),(85,-17,80),(90,-10,75),(90,-10,26),(85,-14,22),(77,-15,22)],1.1,copper)
for z in (30,48,66):
    cylinder('Pressure line compression nut',(90,-10,z),1.6,2,brass,vertices=6)
    box('Pressure pipe saddle',(86,-10,z),(8,3,2.2),iron,detail,.3)
box('Pressure gauge mount',(73,-32,73),(13,5,13),black,detail,1)
cylinder('Pressure gauge bezel',(73,-35.2,74),5.1,1.3,brass,axis=(0,-1,0))
cylinder('Pressure gauge ivory dial',(73,-36,74),4.35,.3,ink,axis=(0,-1,0),bevel=.08)
for i in range(13):
    a=math.radians(-125+250*i/12)
    beam('Gauge scale tick',(73+3.3*math.sin(a),-36.3,74+3.3*math.cos(a)),(73+3.85*math.sin(a),-36.3,74+3.85*math.cos(a)),.09,black)
beam('Gauge needle',(73,-36.55,74),(75.4,-36.55,76),.12,black)
cylinder('Gauge pivot',(73,-36.7,74),.35,.3,black,axis=(0,-1,0))
text('kPa',(73,-36.5,72),.95,black)

# Counter terminal: shaped enclosure, recessed screen, mechanical keys and card reader.
term=box('Shop transaction terminal',(43,-36,51),(18,12,10),iron,detail,1.1)
box('Terminal screen seal',(43,-42.25,52.3),(15,.8,6.8),rubber,detail,.6)
box('Terminal screen glass',(43,-42.75,52.3),(13.6,.25,5.7),black,detail,.35)
text('PARTNER LINK',(43,-43,53.3),1.17,cyan)
text('UPGRADE  /  SYNC',(43,-43,51.6),.81,ink)
for x in (39.4,43,46.6):box('Terminal tactile key',(x,-43,49.1),(2.3,.7,1.05),steel,detail,.2)
box('Terminal reader chassis',(53,-36,48),(3.5,10,4),black,detail,.7)
box('Terminal card slot',(53,-41.15,48),(2.6,.3,.5),cyan,detail,.1)
tube('Terminal data umbilical',[(48,-30,48),(54,-24,45),(57,-14,44),(57,3,24),(58,21,21)],.6,rubber)
for z in (25,32,39):box('Cable saddle',(57,-14,z),(3,2,1),brass,detail,.15)

# Left workbench inventory: a serviceable armored forearm on a cradled mat.
box('Component inspection pad',(-40,-37,46),(28,20,.5),black,stock,.7)
cylinder('Forearm actuator body',(-40,-35,50),3.7,18,steel,stock,(1,0,0))
for x in (-49,-47,-35,-32):cylinder('Forearm machined ring',(x,-35,50),4.1,1.1,iron,stock,(1,0,0))
box('Forearm armored cover',(-40,-35,53),(12,6.5,2.6),paint,stock,.9)
box('Forearm status slot',(-40,-38.4,51.4),(7,.25,.55),cyan,stock,.12)
for x in (-45,-35):
    box('Forearm display cradle',(x,-35,47.2),(2,9,2),brass,stock,.3)
for y in (-38,-32):beam('Exposed actuator tie rail',(-47,y,50),(-33,y,50),.5,brass,stock)
for i in range(4):
    tube('Mechanical hand finger',[(-29,-38+i*2,50),(-25,-38+i*2,50),(-24,-38+i*2,48.2)],.65,iron,stock)
box('Mechanical hand palm',(-29,-35,50),(5,7,2.2),iron,stock,.6)

# Rear shelf kit: individual energy cells, storage boxes and visible armor plates.
def cell(x,y,z,idx):
    cylinder('Inventory cell body',(x,y,z+4),2.9,7.3,iron,stock)
    for zz in (z+.5,z+7.5):cylinder('Inventory cell end cap',(x,y,zz),3.2,1,brass,stock)
    box('Inventory cell indicator',(x,y-2.95,z+4),(1.1,.3,3.5),violet if idx%2 else cyan,stock,.15)
    for dz in (-1,1):bolt((x+1.65,y-2.75,z+4+dz),r=.21)
for idx,x in enumerate((-47,-38,-29,28,37,46)):
    cell(x,29,56.3,idx)
for x in (-40,39):
    box('Latched upgrade transport case',(x,31,38),(25,14,12),paint,stock,1)
    for dx in (-8,8):
        box('Case steel retaining strap',(x+dx,31,38),(1.8,14.4,12.4),steel,stock,.25)
        box('Case front brass latch',(x+dx,23.3,38),(3,1.1,3),brass,stock,.35)
    text('FIELD KIT',(x,22.7,37),2,ink,stock)
for idx,x in enumerate((-43,-23,23,43)):
    armor=box('Spare convex armor plate',(x,31,86),(13,6,13),iron,stock,2)
    armor.rotation_euler.y=(-.12 if idx%2 else .12)
    box('Armor front inset',(x,27.7,86),(9,.7,9),paint,stock,1.2)
    for dx in (-4.8,4.8):bolt((x+dx,26.9,88.5),r=.45)
    box('Armor small violet channel',(x,27.2,85),(5,.3,.6),violet,stock,.1)
# Open diagnostic module on the shelf, deliberately off the merchant's face axis.
box('Open electronics tray',(-19,31,38),(11,14,10),black,stock,.5)
for x in (-23,-20,-17):box('Plug-in circuit blade',(x,31,40),(1,10,9),paint,stock,.2)
for x in (-23,-20,-17):
    for z in (37,40,43):box('Circuit blade edge contact',(x,25.8,z),(1.2,.3,1),brass,stock,.1)

# Upper interior service wiring, separate power and data routes.
for dy in (0,1.8,3.6):
    tube('Interior cable loom',[(-55,37,74),(-47,39,85),(-27,39,89),(26,39,88),(51,35,81),(55,30,70)],.4,rubber)
for x in (-48,-32,32,48):
    box('Interior junction socket',(x,39,72),(7,3,9),iron,detail,.6)
    box('Junction amber pilot',(x,37.25,73),(1,.3,1.2),amber,detail,.1)
for x in (-54,54):tube('Shelf warm task light',[(x,26,82),(x-15 if x>0 else x+15,26,82)],.35,warm,active)

# Rear service door, hinge pins, utility vents and external wiring.
box('Rear door outer frame',(0,47.1,50),(48,2,71),black,detail,1.3)
box('Rear inset access door',(0,48.5,50),(43,1.3,66),paint,detail,1)
for x in (-18,18):
    for z in (20,79):bolt((x,49.5,z),(0,1,0),.7)
for z in (29,69):
    box('Rear door hinge leaf',(-22,49.5,z),(7,1.2,6),steel,detail,.4)
    cylinder('Rear door hinge pin',(-22,50.7,z),.9,7,brass)
tube('Rear door pull handle',[(15,50,48),(15,53,48),(15,53,57),(15,50,57)],.7,steel)
text('SERVICE',(0,49.35,70),3.5,ink,rot=(math.pi/2,0,math.pi))
for z in range(24,44,3):box('Door low ventilation grille',(0,49.3,z),(24,1,.85),black,detail,.2)
for x in (-45,45):
    box('Rear cooling duct',(x,49.4,63),(23,6,28),iron,detail,1.2)
    for z in range(53,75,3):box('Rear duct louver',(x,53,z),(19,2,1.1),black,detail,.2)
    box('Rear junction enclosure',(x,49.5,29),(18,6,15),black,detail,1)
    for dx in (-6,6):bolt((x+dx,53,29),(0,1,0),r=.6)
tube('Rear armored power conduit',[(-47,53,21),(-53,56,14),(45,56,14),(48,53,22)],1.1,rubber)
tube('Rear copper high line',[(-46,53,43),(-55,53,81),(-40,53,86),(42,53,86),(52,50,70)],.8,copper)

# Roof beacon receiver: honest mechanical socket for the native sky marker.
cylinder('Beacon roof pedestal',(22,18,109),8,4,iron)
cylinder('Beacon socket brass rim',(22,18,111.5),6.6,1.4,brass)
for z in (114,117,120,123):cylinder('Beacon ceramic insulator',(22,18,z),4.7,1.9,black)
cylinder('Beacon central conductor',(22,18,120),1.6,20,brass)
for a in (0,math.tau/3,2*math.tau/3):
    tube('Beacon conductor prong',[(22+6*math.sin(a),18+6*math.cos(a),112),(22+7*math.sin(a),18+7*math.cos(a),123),(22+5*math.sin(a),18+5*math.cos(a),130)],.6,steel)
bpy.data.objects['tag_shop_beacon'].location=(22,18,131)
for i in range(5):
    pts=[]
    for j in range(33):
        a=j*math.tau/32;pts.append((22+2.7*math.sin(a),18+2.7*math.cos(a),113+i*2+j/32*1.2))
    tube('Beacon wound copper coil',pts,.28,copper)
box('Roof low air intake',(-34,24,105),(31,24,8),iron,detail,1.3)
for y in range(15,35,3):box('Roof intake slat',(-34,y,109.6),(26,1.2,.8),black,detail,.15)

# Hand-built repairs and sparse edge scratches give scale without covering every face.
plate('Riveted front repair patch',-41,-41.7,25,16,11,brass)
text('07',(-41,-42.55,23),5.5,black)
text('NO REFUNDS',(39,-41.5,31),1.65,ink)
text('AUTHORIZED REPAIR',(39,-41.5,16),1.45,ink)
text('EQUIP  /  REPAIR  /  ENHANCE',(0,-56,42.8),1.55,black)
for i in range(44):
    x=random.uniform(-60,60);y=random.uniform(-53,-27);length=random.uniform(.8,5)
    tube('Counter worn scratch',[(x,y,45.56),(x+length,y+random.uniform(-.6,.6),45.56)],random.uniform(.012,.035),black)
for i in range(24):
    x=random.uniform(-55,55);z=random.choice([14.2,37.5])+random.uniform(-.6,.6)
    beam('Chipped metal edge',(x,-40.91,z),(x+random.uniform(.3,1.8),-40.91,z+.1),.06,steel)
for ob in set(scene.objects)-before:ob['shop_detail_pass']=3
scene.render.engine='CYCLES';scene.cycles.samples=32
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
print(json.dumps({'stage':'detailed_hardware','objects':len(scene.objects),'added':len(set(scene.objects)-before)}))
