"""Bent-tube ITEM SHOP sign with failed E/O and keyframed T/H flicker.

This is an authored Blender animation. Native BO3 switching is a later integration
step; material keyframes do not automatically export into an xmodel.
"""
from pathlib import Path
exec(compile((Path(__file__).with_name('studio.py')).read_text(),str(Path(__file__).with_name('studio.py')),'exec'))
for col in list(bpy.data.collections):
    if col.name=='SHOP | 06 NEON SIGN - individual letters':
        for ob in list(col.objects):bpy.data.objects.remove(ob,do_unlink=True)
        bpy.data.collections.remove(col)
for ob in list(scene.objects):
    if ob.name.startswith(('Main sign carrier','Sign inset face','Sign violet pilot','Sign rear standoff','Marking | THE BROKER')):
        bpy.data.objects.remove(ob,do_unlink=True)
    elif ob.name.startswith('Captive hex head') and ob.location.y<-58 and ob.location.z>94:
        bpy.data.objects.remove(ob,do_unlink=True)
sign=bpy.data.collections.new('SHOP | 06 NEON SIGN - individual letters');scene.collection.children.link(sign)
before=set(scene.objects)
box('Neon | boxed weatherproof carrier',(0,-57,105),(108,4,26),black,sign,2)
box('Neon | aged plum backplate',(0,-59.3,105),(104,.7,22),paint,sign,1.7)
box('Neon | top folded drip hood',(0,-60,118.3),(110,7,1.3),iron,sign,.5)
for x in (-52,52):
    for z in (95,115):cylinder('Neon | captive face screw',(x,-60,z),.6,.4,steel,sign,(0,-1,0),vertices=6,bevel=.06)
for x in (-45,45):
    beam('Neon | sign mounting stand',(x,-42,98),(x,-55,104),1.1,brass,sign)
    box('Neon | bracket foot',(x,-42,98),(8,7,2),steel,sign,.3)
box('Neon | transformer housing',(-31,-53.6,104),(23,4,13),iron,sign,.8)
for x in range(-40,-20,3):box('Neon | transformer vent',(x,-51.4,104),(1,.5,8),black,sign,.1)
text('HV  /  6kV',(-31,-51.05,99.4),1.3,ink,sign,rot=(math.pi/2,0,math.pi))

def poly_tube(name,points,r,mat,cyclic=False):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=4
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    sp.use_cyclic_u=cyclic
    ob=bpy.data.objects.new(name,cu);sign.objects.link(ob);cu.materials.append(mat);return ob
def rounded(points,r=.65):
    if len(points)<3:return points
    result=[points[0]]
    for i in range(1,len(points)-1):
        a,b,c=Vector(points[i-1]),Vector(points[i]),Vector(points[i+1])
        dist=min(r,(a-b).length*.33,(c-b).length*.33)
        p=b+(a-b).normalized()*dist;q=b+(c-b).normalized()*dist
        for j in range(9):
            t=j/8;result.append(tuple((1-t)**2*p+2*(1-t)*t*b+t*t*q))
    result.append(points[-1]);return result

# Each stroke is an actual raised neon tube, with mechanical sockets at its ends.
glyphs={
 'I':[[(0,11),(6.5,11)],[(3.25,11),(3.25,0)],[(0,0),(6.5,0)]],
 'T':[[(0,11),(6.5,11)],[(3.25,11),(3.25,0)]],
 'E':[[(6.5,11),(0,11),(0,0),(6.5,0)],[(0,5.6),(5.4,5.6)]],
 'M':[[(0,0),(0,11),(3.25,5.5),(6.5,11),(6.5,0)]],
 'S':[[(6.4,9.7),(5.2,11),(1.4,11),(0,9.5),(0,7.6),(1.2,6.3),(5.2,4.9),(6.5,3.5),(6.5,1.5),(5.1,0),(1.3,0),(0,1.3)]],
 'H':[[(0,11),(0,0)],[(6.5,11),(6.5,0)],[(0,5.5),(6.5,5.5)]],
 'O':[[(3.25+3.25*math.sin(i*math.tau/64),5.5+5.5*math.cos(i*math.tau/64)) for i in range(65)]],
 'P':[[(0,0),(0,11),(4.9,11),(6.5,9.5),(6.5,7),(4.9,5.5),(0,5.5)]]}
keys={
 'T':[(1,5.5),(19,5.5),(20,0),(22,0),(23,5.5),(24,.35),(26,5.5),(70,5.5),(71,0),(76,0),(77,4),(79,0),(81,5.5),(131,5.5),(132,.4),(134,5.5),(180,5.5)],
 'H':[(1,5.5),(39,5.5),(40,0),(43,0),(44,5.5),(45,0),(47,5.5),(101,5.5),(102,.3),(105,.3),(106,5.5),(156,5.5),(157,0),(164,0),(165,5.5),(180,5.5)]}
