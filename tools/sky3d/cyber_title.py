"""Authored cybercity title monument, built through Blender by build_city.py.

make_cyber_title(GATE, CAM_H, REPO, sign_aov='sign', log=print) -> report dict.
Only the owned collection/materials are replaced. No camera, world, compositor,
render settings, source image, GDT or native game asset is changed here.

The September 29 cybercity direction replaces the earlier haunted gate painting.
Geometry uses its exact title bearing and reference-width convention. The two
sensor nodes and segmented crest retain the first-jump reveal's feature centers.
All dimensions below are fractions of that width, so resizing stays coherent.
"""
import json
import math
import pathlib
import random

import bpy
from mathutils import Matrix, Vector


COLLECTION = 'sky3d_cyber_title'
PREFIX = COLLECTION + '_'
REFERENCE_WIDTH = 1448.0
CREST_LIGHT_RADIUS_FRACTION = .063
SENSOR_RING_RADIUS_FRACTION = .008  # legacy FX contract: now the angular sensor port's half-width
FEATURE_PIXELS = {'title': (0.0, 0.0), 'sub': (-4.0, 100.0),
                  'ring': (-2.0, -215.0),
                  'eye_l': (-42.0, -192.0), 'eye_r': (41.0, -192.0)}
# Linear RGB, not display/sRGB samples. gen_fx.py can AST-read these literals
# without importing bpy. Ring is the energy-weighted mean of its four cyan and
# four magenta segments (.82 and .64 of GATE neon); sensor cores are identical.
CINEMATIC_COLORS = {'title': (.82, .85, 1.0), 'title_core': (.82, .85, 1.0),
                    'sub': (.11, .62, .86),
                    'ring': (.3208904109589041, .4421917808219178, 1.0),
                    'eye_l': (.62, .87, 1.0), 'eye_r': (.62, .87, 1.0)}


