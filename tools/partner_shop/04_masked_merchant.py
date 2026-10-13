"""Current user-approved direction: LED mask, black hood, standing with arms down.

Supersedes 02_merchant.py's initial face and counter pose.
"""
from pathlib import Path
exec(compile((Path(__file__).with_name('studio.py')).read_text(),str(Path(__file__).with_name('studio.py')),'exec'))
for ob in list(vendor.objects):bpy.data.objects.remove(ob,do_unlink=True)
glove=material('black leather gloves',(.018,.017,.019),.05,.6)
maskmat=material('black molded face mask',(.009,.014,.019),.22,.37)
maskLED=material('mask cyan electroluminescent wire',(.008,.61,1),.05,.35,3.2,False)

def loft(name,rows,mat,segments=64,folds=0,cap=True):
    verts=[]
    for j,(x,y,z,rx,ry) in enumerate(rows):
        for i in range(segments):
            a=i*math.tau/segments
            f=folds*(.6*math.sin(11*a+.13*j)+.25*math.sin(19*a-.3*j)+.15*math.cos(7*a))
            verts.append((x+(rx+f)*math.sin(a),y+(ry+f*.55)*math.cos(a),z))
    faces=[(j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i) for j in range(len(rows)-1) for i in range(segments)]
    if cap:faces.extend([tuple(range(segments-1,-1,-1)),tuple((len(rows)-1)*segments+i for i in range(segments))])
    o=mesh(name,verts,faces,mat,vendor,smooth=True)
    sub=o.modifiers.new('Tailored smooth drape','SUBSURF');sub.levels=2;sub.render_levels=2
    return o

loft('Merchant | long black coat',[(0,4,14,12,6),(0,4,19,12.6,6.6),(0,3.5,31,11.6,6.4),(0,3,42,10.8,6.8),(0,2,51,12.2,7.4),(0,1,58,15,7.5),(0,1,62,12.5,6.7),(0,0,64,5.7,4.7)],cloth,folds=.75)
for s in (-1,1):
    sphere('Merchant | boot',(s*6,-.5,14.1),(4,7,2.2),rubber,vendor)
    loft('Merchant | relaxed sleeve',[(s*17,2,31,3,3.2),(s*17.4,2,35,3.4,3.5),(s*17.7,2,43,4.1,4.5),(s*17,1.5,51,5,5.1),(s*15,1.1,58,5.5,5.4),(s*12,1,60.6,3.7,3.7)],cloth,folds=.38)
    cylinder('Merchant | sleeve cuff',(s*17,2,32),3.3,2.6,clothEdge,vendor,vertices=48,bevel=.3)
    sphere('Merchant | lowered glove',(s*17,1,27.5),(2.4,2.2,3.6),glove,vendor)
    tube('Merchant | sleeve seam',[(s*17,-1.3,33),(s*18,-2.6,44),(s*16,-3.6,55),(s*13,-3,60)],.12,clothEdge,vendor)
    tube('Merchant | coat seam',[(s*9,-.3,17),(s*9,-2.7,34),(s*8,-4.4,49),(s*11,-4.1,59)],.13,clothEdge,vendor)
    tube('Merchant | hood drawstring',[(s*4,-6.5,61),(s*4.6,-7.1,57),(s*4.2,-6.7,52)],.12,clothEdge,vendor)
    cylinder('Merchant | drawstring tip',(s*4.2,-6.7,51.7),.21,.9,steel,vendor,vertices=16,bevel=.04)
tube('Merchant | coat front zip',[(0,-2.8,17),(0,-3.6,34),(0,-4.5,46),(0,-6,59)],.12,black,vendor)
for z in range(43,59,2):box('Merchant | zip tooth',(0,-5.6,z),(.45,.3,.3),steel,vendor,.06)
loft('Merchant | covered neck',[(0,0,59,3.4,3),(0,-1,64,3.5,3.3),(0,-1,67,3.2,3.2)],cloth)
sphere('Merchant | covered head',(0,-1.8,70.8),(5.5,4.7,8),black,vendor)

def face_y(x,z):return -8.05-2.05*math.sqrt(max(.04,1-(x/6.0)**2-((z-71.1)/8.25)**2))
verts=[];faces=[];N=96
for j in range(25):
    r=.015+.985*j/24
    for i in range(N):
        a=i*math.tau/N;z=71.1+8.15*r*math.cos(a)
        x=5.65*(.80+.20*max(0,math.cos(a)))*r*math.sin(a)
        verts.append((x,face_y(x,z),z))
