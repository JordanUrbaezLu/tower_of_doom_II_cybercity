"""Execute through Blender MCP (tools/lucky/mcp_call.py): hide the helper overlays (light outlines, the 3D cursor) in the
Golden Zombie viewer so the user sees only the model. Overlays toggle back with the viewport's Overlays button."""
import bpy
for window in bpy.context.window_manager.windows:
    for a in window.screen.areas:
        if a.type == 'VIEW_3D':
            ov = a.spaces.active.overlay
            ov.show_extras = False; ov.show_cursor = False; ov.show_relationship_lines = False
print('GOLDEN_VIEWER overlays hidden')