def _material(name, color, aov_name, emission=0.0, metal=0.0,
              roughness=.55, body=False):
    """Directional machining and broad patina, separate from exposed-edge wear.

    Structural bodies receive a very dim presentation fill (<= .035 W); dark
    letter caps receive a subdued tinted fill below their bright machined rims.
    Letter rims and channels carry the hierarchy. None is a white surface
    hidden under colored emission. All sign surfaces write the existing AOV.
    """
    name = PREFIX + name
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    n, l = mat.node_tree.nodes, mat.node_tree.links
    n.clear()
    out = n.new('ShaderNodeOutputMaterial')
    aov = n.new('ShaderNodeOutputAOV'); aov.aov_name = aov_name
    aov.inputs['Value'].default_value = 1.0
    tex = n.new('ShaderNodeTexCoord')
    broad = n.new('ShaderNodeTexNoise')
    broad.inputs['Scale'].default_value = 11.0 if body else 64.0
    broad.inputs['Detail'].default_value = 2.0
    broad.inputs['Roughness'].default_value = .65
    l.new(tex.outputs['Generated'], broad.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB')
    lo, hi = (.60, 1.16) if body else (.93, 1.0)
    for el, gain in zip(ramp.color_ramp.elements, (lo, hi)):
        el.color = tuple(v * gain for v in color) + (1.0,)
    l.new(broad.outputs['Fac'], ramp.inputs[0])
    if body:
        bs = n.new('ShaderNodeBsdfPrincipled')
        l.new(ramp.outputs['Color'], bs.inputs['Base Color'])
        bs.inputs['Metallic'].default_value = metal
        grain = n.new('ShaderNodeTexNoise')
        grain.inputs['Scale'].default_value = 520.0
        grain.inputs['Detail'].default_value = 2.0
        mapping = n.new('ShaderNodeVectorMath'); mapping.operation = 'MULTIPLY'
        mapping.inputs[1].default_value = (1.0, 18.0, 1.0)
        l.new(tex.outputs['Generated'], mapping.inputs[0])
        l.new(mapping.outputs['Vector'], grain.inputs['Vector'])
        rr = n.new('ShaderNodeMapRange')
        rr.inputs['To Min'].default_value = max(.18, roughness - .09)
        rr.inputs['To Max'].default_value = min(.92, roughness + .10)
        l.new(broad.outputs['Fac'], rr.inputs['Value'])
        l.new(rr.outputs['Result'], bs.inputs['Roughness'])
        bump = n.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .10
        bump.inputs['Distance'].default_value = .045
        l.new(grain.outputs['Fac'], bump.inputs['Height'])
        l.new(bump.outputs['Normal'], bs.inputs['Normal'])
        l.new(ramp.outputs['Color'], bs.inputs['Emission Color'])
        bs.inputs['Emission Strength'].default_value = emission
    else:
        bs = n.new('ShaderNodeEmission')
        l.new(ramp.outputs['Color'], bs.inputs['Color'])
        bs.inputs['Strength'].default_value = emission
    l.new(bs.outputs[0], out.inputs['Surface'])
    mat.diffuse_color = (*color, 1.0)
    if hasattr(mat, 'cycles'):
        mat.cycles.emission_sampling = 'NONE'
    mat['role'] = 'weathered structural surface' if body else 'manufactured light source'
    mat['peak_emission_w'] = emission
    return mat


def _clip_rect(x, y, w, h, cut):
    a, b, c, d = x-w/2, x+w/2, y-h/2, y+h/2
    cut = min(cut, w*.48, h*.48)
    if cut <= 1e-10:
        return [(a,c),(b,c),(b,d),(a,d)]
    return [(a+cut,c),(b-cut,c),(b,c+cut),(b,d-cut),
            (b-cut,d),(a+cut,d),(a,d-cut),(a,c+cut)]


class _Parts:
    def __init__(self, width, transform, collection, gate):
        self.width, self.transform = width, transform
        self.collection, self.gate = collection, gate
        self.data = {}

    def prism(self, material, outline, front=0.0, depth=.01):
        if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(outline,outline[1:]+outline[:1])) < 0:
            outline=list(reversed(outline))
        verts, faces = self.data.setdefault(material, ([], []))
        start = len(verts); count = len(outline)
        verts.extend((x, y, z) for z in (front, front-depth) for x, y in outline)
        faces.append(tuple(start+i for i in range(count)))
        faces.append(tuple(start+count+i for i in reversed(range(count))))
        faces.extend((start+i, start+count+i, start+count+(i+1)%count, start+(i+1)%count)
                     for i in range(count))

    def box(self, material, x, y, w, h, front=0.0, depth=.01, cut=.0):
        self.prism(material, _clip_rect(x,y,w,h,cut), front, depth)

    def line(self, material, a, b, width, front=.001, depth=.001):
        a, b = Vector(a), Vector(b)
        d = b-a
        assert d.length > 1e-9
        p = Vector((-d.y,d.x)).normalized()*width/2
        self.prism(material, [tuple(a-p),tuple(b-p),tuple(b+p),tuple(a+p)], front, depth)

    def ring(self, material, x, y, radius, thickness, front=.0, sides=8,
             rotation=math.pi/8, selected=None):
        for i in range(sides):
            if selected is not None and i not in selected:
                continue
            a, b = rotation+i*math.tau/sides+.012, rotation+(i+1)*math.tau/sides-.012
            r0, r1 = radius-thickness/2, radius+thickness/2
            self.prism(material, [(x+r0*math.cos(a),y+r0*math.sin(a)),
                                  (x+r1*math.cos(a),y+r1*math.sin(a)),
                                  (x+r1*math.cos(b),y+r1*math.sin(b)),
                                  (x+r0*math.cos(b),y+r0*math.sin(b))], front,.002)

    def finish(self):
        objects=[]
        for material,(vertices,faces) in self.data.items():
            mesh=bpy.data.meshes.new(material.name+'_mesh')
            mesh.from_pydata([tuple(Vector(v)*self.width) for v in vertices], [], faces)
            mesh.materials.append(material); mesh.update()
            obj=bpy.data.objects.new(material.name,mesh)
            self.collection.objects.link(obj);obj.matrix_world=self.transform.copy()
            _visibility(obj,self.gate)
            if material.get('role')=='weathered structural surface':
                bevel=obj.modifiers.new('Machined edge radii','BEVEL')
                bevel.width=self.width*.00042;bevel.segments=2
                bevel.limit_method='ANGLE';bevel.angle_limit=math.radians(35)
                bevel.affect='EDGES'
                normal=obj.modifiers.new('Broad machined faces','WEIGHTED_NORMAL')
                normal.keep_sharp=True
            objects.append(obj)
        return objects


