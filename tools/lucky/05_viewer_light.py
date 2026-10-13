"""Execute through Blender MCP (tools/lucky/mcp_call.py) after 03_golden_viewer.py: add the golden zombie's in-game
AURA LIGHT to the live viewer, so the user sees the gold it throws around it, not only the model's own glow.

In game this is the dynamic light inside tod/luck/fx_luck_golden_aura (tools/lucky/make_fx.py golden_light(): gold
(1, 0.76, 0.26), radius 180 u, no shadow map) riding a host on the zombie's spine. Here: a shadowless point light of the
same colour at chest height, cut off at the same 180 u, over a floor as dark as the tower's tiles. The strength is
matched by eye (Blender watts are not BO3 intensity), so the pool's SIZE and COLOUR are the preview, not its exact
brightness - the playtest judges that (GOLDEN_LIGHT_INTENSITY in make_fx.py is the knob).
"""
import bpy
scene = bpy.data.scenes['Golden Zombie viewer']
GOLD = (1.0, 0.76, 0.26)                 # LOCKSTEP make_fx.py GOLDEN_LIGHT
RADIUS = 140                             # LOCKSTEP make_fx.py GOLDEN_LIGHT_RADIUS
ENERGY = 26000                           # ~ make_fx.py GOLDEN_LIGHT_INTENSITY 300 (60000 stood in for the old 700)
CHEST = (0, 0, 52)                       # j_spine4 on the horde body's bind pose, roughly

old = bpy.data.objects.get('Golden light (in-game aura light)')
if old:
    bpy.data.objects.remove(old, do_unlink=True)
d = bpy.data.lights.new('golden aura light', 'POINT')
d.color = GOLD
d.energy = ENERGY
d.shadow_soft_size = 6
d.use_shadow = False                     # the game's FX light has no shadow map: the body does not block it
if hasattr(d, 'use_custom_distance'):
    d.use_custom_distance = True
    d.cutoff_distance = RADIUS
o = bpy.data.objects.new('Golden light (in-game aura light)', d)
scene.collection.objects.link(o)
o.location = CHEST

floor = scene.objects.get('floor')
if floor and floor.data.materials:
    fb = floor.data.materials[0].node_tree.nodes['Principled BSDF']
    fb.inputs['Base Color'].default_value = (.07, .072, .08, 1)   # a dark tower tile, so the gold pool can read on it
print('GOLDEN_VIEWER light added: gold point light at the chest, cut off at %d u, shadowless' % RADIUS)
