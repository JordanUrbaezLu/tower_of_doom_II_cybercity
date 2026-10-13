"""Separate black-hooded male vendor, posed leaning toward the service counter."""
from pathlib import Path
exec(compile((Path(__file__).with_name('studio.py')).read_text(),str(Path(__file__).with_name('studio.py')),'exec'))
for ob in list(vendor.objects):bpy.data.objects.remove(ob,do_unlink=True)
eyes=material('merchant dark eyes',(.026,.018,.013),0,.36)
lip=material('merchant lip and creases',(.073,.036,.028),0,.8)
glove=material('black leather gloves',(.018,.017,.019),.05,.6)

def loft(name,rows,mat,col=vendor,segments=80,folds=0,cap=True):
    # Row: x-center,y-center,z,x-radius,y-radius; longitudinal cloth channels.
    verts=[]
    for j,(x,y,z,rx,ry) in enumerate(rows):
        for i in range(segments):
            a=i*math.tau/segments
            f=folds*(.6*math.sin(11*a+.13*j)+.25*math.sin(19*a-.3*j)+.15*math.cos(7*a))
            verts.append((x+(rx+f)*math.sin(a),y+(ry+f*.55)*math.cos(a),z))
    faces=[]
    for j in range(len(rows)-1):
        for i in range(segments):
            k=j*segments+i; kk=j*segments+(i+1)%segments
            faces.append((k,kk,kk+segments,k+segments))
    if cap:faces.extend([tuple(range(segments-1,-1,-1)),tuple((len(rows)-1)*segments+i for i in range(segments))])
    o=mesh(name,verts,faces,mat,col,smooth=True)
    sub=o.modifiers.new('Tailored smooth drape','SUBSURF');sub.levels=2;sub.render_levels=2
    return o

# Full figure is independent, including boots and lower coat hidden behind the counter.
loft('Merchant | coat body',[(0,4,14,12.5,6.5),(0,4,18,13,7),(0,4,29,11.7,6.8),(0,3,41,10.8,6.6),(0,2,50,12.3,7.5),(0,1,57,16,8),(0,1,61,14,7),(0,0,64,6,5)],cloth,folds=.68)
for x in (-6,6):
    sphere('Merchant | worn boot',(x,-.5,13),(4,7,2.2),rubber,vendor)
    for i in range(3):box('Merchant | boot vamp strap',(x,-3,14+i*.5),(7,.6,.45),clothEdge,vendor,.15)
# Front double-breasted overlap with vertical ridges and stitched seams.
tube('Merchant | coat overlap',[(-3,-3,19),(-1,-4,35),(1,-6,50),(5,-5,61)],.22,clothEdge,vendor)
for s in (-1,1):
    tube('Merchant | long coat side seam',[(s*10,-.7,17),(s*9,-1.8,33),(s*8,-3.8,50),(s*12,-3,59)],.16,clothEdge,vendor)
    box('Merchant | belt pouch',(s*10,-4,38),(5,2.5,7),glove,vendor,.8)
for z in (27,35,44,51):cylinder('Merchant | coat toggle',(2,-5.2,z),.55,.55,brass,vendor,(0,-1,0),vertices=12)

# Draped bent sleeves from shoulder to forearm; cloth made as shaped mesh, not hard cylinders.
def sleeve(name,points,radii):
    verts=[];ns=48
    for j,(co,rad) in enumerate(zip(points,radii)):
        co=Vector(co)
        tangent=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
        q=tangent.to_track_quat('Z','Y')
        for i in range(ns):
            a=i*math.tau/ns
            fold=.18*math.sin(a*9+j*.8)+.11*math.cos(a*5-j)
            d=q@Vector(((rad+fold)*math.cos(a),(rad+fold)*math.sin(a),0))
            verts.append(tuple(co+d))
    faces=[(j*ns+i,j*ns+(i+1)%ns,(j+1)*ns+(i+1)%ns,(j+1)*ns+i) for j in range(len(points)-1) for i in range(ns)]
    o=mesh(name,verts,faces,cloth,vendor,smooth=True)
    sub=o.modifiers.new('Soft sleeve folds','SUBSURF');sub.levels=2;sub.render_levels=2
    return o
