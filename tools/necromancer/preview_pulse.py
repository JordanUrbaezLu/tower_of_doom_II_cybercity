"""MCP: export the authored phase animation and low-angle review."""
import bpy,pathlib
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'art/necromancer/pulse'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'pulse.blend'))
s=next(s for s in bpy.data.scenes if s.name.startswith('Actual crown'))
bpy.context.window_manager.windows[0].scene=s
s.render.resolution_x=480;s.render.resolution_y=270;s.cycles.samples=4
for frame in range(1,87,5):
    s.frame_set(frame);s.render.filepath=str(OUT/f'anim_{frame:02}.png')
    bpy.ops.render.render(write_still=True)
s.frame_set(15)
s.camera.location.z-=40
s.camera.rotation_euler=Vector((0,400,-15)).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(OUT/'low_angle.png');bpy.ops.render.render(write_still=True)
s.view_settings.exposure+=2
s.render.filepath=str(OUT/'low_angle_bright.png');bpy.ops.render.render(write_still=True)
print('PULSE_PREVIEW_EXPORTED 18 animation frames, low angle, bright exposure; bloom off')
