"""01: the Dealer boss studio scene - the donor skeleton, the donor ghost, the stage.

Runs inside the VISIBLE Dealer boss studio (port 9899). Builds the Keeper's
animation skeleton (BO3 base zombie + robe chains + jaw + fingers) as a Blender
armature straight from the installed XMODEL_BIN, imports the Keeper body as a
translucent proportion ghost (never exported), and lays out collections, a dark
review stage and four review cameras. Units: 1 Blender unit = 1 BO3 inch; +X is
the character's FORWARD, +Z up, +Y the character's LEFT (BO3 model space).
"""
import sys, pathlib, json, math
import bpy
from mathutils import Vector, Matrix

ROOT = pathlib.Path(__file__).resolve().parents[2]
ART = ROOT / 'art/dealer_boss'; ART.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel

DONOR = ROOT / 'model_export/tod_keeper/c_zom_dlc4_keeper_fb.XMODEL_BIN'
scene = bpy.context.scene
if not scene.get('tod2_dealer_boss_studio'):
    raise RuntimeError('Not the Dealer boss studio')

# ---------------------------------------------------------------- scene reset
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in list(bpy.data.collections):
    bpy.data.collections.remove(coll)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.armatures, bpy.data.cameras, bpy.data.lights, bpy.data.images):
    for d in list(block):
        if d.users == 0:
            block.remove(d)
scene.unit_settings.system = 'NONE'
scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'SceneEEVEE') and bpy.app.version >= (4, 2) else 'BLENDER_EEVEE'
scene.render.resolution_x = 1600; scene.render.resolution_y = 1200; scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'
scene.render.image_settings.file_format = 'PNG'
scene.world = scene.world or bpy.data.worlds.new('Dealer studio world')
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.012, 0.010, 0.014, 1); bg.inputs[1].default_value = 0.25

COLLS = {}
for name in ['DEALER | 00 RIG (Keeper skeleton, exported bones)',
             'DEALER | 01 BODY - coat, cowl, sleeves (deforming)',
             'DEALER | 02 HEAD - hood, mask (deforming)',
             'DEALER | 03 HANDS - gloves, nails (deforming)',
             'DEALER | 04 GEAR - straps, vials, chains (deforming)',
             'DEALER | 90 STUDIO - exclude from export',
             'DEALER | 91 REFERENCE - Keeper ghost, never exported']:
    c = bpy.data.collections.new(name); scene.collection.children.link(c); COLLS[name[9:11]] = c

# ---------------------------------------------------------------- the skeleton
model = xmodel.Model(); model.LoadFile_Bin(str(DONOR), split_meshes=True)
arm = bpy.data.armatures.new('Keeper_skeleton')
rig = bpy.data.objects.new('DEALER_RIG | Keeper animation skeleton', arm)
COLLS['00'].objects.link(rig)
bpy.context.view_layer.objects.active = rig; rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for b in model.bones:
    eb = arm.edit_bones.new(b.name)
    eb.head = Vector(b.offset)
    # a short bone along the bind matrix's second axis keeps every joint visible without changing data
    eb.tail = Vector(b.offset) + Vector(b.matrix[1]) * 2.0
    eb.align_roll(Vector(b.matrix[2]))
    if b.parent >= 0:
        eb.parent = arm.edit_bones[model.bones[b.parent].name]
bpy.ops.object.mode_set(mode='OBJECT')
rig.show_in_front = True; arm.display_type = 'STICK'
rig['donor'] = str(DONOR.relative_to(ROOT)).replace('\\', '/')
rig['bones'] = len(model.bones)
# exported bone order and bind offsets, for the exporter and the gates
(ART / 'skeleton.json').write_text(json.dumps({
    'donor': rig['donor'],
    'bones': [{'id': i, 'name': b.name, 'parent': b.parent, 'offset': list(b.offset), 'matrix': [list(r) for r in b.matrix]} for i, b in enumerate(model.bones)]
}, indent=1))