for s in (-1,1):
    pts=[(s*13,1,59),(s*16,-3,56),(s*18,-8,51),(s*18,-13,47.3),(s*16,-20,47.3),(s*14,-29,47.7),(s*13,-33,47.8)]
    sleeve('Merchant | bent sleeve',pts,[5.8,6,5.4,5.3,4.4,3.6,3.3])
    cylinder('Merchant | leather cuff',(s*13,-32,47.8),3.35,3,glove,vendor,(0,1,0),vertices=48,bevel=.3)
    for dy in (-33.2,-30.8):
        cylinder('Merchant | cuff stitched binding',(s*13,dy,47.8),3.42,.25,clothEdge,vendor,(0,1,0),vertices=48,bevel=.06)
    # Resting palms and five articulated finger silhouettes, each with knuckle folds.
    sphere('Merchant | gloved palm',(s*13,-36.4,47.2),(3.1,4,1.25),glove,vendor)
    for finger in range(4):
        xx=s*13+(finger-1.5)*1.38
        length=[3.7,4.7,4.4,3.3][finger]
        pts=[(xx,-38,47.4),(xx,-40,47.25),(xx+.1*s,-39.8-length*.6,46.6),(xx+.18*s,-39.5-length,46.25)]
        tube('Merchant | glove finger',pts,.66,glove,vendor)
        for yy in (-40,-41.4):tube('Merchant | finger knuckle stitch',[(xx-.45,yy,47.7),(xx,yy-.16,47.9),(xx+.45,yy,47.7)],.06,clothEdge,vendor)
    tube('Merchant | thumb',[(s*10.6,-34.7,47.5),(s*9.6,-37,47.4),(s*9.4,-39.3,46.7)],.88,glove,vendor)
    tube('Merchant | glove back seam',[(s*11,-34,48.2),(s*11,-37,48.4),(s*13,-38.3,48.4),(s*15,-37,48.2)],.07,clothEdge,vendor)

# Anatomy is individually modeled under a deep cloth hood, no luminous monster eyes.
loft('Merchant | neck',[(0,0,60,3.2,3),(0,-1,63,3.3,3.1),(0,-2,66,3,3)],skin,segments=48)
loft('Merchant | human head',[(0,-2.3,63.7,1.8,2),(0,-2.5,64.5,3.5,3.0),(0,-2.2,66,4.4,3.65),(0,-1.7,69,5.1,4.1),(0,-1.2,72.7,5.3,4.2),(0,-.7,75.8,4.8,4),(0,-.3,77.4,3.8,3.2),(0,0,78.3,1.4,1.3)],skin,segments=64)
for s in (-1,1):
    sphere('Merchant | cheekbone',(s*3.35,-5.35,69.4),(1.7,1.35,1.6),skin,vendor)
    sphere('Merchant | recessed eye socket',(s*2.55,-5.8,72),(1.55,.75,.7),lip,vendor)
    sphere('Merchant | dark eye',(s*2.45,-6.34,72),(1,.27,.29),eyes,vendor)
    brow=sphere('Merchant | heavy brow',(s*2.7,-5.9,73),(1.9,.77,.52),skin,vendor);brow.rotation_euler.y=s*.16
    tube('Merchant | lower eyelid',[(s*.95,-5.95,71.7),(s*2.5,-6.58,71.45),(s*3.8,-5.95,71.65)],.13,skin,vendor)
    tube('Merchant | cheek crease',[(s*1.2,-6.1,69.2),(s*1.55,-6.3,67.6),(s*2.1,-5.9,66.8)],.09,lip,vendor)
# Angular bridge, projecting tip and nostrils.
sphere('Merchant | nose bridge',(0,-6.1,71),(1,1,2),skin,vendor)
sphere('Merchant | nose tip',(0,-7,69.4),(1.17,1.1,.8),skin,vendor)
for x in (-.83,.83):
    sphere('Merchant | nose wing',(x,-6.7,69),(.7,.55,.46),skin,vendor)
    sphere('Merchant | nostril',(x,-7.08,68.85),(.28,.15,.15),lip,vendor)
