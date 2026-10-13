"""Execute through real Blender MCP 9894. Render native, editable filament art.

All output is staged. install.py promotes only complete, inspected artifacts.
No game inputs, lighting, timing or existing studio scenes are changed here.
"""
import bpy, math, random, pathlib, json, hashlib
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'tmp/sky_fx_detail/staged'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 8
scene.render.threads_mode = 'FIXED'
scene.render.threads = 6
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
scene.world.color = (0, 0, 0)
scene.render.resolution_percentage = 100
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 24
rng = random.Random(290926)

def emission(name, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    out = m.node_tree.nodes.new('ShaderNodeOutputMaterial')
    e = m.node_tree.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (strength, strength, strength, 1)
    e.inputs['Strength'].default_value = 1
    m.node_tree.links.new(e.outputs[0], out.inputs['Surface'])
    return m

mats = [emission('Native grayscale %02d' % i, s) for i,s in enumerate((.06,.11,.18,.28,.42,.62,.9))]
collections = {}
for name in ('Rift filaments','Rift dust','Meteor wake'):
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    collections[name] = col

def curve(name, pts, width, mat, collection):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 1
    data.bevel_depth = width
    data.bevel_resolution = 1
    poly = data.splines.new('POLY')
    poly.points.add(len(pts)-1)
    for p,co in zip(poly.points,pts): p.co = (*co,1)
    obj = bpy.data.objects.new(name,data)
    collection.objects.link(obj)
    data.materials.append(mat)
    return obj

# Interrupted orbital braids: negative space through the centre, asymmetric
# turbulence on the ring, rare bright fibres inside much quieter material.
for i in range(84):
    start = rng.uniform(0,2*math.pi)
    length = rng.uniform(.16,2.5)
    radius = rng.uniform(.51,.81)
    phase = rng.uniform(0,2*math.pi)
    pitch = rng.uniform(-.08,.07)
    points=[]
    for j in range(110):
        u=j/109
        t=start+length*u
        r=radius+pitch*u+.012*math.sin(11*t+phase)+.004*math.sin(41*t+phase)
        points.append((r*math.cos(t),r*math.sin(t),.001*i))
    obj=curve('Torn orbital filament %03d'%i, points, rng.uniform(.0006,.0022), mats[rng.randrange(2,7)], collections['Rift filaments'])
    obj.rotation_euler.z = 0
    obj.keyframe_insert(data_path='rotation_euler',frame=1)
    obj.rotation_euler.z = .38 if i%3 else -.25
    obj.keyframe_insert(data_path='rotation_euler',frame=25)

# Wide dim wisps live outside the bright braid; thin internal strands prevent a
# perfectly smooth neon circle. Dust sprite is rendered independently for tint.
for i in range(115):
    start=rng.uniform(0,2*math.pi)
    length=rng.uniform(.08,1.2)
    r0=rng.uniform(.52,.90)
    points=[]
    for j in range(72):
        u=j/71
        t=start+length*u
        r=r0+.035*math.sin(t*7+i)+.02*(u-.5)
        points.append((r*math.cos(t),r*math.sin(t),.001*i))
    curve('Accretion wisp %03d'%i,points,rng.uniform(.001,.007),mats[rng.randrange(0,3)],collections['Rift dust'])

# A meteor's ribbon uses U along the flight and V across the width. Several
# irregular longitudinal ion threads replace the perfectly uniform laser line.
# Same endpoints ensure repeatability where the native geotrail tiles U.
for i in range(23):
    y0=rng.uniform(-.10,.10)
    points=[]
    phase=rng.uniform(0,2*math.pi)
    for j in range(257):
        u=j/256
        x=2*u-1
        y=y0+.009*math.sin(2*math.pi*u*3+phase)+.003*math.sin(2*math.pi*u*13+phase)
        points.append((x,y,.002*i))
    curve('Ion thread %02d'%i,points,rng.uniform(.001,.004),mats[2 if abs(y0)>.055 else rng.randrange(3,7)],collections['Meteor wake'])

cam_data=bpy.data.cameras.new('Native texture orthographic')
cam=bpy.data.objects.new('Native texture orthographic',cam_data)
scene.collection.objects.link(cam)
cam.location=(0,0,8)
cam.rotation_euler=(0,0,0)
cam_data.type='ORTHO'
cam_data.ortho_scale=2
scene.camera=cam

def isolate(name):
    for key,col in collections.items(): col.hide_render=key!=name

scene.frame_set(1)
for col,name in [('Rift filaments','i_tod_sky_rift_fibre'),('Rift dust','i_tod_sky_rift_dust'),('Meteor wake','i_tod_sky_meteor_wake')]:
    isolate(col)
    scene.render.resolution_y=256 if col=='Meteor wake' else 1024
    scene.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)

# Review animation contains the exact editable filament geometry without bloom.
isolate('Rift filaments')
scene.render.resolution_x=scene.render.resolution_y=512
for frame in (1,5,9,13,17,21):
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/('rift_phase_%02d.png'%frame))
    bpy.ops.render.render(write_still=True)
scene.frame_set(1)
scene['review_only']='Grayscale authored sprite sources. Native tint, depth sorting and bloom must be judged in BO3 by the user.'
scene['seed']=290926
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'sky_detail.blend'))
manifest={'seed':290926,'mcp_port':9894,'authoring':'actual Blender MCP, editable curves rendered orthographically',
          'native_playtested':False,'images':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('i_tod_*.png')}}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('SKY DETAIL ART STAGED',json.dumps(manifest))
