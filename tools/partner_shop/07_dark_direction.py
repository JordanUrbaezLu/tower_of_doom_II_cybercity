"""User correction: evil black/oxblood/red shop and shorter, scarier red-mask vendor."""
from pathlib import Path
exec(compile((Path(__file__).with_name('studio.py')).read_text(),str(Path(__file__).with_name('studio.py')),'exec'))
def recolor(name,color,metal=None,rough=None,emit=None):
    m=bpy.data.materials[name];m.diffuse_color=(*color,1)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Emission Color'].default_value=(*color,1)
    if metal is not None:p.inputs['Metallic'].default_value=metal
    if rough is not None:p.inputs['Roughness'].default_value=rough
    if emit is not None:p.inputs['Emission Strength'].default_value=emit
    for n in m.node_tree.nodes:
        if n.type=='VALTORGB':
            n.color_ramp.elements[0].color=(*(v*.72 for v in color),1)
            n.color_ramp.elements[1].color=(*(v*1.2 for v in color),1)
recolor('SHOP / weathered charcoal enamel',(.023,.025,.027),.56,.55)
recolor('SHOP / desaturated plum enamel',(.058,.011,.016),.48,.52)
recolor('SHOP / edge-worn machined steel',(.115,.12,.122),.8,.49)
recolor('SHOP / aged warm brass',(.105,.059,.021),.65,.5)
recolor('SHOP / oxidized copper fittings',(.125,.038,.018),.63,.52)
recolor('SHOP / ivory stencilled markings',(.3,.285,.25),.1,.7)
recolor('SHOP / violet discharge glass',(.46,.004,.009),emit=2.5)
recolor('SHOP / muted cyan phosphor',(.5,.009,.005),emit=1.65)
recolor('SHOP / warm service window tube',(.35,.05,.012),emit=2)
recolor('SHOP / amber instrument lamps',(.3,.095,.012),emit=1.3)
recolor('SHOP / mask cyan electroluminescent wire',(.56,.0015,.005),emit=2.8)
recolor('SHOP / black heavy woven coat',(.008,.008,.009),0,.94)
recolor('SHOP / worn black cloth bindings',(.018,.017,.017),0,.88)
recolor('SHOP / studio ground',(.022,.023,.025),.1,.66)

# Merchant head and shoulders fit deeper below the canopy; arms remain at his sides.
root=bpy.data.objects['MERCHANT_ROOT | active-only separate model']
root.scale=(.91,.91,.88)
root['direction']='Black hood and red LED mask; 12% shorter from floor origin; arms down'
# Replace the tidy second smile arc / extra eye flourishes with damaged uneven wiring.
for ob in list(vendor.objects):
    if ob.name.startswith('Merchant | cyan eye lower echo'):
        bpy.data.objects.remove(ob,do_unlink=True)
grins=sorted([o for o in vendor.objects if o.name.startswith('Merchant | cyan grin arc')],key=lambda o:o.name)
if len(grins)>1:
    ob=grins[1]
    # Same small mesh separation, physically dead rather than a full broad glowing smile.
    ob.data.materials.clear();ob.data.materials.append(maskmat if 'maskmat' in globals() else bpy.data.materials['SHOP / black molded face mask'])
crossbars=sorted([o for o in vendor.objects if o.name.startswith('Merchant | grin stitched crossbar')],key=lambda o:o.name)
for i,ob in enumerate(crossbars):
    if i in (2,7):
        ob.data.materials.clear();ob.data.materials.append(bpy.data.materials['SHOP / black molded face mask'])
    # Make the wire lengths irregular, avoiding the perfect toy grin.
    if not ob.get('dark_wire_adjusted'):
        for sp in ob.data.splines:
            if sp.type=='BEZIER':
                for j,p in enumerate(sp.bezier_points):
                    if j in (0,len(sp.bezier_points)-1):p.co.z += [.22,-.25,.38,-.12][i%4]
        ob['dark_wire_adjusted']=True
eyes=sorted([o for o in vendor.objects if o.name.startswith('Merchant | cyan X eye')],key=lambda o:o.name)
if eyes:
    failed=material('mask failing red eye',(.19,.0007,.002),.03,.4,.45,False)
    eyes[-1].data.materials.clear();eyes[-1].data.materials.append(failed)

