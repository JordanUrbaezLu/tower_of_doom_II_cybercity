"""companion_maps/bake.py - bake the geometry sources the companion texture maps are authored from (W2A, 2026-10-05).

WHY (tmp/design_review/findings.md, user 2026-10-04: "the ai companions dont look correct at all"): the Talon's wing
set, most of the Cerberus's per-part maps (normal / occlusion / reveal / gloss / emissive) and the Civil Protector's
upper-shell, arm and chassis maps exist in no readable source - not the T7 pack, not either tools root, not a sibling
repo (searched 2026-10-05). compose.py AUTHORS them from each model's own UVs; this script bakes its geometry inputs.

RUN (background Blender 4.2, which carries the PyCoD addon; CPU only; ~1 min for everything):
  "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe" --background --factory-startup
      --python tools/companion_maps/bake.py -- [--out DIR] [--only model:group,...]
Needs the installer's pack cache (tmp/partner_assets/, written by tools/partner/install_assets.py).
Writes, per UV set (one texture layout shared by the materials a GROUPS rule selects):
  <model>_<group>_ao.png      ambient occlusion of the group's own faces (T7 per-part convention), 8-bit grey, linear
  <model>_<group>_bevel.png   tangent-space normal of a Cycles Bevel of the low-poly surface (rounded hard edges),
                              GREEN = +V up (OpenGL / Blender) - compose.py converts to the T7 maps' convention
  <model>_<group>_mask.png    coverage: 255 where a face of the group lands (no bake margin), else 0
A face's UVs are shifted by the integer part of its UV centre: the T7 layouts park mirrored islands one tile over
(u 1..2, -1..0) and the engine samples them WRAPPED, so the bake lands them where the texture is read.
Each group bakes on its OWN object (its faces only): a Cycles bake with several target images on one object wrote
only the image of material slot 0 (measured 2026-10-05).

Safety: refuses to run while BlackOps3 / Radiant / cod2map64 / linker_modtools / gdtdb run (16 GB machine).
"""
import bpy, os, sys, math, subprocess, json, hashlib

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PRIV = r'C:\BO3Tools\TOD2Cybercity'
sys.path.insert(0, os.path.expanduser('~/AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel  # noqa: E402

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default


OUT = os.path.abspath(arg('--out', os.path.join(REPO, 'art', 'companion_maps', 'bakes')))
ONLY = set(x for x in (arg('--only', '') or '').split(',') if x)

# The donors the installer builds the companions from, and the Protector donor (the partner IS this mesh/rig/UVs).
PACK = os.path.join(REPO, 'tmp', 'partner_assets', 'T7 Assets V2.8', 'model_export', '_midgetblaster', 'props')
MODELS = {
    'talon': os.path.join(PACK, 't7_veh', 'veh_t7_drone_attack_gun_darkcolor', 'veh_t7_drone_attack_gun_darkcolor_LOD0.xmodel_bin'),
    'cerberus': os.path.join(PACK, 't7_veh', 'veh_t7_drone_amws_armored_mp_dark', 'veh_t7_drone_amws_armored_mp_dark_LOD0.xmodel_bin'),
    'protector': os.path.join(PRIV, 'model_export', 'black_ops_3', 'c_zom_zod_robot_protector',
                              'c_zom_zod_robot_protector_gold_fb.xmodel_bin'),
}
# group -> (texture size, rule). A rule picks the ORIGINAL material names (the donor's) that share one texture layout:
# ('prefix', [name fragments], [excluded fragments]) or ('names', [exact names]). Decal overlays never bake (their
# quads float over the hull and would shadow it).
GROUPS = {
    'talon': {
        'wing_gun': (512, ('prefix', ['drone_attack_wing_gun_'], [])),
        'body': (512, ('prefix', ['drone_attack_body_'], [])),        # has real clean maps: the calibration set
    },
    'cerberus': {
        'armored_hull': (512, ('prefix', ['amws_armored_hull_'], [])),
        'armored_turret': (512, ('prefix', ['amws_armored_turret_'], ['grenade02'])),
        'armored_treadcovers': (512, ('prefix', ['amws_armored_treadcovers_'], [])),
        'armored_swingarm': (512, ('prefix', ['amws_armored_swingarm_'], [])),
        'launcher': (512, ('prefix', ['amws_launcher_'], [])),
        'minigun': (512, ('prefix', ['amws_minigun_'], [])),
        'turret_grenade': (256, ('prefix', ['amws_armored_turret_grenade02'], [])),
    },
    'protector': {
        'upper': (1024, ('names', ['mtl_c_t7_zom_zod_robot_upper_gold', 'mtl_c_t7_zom_zod_robot_lights'])),
        'arm': (1024, ('names', ['mtl_c_t7_zom_zod_robot_arm_gold'])),
        'pelvis': (512, ('names', ['mtl_c_t7_nrc_robot_grunt_chassis_pelvis'])),
        'torso': (256, ('names', ['mtl_c_t7_nrc_robot_grunt_chassis_torso'])),
        'leg': (1024, ('names', ['mtl_c_t7_zom_zod_robot_leg_gold'])),
        'limbs': (1024, ('names', ['mtl_c_t7_zom_zod_robot_limbs_gold'])),
        'foot': (512, ('names', ['mtl_c_t7_zom_zod_robot_foot_gold'])),
    },
}
# AO reach and bevel radius in model units (inches) for a model the AMWS's size (REF_SIZE); scaled per model.
AO_DIST = float(arg('--ao-dist', '4.0'))
BEVEL_R = float(arg('--bevel', '0.12'))
SAMPLES = int(arg('--samples', '128'))
# The T7 per-part occlusion maps are SELF occlusion (each part's own cavities; a wheel under the tread cover still
# reads white in i_veh_t7_drone_amws_wheels_o), so the default bake matches that; --whole-ao lets the rest of the
# model shadow the part too (a look test only).
WHOLE_AO = '--whole-ao' in ARGS
REF_SIZE = 58.0


def members(rule, names):
    if rule[0] == 'names':
        return [n for n in names if n in rule[1]]
    return [n for n in names if 'decal' not in n and any(f in n for f in rule[1]) and not any(x in n for x in rule[2])]


def busy():
    try:
        out = subprocess.run(['tasklist'], capture_output=True, text=True).stdout.lower()
    except Exception:
        return None
    for n in ('blackops3.exe', 'radiant_modtools.exe', 'cod2map64.exe', 'linker_modtools.exe', 'gdtdb.exe'):
        if n in out:
            return n
    return None


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.seed = 7
    sc.cycles.use_denoising = False
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = 6
    sc.world = bpy.data.worlds.new('w')
    return sc


def read(path):
    """-> (verts, [(corner vertex ids, corner uvs, corner normals, material name)], all material names, size)"""
    mdl = xmodel.Model()
    mdl.LoadFile_Bin(path, split_meshes=False)
    src = mdl.meshes[0]
    names = [m.name for m in mdl.materials]
    verts = [tuple(v.offset) for v in src.verts]
    faces = []
    for f in src.faces:
        name = names[f.material_id]
        if 'decal' in name:
            continue
        order = (0, 2, 1)
        uvs = [f.indices[i].uv for i in order]
        cu = math.floor(sum(u for u, v in uvs) / 3.0)
        cv = math.floor(sum(v for u, v in uvs) / 3.0)
        faces.append(([f.indices[i].vertex for i in order], [(u - cu, 1.0 - (v - cv)) for u, v in uvs],
                      [tuple(f.indices[i].normal) for i in order], name))
    size = max(max(v[i] for v in verts) - min(v[i] for v in verts) for i in range(3))
    return verts, faces, names, size


def build(label, verts, faces, mats):
    """An object of these faces; material slot i = mats[i] (a bpy material)."""
    me = bpy.data.meshes.new(label)
    me.from_pydata(verts, [], [f[0] for f in faces])
    me.update()
    uv = me.uv_layers.new(name='uv')
    normals = []
    for poly, f in zip(me.polygons, faces):
        poly.use_smooth = True
        for li, u in zip(poly.loop_indices, f[1]):
            uv.data[li].uv = u
        normals.extend(f[2])
    me.normals_split_custom_set(normals)
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(label, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def target_material(image, kind, bevel_r):
    mat = bpy.data.materials.new('target_' + kind)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    if kind == 'mask':
        sh = nt.nodes.new('ShaderNodeEmission')
        sh.inputs['Strength'].default_value = 1.0
    else:
        sh = nt.nodes.new('ShaderNodeBsdfDiffuse')
        if kind == 'bevel':
            bev = nt.nodes.new('ShaderNodeBevel')
            bev.samples = 16
            bev.inputs['Radius'].default_value = bevel_r
            nt.links.new(bev.outputs[0], sh.inputs['Normal'])
    nt.links.new(sh.outputs[0], out.inputs[0])
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = image
    nt.nodes.active = tex
    return mat


def bake_group(model, g, size, mem, verts, faces, scale):
    out = {}
    for kind in ('ao', 'bevel', 'mask'):
        reset()
        im = bpy.data.images.new('%s_%s_%s' % (model, g, kind), size, size, alpha=False)
        im.colorspace_settings.name = 'Non-Color'
        tgt = build('target', verts, [f for f in faces if f[3] in mem], [target_material(im, kind, BEVEL_R * scale)])
        if kind == 'ao' and WHOLE_AO:
            occ = bpy.data.materials.new('occluder')
            build('occluder', verts, [f for f in faces if f[3] not in mem], [occ])
        sc = bpy.context.scene
        for o in sc.objects:
            o.select_set(False)
        bpy.context.view_layer.objects.active = tgt
        tgt.select_set(True)
        sc.render.bake.use_clear = True
        sc.render.bake.margin_type = 'EXTEND'
        if kind == 'ao':
            sc.cycles.samples = SAMPLES
            sc.render.bake.margin = 6
            sc.world.light_settings.distance = AO_DIST * scale
            bpy.ops.object.bake(type='AO')
        elif kind == 'bevel':
            sc.cycles.samples = 16
            sc.render.bake.margin = 6
            sc.render.bake.normal_space = 'TANGENT'
            bpy.ops.object.bake(type='NORMAL')
        else:
            sc.cycles.samples = 1
            sc.render.bake.margin = 0
            bpy.ops.object.bake(type='EMIT')
        path = os.path.join(OUT, '%s_%s_%s.png' % (model, g, kind))
        im.filepath_raw = path      # byte buffer tagged Non-Color: written raw, no view transform
        im.file_format = 'PNG'
        im.save()
        out[kind] = path
    return out


def main():
    b = busy()
    if b:
        raise SystemExit('companion_maps/bake: %s is running - wait (16 GB machine)' % b)
    os.makedirs(OUT, exist_ok=True)
    rec = os.path.join(OUT, '_bake.json')
    record = json.load(open(rec)) if os.path.exists(rec) else {}
    record.update({'ao_dist': AO_DIST, 'bevel_r': BEVEL_R, 'samples': SAMPLES, 'whole_ao': WHOLE_AO,
                   'blender': bpy.app.version_string})
    record.setdefault('models', {})
    for model, path in MODELS.items():
        todo = {g: v for g, v in GROUPS[model].items() if not ONLY or model + ':' + g in ONLY or model in ONLY}
        if not todo:
            continue
        verts, faces, names, size = read(path)
        scale = size / REF_SIZE
        entry = record['models'].setdefault(model, {'groups': {}})
        entry.update({'binary': os.path.relpath(path, REPO) if path.startswith(REPO) else path, 'size': size,
                      'scale': scale, 'sha256': hashlib.sha256(open(path, 'rb').read()).hexdigest()})
        for g, (sz, rule) in todo.items():
            mem = members(rule, names)
            assert mem, (model, g)
            bake_group(model, g, sz, mem, verts, faces, scale)
            entry['groups'][g] = {'size': sz, 'materials': mem,
                                  'triangles': sum(1 for f in faces if f[3] in mem)}
            print('companion_maps/bake:', model, g, len(mem), 'materials')
    json.dump(record, open(rec, 'w'), indent=1, sort_keys=True)


main()
