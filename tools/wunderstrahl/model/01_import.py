"""MCP step 01: preserve the untouched DG-2 in its own reference scene (art/wunderstrahl/dg2_reference.blend).

Reads the T7 Assets V2.8 kit read-only: the first-person model (12 bones), its animation skeleton, the eight
third-person LODs and their textures. Builds every native mesh with its exact corner normals, UVs and bone groups,
gives it an approximate native preview of its ORIGINAL maps, marks the twelve rig tags, and records every input by
sha256 in art/wunderstrahl/source_inventory.json. Nothing in the kit is modified.
"""
import bpy, importlib, sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, blendlib
importlib.reload(common); importlib.reload(blendlib)
from mathutils import Vector

scene = blendlib.clear_scene()
scene.name = 'DG-2 | untouched reference'
scene.unit_settings.system = 'NONE'
common.ART.mkdir(parents=True, exist_ok=True)

gdt = common.parse_gdt(common.SRC_GDT)
view = common.load_model(common.SRC_VIEW)
skel = common.load_model(common.SRC_SKEL)
worlds = [common.load_model(p) for p in common.SRC_WORLD]
img = common.SRC_IMG


def src_map(name):
    p = img / (name + '.png')
    return p if p.exists() else None


def original_material(native):
    """Preview of the DG-2's own material from its community GDT values (lit_weapon / emissive / transparent)."""
    kind, f = gdt[native]
    lo, hi = float(f.get('glossRangeMin', 0) or 0), float(f.get('glossRangeMax', 8) or 8)
    c = src_map(f.get('colorMap', ''))
    s = src_map(f.get('specColorMap', '')) if f.get('specColorMap') else None
    g = src_map(f.get('cosinePowerMap', '')) if f.get('cosinePowerMap') else None
    n = src_map(f.get('normalMap', '')) if f.get('normalMap') else None
    mtype = f.get('materialType', '')
    e = None; scale = 0.0; etint = (1, 1, 1)
    if 'emissive' in mtype and f.get('colorMap00', '').startswith('i_'):
        e = src_map(f['colorMap00'])
        scale = min(float(f.get('scaleRGB', 0) or 0), 24.0) * .25   # previews only: the source HDR scale is huge
        etint = tuple(float(x) for x in (f.get('colorTint1') or f.get('colorTint') or '1 1 1 1').split()[:3])
        if 'power' in native:
            etint = tuple(float(x) for x in f['colorTint'].split()[:3])
    alpha = (1.0, 0.0) if mtype == 'lit_transparent' else None
    return blendlib.fullspec('DG-2 original | ' + native, c, s, g, n, (lo, hi), e, scale, etint,
                             spec_const=(.22, .22, .22), gloss_const=.55, alpha=alpha)


mats = {m.name: original_material(m.name) for m in view.materials}
src_coll = blendlib.collection('DG-2 | view LOD0 (source, untouched)')
objects = []
for i, xm in enumerate(view.meshes):
    label = view.materials[xm.faces[0].material_id].name.replace('mtl_wpn_t7_zmb_dg2_', '')
    ob = blendlib.mesh_from_xmesh('DG-2 view | %02d %s' % (i, label), view, xm, mats, src_coll, keep_groups=True)
    ob['dg2_source_mesh'] = i
    objects.append(ob)

world_coll = blendlib.collection('DG-2 | world LODs (source, untouched)', hide_render=True)
for lod, wm in enumerate(worlds):
    lc = blendlib.collection('DG-2 world LOD%d' % lod, world_coll, hide_render=True)
    for i, xm in enumerate(wm.meshes):
        label = wm.materials[xm.faces[0].material_id].name.replace('mtl_wpn_t7_zmb_dg2_', '')
        ob = blendlib.mesh_from_xmesh('DG-2 world LOD%d | %02d %s' % (lod, i, label), wm, xm, mats, lc)
        ob.hide_set(True)
    lc.hide_viewport = lod > 0

tags = blendlib.collection('DG-2 | rig tags (12 view bones)')
for b in view.bones:
    e = bpy.data.objects.new(b.name, None); tags.objects.link(e)
    e.empty_display_type = 'ARROWS'; e.empty_display_size = 1.2 if b.name == 'tag_flash' else .6
    e.matrix_world = blendlib.bone_matrix(b)
    e['native_parent'] = view.bones[b.parent].name if b.parent >= 0 else ''

inputs = {}
for p in [common.SRC_VIEW, common.SRC_SKEL, common.SRC_GDT] + common.SRC_WORLD + sorted(img.glob('*.png')) + \
        sorted(common.SRC_XANIM.glob('*.xanim_bin')):
    inputs[common.rel(p)] = dict(sha256=common.sha(p), bytes=p.stat().st_size)


def mesh_rows(model):
    rows = []
    for i, xm in enumerate(model.meshes):
        pts = [v.offset for v in xm.verts]
        rows.append(dict(index=i, material=model.materials[xm.faces[0].material_id].name, verts=len(xm.verts),
                         faces=len(xm.faces), lo=[round(min(q[k] for q in pts), 4) for k in range(3)],
                         hi=[round(max(q[k] for q in pts), 4) for k in range(3)],
                         bones=sorted({model.bones[bi].name for v in xm.verts for bi, _ in v.weights})))
    return rows


inventory = dict(
    kit='T7 Assets V2.8 (DG-2 / Wunderwaffe, The Giant) extracted to tmp/wunderstrahl/src; read-only',
    inputs=inputs,
    view=dict(bones=[dict(name=b.name, parent=b.parent, offset=list(b.offset), matrix=[list(r) for r in b.matrix])
                     for b in view.bones], meshes=mesh_rows(view), triangles=sum(len(m.faces) for m in view.meshes)),
    skeleton=dict(bones=len(skel.bones), weapon_bones={b.name: list(b.offset) for b in skel.bones if b.name in common.VIEW_BONES}),
    world=[dict(lod=i, bones=[b.name for b in w.bones], meshes=mesh_rows(w), triangles=sum(len(m.faces) for m in w.meshes))
           for i, w in enumerate(worlds)],
    materials={m.name: gdt[m.name][1].get('materialType') for m in view.materials},
)
common.write_json(common.ART / 'source_inventory.json', inventory)
bpy.ops.wm.save_as_mainfile(filepath=str(common.ART / 'dg2_reference.blend'))
blendlib.show_in_viewport(shading='MATERIAL')
for win in bpy.context.window_manager.windows:
    for area in win.screen.areas:
        if area.type == 'VIEW_3D':
            with bpy.context.temp_override(window=win, area=area, region=next(r for r in area.regions if r.type == 'WINDOW')):
                bpy.ops.view3d.view_all(center=False)
print('WS_01_IMPORTED view meshes', len(objects), 'tris', inventory['view']['triangles'], 'world LODs',
      [w['triangles'] for w in inventory['world']], 'inputs', len(inputs), flush=True)
