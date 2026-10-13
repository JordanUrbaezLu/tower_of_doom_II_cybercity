"""THE GUARDED HAVEN review (docs/202 v3): the two states of the floor-10 haven in Blender, before the native build.

Opens art/haven/review/haven_review.blend (tools/haven/preview.py: the real emitted hall faces, the shipping dome,
the floor's lights), shows the SAFE dome (the review's lattice mesh, i_tod_haven_field, scaleRGB 4) for the safe state
and - v5 (docs/202, user 2026-10-04: "the two states of the dome to be quite different") - the shipping BREACHED
mesh (model_export/tod_haven/tod_haven_dome_dark_lod0.xmodel_bin: a tenth of its cells gone, the rest cracked panes
on the i_tod_haven_field_dark atlas, scaleRGB 3.5) for the corrupted one, hangs the FLOOR 10 sign card
(model_export/tod_haven/tod_haven_sign.xmodel_bin at the generated anchor, tools/haven_layout.js SIGN) in its two
skins, and stands the guardians' spots as labelled markers inside the field. Renders each state from the porch (the
way in), from the north loggia (face on to the sign) and from the gallery above.

What is NOT real: BO3's lighting bake, probes, exposure and bloom, the looping effects (the corrupt embers, the
safe ambient) and the guardians themselves (markers at their spawn spots). It answers two questions: does the
corrupted field read as a different, hostile thing from the safe one, and does the sign read from the hall?

    "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe" --background --factory-startup --python tools/haven/preview_states.py

Writes art/haven/review/state_{corrupt,safe}_{porch,loggia,gallery}.png + states.json. Held while the game or any
native compiler runs (tools/dealer_presence/process_guard.py).
"""
from pathlib import Path
import bpy, json, sys, math, hashlib, os
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/haven/review'
sys.path.insert(0, str(ROOT / 'tools/dealer_presence'))
from process_guard import check
check()
sys.path.insert(0, str(Path(os.environ['APPDATA']) / 'Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel

SCALE = .0254
scene_data = json.loads((OUT / 'scene.json').read_text())
CX, CY, Z = scene_data['dome']['centre']
manifest = json.loads((ROOT / 'art/haven/manifest.json').read_text())
# the generated anchors (the same numbers _tod_haven.gsc reads)
DATA = (ROOT / 'scripts/zm/zm_tod2_cybercity/_tod_breather_data.gsc').read_text()
import re
m = re.search(r'function haven_sign_org\( z \) \{ return \( (-?[\d.]+), (-?[\d.]+), z \+ (-?[\d.]+) \); \}', DATA)
SIGN_ORG = (float(m.group(1)), float(m.group(2)), Z + float(m.group(3)))
SIGN_YAW = float(re.search(r'function haven_sign_yaw\(\)\s*\{ return (-?[\d.]+); \}', DATA).group(1))
GUARDS = [(float(a), float(b)) for a, b in re.findall(r'a\[ \d+ \] = \( (-?[\d.]+), (-?[\d.]+), z \);', DATA[DATA.index('function haven_guard_spots'):])]

bpy.ops.wm.open_mainfile(filepath=str(OUT / 'haven_review.blend'))
sc = bpy.context.scene
cam = sc.camera


def image_tex(nt, rel):
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(ROOT / rel), check_existing=True)
    tex.interpolation = 'Linear'; tex.extension = 'EXTEND'
    return tex


def emissive_transparent(name, rel, scale_rgb, tint=(1, 1, 1), cull=True):
    """lit_emissive_transparent as the shipping review draws it: alpha = coverage, the image x tint x scaleRGB as emission."""
    mt = bpy.data.materials.new(name); mt.use_nodes = True
    n, l = mt.node_tree.nodes, mt.node_tree.links; n.clear()
    out = n.new('ShaderNodeOutputMaterial')
    tex = image_tex(mt.node_tree, rel)
    mul = n.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1; mul.inputs[2].default_value = (*tint, 1)
    l.new(tex.outputs['Color'], mul.inputs[1])
    em = n.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = float(scale_rgb)
    l.new(mul.outputs[0], em.inputs['Color'])
    tr = n.new('ShaderNodeBsdfTransparent')
    mix = n.new('ShaderNodeMixShader')
    l.new(tex.outputs['Alpha'], mix.inputs['Fac']); l.new(tr.outputs[0], mix.inputs[1]); l.new(em.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs['Surface'])
    mt.surface_render_method = 'BLENDED'
    mt.use_backface_culling = cull
    return mt


dome = next(o for o in bpy.data.objects if o.name.startswith('haven dome'))
mats = manifest['materials']
SAFE = emissive_transparent('review | mtl_tod_haven_field', 'model_export/tod_haven/_images/i_tod_haven_field.png', mats['mtl_tod_haven_field'], (.85, 1, 1))
DARK = emissive_transparent('review | mtl_tod_haven_field_dark', 'model_export/tod_haven/_images/i_tod_haven_field_dark.png', mats['mtl_tod_haven_field_dark'], (1, .9, .9))


def mesh_from_bin(rel, name, material):
    """a shipping xmodel_bin local to the floor centre (x, y round it, z above the floor), placed at the dome's centre"""
    mdl = xmodel.Model(); mdl.LoadFile_Bin(str(ROOT / rel), split_meshes=True)
    verts, faces, uvs = [], [], []
    for mesh in mdl.meshes:
        base = len(verts)
        verts.extend(v.offset for v in mesh.verts)
        for f in mesh.faces:
            faces.append([base + fv.vertex for fv in f.indices])
            uvs.append([(fv.uv[0], 1 - fv.uv[1]) for fv in f.indices])
    me = bpy.data.meshes.new(name)
    me.from_pydata([((CX + v[0]) * SCALE, (CY + v[1]) * SCALE, (Z + v[2]) * SCALE) for v in verts], [], faces); me.update()
    me.materials.append(material)
    uv = me.uv_layers.new()
    for poly, coord in zip(me.polygons, uvs):
        for li, t in zip(poly.loop_indices, coord): uv.data[li].uv = t
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob


# v5: the corrupted dome is its own mesh, breached and cracked - the review shows the shipping binary
dark_dome = mesh_from_bin('model_export/tod_haven/tod_haven_dome_dark_lod0.xmodel_bin', 'haven dome dark (v5 breached mesh)', DARK)
dome.data.materials[0] = SAFE


def show(ob, on):
    ob.hide_render = not on
    ob.hide_viewport = not on


def sign_card(state):
    """the shipping quad at the generated anchor, in the state's skin"""
    mdl = xmodel.Model(); mdl.LoadFile_Bin(str(ROOT / 'model_export/tod_haven/tod_haven_sign.xmodel_bin'), split_meshes=True)
    verts, faces, uvs = [], [], []
    for mesh in mdl.meshes:
        base = len(verts)
        verts.extend(v.offset for v in mesh.verts)
        for f in mesh.faces:
            faces.append([base + fv.vertex for fv in f.indices])
            uvs.append([(fv.uv[0], 1 - fv.uv[1]) for fv in f.indices])
    yaw = math.radians(SIGN_YAW)
    def world(v):
        x = v[0] * math.cos(yaw) - v[1] * math.sin(yaw); y = v[0] * math.sin(yaw) + v[1] * math.cos(yaw)
        return ((SIGN_ORG[0] + x) * SCALE, (SIGN_ORG[1] + y) * SCALE, (SIGN_ORG[2] + v[2]) * SCALE)
    me = bpy.data.meshes.new('haven sign ' + state)
    me.from_pydata([world(v) for v in verts], [], faces); me.update()
    rel = 'model_export/tod_haven/_images/i_tod_haven_sign_10%s.png' % ('_dark' if state == 'corrupt' else '')
    scale = manifest['signs']['scale_rgb']['dark' if state == 'corrupt' else 'safe']
    me.materials.append(emissive_transparent('review | sign ' + state, rel, scale, cull=False))
    uv = me.uv_layers.new()
    for poly, coord in zip(me.polygons, uvs):
        for li, t in zip(poly.loop_indices, coord): uv.data[li].uv = t
    ob = bpy.data.objects.new(me.name, me); sc.collection.objects.link(ob)
    return ob


def guard_markers(state):
    """the guardians' spawn spots: red body-sized markers (the fight) in the corrupted state only"""
    obs = []
    if state != 'corrupt':
        return obs
    mt = bpy.data.materials.new('review | guardian marker'); mt.use_nodes = True
    p = mt.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (.5, .02, .02, 1); p.inputs['Emission Color'].default_value = (1, .2, .1, 1); p.inputs['Emission Strength'].default_value = 2
    for i, (gx, gy) in enumerate(GUARDS):
        bpy.ops.mesh.primitive_cylinder_add(radius=16 * SCALE, depth=72 * SCALE, location=(gx * SCALE, gy * SCALE, (Z + 36) * SCALE))
        ob = bpy.context.active_object; ob.name = 'guardian spot %d' % i
        ob.data.materials.append(mt); obs.append(ob)
    return obs


def look(eye, target, lens):
    cam.data.lens = lens
    cam.location = Vector(eye) * SCALE
    cam.rotation_euler = (Vector(target) * SCALE - cam.location).to_track_quat('-Z', 'Y').to_euler()


SHOTS = [
    ('porch', (-200, -150, Z + 60), (CX + 40, CY, Z + 160), 16),      # the way in: through the arch toward the field and the S wall sign
    ('loggia', (CX, CY + 300, Z + 60), (CX, -235, Z + 300), 18),       # from the north loggia (v4: inside the big field), the sign face on through the dome
    ('gallery', (CX + 170, CY + 180, Z + 330), (CX, CY - 60, Z + 120), 20),   # from the galleries' corner above, down into the heart
]
renders = {}
for state in ('corrupt', 'safe'):
    show(dome, state == 'safe')
    show(dark_dome, state == 'corrupt')
    extras = [sign_card(state)] + guard_markers(state)
    for stem, eye, target, lens in SHOTS:
        look(eye, target, lens)
        name = 'state_%s_%s.png' % (state, stem)
        sc.render.filepath = str(OUT / name); check(); bpy.ops.render.render(write_still=True)
        renders[name] = hashlib.sha256((OUT / name).read_bytes()).hexdigest()
    for ob in extras: bpy.data.objects.remove(ob, do_unlink=True)

receipt = {'schema': 1, 'engine': 'Blender EEVEE (4.2)', 'scene': 'haven_review.blend (tools/haven/preview.py)',
           'sign_anchor': {'org': SIGN_ORG, 'yaw': SIGN_YAW}, 'guard_spots': GUARDS,
           'dome_dark_sha256': hashlib.sha256((ROOT / 'model_export/tod_haven/_images/i_tod_haven_field_dark.png').read_bytes()).hexdigest(),
           'dome_dark_mesh': 'tod_haven_dome_dark_lod0.xmodel_bin (v5: the breached mesh on the cracked-pane atlas)',
           'dome_dark_mesh_sha256': hashlib.sha256((ROOT / 'model_export/tod_haven/tod_haven_dome_dark_lod0.xmodel_bin').read_bytes()).hexdigest(),
           'sign_sha256': hashlib.sha256((ROOT / 'model_export/tod_haven/tod_haven_sign.xmodel_bin').read_bytes()).hexdigest(),
           'limit': 'approximate emissive view; no bake, probes, exposure, bloom, effects or guardians (markers at their spots)',
           'images': renders}
(OUT / 'states.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('STATES_PREVIEW_COMPLETE', json.dumps(list(renders)), flush=True)
