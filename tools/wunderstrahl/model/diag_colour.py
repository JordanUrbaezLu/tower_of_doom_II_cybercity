"""MCP diagnostic (read-only in effect): which colour-management view transforms this Blender accepts (review-render
choice). Each candidate is set and the original transform/look restored afterwards."""
import bpy
vt = bpy.context.scene.view_settings
orig = (vt.view_transform, vt.look)
ok = []
for name in ('Standard', 'Filmic', 'AgX', 'Khronos PBR Neutral', 'Filmic Log', 'False Color', 'Raw'):
    try:
        vt.view_transform = name
        ok.append(name)
    except Exception as e:
        print('WS_DIAG_REFUSED', name, type(e).__name__)
vt.view_transform, vt.look = orig
print('WS_DIAG_VIEW_TRANSFORMS', ok, 'restored', orig)
print('WS_DIAG_BLENDER', bpy.app.version_string)
