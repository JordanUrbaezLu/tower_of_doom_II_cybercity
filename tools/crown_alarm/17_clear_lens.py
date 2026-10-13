"""Actual Blender MCP authoring: clear lens alpha, unchanged RGB/glow/geometry.

Runs only against a current shipping snapshot. Reviews use imported native
housing/rotor binaries, not a different polished studio mesh.
"""
import bpy, hashlib, importlib.util, json, pathlib, re, sys
import numpy as np
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORK = ROOT / 'tmp/alarm_lens_repair'
BASE, STAGE = WORK / 'baseline', WORK / 'staged'
ART = STAGE / 'art/crown_alarm'
REVIEW = ART / 'lens_review'
REVIEW.mkdir(parents=True, exist_ok=True)
helper = STAGE / 'tools/crown_alarm/surface_realism.py'
if not helper.exists():
    helper = ROOT / 'tools/crown_alarm/surface_realism.py'
spec = importlib.util.spec_from_file_location('reviewed_alarm_surface', helper)
surface_realism = importlib.util.module_from_spec(spec)
spec.loader.exec_module(surface_realism)
xmodel = surface_realism.xmodel
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

manifest = json.loads((BASE / 'art/crown_alarm/manifest.json').read_text())
gdt = (BASE / 'source_data/tod_crown_alarm.gdt').read_text()
definitions = {n: dict(re.findall(r'"([^"\n]+)" "([^"\n]*)"', body))
               for n, kind, body in re.findall(r'"([^"\n]+)" \( "([^"\n]+).gdf" \)\s*\{(.*?)\n\t\}', gdt, re.S)}
definitions['mtl_tod_alarm_lens']['specColorTint'] = '.220916 .220916 .220916 1'
definitions['mtl_tod_alarm_lens']['specColorMap'] = '$black_specular'
# The old native material was invalid/reference-only. Reconstruct its source
# opacity with the same repaired valid shader used after; this is not a game
# fallback or a measured native before-state.
before_lens = dict(definitions['mtl_tod_alarm_lens'])
gdt, count = re.subn(r'("mtl_tod_alarm_lens" \( "material.gdf" \)\s*\{.*?"specColorTint" ")1 1 1 1(")',
                      r'\g<1>.220916 .220916 .220916 1\2', gdt, flags=re.S)
assert count == 1
gdt, count = re.subn(r'("mtl_tod_alarm_lens" \( "material.gdf" \)\s*\{.*?"specColorMap" ")i_tod_alarm_lens_s(")',
                      r'\g<1>$black_specular\2', gdt, flags=re.S)
assert count == 1
(STAGE / 'source_data/tod_crown_alarm.gdt').write_text(gdt)

