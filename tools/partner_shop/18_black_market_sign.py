"""THE BLACK MARKET (user 2026-09-29: "The Item Shop / Black Market is confusing.
Lets just rename it Black Market all together and update the model with Blender MCP").

Live MCP revision on top of 16_fault_and_mask.py. The bent-tube ITEM SHOP letters
become BLACK MARKET in the same construction: a luminous tube over a charcoal glass
bedding, a ceramic electrode with a return lead at every tube end, two glass
standoffs and brass retaining clips per tube. The carrier, backplate, hood, screws,
stands, transformer, the broken border and its loose wire are untouched.

One line of condensed letters (5.7 wide, 11 tall) fits the unchanged border. The two
words keep the old sign's two reds (first word crimson, second orange-red).
C, E and T blink on the shared fault bus. They fill the three native blink slots:
letter_t and letter_e keep their letters, letter_c replaces letter_h. Every other
letter is steady. The three sign spark events move with their letters; the sign T
arc/spark geometry is unchanged, because the native mesh particles are cut from it.
Two catalogue stencils on the counter are re-lettered for a black market.

Idempotent: a re-run removes every sign letter and rebuilds it, and re-derives every
output. Writes neon_timing.json, electrical_timing.json (events + report),
electrical_validation.json and native_groups.json.
"""
from pathlib import Path
import shutil
PRESERVE_SHOP_MATERIALS=True
exec(compile(Path(__file__).with_name('studio.py').read_text(),str(Path(__file__).with_name('studio.py')),'exec'))
if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
backup=OUT/'checkpoints/20260929_before_black_market.blend';backup.parent.mkdir(exist_ok=True)
if not backup.exists():shutil.copy2(OUT/'partner_shop.blend',backup)
scene['shop_powered']=1.0;scene.frame_set(1)

TEXT='BLACK MARKET'
BLINK='CET'                                   # native slots letter_c / letter_e / letter_t
WORD_RGB=[(.48,.008,.012),(.60,.012,.006)]    # the old sign's reds: word 1 crimson, word 2 orange-red
W=5.7;GAP=2.5;WORD_GAP=6.4;TALL=11.0;BASE_Z=99.5;TUBE_Y=-61.45;SPARK_Y=-62.0
sign=bpy.data.collections['SHOP | 06 NEON SIGN - individual letters']
fx=bpy.data.collections['SHOP | 08 ELECTRICAL FX - preview only']
rubber=bpy.data.materials['SHOP / rubber and cable jackets'];ink=bpy.data.materials['SHOP / ivory stencilled markings']
steel=bpy.data.materials['SHOP / edge-worn machined steel'];brass=bpy.data.materials['SHOP / aged warm brass']

# ---- remove every sign letter (the 06 ITEM SHOP letters, or this script's own last run)
LETTER_PARTS=(' luminous tube ',' tube bedding ')
HELPERS=('Neon | ceramic electrode','Neon | electrode return lead','Neon | glass standoff','Neon | tube retaining clip')
removed=0
for ob in list(sign.objects):
    if ob.get('bm_sign') or any(s in ob.name for s in LETTER_PARTS) or ob.name.startswith(HELPERS):
        bpy.data.objects.remove(ob,do_unlink=True);removed+=1
for coll in (bpy.data.curves,bpy.data.meshes):
    for d in list(coll):
        if d.users==0:coll.remove(d)

def var(d,name,path):
    v=d.variables.new();v.name=name;v.type='SINGLE_PROP';v.targets[0].id_type='SCENE';v.targets[0].id=scene;v.targets[0].data_path=path