for j in range(24):
    for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
faces.append(tuple(range(N-1,-1,-1)))
mask=mesh('Merchant | black contoured LED mask',verts,faces,maskmat,vendor,smooth=True)
solid=mask.modifiers.new('Mask shell thickness','SOLIDIFY');solid.thickness=.24
def wire(name,xz,r=.11):return tube(name,[(x,face_y(x,z)-.22,z) for x,z in xz],r,maskLED,vendor)
for center in (-2.55,2.55):
    for s in (-1,1):wire('Merchant | cyan X eye',[(center-1.3,74.7+s*1.55),(center,74.7),(center+1.3,74.7-s*1.55)],.12)
    wire('Merchant | cyan eye lower echo',[(center-1.15,72.7),(center,72.3),(center+1.15,72.7)],.065)
for off in (-.55,.5):
    wire('Merchant | cyan grin arc',[(x:=(-4.25+i*8.5/24),65.9+3.1*(x/4.25)**2+off) for i in range(25)],.1)
for i in range(11):
    x=-3.85+i*.77;z=65.9+3.1*(x/4.25)**2
    wire('Merchant | grin stitched crossbar',[(x-.06,z-1.12),(x,z),(x+.08,z+1.16)],.085)
for s in (-1,1):wire('Merchant | cheek smile hook',[(s*4.12,68.4),(s*4.55,69.5),(s*4.6,71)],.075)

# Tailored open hood, opaque cloth back and no human face visible.
verts=[];faces=[];N=112
rows=[(-11.8,7.1,10.4,71),(-11.3,7.6,10.9,71.2),(-8.2,8.6,11.5,71.7),(-2.5,9.1,11.9,71.9),(3.5,8.6,11.4,71.6),(7,6.7,9.1,71.2),(9.4,3.8,6.1,70.8),(10.3,.25,.4,70.8)]
for j,(y,rx,rz,zc) in enumerate(rows):
    for i in range(N):
        a=i*math.tau/N
        fold=(.28*math.sin(9*a+.3*j)+.12*math.sin(17*a-j*.2))*math.sin(math.pi*j/(len(rows)-1))
        verts.append(((rx+fold)*math.sin(a),y-.65*math.cos(a*2)-.25*math.sin(a*5),zc+rz*math.cos(a)+1.1*max(0,math.cos(a))**10))
for j in range(len(rows)-1):
    for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
hood=mesh('Merchant | deep black hood',verts,faces,cloth,vendor,smooth=True)
sol=hood.modifiers.new('Heavy hood fabric','SOLIDIFY');sol.thickness=.28
sub=hood.modifiers.new('Hood drape smoothing','SUBSURF');sub.levels=2;sub.render_levels=2
tube('Merchant | hood rolled binding',verts[:N],.3,clothEdge,vendor,True)
for off in (-.28,.28):tube('Merchant | crown seam',[(off,-12,82.4),(off,-7,84.3),(off,0,84.4),(off,6,81),(off,10,72.4)],.085,clothEdge,vendor)
loft('Merchant | shoulder cowl',[(0,0,56.5,12,7.8),(0,0,58.5,15.6,8.2),(0,0,60.5,14,8.2),(0,.1,63,9,7.6),(0,.2,65,7,6.8)],cloth,folds=.38,cap=False)
for s in (-1,1):tube('Merchant | cowl fold',[(s*5,-8.8,64),(s*8,-7.6,61),(s*13,-5.6,58.5)],.13,clothEdge,vendor)
root=bpy.data.objects.new('MERCHANT_ROOT | active-only separate model',None);vendor.objects.link(root);root.location=(0,0,11.9)
bpy.context.view_layer.update()
for ob in list(vendor.objects):
    if ob!=root:
        mw=ob.matrix_world.copy();ob.parent=root;ob.matrix_world=mw
root['runtime']='Separate static merchant; visible only at active shop'
root['reference']='references/masked_merchant_reference.png'
root['pose']='Standing still, arms at sides, hands below counter'
scene['shop_vendor_present']=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
print(json.dumps({'stage':'masked_merchant','vendor_objects':len(vendor.objects),'hands_below_counter':True}))
