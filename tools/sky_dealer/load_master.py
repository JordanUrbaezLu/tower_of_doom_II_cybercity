"""Restore the saved editable master in the dedicated MCP studio for material work."""
import pathlib
import bpy
ROOT = pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'tmp/sky_dealer/dealer.blend'))
print('SAVED_CONSISTENCY_MASTER_OPEN')
