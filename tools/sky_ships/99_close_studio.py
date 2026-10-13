"""Save the sky-fleet studio and close it cleanly (peers need the RAM for a lighting bake; docs/192).
The quit runs one second after this call returns, so the MCP response gets back first."""
import bpy
bpy.ops.wm.save_mainfile()
bpy.app.timers.register(lambda: bpy.ops.wm.quit_blender(), first_interval=1.0)
print('SKY_STUDIO_CLOSING saved', bpy.data.filepath)