def neon(name,rgb,blink):
    """The shipped letter material: authored 5.5 radiance -> [shared fault] -> master power."""
    m=bpy.data.materials.get('SHOP / '+name) or bpy.data.materials.new('SHOP / '+name)
    m.use_nodes=True
    if m.node_tree.animation_data:m.node_tree.animation_data_clear()
    n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled')
    # Red glass stays physical and reads unpowered at zero emission (11_power_states.py).
    p.inputs['Base Color'].default_value=(*[v*.11 for v in rgb],1)
    p.inputs['Metallic'].default_value=.12;p.inputs['Roughness'].default_value=.29
    p.inputs['Emission Color'].default_value=(*rgb,1)
    l.new(p.outputs['BSDF'],out.inputs['Surface'])
    value=n.new('ShaderNodeValue');value.name='Electrical timeline';value.outputs[0].default_value=5.5
    gate=n.new('ShaderNodeMath');gate.name='Shop master power';gate.operation='MULTIPLY';gate.inputs[1].default_value=1
    src=value
    if blink:
        fault=n.new('ShaderNodeMath');fault.name='Shared electrical fault';fault.operation='MULTIPLY';fault.inputs[1].default_value=1
        l.new(value.outputs[0],fault.inputs[0]);src=fault
        d=fault.inputs[1].driver_add('default_value').driver;d.type='SCRIPTED';d.expression='bus';var(d,'bus','["shop_fault_bus"]')
    l.new(src.outputs[0],gate.inputs[0]);l.new(gate.outputs[0],p.inputs['Emission Strength'])
    d=gate.inputs[1].driver_add('default_value').driver;d.type='SCRIPTED';d.expression='power';var(d,'power','["shop_powered"]')
    m['shop_emissive']=True;m.diffuse_color=(*rgb,1)
    return m
def jacket(name,rgb):
    m=bpy.data.materials.get('SHOP / '+name) or bpy.data.materials.new('SHOP / '+name)
    m.use_nodes=True
    if m.node_tree.animation_data:m.node_tree.animation_data_clear()
    n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');c=tuple(v*.045 for v in rgb)
    p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=.15;p.inputs['Roughness'].default_value=.32
    p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=0
    l.new(p.outputs['BSDF'],out.inputs['Surface']);m.diffuse_color=(*c,1)
    return m
def poly_tube(name,points,r,mat):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=4
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    ob=bpy.data.objects.new(name,cu);sign.objects.link(ob);cu.materials.append(mat);ob['bm_sign']=True;return ob
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
def tag(ob):
    ob['bm_sign']=True;return ob

# Glyphs in the old sign's 6.5 x 11 design box (scaled to W). Each stroke is one
# real tube. Tube ends overlapping another tube (E's bar, R's leg) sit behind it.
glyphs={
 'B':[[(0,0),(0,11),(4.7,11),(6.0,9.7),(6.0,6.9),(4.8,5.6),(0,5.6)],[(4.8,5.6),(6.5,4.2),(6.5,1.4),(5.1,0),(.6,0)]],
 'L':[[(0,11),(0,0),(6.5,0)]],
 'A':[[(0,0),(2.5,11),(4.0,11),(6.5,0)],[(.98,4.3),(5.52,4.3)]],
 'C':[[(3.25+3.25*math.sin(a),5.5+5.5*math.cos(a)) for a in [math.tau*(.12-.76*i/48) for i in range(49)]]],
 'K':[[(0,11),(0,0)],[(6.3,11),(.35,4.6)],[(2.35,6.75),(6.5,0)]],
 'M':[[(0,0),(0,11),(3.25,5.5),(6.5,11),(6.5,0)]],
 'R':[[(0,0),(0,11),(4.9,11),(6.5,9.5),(6.5,7),(4.9,5.5),(0,5.5)],[(3.3,5.5),(6.5,0)]],
 'E':[[(6.5,11),(0,11),(0,0),(6.5,0)],[(0,5.6),(5.4,5.6)]],
 'T':[[(0,11),(6.5,11)],[(3.25,11),(3.25,0)]],
}
SMOOTH={'C'}   # already a sampled arc: no corner rounding
sx=W/6.5
words=TEXT.split(' ')
total=sum(len(w) for w in words)*W+sum(len(w)-1 for w in words)*GAP+(len(words)-1)*WORD_GAP
x=-total/2;layout=[]
for wi,word in enumerate(words):
    for li,ch in enumerate(word):
        layout.append((ch,wi,x));x+=W+(GAP if li<len(word)-1 else 0)
    x+=WORD_GAP
