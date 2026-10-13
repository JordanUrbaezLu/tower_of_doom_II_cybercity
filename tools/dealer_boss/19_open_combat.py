"""Restore the reviewed Dealer combat camera with scene lighting in the owned studio."""
import bpy
import json
import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/dealer_combat/review/dealer_combat.blend'))
scene=bpy.context.scene
scene.frame_set(15)
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.camera.data.show_passepartout=True
scene.camera.data.passepartout_alpha=.95
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.shading.type='RENDERED'
            space.shading.use_scene_lights_render=True
            space.shading.use_scene_world_render=True
            space.region_3d.view_perspective='CAMERA'
            space.region_3d.view_camera_zoom=18
            space.overlay.show_overlays=False
proof={'file':bpy.data.filepath,'engine':scene.render.engine,'camera':scene.camera.name,
       'areas':[dict(type=a.spaces.active.shading.type,scene_lights=a.spaces.active.shading.use_scene_lights_render,
                     scene_world=a.spaces.active.shading.use_scene_world_render,
                     perspective=a.spaces.active.region_3d.view_perspective,
                     camera_zoom=a.spaces.active.region_3d.view_camera_zoom)
                for s in bpy.data.screens for a in s.areas if a.type=='VIEW_3D'],
       'approximation':'Actual native rig/weapon clips; preview effect geometry and studio lighting are not BO3.'}
(ROOT/'art/dealer_combat/review/visible_preview.json').write_text(json.dumps(proof,indent=2))
print('DEALER COMBAT RENDERED PREVIEW:',json.dumps(proof))
