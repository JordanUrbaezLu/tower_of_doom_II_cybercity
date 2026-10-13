"""Render the MCP-authored asset; only writes local review artifacts."""
import bpy,pathlib,math
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'art/crown_alarm'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'crown_alarm.blend'))
s=bpy.context.scene
s.render.filepath=str(OUT/'off.png');bpy.ops.render.render(write_still=True)
for ob in s.objects:
    if ob.type=='MESH':
        for slot in ob.material_slots:
            if slot.material and slot.material.name=='mtl_tod_alarm_lamp_off':slot.material=bpy.data.materials['mtl_tod_alarm_lamp_on']
s.frame_set(32);s.render.filepath=str(OUT/'on.png');bpy.ops.render.render(write_still=True)
for f in [1,10,19,28]:
    s.render.resolution_x=640;s.render.resolution_y=500;s.cycles.samples=16
    s.frame_set(f);s.render.filepath=str(OUT/('phase_'+str(f)+'.png'));bpy.ops.render.render(write_still=True)
s.render.resolution_x=560;s.render.resolution_y=440;s.cycles.samples=12
frames=OUT/'frames';frames.mkdir(exist_ok=True)
for f in range(1,37):
    s.frame_set(f);s.render.filepath=str(frames/(str(f).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
print('ALARM_PREVIEW_COMPLETE',flush=True)
