"""A readable, restrained Skyrail station for the rendered city sky.

Integration: reserve station_plan(RAIL_LINES[0], CAM_H) before placing buildings;
after city.build_all() call make_cyber_station(RAIL_LINES[0], CAM_H, REPO).
Skip the old first-line stations and its near-point train, but consume their old
random draws. Keep the existing rail line: the new opaque station bed covers the
old central luminous beam and the two platform tracks merge back into it.

Only the owned collection/materials are replaced. No camera, lighting, compositor,
sky image, GDT, or game file is changed. Importing station_plan needs no Blender.
"""
import json
import math
import pathlib
import random


COLLECTION = 'sky3d_cyber_station'
PREFIX = COLLECTION + '_'
STATION_SPEC = {
    'platform_length_m': 310.0, 'canopy_length_m': 288.0,
    'platform_centers_m': [-44.0, 44.0], 'platform_width_m': 18.0,
    'track_centers_m': [-29.0, 29.0], 'canopy_top_above_deck_m': 34.0,
    'train_cars': 5, 'train_car_length_m': 36.0, 'train_car_gap_m': 2.5,
    'train_width_m': 7.6, 'train_height_m': 11.5,
    'train_center_along_m': 92.0, 'train_track_m': -29.0,
    'approach_half_length_m': 360.0,
}


def _frame(rail_line):
    az, distance, radius, deck, *_ = rail_line
    if distance <= radius:
        raise ValueError('Hero station requires an offset rail circle outside the camera.')
    a=math.radians(az);away=(math.sin(a),math.cos(a))
    tangent=(math.cos(a),-math.sin(a));near=distance-radius
    return near, float(radius), float(deck), tangent, away


def _point(rail_line, u, v, z):
    near,radius,deck,tangent,away=_frame(rail_line)
    angle=u/radius
    along=(radius-v)*math.sin(angle)
    radial=near+radius-(radius-v)*math.cos(angle)
    return (along*tangent[0]+radial*away[0],
            along*tangent[1]+radial*away[1],deck+z)


def station_plan(rail_line, cam_h):
    """JSON-safe dimensions and visibility reservation, available outside Blender.

    The physical exclusion is a capsule around the station, not a kilometre-wide
    empty disk. Foreground protection is a separate angular corridor: only cap
    buildings closer than the station, leaving the distant skyline available.
    """
    near,radius,deck,tangent,away=_frame(rail_line)
    def angles(point):
        x,y,z=point
        return math.degrees(math.atan2(x,y)),math.degrees(math.atan2(z-cam_h,math.hypot(x,y)))
    corners=[_point(rail_line,u,v,z) for u in (-218,218) for v in (-60,65) for z in (0,46)]
    angular=[angles(point) for point in corners]
    azmin,azmax=min(p[0] for p in angular),max(p[0] for p in angular)
    elmin,elmax=min(p[1] for p in angular),max(p[1] for p in angular)
    center=_point(rail_line,0,0,0)
    keepout={'center_xy_m':list(center[:2]),'tangent_xy':list(tangent),'away_xy':list(away),
             'capsule_half_length_m':222.0,'capsule_radius_m':94.0,
             'foreground_azimuth_deg':[azmin-3,azmax+3],
             'foreground_elevation_deg':[elmin-2,elmax+2],
             'foreground_max_radius_m':near+65,
             'max_foreground_top_elevation_deg':max(3.0,elmin-2),
             'note':'Reserve physical capsule for buildings; in foreground angular corridor cap building tops below its lower elevation. Do not clear distant city.'}
    return {'version':'cyber_station_1','collection':COLLECTION,'rail_line':list(rail_line),
            'center_xyz_m':list(center),'azimuth_elevation_deg':list(angles(center)),
            'station_bounds_deg':{'azimuth':[azmin,azmax],'elevation':[elmin,elmax]},
            'keepout':keepout,'spec':dict(STATION_SPEC),
            'sign_text':'SKYRAIL STATION',
            'geometry_intent':'Two boarding platforms, two visible tracks, one long split canopy, one five-car train; no added towers, holograms, rings or light beams.'}