def bind_lens(fields, folder):
    """Actual native masked dielectric formula, including the shipped tint."""
    mat = bpy.data.materials['mtl_tod_alarm_lens']
    surface_realism.bind_material(mat, fields, folder)
    f0 = surface_realism.native_lens_f0(fields)
    gloss = next(n for n in mat.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfAnisotropic')
    gloss.inputs['Color'].default_value = (*f0, 1)
    mat['preview_specular'] = 'Native $black_specular scalar mask=0; F0=.04 and diffuse factor=1. Gray32 is thermalHeatmap.'
    mat['native_f0'] = list(f0)
texrel = 'model_export/tod_crown_alarm/_images/i_tod_alarm_lens_c.png'
source = bpy.data.images.load(str(BASE / texrel), check_existing=False)
source.colorspace_settings.name = 'Non-Color'  # Read exact encoded native bytes.
w, h = source.size
pixels = np.array(source.pixels[:], np.float32).reshape(h, w, 4)
old_alpha = pixels[:, :, 3].copy()
# Transparent padding prevents fully opaque atlas gutters bleeding into mips.
pixels[:, :, 3] = .045
parts = manifest['surface_realism']['atlas_parts']
for name, entry in parts.items():
    if entry['material'] != 'mtl_tod_alarm_lens':
        continue
    assert entry['size'] == w
    x, y, size = entry['tile']
    pixels[y:y + size, x:x + size, 3] = .10 if 'dome' in name else .05
image = bpy.data.images.new('Clear ruby lens - native RGBA', width=w, height=h, alpha=True)
image.colorspace_settings.name = 'Non-Color'
image.pixels.foreach_set(pixels.ravel())
image.filepath_raw = str(STAGE / texrel)
image.file_format = 'PNG'
image.save()

for rel in ('art/crown_alarm/crown_alarm.blend', 'art/crown_alarm/visibility_review/high_fixture.blend'):
    bpy.ops.wm.open_mainfile(filepath=str(BASE / rel))
    bind_lens(definitions['mtl_tod_alarm_lens'], STAGE / 'model_export/tod_crown_alarm/_images')
    scene = bpy.context.scene
    scene['lens_repair'] = 'Clear ruby cover: dome alpha .10, optical ribs .05; transparent atlas gutters .045; valid stock black specular mask and dielectric tint. Native glow and geometry unchanged.'
    scene['preview_limit'] = 'Actual BO3 maps; approximate Blender BRDF. Native appearance awaits user playtest.'
    window = bpy.context.window_manager.windows[0]
    main_area = max(window.screen.areas, key=lambda a: a.width * a.height)
    main_area.type = 'VIEW_3D'
    main_area.spaces.active.region_3d.view_perspective = 'CAMERA'
    scene.cycles.preview_samples = 16
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.shading.type = 'RENDERED'
                area.spaces.active.shading.use_scene_world_render = True
                area.spaces.active.shading.use_scene_lights_render = True
    bpy.ops.wm.save_as_mainfile(filepath=str(STAGE / rel))
    # Rendered is saved for the user's preview, but authoring does not need a
    # second live viewport render competing with the controlled still renders.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.shading.type = 'SOLID'

# Retain the approved studio lights/floor; replace the modeled parts with the
# exact native binary export for before/after, rotation and distance inspection.
bpy.ops.wm.open_mainfile(filepath=str(ART / 'crown_alarm.blend'))
scene = bpy.context.scene
scene.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'SOLID'
for ob in scene.objects:
    if ob.type == 'MESH' and 'alarm_group' in ob:
        ob.hide_render = True
        ob.hide_viewport = True
for mat in list(bpy.data.materials):
    if mat.name in definitions:
        surface_realism.bind_material(mat, definitions[mat.name], STAGE / 'model_export/tod_crown_alarm/_images')
bind_lens(definitions['mtl_tod_alarm_lens'], STAGE / 'model_export/tod_crown_alarm/_images')

native_objects = []
def import_lod(lod):
    for ob in native_objects:
        bpy.data.objects.remove(ob, do_unlink=True)
    native_objects.clear()
    for asset, pivot in [('tod_crown_alarm_housing', 0), ('tod_crown_alarm_rotor_off', 26)]:
        row = next(r for r in manifest['models'] if r['asset'] == asset and r['lod'] == lod)
        model = xmodel.Model()
        model.LoadFile_Bin(str(BASE / row['file']), split_meshes=True)
        for part in model.meshes:
            verts = [tuple(Vector(v.offset) + Vector((0, 0, pivot))) for v in part.verts]
            faces = [tuple(f.indices[i].vertex for i in (0, 2, 1)) for f in part.faces]
            mesh = bpy.data.meshes.new('Native ' + part.name)
            mesh.from_pydata(verts, [], faces)
            mesh.update()
            uv = mesh.uv_layers.new(name='Native atlas')
            normals = []
            for polygon, face in zip(mesh.polygons, part.faces):
                polygon.use_smooth = True
                for loop, corner in zip(polygon.loop_indices, (face.indices[i] for i in (0, 2, 1))):
                    uv.data[loop].uv = (corner.uv[0], 1 - corner.uv[1])
                    normals.append(corner.normal)
            mesh.normals_split_custom_set(normals)
            name = model.materials[part.faces[0].material_id].name
            mesh.materials.append(bpy.data.materials[name])
            ob = bpy.data.objects.new('EXPORTED ' + part.name, mesh)
            scene.collection.objects.link(ob)
            native_objects.append(ob)

def state(on):
    for ob in native_objects:
        for slot in ob.material_slots:
            if slot.material.name.startswith('mtl_tod_alarm_lamp_'):
                slot.material = bpy.data.materials['mtl_tod_alarm_lamp_on' if on else 'mtl_tod_alarm_lamp_off']

scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.cycles.transparent_max_bounces = 24
scene.cycles.max_bounces = 12
scene.render.threads_mode = 'FIXED'
scene.render.threads = 6
scene.render.resolution_x = 900
scene.render.resolution_y = 850
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.use_nodes = False  # No bloom obscures the inside during the primary review.
cam = scene.camera
cam.location = (78, -104, 58)
cam.rotation_euler = (Vector((0, 0, 26)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 64
import_lod(0)
for version, folder in [('before', BASE), ('after', STAGE)]:
    bind_lens(before_lens if version == 'before' else definitions['mtl_tod_alarm_lens'], folder / 'model_export/tod_crown_alarm/_images')
    for on in (False, True):
        state(on)
        scene.render.filepath = str(REVIEW / (version + ('_on' if on else '_off') + '.png'))
        bpy.ops.render.render(write_still=True)

# A lower LOD with the same native lens and a practical smaller screen footprint.
import_lod(2)
cam.data.ortho_scale = 190
for on in (False, True):
    state(on)
    scene.render.filepath = str(REVIEW / ('distance' + ('_on' if on else '_off') + '.png'))
    bpy.ops.render.render(write_still=True)
state(False)
import_lod(0)
cam.data.ortho_scale = 72
scene['review_geometry'] = 'Imported unchanged native LOD0 housing and rotor, native UV/normals; distance images use LOD2.'
scene['before_comparison'] = 'Reconstructed original source alpha using the repaired valid shader; not the invalid native fallback.'
bpy.ops.wm.save_as_mainfile(filepath=str(REVIEW / 'native_preview.blend'))

manifest['textures']['i_tod_alarm_lens_c.png'] = sha(STAGE / texrel)
manifest['gdt_sha256'] = sha(STAGE / 'source_data/tod_crown_alarm.gdt')
manifest['lens_repair'] = {'revision': '2026-10-01 clear glass', 'authoring': 'Actual Blender MCP execute_blender_code',
    'dome_alpha': .10, 'rib_alpha': .05, 'padding_alpha': .045,
    'rgb_unchanged': True, 'native_geometry_unchanged': True, 'glow_unchanged': True,
    'specColorTint': '.220916 .220916 .220916 1', 'specColorMap': '$black_specular',
    'native_specular_mask': 0.0,
    'native_f0_after': .04,
    'before_comparison': 'Reconstructed original source alpha using the repaired valid shader; not the invalid native fallback.',
    'review': 'lens_review', 'native_visual_verified': False, 'native_playtested': False}
(ART / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
receipt = dict(manifest['lens_repair'], source_sha256=sha(BASE / texrel), output_sha256=sha(STAGE / texrel),
               old_alpha_range=[float(old_alpha.min()), float(old_alpha.max())],
               pre_finish_preview_sha256=sha(REVIEW / 'native_preview.blend'),
               renders={p.name: sha(p) for p in REVIEW.glob('*.png')})
(REVIEW / 'authoring.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('CLEAR_LENS_AUTHORED', json.dumps(receipt), flush=True)