for idx,(letter,x0) in enumerate(zip('ITEMSHOP',[-45,-34,-23,-12,6,17,28,39])):
    dead=letter in ('E','O')
    color=(.48,.008,.012) if idx<4 else (.60,.012,.006)
    m=material('neon letter '+letter,tuple(v*.16 for v in color) if dead else color,.12,.29,0 if dead else 5.5,False)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    if letter in keys:
        for frame,value in keys[letter]:
            p.inputs['Emission Strength'].default_value=value
            p.inputs['Emission Strength'].keyframe_insert('default_value',frame=frame)
        action=m.node_tree.animation_data.action
        # Blender 5 layered actions: constant keys give electrical stutters, not fades.
        for layer in action.layers:
            for strip in layer.strips:
                for slot in action.slots:
                    bag=strip.channelbag(slot)
                    if bag:
                        for fc in bag.fcurves:
                            for k in fc.keyframe_points:k.interpolation='CONSTANT'
    glass=material('neon glass jacket '+letter,tuple(v*.045 for v in color),.15,.32,0,False)
    for si,path in enumerate(glyphs[letter]):
        coords=rounded([(x0+x,-61.45,99.5+z) for x,z in path]) if letter!='O' else [(x0+x,-61.45,99.5+z) for x,z in path]
        # Raised charcoal backing makes the failed letters still legible.
        poly_tube('Neon | '+letter+' tube bedding '+str(si),[(x,y+.22,z) for x,y,z in coords],.32,glass)
        ob=poly_tube('Neon | '+letter+' luminous tube '+str(si),coords,.245,m)
        ob['neon_letter']=letter;ob['neon_dead']=dead;ob['neon_flickers']=letter in keys
        for loc in (coords[0],coords[-1]):
            x,y,z=loc
            cylinder('Neon | ceramic electrode',(x,y+.75,z),.45,1.2,ink,sign,(0,1,0),vertices=20,bevel=.09)
            tube('Neon | electrode return lead',[(x,y+.4,z),(x+.6,-60.6,z-1),(x+.9,-59.8,96.9)],.1,rubber,sign)
        for loc in (coords[len(coords)//3],coords[len(coords)*2//3]):
            x,y,z=loc
            cylinder('Neon | glass standoff',(x,y+1,z),.28,1.7,steel,sign,(0,1,0),vertices=16,bevel=.06)
            tube('Neon | tube retaining clip',[(x-.36,y,z),(x-.26,y-.25,z),(x+.26,y-.25,z),(x+.36,y,z)],.055,brass,sign)
# Segmented border has a physically broken lower-right piece and exposed cable.
border=material('neon damaged red border',(.34,.003,.008),.1,.3,3.3,False)
for pts in [[(-49,-61,95),(-50,-61,96),(-50,-61,114),(-48,-61,115),(48,-61,115),(50,-61,113),(50,-61,99)], [(-47,-61,95),(22,-61,95)],[(34,-61,95),(46,-61,95)]]:
    poly_tube('Neon | bent border',rounded(pts,1),.18,border)
tube('Neon | loose broken-border wire',[(25,-60,95),(27,-61.8,92.7),(30,-61.4,92.4),(32,-60.7,95)],.1,rubber,sign)
for x in (-46,46):text('DANGER HV' if x<0 else 'NS-07',(x,-60,92.6),.85,ink,sign)
# Reassign all detail helper products to the sign collection for clean export grouping.
for ob in set(scene.objects)-before:
    for col in list(ob.users_collection):col.objects.unlink(ob)
    sign.objects.link(ob)
scene.frame_start=1;scene.frame_end=180;scene.render.fps=30;scene.frame_set(1)
scene['shop_sign_text']='ITEM SHOP'
scene['shop_sign_dead_letters']='E,O'
scene['shop_sign_flicker']='T,H; 180 frames at 30 fps; constant interpolation'
scene['shop_sign_native_status']='Blender preview only. Use native per-letter skin/model switching or FX during later integration.'
scene.name='TOD2 | ITEM SHOP | Live art study'
(OUT/'neon_timing.json').write_text(json.dumps({'fps':30,'frames':180,'dead_letters':['E','O'],'animated_emission':keys,'native_integrated':False},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
print(json.dumps({'sign':'ITEM SHOP','dead':['E','O'],'flicker':['T','H'],'objects':len(sign.objects)}))
