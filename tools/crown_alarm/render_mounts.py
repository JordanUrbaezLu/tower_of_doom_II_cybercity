import bpy,pathlib,math
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/crown_alarm'
bpy.ops.wm.open_mainfile(filepath=str(ART/'mount_review.blend'));s=bpy.context.scene
s.render.filepath=str(ART/'hall_mounts.png');bpy.ops.render.render(write_still=True)
origin=Vector((0,8608,19392));cam=s.camera
cam.location=Vector((7000,1100,23200))-origin;cam.rotation_euler=(Vector((0,8608,22200))-origin-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=17000
s.render.resolution_x=1300;s.render.resolution_y=1500;s.render.filepath=str(ART/'exterior_mounts.png');bpy.ops.render.render(write_still=True)
print('CROWN_MOUNT_RENDERS_DONE',flush=True)