def _visibility(obj, gate):
    obj.visible_shadow=False
    if not gate.get('lights',False):
        obj.visible_diffuse=False
        obj.visible_transmission=False
        obj.visible_volume_scatter=False


def _text(body, font, cap, max_width, cx, cy, depth, width, transform,
          collection, face, edge, side, gate, inset=None):
    """Actual font geometry, uniformly fitted; zero raster lettering."""
    curve=bpy.data.curves.new(PREFIX+body.replace(' ','_'),'FONT')
    curve.body=body;curve.font=font;curve.align_x='CENTER'
    curve.size=1.0;curve.space_character=1.10
    curve.extrude=.030;curve.bevel_depth=.008;curve.bevel_resolution=2
    curve.resolution_u=8
    temp=bpy.data.objects.new(curve.name,curve);collection.objects.link(temp)
    bpy.context.view_layer.update()
    mesh=bpy.data.meshes.new_from_object(temp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    inset_mesh=None
    if inset is not None:
        # Shrink each stroke, not the word: preserve letter centers and spacing.
        # The dark cap leaves a real, bright machined rim around every contour.
        inset_curve=curve.copy();inset_curve.offset=-.010
        inset_curve.extrude=.006;inset_curve.bevel_depth=.002
        inset_obj=bpy.data.objects.new(curve.name+'_inset',inset_curve)
        collection.objects.link(inset_obj);bpy.context.view_layer.update()
        inset_mesh=bpy.data.meshes.new_from_object(inset_obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        bpy.data.objects.remove(inset_obj,do_unlink=True);bpy.data.curves.remove(inset_curve)
    bpy.data.objects.remove(temp,do_unlink=True);bpy.data.curves.remove(curve)
    mn=Vector(tuple(min(v.co[i] for v in mesh.vertices) for i in range(3)))
    mx=Vector(tuple(max(v.co[i] for v in mesh.vertices) for i in range(3)))
    scale=min(cap/(mx.y-mn.y),max_width/(mx.x-mn.x))*width
    for v in mesh.vertices:
        v.co.x=(v.co.x-(mn.x+mx.x)/2)*scale+cx*width
        v.co.y=(v.co.y-(mn.y+mx.y)/2)*scale+cy*width
        v.co.z=(v.co.z-mn.z)*scale+depth*width
    mesh.update()
    for mat in (face,edge,side):mesh.materials.append(mat)
    for poly in mesh.polygons:
        poly.material_index=0 if poly.normal.z>.995 else (1 if poly.normal.z>.15 else 2)
    if inset_mesh is not None:
        inset_min=min(v.co.z for v in inset_mesh.vertices)
        front=(mx.z-mn.z)*scale+depth*width
        for v in inset_mesh.vertices:
            v.co.x=(v.co.x-(mn.x+mx.x)/2)*scale+cx*width
            v.co.y=(v.co.y-(mn.y+mx.y)/2)*scale+cy*width
            v.co.z=front+.00065*width+(v.co.z-inset_min)*scale*.18
        inset_mesh.update()
        verts=[tuple(v.co) for v in mesh.vertices]
        faces=[tuple(p.vertices) for p in mesh.polygons]
        indices=[p.material_index for p in mesh.polygons]
        count=len(verts);verts.extend(tuple(v.co) for v in inset_mesh.vertices)
        faces.extend(tuple(i+count for i in p.vertices) for p in inset_mesh.polygons)
        indices.extend(3 if p.normal.z>.15 else 2 for p in inset_mesh.polygons)
        layered=bpy.data.meshes.new(mesh.name+'_machined_caps')
        layered.from_pydata(verts,[],faces);layered.update()
        for mat in (face,edge,side,inset):layered.materials.append(mat)
        for poly,index in zip(layered.polygons,indices):poly.material_index=index
        bpy.data.meshes.remove(mesh);bpy.data.meshes.remove(inset_mesh);mesh=layered
    obj=bpy.data.objects.new(PREFIX+body.replace(' ','_'),mesh)
    collection.objects.link(obj);obj.matrix_world=transform.copy();_visibility(obj,gate)
    obj['text']=body;obj['font_source']=font.filepath
    return obj


def make_cyber_title(gate, cam_h, repo, sign_aov='sign', log=print):
    """Return a JSON-safe receipt; the caller owns scene render/save/integration.

    GATE's 65-degree reference width, D, and text-box bearing are preserved.
    Actual silhouette extents are reported separately because pylons have height.
    'cinematic_features' gives both exact world angular centers and old reference
    offsets, allowing the jump reveal to retain its timing and retarget colors.
    """
    old=bpy.data.collections.get(COLLECTION)
    if old:
        for obj in list(old.objects):
            data=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
            if isinstance(data,bpy.types.Mesh) and not data.users:bpy.data.meshes.remove(data)
        bpy.data.collections.remove(old)
    collection=bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(collection)
    font_path=pathlib.Path(repo)/'fonts/orbitron.ttf'
    if not font_path.is_file():raise FileNotFoundError('Cyber title requires repository font '+str(font_path))
    font=next((f for f in bpy.data.fonts if pathlib.Path(bpy.path.abspath(f.filepath))==font_path),None)
    font=font or bpy.data.fonts.load(str(font_path));font.pack()
    width=2*float(gate['D'])*math.tan(math.radians(float(gate['w_deg'])/2))
    e=math.radians(float(gate['box_el']));cam=Vector((0,0,float(cam_h)))
    right=Vector((1,0,0));up=Vector((0,-math.sin(e),math.cos(e)))
    direction=Vector((0,math.cos(e),math.sin(e)));center=cam+direction*float(gate['D'])
    transform=Matrix((right,up,-direction)).transposed().to_4x4();transform.translation=center
    white=float(gate.get('white',1));neon=white*float(gate.get('neon',3))
    mats={
        'body':_material('graphite_chassis',(.024,.034,.058),sign_aov,.025*white,.65,.54,True),
        'panel':_material('inset_enamel',(.012,.020,.038),sign_aov,.018*white,.18,.62,True),
        'metal':_material('machined_titanium',(.11,.14,.20),sign_aov,.035*white,.78,.38,True),
        'joint':_material('seam_dirt',(.006,.009,.014),sign_aov,.012*white,.05,.82,True),
        'patina':_material('fastener_patina',(.050,.054,.058),sign_aov,.015*white,.40,.71,True),
        'wear':_material('exposed_contact_edges',(.15,.18,.23),sign_aov,.035*white,.72,.43,True),
        'cyan':_material('cyan_channels',(.025,.76,1.0),sign_aov,neon*.82),
        'magenta':_material('magenta_channels',(.70,.035,1.0),sign_aov,neon*.64),
        'face':_material('ivory_letter_faces',CINEMATIC_COLORS['title'],sign_aov,white*1.55),
        'violet':_material('violet_letter_bevel',(.39,.17,.80),sign_aov,white*.82),
        'sub':_material('cyan_subtitle',CINEMATIC_COLORS['sub'],sign_aov,white*1.22),
        'sensor':_material('sensor_cores',CINEMATIC_COLORS['eye_l'],sign_aov,neon*.95),
        'letter_cap':_material('recessed_letter_caps',(.080,.095,.155),sign_aov,.45*white,.55,.38,True),
    }
    p=_Parts(width,transform,collection,gate)
    # Chamfered armor overlaps a separate recessed enamel face and a back spine.
    armor=[(-.422,-.077),(-.389,-.123),(.332,-.123),(.422,-.082),
           (.422,.063),(.370,.122),(-.330,.122),(-.422,.080)]
    p.prism(mats['body'],armor,-.009,.028)
    p.prism(mats['metal'],[(x*.965,y*.89) for x,y in armor],-.002,.016)
    p.box(mats['joint'],0,0,.799,.203,.000,.005,.014)
    p.box(mats['panel'],0,0,.787,.193,.001,.006,.013)
    # Broad top/bottom service rails, interrupted luminous tracks and bolted seams.
    for sy in (-1,1):
        yy=sy*.111
        for i in range(8):
            a=-.388+i*.097
            p.line(mats['joint'],(a,yy),(a+.087,yy),.006,.004,.004)
            material=mats['cyan'] if (i+int(sy>0))%3 else mats['magenta']
            p.line(material,(a+.003,yy),(a+.078,yy),.0018,.006,.001)
        for i in range(15):
            x=-.371+i*.053
            p.ring(mats['patina'],x,sy*.095,.0032,.0012,.005,sides=8)
            outline=[(x+.002*math.cos(k*math.tau/6),sy*.095+.002*math.sin(k*math.tau/6)) for k in range(6)]
            p.prism(mats['metal'],outline,.006,.003)
            p.box(mats['joint'],x,sy*.095,.0017,.00055,.0062,.0003)
    # Armor cheeks route power around the headline. Asymmetric cuts, inset slots
    # and broad shadow steps give the face construction, without an all-neon cage.
    for sx in (-1,1):
        cheek=[(sx*.312,-.058),(sx*.367,-.078),(sx*.385,-.054),
               (sx*.385,.067),(sx*.343,.082),(sx*.321,.055)]
        if sx<0:cheek.reverse()
        p.prism(mats['body'],cheek,.006,.013)
        p.line(mats['metal'],(sx*.378,-.050),(sx*.378,.059),.005,.009,.004)
        route=[(sx*.369,.071),(sx*.345,.050),(sx*.345,-.029),(sx*.321,-.050)]
        for a,b in zip(route,route[1:]):
            p.line(mats['joint'],a,b,.007,.010,.003)
            p.line(mats['cyan'] if sx<0 else mats['magenta'],a,b,.0016,.011,.001)
        for j in range(3):
            p.box(mats['metal'],sx*(.359+j*.007),-.054+j*.002,.003,.011,.012,.003,.001)
        # Offset overlapping guards at the engineered corners, with recessed bolts.
        p.prism(mats['metal'],[(sx*.374,.087),(sx*.411,.067),(sx*.404,.051),(sx*.366,.074)][::(-1 if sx<0 else 1)],.011,.012)
        p.prism(mats['body'],[(sx*.356,-.095),(sx*.399,-.076),(sx*.397,-.061),(sx*.349,-.080)][::(-1 if sx<0 else 1)],.013,.015)
    # Tall split blades share the city's slab silhouette. Their open centers and
    # staggered crowns carry the monument into the surrounding skyline.
    foot=-center.z/up.z/width
    for sx in (-1,1):
        x=sx*.46
        top=.269 if sx<0 else .287
        p.box(mats['body'],x,(.17+foot)/2,.067,.17-foot,-.030,.039,.010)
        p.box(mats['metal'],x,foot+.010,.080,.020,0,.050,.004)
        for branch in (-1,1):
            bx=x+branch*.025
            blade_top=top+(.025 if branch*sx<0 else -.018)
            blade=[(bx-.015,foot+.019),(bx+.015,foot+.019),
                   (bx+.015,blade_top-.025),(bx+.003,blade_top),
                   (bx-.015,blade_top-.012)]
            p.prism(mats['body'],blade,-.006,.045)
            p.line(mats['metal'],(bx-branch*.011,foot+.034),(bx-branch*.011,blade_top-.025),.0027,-.002,.005)
            if branch*sx<0:
                for start,stop in ((foot+.047,-.159),(-.137,.073),(.153,blade_top-.035)):
                    p.line(mats['joint'],(bx,start),(bx,stop),.006,0,.005)
                    p.line(mats['cyan'] if sx<0 else mats['magenta'],(bx,start),(bx,stop),.0021,.002,.002)
        # Three dimensional cross braces sit behind the split blades.
        for yy in (foot+.13,.102,.209):
            p.box(mats['metal'],x,yy,.073,.008,-.016,.018,.002)
            p.box(mats['panel'],x,yy+.010,.036,.010,-.010,.011,.002)
        for j in range(7):
            y=foot+.036+j*(.18-foot-.065)/7
            p.box(mats['joint'],x,y,.039,.004,-.016,.005)
            p.box(mats['metal'],x,y+.004,.042,.004,-.015,.007)
            p.box(mats['panel'],x,y+.020,.023,.019,-.012,.003,.002)
        # Paired buttresses carry the sign's mass into the two segmented pylons.
        p.line(mats['body'],(sx*.451,-.178),(sx*.328,-.109),.025,-.023,.026)
        p.line(mats['metal'],(sx*.450,-.166),(sx*.337,-.109),.006,-.003,.006)
        p.line(mats['cyan'] if sx<0 else mats['magenta'],(sx*.450,-.163),(sx*.358,-.116),.0016,.001,.002)
        # Purposeful service cooling slots, all contained in the side cheeks.
        for j in range(9):
            p.box(mats['joint'],sx*.405,-.075+j*.019,.015,.0038,.004,.003,.001)
            p.box(mats['metal'],sx*.405,-.074+j*.019,.014,.0008,.0044,.0005)
    # Open scan cage and angular energy emblem. No solid face, paired round eyes
    # or upright ears: the preserved reveal points are now narrow inset ports.
    rx,ry=FEATURE_PIXELS['ring'];rx/=REFERENCE_WIDTH;ry/=-REFERENCE_WIDTH
    p.ring(mats['body'],rx,ry,.075,.013,-.012)
    p.ring(mats['metal'],rx,ry,.070,.010,-.007)
    p.ring(mats['joint'],rx,ry,.062,.007,-.005)
    p.ring(mats['cyan'],rx,ry,CREST_LIGHT_RADIUS_FRACTION,.0022,-.003,selected=(0,1,3,4))
    p.ring(mats['magenta'],rx,ry,CREST_LIGHT_RADIUS_FRACTION,.0022,-.003,selected=(2,5,6,7))
    # Split diamond: manufactured energy coupler rather than a character's head.
    emblem=[(rx,ry+.047),(rx+.023,ry+.017),(rx,ry-.012),(rx-.023,ry+.017)]
    for i,(a,b) in enumerate(zip(emblem,emblem[1:]+emblem[:1])):
        p.line(mats['metal'],a,b,.006,-.007,.010)
        p.line(mats['cyan'] if i in (0,3) else mats['magenta'],a,b,.0018,-.004,.002)
    p.box(mats['body'],rx,ry+.017,.009,.034,-.006,.014,.002)
    p.box(mats['sensor'],rx,ry+.017,.0018,.023,-.003,.001)
    p.line(mats['metal'],(rx-.045,ry-.041),(rx-.021,ry-.015),.006,-.008,.013)
    p.line(mats['metal'],(rx+.045,ry-.041),(rx+.021,ry-.015),.006,-.008,.013)
    for key in ('eye_l','eye_r'):
        x,y=FEATURE_PIXELS[key];x/=REFERENCE_WIDTH;y/=-REFERENCE_WIDTH
        half=SENSOR_RING_RADIUS_FRACTION
        p.box(mats['metal'],x,y,half*2+.010,.013,-.002,.010,.004)
        p.box(mats['joint'],x,y,half*2+.005,.008,-.001,.006,.003)
        p.box(mats['cyan'] if key=='eye_l' else mats['magenta'],x,y,half*2,.0035,0,.002,.0015)
        p.box(mats['sensor'],x,y,half*1.45,.0013,.0001,.001,.0005)
    # Selective broken wear on handled edges/joints, not a universal noise coat.
    rng=random.Random(929071)
    for sy in (-1,1):
        for j in range(18):
            x=rng.uniform(-.373,.373);length=rng.uniform(.002,.008)
            p.line(mats['wear'],(x,sy*.105),(x+length,sy*.105+rng.uniform(-.0004,.0004)),
                   rng.uniform(.00025,.0006),.0063,.0003)
    for sx in (-1,1):
        for j in range(6):
            y=foot+.038+j*.060
            p.line(mats['wear'],(sx*.429,y),(sx*.429,y+.007),.00065,.002,.0005)
    objects=p.finish()
    text_objects=[]
    for body,cap,max_w,x,y,face in [
        ('TOWER OF',.031,.49,0,.067,mats['violet']),
        ('DOOM II',.094,.728,0,0,mats['face']),
        ('CYBERCITY',.023,.47,-4/REFERENCE_WIDTH,-100/REFERENCE_WIDTH,mats['sub'])]:
        ob=_text(body,font,cap,max_w,x,y,.006,width,transform,collection,face,mats['violet'],mats['metal'],gate,
                 inset=mats['letter_cap'] if body=='DOOM II' else None)
        text_objects.append(ob);objects.append(ob)
    vl=bpy.context.view_layer
    if sign_aov not in [a.name for a in vl.aovs]:
        aov=vl.aovs.add();aov.name=sign_aov;aov.type='VALUE'
    def angles(point):
        q=point-cam
        return [math.degrees(math.atan2(q.x,q.y)),math.degrees(math.atan2(q.z,math.hypot(q.x,q.y)))]
    def bounds(obs):
        pairs=[angles(ob.matrix_world@v.co) for ob in obs for v in ob.data.vertices]
        return {'azimuth_deg':[min(p[0] for p in pairs),max(p[0] for p in pairs)],
                'elevation_deg':[min(p[1] for p in pairs),max(p[1] for p in pairs)]}
    features={key:{'reference_offset_px':[x,y],
                   'azimuth_elevation_deg':angles(center+right*(x/REFERENCE_WIDTH*width)-up*(y/REFERENCE_WIDTH*width)),
                   'sign_plane_offset_m':[x/REFERENCE_WIDTH*width,-y/REFERENCE_WIDTH*width]}
              for key,(x,y) in FEATURE_PIXELS.items()}
    report={'version':'cyber_monument_2','collection':COLLECTION,'font':str(font_path),
            'width_m':width,'reference_width_deg':float(gate['w_deg']),
            'title_anchor_deg':[0,float(gate['box_el'])],'distance_m':float(gate['D']),
            'sign_bounds':bounds(objects),'text_bounds':{ob['text']:bounds([ob]) for ob in text_objects},
            'cinematic_features':features,'cinematic_colors_linear_rgb':CINEMATIC_COLORS,
            'crest_light_radius_m':CREST_LIGHT_RADIUS_FRACTION*width,
            'sensor_port_half_width_m':SENSOR_RING_RADIUS_FRACTION*width,
            'sign_aov':sign_aov,'sign_aov_value':1.0,
            'objects':len(objects),'base_faces':sum(len(ob.data.polygons) for ob in objects),
            'emission_w':{key:mat['peak_emission_w'] for key,mat in mats.items()},
            'lights_city':bool(gate.get('lights',False)),
            'notes':'Native Blender typography/geometry; physical edge wear and procedural finish. Caller applies the existing sky finish and sign knee.'}
    collection['authoring_receipt']=json.dumps(report,sort_keys=True)
    log('cyber title: '+json.dumps(report,sort_keys=True))
    return report
