"""Record authored material bindings and release viewport GPU for the render."""
import json
import pathlib
import re
import bpy

root = pathlib.Path(__file__).resolve().parents[2]
records = []
for ob in bpy.context.scene.objects:
    if hasattr(ob.data, 'materials'):
        records.append(dict(object=ob.name, faces=len(ob.data.polygons) if ob.type == 'MESH' else None,
                            materials=[m.name if m else None for m in ob.data.materials]))
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'SOLID'
            area.tag_redraw()
used = {m for r in records for m in r['materials']}
# Reauthoring in the same Blender process may suffix fresh datablock names;
# the bindings are the actual used materials, not orphaned prior iterations.
canonical = {re.sub(r'\.\d{3}$', '', m) for m in used if m}
assert 'sky3d_landmark_armour' in canonical and 'sky3d_cyber_armour' in canonical
assert not canonical.intersection({'sky3d_facade', 'sky3d_roof', 'sky3d_crystal'}), 'Legacy facade still visible'
receipt = dict(objects=records, visible_materials=sorted(m for m in used if m),
               legacy_facade_visible=False, native_visual_verified=False)
(root / 'art/sky3d/dealer_review/scene_materials.json').write_text(json.dumps(receipt, indent=2)+'\n')
print('CONSISTENT_SCENE_MATERIALS', len(records), sorted(m for m in used if m))