def in_station_footprint(x, y, plan, margin=0.0):
    """Conservative horizontal building keepout; margin can be a lot radius."""
    k=plan['keepout'];dx=x-k['center_xy_m'][0];dy=y-k['center_xy_m'][1]
    u=dx*k['tangent_xy'][0]+dy*k['tangent_xy'][1]
    v=dx*k['away_xy'][0]+dy*k['away_xy'][1]
    end=max(0.0,abs(u)-k['capsule_half_length_m'])
    return math.hypot(end,v)<k['capsule_radius_m']+margin


def _material(name, color, emission=0.0, metal=.0, rough=.6, light=False):
    mat=bpy.data.materials.get(PREFIX+name) or bpy.data.materials.new(PREFIX+name)
    mat.use_nodes=True;n,l=mat.node_tree.nodes,mat.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputMaterial')
    if light:
        node=n.new('ShaderNodeEmission');node.inputs['Color'].default_value=(*color,1)
        node.inputs['Strength'].default_value=emission
    else:
        coord=n.new('ShaderNodeTexCoord')
        noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=18
        noise.inputs['Detail'].default_value=3;noise.inputs['Roughness'].default_value=.7
        l.new(coord.outputs['Generated'],noise.inputs['Vector'])
        color_ramp=n.new('ShaderNodeValToRGB')
        for el,gain in zip(color_ramp.color_ramp.elements,(.66,1.12)):
            el.color=tuple(c*gain for c in color)+(1,)
        l.new(noise.outputs['Fac'],color_ramp.inputs[0])
        node=n.new('ShaderNodeBsdfPrincipled')
        l.new(color_ramp.outputs[0],node.inputs['Base Color'])
        l.new(color_ramp.outputs[0],node.inputs['Emission Color'])
        node.inputs['Emission Strength'].default_value=emission
        node.inputs['Metallic'].default_value=metal
        rr=n.new('ShaderNodeMapRange');rr.inputs['To Min'].default_value=max(.15,rough-.09)
        rr.inputs['To Max'].default_value=min(.95,rough+.10)
        l.new(noise.outputs['Fac'],rr.inputs['Value']);l.new(rr.outputs[0],node.inputs['Roughness'])
        fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=380
        fine.inputs['Detail'].default_value=2;l.new(coord.outputs['Generated'],fine.inputs['Vector'])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12
        bump.inputs['Distance'].default_value=.035
        l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],node.inputs['Normal'])
    l.new(node.outputs[0],out.inputs['Surface'])
    mat.diffuse_color=(*color,1);mat['emission_w']=emission
    mat.cycles.emission_sampling='NONE'
    return mat


