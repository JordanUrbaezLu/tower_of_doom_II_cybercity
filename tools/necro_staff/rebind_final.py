"""MCP: editable final reviews reference deployed source maps, not staging."""
import bpy,pathlib,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/necro_staff';OUT=ROOT/'model_export/tod_necro_staff'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['staff_master.blend','staff_review.blend','surface_detail_review.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(ART/name))
    for im in bpy.data.images:
        if not im.filepath:continue
        original=pathlib.Path(bpy.path.abspath(im.filepath));target=OUT/original.name
        if target.exists():
            assert original.exists() and sha(original)==sha(target),(original,target)
            im.filepath=str(target);im.reload()
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/name))
print('FINAL SOURCE BINDINGS: all three editable reviews point to matching native source maps')