sphere('Merchant | muzzle',(0,-5.5,67.1),(2.45,.78,1.15),skin,vendor)
tube('Merchant | closed mouth',[(-1.9,-6.14,67.0),(-.8,-6.35,67.05),(0,-6.33,66.98),(.8,-6.35,67.05),(1.9,-6.14,67)],.11,lip,vendor)
sphere('Merchant | lower lip',(0,-6.13,66.65),(1.6,.3,.23),skin,vendor)
sphere('Merchant | chin',(0,-4.9,65.2),(2.6,.9,1),skin,vendor)

# Open hood: each ring is a tailored section, front aperture remains genuinely open.
verts=[];faces=[];N=112
rows=[(-10.4,7.1,10.4,70.6),(-9.8,7.6,10.9,70.8),(-7.1,8.6,11.5,71.3),(-2.0,9.1,11.9,71.5),(3.6,8.6,11.4,71.2),(7,6.7,9.1,70.8),(9.4,3.8,6.1,70.4),(10.3,.25,.4,70.4)]
for j,(y,rx,rz,zc) in enumerate(rows):
    for i in range(N):
        a=i*math.tau/N
        fold=(.22*math.sin(9*a+.3*j)+.12*math.sin(17*a-j*.2))*math.sin(math.pi*j/(len(rows)-1))
        x=(rx+fold)*math.sin(a)
        z=zc+rz*math.cos(a)+1.1*max(0,math.cos(a))**10
        yy=y-.65*math.cos(a*2)-.25*math.sin(a*5)
        verts.append((x,yy,z))
for j in range(len(rows)-1):
    for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
hood=mesh('Merchant | deep open black hood',verts,faces,cloth,vendor,smooth=True)
sol=hood.modifiers.new('Heavy hood cloth thickness','SOLIDIFY');sol.thickness=.25
sub=hood.modifiers.new('Hood drape smoothing','SUBSURF');sub.levels=2;sub.render_levels=2
rim=verts[:N]
tube('Merchant | hood rolled binding',rim,.28,clothEdge,vendor,True)
for off in (-.36,.36):
    tube('Merchant | crown tailored seam',[(off,-10.4,82.1),(off,-6,83.9),(off,0,84),(off,6,80.6),(off,10,72)],.1,clothEdge,vendor)
# Asymmetric folded cowl falls over shoulders, concealing the hood/coat junction.
for s in (-1,1):
    v=[(s*6.2,-8.9,64),(s*8.6,-3,69),(s*12,2,63),(s*16,-1,59),(s*8,-7.2,56),(s*1,-8,58.8)]
    c=mesh('Merchant | folded shoulder cowl',v,[(0,1,2,3,4,5)],cloth,vendor)
    sol=c.modifiers.new('Cowl weight','SOLIDIFY');sol.thickness=.7
    be=c.modifiers.new('Cowl softened edge','BEVEL');be.width=.45;be.segments=3
    tube('Merchant | cowl edge binding',[v[0],v[5],v[4],v[3]],.2,clothEdge,vendor)
    for i in range(3):tube('Merchant | cowl fold',[(s*(6+i*.75),-7.9,63-i*.6),(s*(8+i*1.4),-5.5,60-i*.75),(s*(9+i*1.4),-4.7,57.3)],.16,clothEdge,vendor)
# Vendor origin is export-friendly and keyed independently of the fixed kiosk.
root=bpy.data.objects.new('MERCHANT_ROOT | active-only separate model',None);vendor.objects.link(root)
root.location=(0,0,11.9)
for ob in list(vendor.objects):
    if ob!=root:
        mw=ob.matrix_world.copy();ob.parent=root;ob.matrix_world=mw
root['runtime']='Separate merchant model; show only at the active shop; no stock AI required for a static pose'
scene['shop_vendor_present']=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
print(json.dumps({'stage':'merchant','vendor_objects':len(vendor.objects),'active_only':True}))
