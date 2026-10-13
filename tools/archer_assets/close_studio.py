"""Save and close only the dedicated Archer MCP scene receiving this request."""
import bpy
from pathlib import Path

master = Path(__file__).resolve().parents[2] / 'art/archer_assets/archer_equipment.blend'
if Path(bpy.data.filepath).resolve() != master.resolve():
    raise RuntimeError('Refusing to close a studio with a different active master')
bpy.ops.wm.save_as_mainfile(filepath=str(master))
print('ARCHER_STUDIO_SAVED; quitting dedicated studio')
bpy.app.timers.register(lambda: bpy.ops.wm.quit_blender() and None, first_interval=2)
