"""Frame the live studio viewport for a review screenshot (no scene edits, no save).

Reads scene['shop_review_view'] (default 'player'): 'player' = the service-window
camera, 'hero' = the three-quarter hero, 'sign' = a close frontal sign view,
'counter' = the counter stencils. Rendered EEVEE shading, powered, frame 1 (all
letters lit), playback stopped so the still is repeatable.
"""
import bpy
from mathutils import Vector
scene=bpy.context.scene
if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
view=scene.get('shop_review_view','player')
scene['shop_powered']=1.0;scene.frame_set(int(scene.get('shop_review_frame',1)))
for m in bpy.data.materials:
    if m.get('shop_emissive'):m.node_tree.update_tag()
bpy.context.view_layer.update()
scene.render.engine='BLENDER_EEVEE'
targets={'player':((0,-300,78),(0,-40,80),300),'hero':None,'sign':((0,-190,106),(0,-58,104),150),'counter':((0,-150,40),(0,-40,36),110),'fault':((0,-190,106),(0,-58,104),150)}
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type!='VIEW_3D':continue
        s=area.spaces.active;s.shading.type='RENDERED';s.overlay.show_overlays=False;s.clip_end=5000
        r=s.region_3d
        if view=='hero':
            cam=bpy.data.objects['01 HERO - three-quarter'];r.view_rotation=cam.rotation_euler.to_quaternion();r.view_location=(0,-2,61);r.view_distance=305
        else:
            eye,look,dist=targets[view];eye=Vector(eye);look=Vector(look)
            r.view_rotation=(look-eye).to_track_quat('-Z','Y');r.view_location=look;r.view_distance=dist
        r.view_perspective='PERSP'
        area.tag_redraw()
print('REVIEW_VIEW',view,'frame',scene.frame_current)