# Remove the opaque shell that previously obscured the core; tie bars and bands cage it.
for ob in list(detail.objects):
    if ob.name=='Violet core chamber':bpy.data.objects.remove(ob,do_unlink=True)
for ob in list(scene.objects):
    if ob.get('shop_dark_pass'):bpy.data.objects.remove(ob,do_unlink=True)
before=set(scene.objects)
# Fill the rear roof gable so the merchant's backdrop is solid dark construction.
profile=[(-64,89),(-64,100.5),(0,111),(64,100.5),(64,89)]
verts=[(x,y,z) for y in (42.5,45.5) for x,z in profile]
mesh('Dark | sealed rear roof gable',verts,[(4,3,2,1,0),(5,6,7,8,9)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)],iron,shell,.3)
# Angular framing makes the service opening and silhouette harsher without hiding the face.
for s in (-1,1):
    verts=[(s*59,-45.5,87),(s*50,-45.5,87),(s*56,-45.5,78),(s*59,-45.5,75),
           (s*59,-44,87),(s*50,-44,87),(s*56,-44,78),(s*59,-44,75)]
    mesh('Dark | angled window corner casting',verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],iron,detail,.35)
    tube('Dark | red corner recess',[(s*57.5,-46,85.5),(s*54,-46,85.5),(s*57.7,-46,79.7)],.15,violet,active)
    # Rugged roof corner brackets read as workshop hardware, not an ornamental crown.
    verts=[(s*72,-44,94),(s*82,-44,96),(s*84,-44,108),(s*77,-44,101),
           (s*72,-40,94),(s*82,-40,96),(s*84,-40,108),(s*77,-40,101)]
    mesh('Dark | swept canopy end bracket',verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],iron,detail,.4)
# Panel repairs, welded patches and hanging wire runs with strain-relief collars.
for s in (-1,1):
    for i in range(3):
        x=s*(48+i*2)
        tube('Dark | hanging loom',[(x,2,87),(x-s*2,-1,79-i*2),(x-s*4,3,64-i*3),(x,12,60-i*3)],.35+.1*i,rubber)
        cylinder('Dark | loom gland',(x,2,86),.8,2.1,brass,vertices=12)
for x in (-27,-14,4,19):
    for z in (17,36):
        tube('Dark | front welded repair bead',[(x,-40.95,z),(x+2,-41,z+.1),(x+4,-40.96,z),(x+6,-41,z+.1)],.10,steel)
for ob in detail.objects:
    if ob.type=='FONT' and ob.data.body=='AUTHORIZED REPAIR':ob.data.body='UNREGISTERED HARDWARE'
# Backlight the recess subtly; neutral front light still exposes the modeled surfaces.
for name,color,power in [
 ('Studio cool broad key',(.78,.77,.75),350000),
 ('Studio left soft fill',(.72,.67,.65),135000),
 ('Studio rear violet rim',(1,.025,.015),310000),
 ('Window practical',(1,.11,.028),5500)]:
    l=bpy.data.objects[name].data;l.color=color;l.energy=power
light('Dark | red shelf backlight',(0,33,71),(1,.005,.009),5500,45,(0,0,57))
light('Dark | subtle front cloth fill',(-8,-70,76),(.57,.52,.49),6000,36,(0,0,60))
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.13,.13,.14,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.22
hero=bpy.data.objects['01 HERO - three-quarter']
hero.location=(212,-346,130);hero.rotation_euler=(Vector((0,-2,61))-hero.location).to_track_quat('-Z','Y').to_euler();hero.data.lens=48
scene.camera=hero
for ob in set(scene.objects)-before:ob['shop_dark_pass']=True
scene['shop_art_direction']='Evil black/oxblood/red, lower red-mask merchant; subdued amber details'
scene.frame_set(1)
bpy.context.view_layer.update()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.shading.type='RENDERED';s.overlay.show_overlays=False
            s.region_3d.view_rotation=hero.rotation_euler.to_quaternion();s.region_3d.view_location=(0,-2,61);s.region_3d.view_distance=305
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
print(json.dumps({'direction':scene['shop_art_direction'],'vendor_scale':list(root.scale),'objects':len(scene.objects)}))
