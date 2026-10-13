"""06: studio lighting and cameras for review renders (re-runnable).

The scene is in inches but Blender lights fall off as if the units were metres,
so the stage needs theatre-scale wattage. Three-point rig: a cool key, a soft
fill, hot red and violet rims that catch the coat's edges, and a low red floor
bounce that lights the hood's underside the way the Black Market's lamps do.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
studio = coll('90')
for ob in list(studio.objects):
    if ob.type == 'LIGHT':
        bpy.data.objects.remove(ob, do_unlink=True)
def light(name, loc, color, energy, size, aim=(0, 0, 42), kind='AREA', spot=None):
    l = bpy.data.lights.new(name, kind); l.color = color; l.energy = energy
    if kind == 'AREA':
        l.size = size; l.shape = 'DISK'
    elif kind == 'SPOT':
        l.spot_size = math.radians(spot or 40); l.spot_blend = 0.5; l.shadow_soft_size = size
    ob = bpy.data.objects.new(name, l); studio.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return ob
light('Studio | cool key', (150, -120, 150), (0.80, 0.84, 0.95), 7.5e5, 70)
light('Studio | soft fill', (-40, 180, 100), (0.62, 0.58, 0.68), 1.6e5, 120)
light('Studio | red rim', (-160, 70, 100), (1.0, 0.07, 0.04), 1.3e6, 45)
light('Studio | violet rim', (-130, -150, 80), (0.5, 0.1, 1.0), 7.0e5, 45)
light('Studio | low red bounce', (70, 10, 6), (1.0, 0.04, 0.02), 9.0e4, 60, aim=(0, 0, 60))
light('Studio | face spot', (120, -30, 90), (0.9, 0.9, 1.0), 3.5e5, 4, aim=(3, 0, 70), kind='SPOT', spot=18)
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.02, 0.016, 0.024, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.45
# cameras tightened on the figure
def cam(name, loc, aim, lens):
    ob = bpy.data.objects[name]; ob.location = loc; ob.data.lens = lens
    ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
cam('CAM 01 | hero three-quarter', (138, -96, 60), (0, 0, 43), 60)
cam('CAM 02 | front full', (178, 0, 44), (0, 0, 42), 60)
cam('CAM 03 | side full', (8, -180, 44), (0, 0, 42), 60)
cam('CAM 04 | mask close', (40, -12, 71), (3, 0, 70.5), 85)
cam('CAM 05 | hands and nails', (44, -36, 41), (2.5, -11.5, 37.5), 75)
cam('CAM 06 | back', (-178, 30, 46), (0, 0, 42), 60)
view_hero()
save(scene.get('dealer_stage', '06_lighting'))
print(json.dumps({'stage': '06_lighting', 'lights': sum(1 for o in studio.objects if o.type == 'LIGHT')}))