assert sorted(set(BLINK))==sorted(BLINK) and all(sum(1 for c,_,_ in layout if c==b)==1 for b in BLINK),'each blink letter must be unique on the sign'
assert layout[0][2]>-47 and layout[-1][2]+W<47,'the letters must sit inside the border (x -50..50)'

strokes=0;positions={}
for ch,wi,x0 in layout:
    blink=ch in BLINK
    m=neon('neon letter '+ch if blink else 'neon word '+words[wi],WORD_RGB[wi],blink)
    glass=jacket('neon glass jacket '+words[wi],WORD_RGB[wi])
    positions.setdefault(ch,x0)
    for si,path in enumerate(glyphs[ch]):
        pts=[(x0+px*sx,TUBE_Y,BASE_Z+pz*TALL/11) for px,pz in path]
        coords=pts if ch in SMOOTH else rounded(pts)
        # Raised charcoal bedding keeps a dropped-out letter legible (06_neon_sign.py).
        poly_tube('Neon | '+ch+' tube bedding '+str(wi)+str(si),[(px,py+.22,pz) for px,py,pz in coords],.32,glass)['shop_native_group']='solid'
        ob=poly_tube('Neon | '+ch+' luminous tube '+str(wi)+str(si),coords,.245,m)
        ob['neon_letter']=ch;ob['neon_word']=words[wi];ob['neon_dead']=False;ob['neon_flickers']=blink
        ob['shop_native_group']='letter_'+ch.lower() if blink else 'steady'
        for loc in (coords[0],coords[-1]):
            px,py,pz=loc
            tag(cylinder('Neon | ceramic electrode',(px,py+.75,pz),.45,1.2,ink,sign,(0,1,0),vertices=20,bevel=.09))['shop_native_group']='solid'
            tag(tube('Neon | electrode return lead',[(px,py+.4,pz),(px+.6,-60.6,pz-1),(px+.9,-59.8,96.9)],.1,rubber,sign))['shop_native_group']='solid'
        for loc in (coords[len(coords)//3],coords[len(coords)*2//3]):
            px,py,pz=loc
            tag(cylinder('Neon | glass standoff',(px,py+1,pz),.28,1.7,steel,sign,(0,1,0),vertices=16,bevel=.06))['shop_native_group']='solid'
            tag(tube('Neon | tube retaining clip',[(px-.36,py,pz),(px-.26,py-.25,pz),(px+.26,py-.25,pz),(px+.36,py,pz)],.055,brass,sign))['shop_native_group']='solid'
        strokes+=1
for ob in sign.objects:
    if ob.get('bm_sign'):ob['shop_part']=sign.name

# Old letter materials that nothing uses any more.
for m in list(bpy.data.materials):
    if m.users==0 and (m.name.startswith('SHOP / neon letter ') or m.name.startswith('SHOP / neon glass jacket ')):
        bpy.data.materials.remove(m)

# ---- the counter stencils: a black market's catalogue, not an upgrade shop's
for old,new in (('PARTNER  /  UPGRADES','NO QUESTIONS ASKED'),('EQUIP  /  REPAIR  /  ENHANCE','SPIN  /  SOCKET  /  SCRAP')):
    ob=next((o for o in scene.objects if o.type=='FONT' and o.data.body in (old,new)),None)
    if ob is None:raise RuntimeError('stencil not found: '+old)
    ob.data.body=new;ob.name='Marking | '+new

# ---- the sign's spark events follow their letters
def letter_x(ch):
    return next(x0 for c,_,x0 in layout if c==ch)
new_org={
    'sign T':(round(letter_x('T')+3.25*sx,3),SPARK_Y,round(BASE_Z+TALL,3)),          # the T's top bar, as before
    'sign E':(round(letter_x('E'),3),SPARK_Y,round(BASE_Z+5.5*TALL/11,3)),            # the E's spine, mid height, as before
    'sign C':(round(letter_x('C')+(3.25+3.25*math.sin(math.tau*.12))*sx,3),SPARK_Y,round(BASE_Z+(5.5+5.5*math.cos(math.tau*.12))*TALL/11,3)),  # the C's upper tube end
}
def fcurves(owner):
    a=owner.animation_data.action if owner.animation_data else None
    return [] if not a else [fc for layer in a.layers for strip in layer.strips for slot in a.slots if (bag:=strip.channelbag(slot)) for fc in bag.fcurves]
moved=0
for ob in list(fx.objects):
    event=ob.get('fx_event')
    if event=='sign H':
        event='sign C';ob['fx_event']=event;ob.name=ob.name.replace('sign H','sign C')
    if event not in new_org:continue
    kind=ob.get('fx_kind')
    # The arc's authored origin is its location; a spark starts at the event origin (frame 1 key).
    if kind=='arc':
        old=Vector(ob.location)
    else:
        loc=[fc for fc in fcurves(ob) if fc.data_path=='location']
        old=Vector([next(fc for fc in loc if fc.array_index==i).keyframe_points[0].co[1] for i in range(3)])
    delta=Vector(new_org[event])-old
    if delta.length<1e-6:continue
    loc=[fc for fc in fcurves(ob) if fc.data_path=='location']
    if loc:
        for fc in loc:
            for k in fc.keyframe_points:
                k.co[1]+=delta[fc.array_index];k.handle_left[1]+=delta[fc.array_index];k.handle_right[1]+=delta[fc.array_index]
            fc.update()
    else:
        ob.location=Vector(ob.location)+delta
    moved+=1
scene.frame_set(1);bpy.context.view_layer.update()

# ---- outputs the build gates and the timing generator read
timing=json.loads((OUT/'electrical_timing.json').read_text())
bus=timing['power_bus']
events=[]
for name,org,frame in timing['events']:
    if name=='sign H':name='sign C'
    events.append([name,list(new_org[name]) if name in new_org else org,frame])
assert [e[0] for e in events if e[0].startswith('sign')]==['sign T','sign E','sign C'],events
steady=sorted({c for c,_,_ in layout if c not in BLINK})
report=dict(timing['report'])
report.update({'revision':3,'sign_text':TEXT,'blinking_letters':list(BLINK),'steady_letters':steady,'dead_letters':[],
               'fx_objects':len(fx.objects),'native_integrated':False,'native_playtested':False})
sign_curves={c:[(f,v*5.5) for f,v in bus] for c in BLINK}
(OUT/'electrical_timing.json').write_text(json.dumps({'sign':sign_curves,'power_bus':bus,'events':events,'report':report},indent=2))
(OUT/'neon_timing.json').write_text(json.dumps({'fps':30,'frames':180,'sign_text':TEXT,'dead_letters':[],'animated_emission':sign_curves,'shared_power_bus':True},indent=2))
(OUT/'electrical_validation.json').write_text(json.dumps(report,indent=2))
groups={}
for ob in scene.objects:
    if 'shop_native_group' in ob:groups.setdefault(ob['shop_native_group'],[]).append(ob.name)
assert 'letter_h' not in groups and all(('letter_'+c.lower()) in groups for c in BLINK),sorted(groups)
(OUT/'native_groups.json').write_text(json.dumps(groups,indent=2))
scene['shop_sign_text']=TEXT
scene['shop_sign_blink']=BLINK
scene['shop_sign_dead_letters']=''
scene['shop_sign_flicker']=','.join(BLINK)+'; all letters functional'
scene['shop_electrical_revision']='3: BLACK MARKET sign; synchronized C/E/T and capacitor faults; independent slow mask breath; large sparks both sides; 100-degree indexed valve'
scene['shop_power_state_contract']='OFF: merchant absent, all emission/sparks/practicals disabled; physical hut and inventory remain. ON: C/E/T blink, other letters steady, mask slow pulse.'
scene['shop_name']='BLACK MARKET (renamed from the Item Shop 2026-09-29, user)'
scene.name='TOD2 | BLACK MARKET | Live art study'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
print(json.dumps({'sign':TEXT,'blink':BLINK,'letters':len(layout),'strokes':strokes,'removed_objects':removed,'fx_moved':moved,
                  'span':[round(layout[0][2],3),round(layout[-1][2]+W,3)],'spark_orgs':new_org,
                  'sign_objects':len(sign.objects),'groups':{g:len(v) for g,v in sorted(groups.items())}}))