# ---------------------------------------------------------------- the ghost
ghost_mat = bpy.data.materials.new('REF / Keeper ghost'); ghost_mat.use_nodes = True
p = ghost_mat.node_tree.nodes['Principled BSDF']
p.inputs['Base Color'].default_value = (0.25, 0.45, 0.6, 1); p.inputs['Alpha'].default_value = 0.18; p.inputs['Roughness'].default_value = 0.8
ghost_mat.blend_method = 'BLEND'; ghost_mat.diffuse_color = (0.25, 0.45, 0.6, 0.18)
bone_names = [b.name for b in model.bones]
for mi, sm in enumerate(model.meshes):
    me = bpy.data.meshes.new('ref_keeper_%d' % mi)
    me.from_pydata([v.offset for v in sm.verts], [], [[f.indices[k].vertex for k in (0, 2, 1)] for f in sm.faces])
    me.update(); me.materials.append(ghost_mat)
    ob = bpy.data.objects.new('REF | Keeper ' + model.materials[sm.faces[0].material_id].name.replace('mtl_c_zom_dlc4_keeper_', ''), me)
    COLLS['91'].objects.link(ob)
    for poly in me.polygons: poly.use_smooth = True
    # the donor's weights ride along: the Data Transfer modifiers of later steps read them
    for bn in bone_names: ob.vertex_groups.new(name=bn)
    for vi, v in enumerate(sm.verts):
        for bi, w in v.weights: ob.vertex_groups[bi].add([vi], w, 'REPLACE')
    ob.parent = rig; ob.modifiers.new('Keeper weights', 'ARMATURE').object = rig
    ob.hide_render = True; ob.display_type = 'WIRE' if mi in (6, 7) else 'SOLID'
    ob['reference_only'] = True

# ---------------------------------------------------------------- the stage
studio = COLLS['90']
def light(name, loc, color, energy, size, aim=(0, 0, 40), kind='AREA'):
    l = bpy.data.lights.new(name, kind); l.color = color; l.energy = energy
    if kind == 'AREA': l.size = size; l.shape = 'DISK'
    elif kind == 'SPOT': l.spot_size = math.radians(size); l.spot_blend = 0.6; l.shadow_soft_size = 6
    ob = bpy.data.objects.new(name, l); studio.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return ob
light('Studio | cool key', (140, -110, 150), (0.72, 0.76, 0.85), 26000, 60)
light('Studio | left fill', (-60, 160, 90), (0.55, 0.52, 0.6), 7000, 90)
light('Studio | red rim', (-150, 60, 95), (1.0, 0.08, 0.05), 22000, 40)
light('Studio | violet rim', (-120, -140, 70), (0.55, 0.12, 1.0), 12000, 40)
light('Studio | under floor red', (40, 0, 4), (1.0, 0.03, 0.02), 2500, 70, aim=(0, 0, 60))
floor_me = bpy.data.meshes.new('studio floor'); floor_me.from_pydata([(-400, -400, 0), (400, -400, 0), (400, 400, 0), (-400, 400, 0)], [], [(0, 1, 2, 3)]); floor_me.update()
floor_mat = bpy.data.materials.new('STUDIO / wet black floor'); floor_mat.use_nodes = True
fp = floor_mat.node_tree.nodes['Principled BSDF']; fp.inputs['Base Color'].default_value = (0.02, 0.02, 0.023, 1); fp.inputs['Roughness'].default_value = 0.28
floor_me.materials.append(floor_mat)
floor = bpy.data.objects.new('Studio | floor', floor_me); studio.objects.link(floor)
def camera(name, loc, aim, lens=50):
    c = bpy.data.cameras.new(name); c.lens = lens; c.clip_end = 5000
    ob = bpy.data.objects.new(name, c); studio.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return ob
hero = camera('CAM 01 | hero three-quarter', (175, -120, 62), (0, 0, 40), 55)
camera('CAM 02 | front full', (230, 0, 40), (0, 0, 38), 55)
camera('CAM 03 | side full', (10, -230, 40), (0, 0, 38), 55)
camera('CAM 04 | mask close', (46, -14, 70), (2, 0, 69.5), 85)
camera('CAM 05 | hands and nails', (60, -30, 42), (3, 2, 38), 70)
camera('CAM 06 | back', (-230, 40, 44), (0, 0, 38), 55)
scene.camera = hero

# ---------------------------------------------------------------- viewport
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            s = area.spaces.active; s.shading.type = 'MATERIAL'; s.overlay.show_overlays = True
            s.clip_end = 5000
            s.region_3d.view_location = (0, 0, 40); s.region_3d.view_distance = 190
            s.region_3d.view_rotation = hero.rotation_euler.to_quaternion()
scene['dealer_stage'] = '01_rig_reference'
scene['dealer_space'] = 'BO3 model space: +X forward, +Y left, +Z up, inches'
bpy.ops.wm.save_as_mainfile(filepath=str(ART / 'dealer_boss.blend'))
print(json.dumps({'stage': '01_rig_reference', 'bones': len(model.bones), 'ghost_meshes': len(model.meshes),
                  'height_in': round(max(v.offset[2] for m in model.meshes for v in m.verts), 2), 'blend': str(ART / 'dealer_boss.blend')}))
