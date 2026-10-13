"""Read-only diagnostics for the actual visible glass preview."""
import bpy
import json

scene = bpy.context.scene
proof = {'file': bpy.data.filepath, 'scene': scene.name,
         'engine': scene.render.engine, 'device': scene.cycles.device,
         'preview_pause': scene.cycles.preview_pause,
         'camera': scene.camera.name if scene.camera else None,
         'visible_meshes': [ob.name for ob in scene.objects if ob.type == 'MESH' and ob.visible_get()],
         'lights': [{'name': ob.name, 'power': ob.data.energy, 'visible': ob.visible_get()}
                    for ob in scene.objects if ob.type == 'LIGHT'],
         'viewports': [{'shading': area.spaces.active.shading.type,
                        'camera': area.spaces.active.camera.name if area.spaces.active.camera else None,
                        'perspective': area.spaces.active.region_3d.view_perspective,
                        'local_view': bool(area.spaces.active.local_view)}
                       for window in bpy.context.window_manager.windows
                       for area in window.screen.areas if area.type == 'VIEW_3D']}
print(json.dumps(proof, indent=2))
