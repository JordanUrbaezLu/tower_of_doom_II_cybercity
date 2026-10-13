"""11: THE DEALER'S WEAPONS in his hands - the Wunderwaffe DG-2, the Dingo machine
gun (stock world models, previewed at the right hand's weapon tag) and HIS SCYTHE,
authored here: a long blackened-steel snath with a hooked, red-neon-edged blade,
chain and grip wraps, in the Dealer's own material language.

Each weapon is a separate object parented to tag_weapon_right exactly the way the
engine attaches a model to a tag, so the studio shows the real in-hand fit under
any Keeper pose. The scythe exports as its own rigid xmodel (origin = the grip).
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('studio.py').read_text(encoding='utf-8'), str(Path(__file__).with_name('studio.py')), 'exec'))
import sys as _sys
_sys.path.insert(0, str(Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
M = library()
DON = ART / 'donors'
man = json.loads((DON / 'manifest.json').read_text())
# Blender caps a collection name at 63 characters: a longer name never matches itself again and every
# run used to leave a fresh copy behind (the 2026-09-30 diag found five generations of weapons)
name = 'DEALER | 06 WEAPONS - scythe, DG-2, Dingo'
stale = [c for c in bpy.data.collections if c.name.startswith('DEALER | 06')]
for c in stale:
    for ob in list(c.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
for c in stale[1:]:
    bpy.data.collections.remove(c)
cw = stale[0] if stale else bpy.data.collections.new(name)
cw.name = name
if cw.name not in scene.collection.children:
    scene.collection.children.link(cw)

TAG = 'tag_weapon_right'
tagb = BONES[TAG]
tag_mat = Matrix.Identity(4)
X, Y, Z = (Vector(tagb['matrix'][i]) for i in range(3))
for r in range(3):
    tag_mat[r][0], tag_mat[r][1], tag_mat[r][2], tag_mat[r][3] = X[r], Y[r], Z[r], tagb['offset'][r]


def donor_material(mat_name):
    bm = bpy.data.materials.get('DONOR / ' + mat_name)
    if bm:
        return bm
    bm = bpy.data.materials.new('DONOR / ' + mat_name); bm.use_nodes = True
    p = bm.node_tree.nodes['Principled BSDF']; p.inputs['Roughness'].default_value = 0.45; p.inputs['Metallic'].default_value = 0.3
    maps = (man['materials'].get(mat_name) or {}).get('maps') or {}
    col = maps.get('colorMap')
    if col and man['images'].get(col, {}).get('png'):
        t = bm.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(DON / '_images' / man['images'][col]['png']), check_existing=True)
        bm.node_tree.links.new(t.outputs['Color'], p.inputs['Base Color'])
    bm['donor_material'] = mat_name; bm['atlas'] = 'donor'
    return bm


def import_world_model(key, label):
    info = man['models'][key]
    m = xmodel.Model(); m.LoadFile_Bin(str(DON / info['file']), split_meshes=True)
    objs = []
    for mi, sm in enumerate(m.meshes):
        if not sm.verts:
            continue
        me = bpy.data.meshes.new('%s_%d' % (key, mi))
        me.from_pydata([tuple(v.offset) for v in sm.verts], [], [[f.indices[k].vertex for k in (0, 2, 1)] for f in sm.faces]); me.update()
        used = sorted({m.materials[f.material_id].name for f in sm.faces})
        for u in used:
            me.materials.append(donor_material(u))
        uv = me.uv_layers.new(name='Native_UV')
        for poly, f in zip(me.polygons, sm.faces):
            poly.material_index = used.index(m.materials[f.material_id].name); poly.use_smooth = True
            for li, k in zip(poly.loop_indices, (0, 2, 1)):
                uv.data[li].uv = (f.indices[k].uv[0], 1 - f.indices[k].uv[1])
        ob = bpy.data.objects.new('%s | %s %d' % (label, key, mi), me); cw.objects.link(ob)
        ob['weapon'] = key; ob['stock_preview'] = True
        objs.append(ob)
    # the engine aligns the model's origin to the tag: parent with the tag's bind frame
    for ob in objs:
        ob.parent = RIG; ob.parent_type = 'BONE'; ob.parent_bone = TAG
        # Blender bone-parenting puts the child at the bone's TAIL along Y; undo that so origin = bone head, axes = bind axes
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_world = tag_mat
    return objs


dg2 = import_world_model('dg2', 'Weapon | Wunderwaffe DG-2')
dingo = import_world_model('dingo', 'Weapon | Dingo LMG')

# ---------------------------------------------------------------- THE SCYTHE (model space: origin = the right hand grip)
# The tag's +X points down and forward in the bind pose (a gun's barrel), so the snath runs along -X:
# held like a staff with the blade rising OVER the shoulder; the swipe clips bring it down in a reaper's arc.
steel = M['blackened steel']; brass = M['aged brass fittings']; leather = M['worn black leather']; neon = M['red neon wire']
snath_pts = [Vector((16, 0, 0)), Vector((6, 0, 0.2)), Vector((-6, 0, 0.6)), Vector((-20, 0, 1.3)), Vector((-34, 0, 2.4)), Vector((-46, 0, 4.0))]
snath = tube('Scythe | snath', snath_pts, [0.95, 1.0, 1.0, 0.95, 0.9, 0.85], steel, cw, segments=14, cap_start=True, cap_end=True, noise_amt=0.03)
for i, c in enumerate((-6, 2, 8)):
    wrap = tube('Scythe | grip wrap %d' % i, [Vector((c, 0, 0)), Vector((c + 3.2, 0, 0.1))], [1.12, 1.12], leather, cw, segments=14)
    stitch = tube('Scythe | grip stitch %d' % i, [Vector((c + 1.6 + 0.02 * k, 1.16 * math.cos(k * 0.9), 1.16 * math.sin(k * 0.9))) for k in range(8)], [0.06] * 8, M['red stitch thread'], cw, segments=5)
pommel = sphere('Scythe | pommel', (16.6, 0, 0), (1.2, 1.05, 1.05), brass, cw, rings=10, segments=14)
ferrule = tube('Scythe | ferrule', [Vector((-44.5, 0, 3.75)), Vector((-48.5, 0, 4.4))], [1.05, 1.15], brass, cw, segments=14, cap_end=True)
# the tang bends the blade back along the snath: a hooked crescent, 30 in long, curling off the top
blade_pts = []
for i in range(13):
    t = i / 12
    a = math.radians(-10 + 125 * t)
    r = 23.0
    blade_pts.append(Vector((-48 - r * math.sin(a) * 0.95, 0, 4.6 - (1 - math.cos(a)) * r * 0.8 + 0.0)))
blade_verts = []; blade_faces = []
for i, p in enumerate(blade_pts):
    t = i / 12
    w = 4.2 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.7 + 0.3          # the blade's width from the spine to the edge
    spine_dir = (blade_pts[min(i + 1, 12)] - blade_pts[max(i - 1, 0)]).normalized()
    outward = Vector((0, 0, 1)).cross(spine_dir).normalized()                # in-plane, toward the edge (down/forward)
    edge = p + Vector((0, 0, -1)) * w * 0.9 + spine_dir * w * 0.25
    thick = 0.55 * (1 - 0.75 * t) + 0.08
    blade_verts += [p + Vector((0, thick, 0)), p - Vector((0, thick, 0)), edge]
    if i:
        b = 3 * (i - 1); c = 3 * i
        blade_faces += [(b, b + 1, c + 1, c), (b, c, c + 2, b + 2), (b + 1, b + 2, c + 2, c + 1)]
blade_faces += [(0, 1, 2), (3 * 12, 3 * 12 + 2, 3 * 12 + 1)]
blade = mesh('Scythe | hooked blade', blade_verts, blade_faces, steel, cw, smooth=True, bevel=0.12)
# the neon edge: a thin red tube along the cutting edge
edge_pts = [blade_verts[3 * i + 2] + Vector((0, 0, 0.05)) for i in range(13)]
edge = tube('Scythe | neon edge', edge_pts, [0.12 * (1 - 0.5 * i / 12) + 0.04 for i in range(13)], neon, cw, segments=8)
# etched channels on the blade face (lit)
for s in (-1, 1):
    ch = tube('Scythe | etched channel %d' % s, [blade_pts[i] + Vector((0, s * 0.62, -1.0 - 1.4 * (i / 12))) for i in range(2, 10)], [0.07] * 8, M['red stitch thread'], cw, segments=5)
# a short chain and a token hanging from the ferrule
chain = tube('Scythe | chain', [Vector((-47.5, 0, 3.0)) + Vector((0.2 * math.sin(k), 0.3 * math.cos(k * 1.3), -1.1 * k)) for k in range(6)], [0.14] * 6, steel, cw, segments=6, noise_amt=0.04)
token = tube('Scythe | token', [Vector((-47.9, -0.12, -3.6)), Vector((-47.9, 0.12, -3.6))], [(0.7, 0.7), (0.7, 0.7)], M['tarnished silver coin'], cw, segments=14, cap_start=True, cap_end=True)
for ob in cw.objects:
    if ob.name.startswith('Scythe |'):
        ob['weapon'] = 'scythe'; ob['dealer_part'] = False; ob['scythe_part'] = True
        ob.parent = RIG; ob.parent_type = 'BONE'; ob.parent_bone = TAG; ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_world = tag_mat @ ob.matrix_world
# show one weapon at a time (SHOW_WEAPON = 'scythe' | 'dg2' | 'dingo' | 'none')
show = globals().get('SHOW_WEAPON', 'scythe')
for ob in cw.objects:
    hid = ob.get('weapon') != show
    ob.hide_viewport = hid; ob.hide_render = hid
view_hero()
save('11_weapons')
print(json.dumps({'stage': '11_weapons', 'dg2_meshes': len(dg2), 'dingo_meshes': len(dingo), 'scythe_parts': sum(1 for o in cw.objects if o.get('scythe_part')), 'showing': show}))