class _Parts:
    def __init__(self, rail, collection):
        self.rail,self.collection=rail,collection;self.data={}

    def mesh(self, mat, vertices, faces):
        verts,polys=self.data.setdefault(mat,([],[]));start=len(verts)
        verts.extend(vertices);polys.extend(tuple(start+i for i in f) for f in faces)

    def prism(self, mat, outline, bottom, top):
        outline=list(outline)
        if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(outline,outline[1:]+outline[:1]))<0:
            outline.reverse()
        n=len(outline)
        verts=[(u,v,z) for z in (bottom,top) for u,v in outline]
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
        self.mesh(mat,verts,faces)

    def box(self, mat, u, v, z, length, width, height, cut=0.0):
        a,b=u-length/2,u+length/2;c,d=v-width/2,v+width/2
        if cut:
            outline=[(a+cut,c),(b-cut,c),(b,c+cut),(b,d-cut),(b-cut,d),(a+cut,d),(a,d-cut),(a,c+cut)]
        else:outline=[(a,c),(b,c),(b,d),(a,d)]
        self.prism(mat,outline,z-height/2,z+height/2)

    def strip(self, mat, a, b, width, height):
        du,dv=b[0]-a[0],b[1]-a[1];length=math.hypot(du,dv)
        pu,pv=-dv/length*width/2,du/length*width/2
        self.prism(mat,[(a[0]-pu,a[1]-pv),(b[0]-pu,b[1]-pv),
                        (b[0]+pu,b[1]+pv),(a[0]+pu,a[1]+pv)],a[2]-height/2,a[2]+height/2)

    def finish(self):
        objects=[]
        for mat,(verts,faces) in self.data.items():
            mesh=bpy.data.meshes.new(mat.name+'_mesh')
            mesh.from_pydata([_point(self.rail,*p) for p in verts],[],faces)
            mesh.materials.append(mat);mesh.update()
            obj=bpy.data.objects.new(mat.name,mesh);self.collection.objects.link(obj)
            # World sky materials use a dim ambient presentation floor too.
            # These emitters do not add a second light bath to the city/fog.
            obj.visible_diffuse=False;obj.visible_volume_scatter=False
            if mat.get('emission_w',0)<.2:
                bevel=obj.modifiers.new('Fabricated edge radii','BEVEL')
                bevel.width=.14;bevel.segments=2;bevel.limit_method='ANGLE'
                norm=obj.modifiers.new('Machined face normals','WEIGHTED_NORMAL');norm.keep_sharp=True
            objects.append(obj)
        return objects


def _text(parts, collection, font, material, body, u, v, z, cap, max_width):
    curve=bpy.data.curves.new(PREFIX+body.replace(' ','_'),'FONT')
    curve.body=body;curve.font=font;curve.size=1;curve.align_x='CENTER'
    curve.extrude=.018;curve.bevel_depth=.003;curve.bevel_resolution=1
    obj=bpy.data.objects.new(curve.name,curve);collection.objects.link(obj)
    bpy.context.view_layer.update()
    mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(obj,do_unlink=True);bpy.data.curves.remove(curve)
    xmin=min(v.co.x for v in mesh.vertices);xmax=max(v.co.x for v in mesh.vertices)
    ymin=min(v.co.y for v in mesh.vertices);ymax=max(v.co.y for v in mesh.vertices)
    scale=min(cap/(ymax-ymin),max_width/(xmax-xmin))
    vertices=[(u+(p.co.x-(xmin+xmax)/2)*scale,v-p.co.z*scale,
               z+(p.co.y-(ymin+ymax)/2)*scale) for p in mesh.vertices]
    parts.mesh(material,vertices,[tuple(p.vertices) for p in mesh.polygons])
    bpy.data.meshes.remove(mesh)


