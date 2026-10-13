"""Studio view helper: re-apply the viewport glow settings and frame one ship (or all) from below.
Edit SHIP below before sending ('' = every ship)."""
import bpy, sys, importlib, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sky_lib
importlib.reload(sky_lib)
SHIP = globals().get('SHIP', '')
gl = next((n for n in bpy.context.scene.node_tree.nodes if n.bl_idname == 'CompositorNodeGlare'), None)
if gl:
    gl.threshold = 2.0; gl.size = 6; gl.mix = -0.55
objs = [o for c in bpy.data.collections if c.name.startswith('SHIP ') and (not SHIP or c['ship'] == SHIP) for o in c.objects]
sky_lib.frame(objs)
print('SKY_VIEW', SHIP or 'all', len(objs))
