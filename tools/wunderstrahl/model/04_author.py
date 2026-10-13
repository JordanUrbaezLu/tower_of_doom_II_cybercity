"""MCP step 04: author THE WUNDERSTRAHL master (art/wunderstrahl/wunderstrahl.blend) from the untouched reference.

* The DG-2's own meshes (exact geometry, normals, UVs and bone weights) are duplicated into the Wunderstrahl
  collection and wear the step-03 surfaces through approximate native previews (materials.py is the registry).
  The pointed rod tip that ran to tag_flash is removed from the coil copy: the focusing crystal now ends there.
* The emitter assembly (emitter.py, level 0) is built part by part, fitted to the DG-2's flaring copper claws:
  ring 1 encloses the copper cage ring the claws grow from; ring 2 sits inside the claw tulip (both gunmetal,
  raised knurled brass bands, yellow emissive lips front and rear); the FOCUSING RING is an open wheel behind the
  hook tips - a hoop with a knurled brass band and an engraved focus scale, each hook plugging into a brass ferrule
  on it, five spokes between the claws, a hub with a brass bolt circle and glowing bore lips carrying the lens
  housing; three tie rods with brass nuts in the claw gaps (on the spoke lines); the lens housing (brass retaining
  ring, six set screws) and the cut yellow focusing crystal (staggered triangle facets, a star table whose apex sits
  at x 40.998; tag_flash 41.0); two conduits from brass glands on the glass tube's front cap to ring 1 (dark braid
  with a windowed yellow light line on top, clamp collars and standoffs).
* All emitter islands are shelf-packed once into the shared 2048 atlas (engine_kit/atlas.json); the zone materials
  are procedural (zones.py) and are baked by step 05.
"""
import bpy, bmesh, importlib, json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, blendlib, emitter, zones, materials, views
for m in (common, blendlib, materials, emitter, zones, views):
    importlib.reload(m)
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=str(common.ART / 'dg2_reference.blend'))
scene = bpy.context.scene
scene.name = 'Wunderstrahl | authoring master'
IMG = common.IMG
common.KIT.mkdir(parents=True, exist_ok=True)


def map_path(name):
    return None if name is None or name.startswith('$') else IMG / (name + '.png')


def preview_material(name):
    m = materials.MATERIALS[name]; mp = m['maps']
    if m['kind'] == 'glass':
        return blendlib.fullspec('WS | ' + name, map_path(mp['c']), None, map_path(mp['g']), map_path(mp['n']), m['gloss'],
                                 spec_const=(.22, .22, .22), alpha=(1.0, 0.0))
    e = map_path(mp.get('e')) if m['kind'] == 'emissive' else None
    return blendlib.fullspec('WS | ' + name, map_path(mp['c']), map_path(mp['s']), map_path(mp['g']), map_path(mp['n']),
                             m['gloss'], e, m.get('scale', 0) * materials.PREVIEW_EMIT, e_falloff=m.get('falloff', 0.0))


ws_mats = {name: preview_material(name) for name in materials.MATERIALS if name != common.EMITTER_MATERIAL}

# ---- the DG-2 meshes, re-surfaced --------------------------------------------------------------------------------
src_coll = bpy.data.collections['DG-2 | view LOD0 (source, untouched)']
src_coll.hide_render = True
for ob in src_coll.objects:
    ob.hide_set(True)