def make_cyber_station(rail_line, cam_h, repo, log=print):
    global bpy
    import bpy
    plan=station_plan(rail_line,cam_h)
    old=bpy.data.collections.get(COLLECTION)
    if old:
        for obj in list(old.objects):
            data=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
            if isinstance(data,bpy.types.Mesh) and not data.users:bpy.data.meshes.remove(data)
        bpy.data.collections.remove(old)
    collection=bpy.data.collections.new(COLLECTION);bpy.context.scene.collection.children.link(collection)
    mats={
        'structure':_material('weathered_graphite',(.055,.065,.085),.080,.5,.62),
        'platform':_material('worn_platform_enamel',(.090,.10,.12),.065,.12,.78),
        'roof':_material('oxidized_roof_metal',(.105,.13,.16),.065,.65,.55),
        'rail':_material('polished_rail_crowns',(.26,.28,.30),.060,.88,.25),
        'joint':_material('joint_dirt',(.009,.012,.018),.09,.0,.90),
        'wear':_material('rubbed_edges',(.16,.18,.20),.080,.55,.46),
        'train':_material('train_ivory_enamel',(.40,.44,.49),.105,.32,.40),
        'blue':_material('train_lower_livery',(.035,.080,.12),.090,.22,.50),
        'glass':_material('cool_window_glass',(.085,.19,.23),.090,.12,.23),
        'cabin':_material('warm_cabin_light',(.90,.78,.56),.145,light=True),
        'lamp':_material('platform_task_lights',(.72,.85,.95),.28,light=True),
        'cyan':_material('transit_cyan',(.035,.65,.82),.30,light=True),
        'amber':_material('safety_amber',(.58,.34,.055),.19,light=True),
        'letters':_material('station_lettering',(.74,.83,.9),.50,light=True),
    }
    p=_Parts(rail_line,collection);deck=plan['center_xyz_m'][2]
    # Two-track station deck; its matte top covers the old glowing single beam.
    cell=STATION_SPEC['platform_length_m']/16
    for i in range(16):
        u=-STATION_SPEC['platform_length_m']/2+(i+.5)*cell
        p.box(mats['structure'],u,0,-2.4,cell,112,7.5)
        p.box(mats['joint'],u,0,1.5,cell,69,1.3)
        for v in STATION_SPEC['platform_centers_m']:
            p.box(mats['platform'],u,v,2.2,cell-.3,18,2.1)
            inner=v-math.copysign(8.4,v)
            p.box(mats['amber'],u,inner,3.29,cell-1.6,.72,.14)
            # Wide enough to survive the final sphere, only at a useful safety edge.
            p.box(mats['wear'],u,v-math.copysign(8.9,v),3.34,14,.22,.12)
    # Structural piers and obvious access cores, not decorative towers.
    for u in (-122,0,122):
        for v in (-36,36):
            p.box(mats['structure'],u,v,-deck/2-2,9,11,deck-4,cut=1.2)
            p.box(mats['roof'],u,v,-10,18,24,4,cut=2)
    for u in (-119,119):
        p.box(mats['structure'],u,62,-deck/2+2,20,22,deck+4,cut=2)
        p.box(mats['roof'],u,61,5,32,35,9,cut=3)
        # A practical landing bridge links the far platform to the lift.
        p.box(mats['platform'],u,53,2.2,25,27,2.1)
        p.box(mats['cyan'],u,74,8,7,.4,1.0)
    # Visible rails with cross ties; gentle station turnouts rejoin the existing
    # centerline outside the station, so no disconnected floating track ends.
    for u in range(-354,355,12):
        spread=max(0,min(1,(360-abs(u))/(360-166)))
        for side in (-1,1):
            v=side*29*spread
            p.box(mats['structure'],u,v,-.3,12.4,8.6,3.4)
            p.box(mats['joint'],u,v,1.65,1.05,8.2,.6)
            for gauge in (-2.8,2.8):
                p.box(mats['rail'],u,v+gauge,2.30,12.5,.64,.42)
    # Two long roof wings and a clear center light well. The underside remains
    # open, exposing the train and the repeated platform columns at play angle.
    for u in range(-132,133,24):
        for side in (-1,1):
            v0,v1=side*11,side*56
            roof=[(u-11.7,v0,34),(u+11.7,v0,34),(u+11.7,v1,28),(u-11.7,v1,28),
                  (u-11.7,v0,32.2),(u+11.7,v0,32.2),(u+11.7,v1,26.2),(u-11.7,v1,26.2)]
            faces=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
            if side<0:faces=[tuple(reversed(face)) for face in faces]
            p.mesh(mats['roof'],roof,faces)
            p.box(mats['structure'],u,side*44,15,1.45,1.45,24)
            p.box(mats['lamp'],u,side*46,25.85,14,1.1,.18)
            # Raised seams and small drain breaks follow the roof construction.
            p.box(mats['joint'],u-11.65,side*36,30.6,.24,39,.35)
    # One legible transit sign, with platform identifiers at the ends.
    p.box(mats['structure'],0,-56.5,32.6,175,2.3,14.5,cut=.75)
    p.box(mats['cyan'],0,-57.8,38.75,165,.3,.70)
    font_path=pathlib.Path(repo)/'fonts/orbitron.ttf'
    if not font_path.is_file():raise FileNotFoundError(str(font_path))
    font=bpy.data.fonts.load(str(font_path));font.pack()
    _text(p,collection,font,mats['letters'],'SKYRAIL STATION',0,-58.1,32.6,7.5,160)
    for u,label in ((-127,'01'),(127,'02')):
        p.box(mats['structure'],u,-56.3,30,19,2,10,cut=.7)
        _text(p,collection,font,mats['letters'],label,u,-57.5,30,5.9,13)
    # Parked train, partially projecting beyond the canopy. Its pale hull, dark
    # window band, separate doors, articulated gaps and wedge nose read as a train.
    spec=STATION_SPEC
    pitch=spec['train_car_length_m']+spec['train_car_gap_m']
    for c in range(spec['train_cars']):
        u=spec['train_center_along_m']+(c-(spec['train_cars']-1)/2)*pitch
        v=spec['train_track_m'];half=spec['train_width_m']/2
        p.box(mats['structure'],u,v,3.2,30,6.8,2.6,cut=.8)
        p.box(mats['blue'],u,v,5.0,36,7.6,3.2,cut=.9)
        # Chamfered transverse section makes an enclosed rail car, not a light bar.
        section=[(-half,5.3),(-half,11.3),(-half+.9,14.5),
                 (half-.9,14.5),(half,11.3),(half,5.3)]
        section.reverse()  # CCW in the transverse plane: outward end-cap normals.
        vertices=[(u+end,v+vv,z) for end in (-18,18) for vv,z in section]
        if c==spec['train_cars']-1:
            vertices=[(uu-(max(0,zz-9.5)*.62 if uu>u else 0),vv,zz) for uu,vv,zz in vertices]
        n=len(section);faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
        p.mesh(mats['train'],vertices,faces)
        for side in (-1,1):
            facev=v+side*(half+.04)
            # Large actual window bays with dark mullions; warm interior is limited
            # to selected bays, avoiding another continuous neon ribbon.
            for j in range(5):
                x=u-12+j*6
                material=mats['cabin'] if (j+c)%3==0 else mats['glass']
                p.box(material,x,facev,10.8,4.6,.12,3.7)
            for x in (u-7.5,u+7.5):
                p.box(mats['joint'],x,facev+side*.1,9.0,3.0,.12,7.1)
                p.box(mats['train'],x,facev+side*.18,8.95,2.65,.12,6.85)
                p.box(mats['glass'],x,facev+side*.26,10.7,2.0,.12,2.8)
            p.box(mats['cyan'],u,facev,6.05,30,.12,.38)
        if c<spec['train_cars']-1:
            p.box(mats['joint'],u+19.25,v,8.5,2.1,5.8,7)
        if c==spec['train_cars']-1:
            p.box(mats['glass'],u+16.3,v,11.0,.22,5.7,2.8)
            for side in (-1,1):p.box(mats['lamp'],u+18.1,v+side*2.4,6.6,.2,1.1,.8)
        p.box(mats['joint'],u,v,14.6,14,3.0,.6,cut=.4)
    # Construction-driven grime, contact scuffs and drain marks, all nonemissive.
    rng=random.Random(929143)
    for u in (-122,0,122):
        for v in (-44,44):
            p.box(mats['joint'],u,v,3.31,3.1,3.0,.06)
    for side in (-1,1):
        for i in range(21):
            u=rng.uniform(-150,150)
            p.box(mats['wear'],u,side*52.8,2.9,rng.uniform(.7,2.4),.15,.25)
        for i in range(10):
            p.box(mats['joint'],-128+i*27,side*55.5,27.95,.7,.35,1.35)
    objects=p.finish()
    plan['objects']=len(objects);plan['base_faces']=sum(len(ob.data.polygons) for ob in objects)
    plan['materials']={key:float(mat['emission_w']) for key,mat in mats.items()}
    plan['native_visual_verified']=False
    collection['authoring_receipt']=json.dumps(plan,sort_keys=True)
    log('cyber station: '+json.dumps(plan,sort_keys=True))
    return plan
