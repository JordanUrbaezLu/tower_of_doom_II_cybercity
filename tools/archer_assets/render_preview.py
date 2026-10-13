"""Background rendering only, after the scene has been authored through MCP."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/archer_assets'
bpy.ops.wm.open_mainfile(filepath=str(ART/'archer_equipment.blend'))
scene=bpy.data.scenes['Cable phases | visual reference, not engine validation']
if bpy.context.window:bpy.context.window.scene=scene
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:scene.cycles.device='CPU'
out=ROOT/'tmp/archer_assets_mcp/frames';out.mkdir(parents=True,exist_ok=True)
scene.render.filepath=str(out/'phase_')
bpy.ops.render.render(animation=True,scene=scene.name)
print('ARCHER_PREVIEW_RENDERED',flush=True)
