"""Execute through Blender MCP (tools/lucky/mcp_call.py): save the lucky studio (art/lucky/lucky.blend) and quit it.
The quit runs on a timer so the MCP reply gets back first (the sky studio's 99_close_studio.py pattern)."""
import bpy, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'art/lucky/lucky.blend'))
bpy.app.timers.register(lambda: bpy.ops.wm.quit_blender(), first_interval=1.0)
print('LUCKY_STUDIO_CLOSING saved', str(ROOT / 'art/lucky/lucky.blend'))
