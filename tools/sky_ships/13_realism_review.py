"""Matched native-map previews via real Blender MCP. Job: tmp/sky_realism/render_job.json.

Uses shared fullspec approximation, native maps/gloss, no bloom, identical cameras
and lights on both sides. Does not save preview shader substitutes into the master.
"""
import bpy, sys, pathlib, json, math
from mathutils import Vector
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/art_cohesion'))
import native_preview
job = json.loads((ROOT/'tmp/sky_realism/render_job.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/job.get('source_blend','art/sky_ships/sky_fleet.blend')))
scene = bpy.context.scene
scene.render.engine = job.get('engine', 'BLENDER_EEVEE')
scene.cycles.device = 'CPU'
scene.cycles.samples = 12
scene.cycles.use_denoising = True
scene.render.resolution_percentage = 100
scene.render.resolution_x, scene.render.resolution_y = 960, 640
scene.render.image_settings.file_format = 'PNG'
scene.use_nodes = False
scene.render.use_compositing = False
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = job.get('exposure',-1)
world = bpy.data.worlds.new('Realism neutral backdrop')
scene.world = world
world.use_nodes = True
world.node_tree.nodes.get('Background').inputs[0].default_value = (.025, .025, .025, 1)
world.node_tree.nodes.get('Background').inputs[1].default_value = .6
for ob in bpy.data.objects:
    if ob.type == 'LIGHT':
        ob.hide_render = True
    if ob.type == 'MESH' and not any(c.name.startswith(('SHIP ', 'ROCK ')) for c in ob.users_collection):
        ob.hide_render = True
for name, angles, energy, rgb in [('key', (.7,.15,.9), 3.5, (.86,.91,1)), ('fill', (3,-.3,-2.2), .7, (.7,.78,1))]:
    data = bpy.data.lights.new('Realism '+name, 'SUN')
    data.energy, data.color, data.angle = energy, rgb, .12
    ob = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(ob)
    ob.rotation_euler = angles
gdt = ROOT/job.get('gdt', 'source_data/tod_sky_ships.gdt')
folder = ROOT/job.get('images', 'model_export/tod_sky_ships/_images')
mats = {}
gdt_text = gdt.read_text()
for m in list(bpy.data.materials):
    if m.name.startswith('mtl_tod_sky_') and ('"'+m.name+'" ( "material.gdf" )') in gdt_text:
        mats[m.name] = native_preview.fullspec(gdt, m.name, folder)
collections = [c for c in bpy.data.collections if c.name.startswith(('SHIP ', 'ROCK '))]
original = {}
for c in collections:
    for ob in c.objects:
        if ob.type == 'MESH':
            original[ob.name] = ob.data.materials[0].name
cam = bpy.data.objects.new('REALISM REVIEW CAMERA', bpy.data.cameras.new('REALISM REVIEW CAMERA'))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.clip_start, cam.data.clip_end = 1, 2e6
cam.data.angle = math.radians(40)
out = ROOT/'art/sky_ships/review/realism'/job['phase']
out.mkdir(parents=True, exist_ok=True)
variants = {'dreadnought': [('neon_red','neon_cyan')], 'hauler': [('neon_amber','neon_teal'),('ads','ads_b')],
            'gunship': [('neon_magenta','neon_green')], 'fighter': [('neon_cyan','neon_orange')],
            '3': [('neon_magenta','neon_cyan')], '4': [('neon_cyan','neon_amber')]}
done=[]
for c in collections:
    rock = c.name.startswith('ROCK ')
    key = c['rock'] if rock else c['ship']
    for other in collections: other.hide_render = other != c
    for variant in (['', '_b'] if job.get('variants', True) and key in variants else ['']):
        swaps = {'mtl_tod_sky_'+a:'mtl_tod_sky_'+b for a,b in variants.get(key, [])} if variant else {}
        if rock and variant:
            authored=dict(json.loads(c['variants'])).get(variant,[])
            swaps={'mtl_tod_sky_'+a:'mtl_tod_sky_'+b for a,b in authored}
        for ob in c.objects:
            if ob.type == 'MESH':
                name = original[ob.name]
                ob.data.materials[0] = mats[swaps.get(name,name)]
        name = ('rock_' if rock else '')+key+variant
        if job.get('only') and name not in job['only']: continue
        points = [ob.matrix_world@Vector(p) for ob in c.objects if ob.type=='MESH' for p in ob.bound_box]
        lo, hi = Vector([min(p[a] for p in points) for a in range(3)]), Vector([max(p[a] for p in points) for a in range(3)])
        target = (lo+hi)/2
        direction = Vector((.55,-.7,.45) if rock else (-.4,-.6,.66)).normalized()
        distance = (hi-lo).length*.56/math.tan(cam.data.angle/2)
        if job.get('detail'):
            detail={'dreadnought':((-4450,-1350,100),(-.6,-.75,.25),.25),
                    'hauler':((380,-470,50),(.25,-.68,.65),.33),
                    '2':((0,-250,60),(.55,-.7,.45),.45)}
            if key not in detail:continue
            position,look,scale=detail[key]
            target=Vector(c['offset'])+Vector(position)
            direction=Vector(look).normalized()
            distance*=scale
            name+='_detail'
        cam.location = target + direction*distance
        cam.rotation_euler = (target-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath = str(out/(name+'.png'))
        bpy.ops.render.render(write_still=True)
        done.append(name)
print('REALISM_REVIEW', job['phase'], done, native_preview.DESCRIPTION)