view_coll = blendlib.collection('WUNDERSTRAHL | view meshes (DG-2 geometry, new surfaces)')
for ob in list(view_coll.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
removed_tip = 0
for ob in sorted(src_coll.objects, key=lambda o: o.name):
    new = ob.copy(); new.data = ob.data.copy(); view_coll.objects.link(new)
    new.name = ob.name.replace('DG-2 view', 'WS view'); new.hide_set(False); new.hide_render = False
    for slot in new.material_slots:
        native = slot.material.name.replace('DG-2 original | ', '')
        slot.material = ws_mats[common.MATERIAL_MAP[native]]
    if ob.get('dg2_source_mesh') == 1:   # the coil/pipe mesh carries the pointed tip
        bm = bmesh.new(); bm.from_mesh(new.data)
        tip = [f for f in bm.faces if all(v.co.x > 39.62 and math.hypot(v.co.y, v.co.z - emitter.AXZ) < .45 for v in f.verts)]
        removed_tip = len(tip)
        bmesh.ops.delete(bm, geom=tip, context='FACES')
        bm.to_mesh(new.data); bm.free(); new.data.update()

# ---- the emitter assembly -----------------------------------------------------------------------------------------
zone_mats = {z: zones.build(z) for z in emitter.ZONES}
em_coll = blendlib.collection('WUNDERSTRAHL | emitter assembly (new, rigid to tag_weapon)')
for ob in list(em_coll.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
parts = emitter.build(0)
islands = {k: v for p in parts for k, v in p.islands.items()}
pack, scale = emitter.shelf_pack(islands, margin_px=10, size=2048)
assert pack is not None and len(pack) == len(islands)


def part_object(part, coll):
    me = bpy.data.meshes.new(part.name)
    me.from_pydata([tuple(v) for v in part.verts], [], [f[0] for f in part.faces])
    me.update()
    used = [z for z in emitter.ZONES if any(f[1] == z for f in part.faces)]
    slot = {z: i for i, z in enumerate(used)}
    for z in used:
        me.materials.append(zone_mats[z])
    uv = me.uv_layers.new(name='UVMap')
    for poly, (ids, zone, uvs, key) in zip(me.polygons, part.faces):
        poly.material_index = slot[zone]
        poly.use_smooth = not part.flat
        t = pack[key]
        for li, (u, v) in zip(poly.loop_indices, uvs):
            uv.data[li].uv = emitter.island_uv(t, u, v)
    if not part.flat:
        me.set_sharp_from_angle(angle=math.radians(part.smooth_angle))
    ob = bpy.data.objects.new(part.name, me); coll.objects.link(ob)
    ob['ws_part'] = part.name; ob['ws_level'] = 0
    return ob


objs = [part_object(p, em_coll) for p in parts]
tris = {}
for ob in objs:
    ob.data.calc_loop_triangles(); tris[ob.name] = len(ob.data.loop_triangles)
atlas = dict(size=2048, margin_px=10, inches_to_uv=scale, texels_per_inch=round(scale * 2048, 1),
             islands={k: dict(size_in=[round(x, 4) for x in v], transform=list(pack[k])) for k, v in islands.items()},
             used_fraction=round(sum((v[0] * scale + 10 / 2048) * (v[1] * scale + 10 / 2048) for v in islands.values()), 4))
common.write_json(common.KIT / 'atlas.json', atlas)
design = dict(beam_axis=dict(y=0.0, z=emitter.AXZ, tag_flash=list(common.TAG_FLASH)),
              rings=[dict(name=r[0], x=r[1], depth=r[2], bore=r[3], outer=r[4], band=r[5]) for r in emitter.RINGS],
              focusing_ring=dict(x=[emitter.FR_X0, emitter.FR_X1], hoop=[emitter.HOOP_IN, emitter.HOOP_OUT, emitter.HOOP_BAND],
                                 hub=[emitter.HUB_IN, emitter.HUB_OUT], spokes=dict(angles=list(emitter.SPOKE_ANGLES),
                                 radius=[emitter.SPOKE_R0, emitter.SPOKE_R1], x=[emitter.SPOKE_X0, emitter.SPOKE_X1],
                                 width=emitter.SPOKE_W), claw_tip_x=emitter.CLAW_TIP_X,
                                 claw_tips=[dict(radius=r, angle=a) for r, a in emitter.CLAW_TIPS],
                                 claw_ferrules=dict(hook_dir_xr=list(emitter.HOOK_DIR), radius=emitter.FERRULE_R,
                                                    past_tip=emitter.FERRULE_IN, behind_tip=emitter.FERRULE_OUT),
                                 hub_bolts=dict(angles=list(emitter.HUB_BOLT_ANGLES), radius=emitter.HUB_BOLT_R)),
              crystal_cut=dict(stagger_levels='0..1', table_apex_x=emitter.LENS_TIP),
              far_lod_spine=dict(x=[emitter.SPINE_X0, emitter.SPINE_X1], radius=emitter.SPINE_R, levels='5..7'),
              far_lod_claws=dict(levels={str(k): dict(sides=v[0], radius=v[1], step=v[2]) for k, v in emitter.FAR_CLAW.items()},
                                 ring_centre_dz=emitter.CLAW_RING_DZ, path_x_rho=emitter.CLAW_PATH,
                                 material='mtl_tod2_ws_coil (a copper patch of its atlas)'),
              housing=[emitter.HOUSING_X0, emitter.HOUSING_X1],
              crystal=dict(back=emitter.LENS_BACK, girdle=[emitter.LENS_GIRDLE0, emitter.LENS_GIRDLE1], front=emitter.LENS_FRONT,
                           radius=emitter.LENS_R, table_radius=emitter.LENS_TABLE_R),
              max_radius=round(max(math.hypot(v.y, v.z - emitter.AXZ) for p in parts for v in p.verts), 4),
              tie_rods=dict(angles=list(emitter.TIE_ANGLES), radius=emitter.TIE_R, rod=emitter.TIE_ROD_R),
              conduits=dict(y=emitter.CONDUIT_Y, radius=emitter.CONDUIT_R, path_xz=emitter.CONDUIT_PATH),
              removed_tip_faces=removed_tip, level0_triangles=tris, level0_total=sum(tris.values()))
common.write_json(common.ART / 'design.json', design)

blendlib.setup_render(scene, samples=96, glare=True)
blendlib.studio(scene, views.CENTRE)
for name, (loc, tgt, lens, ortho, res) in views.VIEWS.items():
    blendlib.camera('Review | ' + name, loc, tgt, lens=lens or 50, ortho=ortho)
for ob in scene.objects:
    if ob.type == 'EMPTY':
        ob.hide_render = True
scene['ws_brief'] = ('The DG-2, rebuilt as a focused-light weapon: stepped gunmetal emitter rings with knurled brass bands '
                     'and yellow inner lips, a faceted yellow focusing crystal at tag_flash, a yellow laser filament in '
                     'the glass tube, warm yellow bulbs, two yellow-lined conduits, worn gunmetal/brass/aged copper, '
                     'dark lacquered composite stock. No cyan or blue.')
scene['native_playtested'] = False
bpy.ops.wm.save_as_mainfile(filepath=str(common.ART / 'wunderstrahl.blend'))
cam = bpy.data.objects['Review | lens_close']
blendlib.show_in_viewport(cam, 'MATERIAL')
print('WS_04_AUTHORED parts', len(parts), 'emitter tris', sum(tris.values()), 'removed tip faces', removed_tip,
      'atlas px/inch', atlas['texels_per_inch'], flush=True)
