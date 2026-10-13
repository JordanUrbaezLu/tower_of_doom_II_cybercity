"""MCP: update the existing baked master to author.py's corrected neck height."""
import bpy,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/necro_staff/staff_master.blend'))
for ob in bpy.context.scene.objects:
    target=26.8 if ob.name.startswith('Socket neck T') else 28.0 if ob.name.startswith('Skull mounting ferrule T') else None
    if target is None:continue
    delta=target-ob.location.z;ob.location.z=target
    for poly in ob.data.polygons:
        if abs(poly.normal.z)<.8:
            for li in poly.loop_indices:ob.data.uv_layers.active.data[li].uv.y+=delta/12
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/necro_staff/staff_master.blend'))
print('Mount ferrule seats 0.15 units into skull underside; shaft remains straight')
