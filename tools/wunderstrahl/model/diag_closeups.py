"""MCP diagnostic (read-only renders to tmp/wunderstrahl/scratch): close views of the barrel between the glass tube
and the muzzle, to plan the emitter mount and the conduit route. Saves no .blend."""
import bpy, importlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, blendlib
importlib.reload(common); importlib.reload(blendlib)

bpy.ops.wm.open_mainfile(filepath=str(common.ART / 'dg2_reference.blend'))
scene = bpy.context.scene
blendlib.setup_render(scene, samples=48, res=(1800, 900), glare=False)
for ob in scene.objects:
    if ob.type == 'EMPTY':
        ob.hide_render = True
blendlib.studio(scene, (27, 0.5, 3.2), scale=.6)
out = common.SCRATCH
shots = {
    'diag_barrel_left': ((27.0, 40.0, 4.0), (27.0, 0.0, 3.4), None, 24.0),
    'diag_barrel_top': ((27.0, 0.3, 40.0), (27.0, 0.3, 3.4), None, 24.0),
    'diag_barrel_topleft': ((17.0, 14.0, 14.0), (30.0, 0.0, 3.6), 45, None),
    'diag_front_axis': ((60.0, 0.0, 3.14), (30.0, 0.0, 3.14), 120, None),
}
for name, (loc, tgt, lens, ortho) in shots.items():
    cam = blendlib.camera('Diag | ' + name, loc, tgt, lens=lens or 50, ortho=ortho)
    blendlib.render(scene, cam, out / (name + '.png'))
print('WS_DIAG_CLOSEUPS', list(shots))
