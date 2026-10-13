"""THE HAVEN review (docs/202 v2, THE HEART): the floor-10 safe zone in Blender, before the native build.

What is REAL here: every brush face around the haven as the generator emitted it
(tools/haven/review_scene.js), the map's own kit materials and maps (the shared
APPROXIMATE fullspec view, tools/art_cohesion/native_preview.py), the shipping
force-field dome (model_export/tod_haven, its field texture as emission + alpha the
way lit_emissive_transparent draws it, at the base material's scaleRGB), the map's
light entities at their origins and colours, and player-eye cameras 60 units over the
floor. What is NOT: BO3's lighting bake, probes, exposure, bloom and the effects (the
ambient motes, the crossing ripple); the stock machines (perk, PaP, altar, crate) are
labelled blocks at their real anchors and footprints. The look in game is the user's
call; this is the design review.

    "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe" --background --factory-startup --python tools/haven/preview.py

Writes art/haven/review/{approach,inside,loggia,gallery,pad,plan}.png + haven_review.blend + preview.json.
The plan is a SECTION: the camera's near clip cuts the hall 150 over its floor, so the
flights and the ceiling above do not hide it.
Held while the game or any native compiler runs (tools/dealer_presence/process_guard.py).
"""
from pathlib import Path
import bpy, json, sys, math, hashlib
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/haven/review'
sys.path.insert(0, str(ROOT / 'tools/dealer_presence'))
from process_guard import check
check()
sys.path.insert(0, str(ROOT / 'tools'))
from art_cohesion.native_preview import fullspec, fields, DESCRIPTION
import os
sys.path.insert(0, str(Path(os.environ['APPDATA']) / 'Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel

SCALE = .0254
scene_data = json.loads((OUT / 'scene.json').read_text())
kit = json.loads((ROOT / 'tools/art_cohesion/crown_materials.json').read_text())['materials']
Z = scene_data['z']

for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
sc = bpy.context.scene

# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
mats = {}
def kit_mat(name):
    if name not in mats:
        if name.startswith('tod_cc_'):
            mats[name] = fullspec(ROOT / 'source_data/tod_surface.gdt', name, ROOT / 'model_export/tod_surface/_images')
        else:
            m = bpy.data.materials.new('Unmapped ' + name); m.use_nodes = True
            m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.05, .05, .06, 1)
            mats[name] = m
    return mats[name]

def flat(name, rgb, emit=0.0, rough=.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough
    if emit:
        p.inputs['Emission Color'].default_value = (*rgb, 1); p.inputs['Emission Strength'].default_value = emit
    return m

def field_material(scale_rgb, tint=(.85, 1, 1)):
    """lit_emissive_transparent: colorTint 0 0 0 (no lit diffuse), colorMap00 = the glow,
    alpha = coverage, scaleRGB = brightness. The texture's own alpha drives the blend."""
    f = fields(ROOT / 'art/haven/tod_haven.gdt', 'mtl_tod_haven_field')
    m = bpy.data.materials.new('Native approximation | mtl_tod_haven_field'); m.use_nodes = True
    m['preview_limit'] = DESCRIPTION; m['native_fields'] = str(f)
    n, l = m.node_tree.nodes, m.node_tree.links; n.clear()
    out = n.new('ShaderNodeOutputMaterial')
    tex = n.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(ROOT / 'model_export/tod_haven/_images/i_tod_haven_field.png'), check_existing=True)
    tex.interpolation = 'Linear'; tex.extension = 'EXTEND'
    mul = n.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
    mul.inputs[2].default_value = (*tint, 1)
    l.new(tex.outputs['Color'], mul.inputs[1])
    em = n.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = float(scale_rgb)
    l.new(mul.outputs[0], em.inputs['Color'])
    tr = n.new('ShaderNodeBsdfTransparent')
    mix = n.new('ShaderNodeMixShader')
    l.new(tex.outputs['Alpha'], mix.inputs['Fac']); l.new(tr.outputs[0], mix.inputs[1]); l.new(em.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'BLENDED'
    # the native field is single-sided like every BO3 model face: the dome is two
    # shells (outer faces out, inner faces in), so from inside you look through ONE
    # layer and from outside through two. Culling the back faces draws exactly that.
    m.use_backface_culling = True
    return m

# ---------------------------------------------------------------------------
# the map's brushes (one object, a slot per material)
# ---------------------------------------------------------------------------
def build_world():
    verts, faces, slot_of, uvs, face_mat = [], [], {}, [], []
    for b in scene_data['brushes']:
        for f in b['faces']:
            start = len(verts)
            verts.extend(f['v']); faces.append(list(range(start, len(verts))))
            mat = f['mat']
            if mat not in slot_of: slot_of[mat] = len(slot_of)
            face_mat.append(slot_of[mat])
            size = kit.get(mat.removeprefix('tod_cc_'), {}).get('size', 256)
            axis = max(range(3), key=lambda i: abs(f['n'][i]))
            uvs.append([((v[1] if axis == 0 else v[0]) / size, (v[1] if axis == 2 else v[2]) / size) for v in f['v']])
    me = bpy.data.meshes.new('haven floor 10 world')
    me.from_pydata([tuple(c * SCALE for c in v) for v in verts], [], faces); me.update()
    for mat in slot_of: me.materials.append(kit_mat(mat))
    uv = me.uv_layers.new()
    for poly, s, coord in zip(me.polygons, face_mat, uvs):
        poly.material_index = s
        for li, t in zip(poly.loop_indices, coord): uv.data[li].uv = t
    ob = bpy.data.objects.new(me.name, me); sc.collection.objects.link(ob)
    return ob

# ---------------------------------------------------------------------------
# the shipping dome (PyCoD reads the exported xmodel_bin)
# ---------------------------------------------------------------------------
def build_dome(name, scale_rgb):
    m = xmodel.Model(); m.LoadFile_Bin(str(ROOT / 'model_export/tod_haven/tod_haven_dome_lod0.xmodel_bin'), split_meshes=True)
    c = scene_data['dome']['centre']
    verts, faces, uvs = [], [], []
    for mesh in m.meshes:
        base = len(verts)
        verts.extend(v.offset for v in mesh.verts)
        for f in mesh.faces:
            faces.append([base + fv.vertex for fv in f.indices])
            uvs.append([(fv.uv[0], 1 - fv.uv[1]) for fv in f.indices])
    me = bpy.data.meshes.new(name)
    me.from_pydata([((v[0] + c[0]) * SCALE, (v[1] + c[1]) * SCALE, (v[2] + c[2]) * SCALE) for v in verts], [], faces); me.update()
    me.materials.append(field_material(scale_rgb))
    uv = me.uv_layers.new()
    for poly, coord in zip(me.polygons, uvs):
        for li, t in zip(poly.loop_indices, coord): uv.data[li].uv = t
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob

# ---------------------------------------------------------------------------
# the stock machines: labelled blocks at their real anchors
# ---------------------------------------------------------------------------
MACHINE = {'pap': ((.32, .10, .45), 'PACK-A-PUNCH'), 'station': ((.75, .62, .30), 'HEAVENLY ALTAR'),
           'crate': ((.25, .35, .20), 'AMMO CRATE'), 'perk_a': ((.55, .12, .10), 'PERK PAD'), 'perk_b': ((.10, .30, .55), 'PERK PAD')}
def build_machines():
    obs = []
    for f in scene_data['furniture']:
        rgb, label = MACHINE[f['key']]
        half, back, h = f['half'], f['back'], f['h']
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object; ob.name = 'placeholder ' + label + ' ' + f['key']
        ob.scale = (back * 2 * SCALE, half * 2 * SCALE, h * SCALE)
        face = math.radians(f['face'])
        # the block's +X is its front (the machine faces `face`); its back sits `back` behind the anchor
        ob.rotation_euler = (0, 0, face)
        ob.location = (f['org'][0] * SCALE, f['org'][1] * SCALE, (f['org'][2] + h / 2) * SCALE)
        ob.data.materials.append(flat('Placeholder ' + label, rgb, emit=.4, rough=.4))
        obs.append(ob)
    tp = scene_data['teleporter']
    bpy.ops.mesh.primitive_cylinder_add(radius=96 * SCALE, depth=14 * SCALE, location=(tp[0] * SCALE, tp[1] * SCALE, (tp[2] + 7) * SCALE))
    ob = bpy.context.active_object; ob.name = 'placeholder TELEPORTER (tod_teleporter)'
    ob.data.materials.append(flat('Placeholder teleporter', (.2, .9, 1), emit=1.5)); obs.append(ob)
    return obs

# ---------------------------------------------------------------------------
# the map's lights (approximate energy from radius + stops), a night world
# ---------------------------------------------------------------------------
def build_lights():
    for L in scene_data['lights']:
        d = bpy.data.lights.new(L['name'], 'POINT')
        d.color = L['color'][:3]
        d.energy = (2 ** (L['stops'] - 8.0)) * (L['radius'] * SCALE) ** 2 * 9   # ~ a few W/m2 at half the radius
        d.shadow_soft_size = .25
        d.use_custom_distance = True; d.cutoff_distance = L['radius'] * SCALE * 1.25
        o = bpy.data.objects.new(L['name'], d); sc.collection.objects.link(o)
        o.location = tuple(v * SCALE for v in L['origin'])
    world = bpy.data.worlds.new('Night review sky'); world.use_nodes = True; sc.world = world
    bg = world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (.012, .014, .03, 1); bg.inputs[1].default_value = 1.0
    sun = bpy.data.lights.new('Review moonlight (no BO3 equivalent)', 'SUN'); sun.energy = .35; sun.color = (.55, .62, 1); sun.angle = .3
    so = bpy.data.objects.new(sun.name, sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(55), 0, math.radians(-35))

world_ob = build_world()
dome = build_dome('haven dome (tod_haven_dome)', 4.0)
machines = build_machines()
build_lights()

camd = bpy.data.cameras.new('Player eye'); cam = bpy.data.objects.new(camd.name, camd); sc.collection.objects.link(cam); sc.camera = cam
camd.lens = 18; camd.clip_start = .01; camd.clip_end = 2000
sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1600, 900, 100
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = .6
try:
    sc.eevee.use_bloom = True
except AttributeError:
    pass
sc.eevee.taa_render_samples = 64

C = scene_data['dome']['centre']
def look(eye, target, lens=18):
    camd.lens = lens
    cam.location = Vector(eye) * SCALE
    cam.rotation_euler = (Vector(target) * SCALE - cam.location).to_track_quat('-Z', 'Y').to_euler()

VIEWS = {
    # coming down the tower: on the SW landing, looking through the porch archway into the hall
    'approach': ((-340, -250, Z + 60), (C[0], C[1], Z + 90), 16),
    # v4: INSIDE the field in its open south-east quarter, looking across the machines' ring and the pad to the far
    # side of the dome (does the lattice stay see-through from inside a field this big?)
    'inside': ((250, -110, Z + 60), (-40, 230, Z + 110), 14),
    # v4: from the north-east corner OUTSIDE the field (beside a post and the risers), across the dome to the porch
    'loggia': ((372, 352, Z + 60), (-60, -80, Z + 110), 14),
    # coming down the next lap's E flight (tread 9), a player's eye over its sloped handrail: the dome passes under it
    'gallery': ((276, 16, Z + 360), (0, -20, Z + 200), 16),
    # at the up-riders' arrival, looking south over the teleporter to the PaP and the porch
    'pad': ((C[0], C[1] + 208, Z + 60), (C[0] - 60, C[1] - 200, Z + 60), 16),
}
renders = {}
for name, (eye, target, lens) in VIEWS.items():
    look(eye, target, lens)
    sc.render.filepath = str(OUT / (name + '.png')); check(); bpy.ops.render.render(write_still=True)
    renders[name + '.png'] = hashlib.sha256((OUT / (name + '.png')).read_bytes()).hexdigest()

# a top-down SECTION plan (orthographic): the near clip cuts 150 over the hall floor
camd.type = 'ORTHO'; camd.ortho_scale = 1000 * SCALE
cam.location = Vector((90, 90, Z + 1500)) * SCALE; cam.rotation_euler = (0, 0, 0)
camd.clip_start = (1500 - 150) * SCALE
sc.render.resolution_x, sc.render.resolution_y = 1200, 1200
sc.render.filepath = str(OUT / 'plan.png'); check(); bpy.ops.render.render(write_still=True)
renders['plan.png'] = hashlib.sha256((OUT / 'plan.png').read_bytes()).hexdigest()
camd.type = 'PERSP'; camd.clip_start = .01

# not packed: the scene references the repo's own maps by path (a packed copy would add ~100 MB to the repo)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'haven_review.blend'))
receipt = {
    'schema': 1, 'engine': 'Blender EEVEE (4.2)', 'limit': DESCRIPTION + '; real emitted haven faces + the shipping dome; '
    'BO3 bake / probes / exposure / bloom / effects not reproduced; stock machines are labelled blocks',
    'scene_sha256': hashlib.sha256((OUT / 'scene.json').read_bytes()).hexdigest(),
    'dome_sha256': hashlib.sha256((ROOT / 'model_export/tod_haven/tod_haven_dome_lod0.xmodel_bin').read_bytes()).hexdigest(),
    'images': renders,
}
(OUT / 'preview.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('HAVEN_PREVIEW_COMPLETE', json.dumps(renders), flush=True)
