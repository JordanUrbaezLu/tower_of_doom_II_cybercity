"""Studio helper: line the fleet up for review (studio offsets only; the export reads mesh space, so
moving objects here never changes a model) and frame all four ships from below in the viewport."""
import bpy, sys, importlib, pathlib, math
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib
importlib.reload(sky_lib)
LAYOUT = {'dreadnought': (0, 0, 0), 'hauler': (-2500, 6200, 1400), 'gunship': (2500, -4600, 900), 'fighter': (6200, -2600, 1800)}
objs = []
for c in bpy.data.collections:
    if c.name.startswith('SHIP ') and c['ship'] in LAYOUT:
        off = Vector(LAYOUT[c['ship']])
        c['offset'] = list(off)
        for o in c.objects:
            o.location = off
            objs.append(o)
for win in bpy.context.window_manager.windows:
    for area in win.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'PERSP'
            area.spaces.active.overlay.show_overlays = True
sky_lib.frame(objs)
print('SKY_FLEET_REVIEW', len(objs))
