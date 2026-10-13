"""MCP step 05: bake the emitter atlas (2048) from the procedural zone materials of the level-0 parts.

  c  diffuse            sRGB   EMIT bake of the zone's diffuse channel (linear values -> stored as sRGB codes)
  s  specular F0        sRGB   EMIT bake of the zone's fullspec specular colour
  g  gloss              linear EMIT bake of the gloss channel (relative to glossRange 0..12)
  e  emission           sRGB   EMIT bake of emission / EMISSION_SCALE (the material's scaleRGB restores it)
  n  normal             linear Cycles NORMAL bake, tangent space, DirectX green (NEG_Y) - the relief from zones.py
Send with CHANNELS=c,s (etc.) to stay inside the 180 s MCP answer window; every call rebuilds the same bake target
from the master (deterministic) and writes model_export/tod_wunderstrahl/_images/i_tod2_ws_emitter_<ch>.png with the
deterministic PNG writer, then records hashes in art/wunderstrahl/engine_kit/bake.json.
"""
import bpy, importlib, json, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, blendlib, materials, emitter, zones, pngio
for m in (common, blendlib, materials, emitter, zones, pngio):
    importlib.reload(m)

CHANNELS = globals().get('CHANNELS', 'c,s,g,e,n').split(',')
SIZE = 2048
bpy.ops.wm.open_mainfile(filepath=str(common.ART / 'wunderstrahl.blend'))
scene = bpy.context.scene
device = blendlib.setup_render(scene, samples=96, glare=False)
parts = [ob for ob in scene.objects if ob.get('ws_part') and ob.get('ws_level') == 0]
assert parts, 'no emitter parts in the master'
for ob in scene.objects:
    ob.select_set(False)
copies = []
for ob in parts:
    c = ob.copy(); c.data = ob.data.copy(); scene.collection.objects.link(c); copies.append(c)
layer = scene.view_layers[0]
with bpy.context.temp_override(window=bpy.context.window_manager.windows[0], scene=scene, view_layer=layer,
                               active_object=copies[0], object=copies[0], selected_objects=copies,
                               selected_editable_objects=copies):
    bpy.ops.object.join()
assert len([o for o in scene.objects if o.name.startswith(copies[0].name.split('.')[0])]) >= 1
target = copies[0]; target.name = 'WS emitter | bake target'
for ob in scene.objects:
    ob.select_set(False)
target.hide_set(False); target.hide_render = False; target.select_set(True); layer.objects.active = target
mats = [m for m in target.data.materials]
record_path = common.KIT / 'bake.json'
record = common.read_json(record_path) if record_path.exists() else dict(textures={})
for ch in CHANNELS:
    t = time.time()
    linear = ch in ('g', 'n')
    name = 'i_tod2_ws_emitter_' + ch
    old = bpy.data.images.get(name)
    if old:
        bpy.data.images.remove(old)
    img = bpy.data.images.new(name, SIZE, SIZE, alpha=False, float_buffer=False)
    img.colorspace_settings.name = 'Non-Color' if linear else 'sRGB'
    for m in mats:
        nt = m.node_tree
        for n in [n for n in nt.nodes if n.label == 'bake target']:
            nt.nodes.remove(n)
        node = nt.nodes.new('ShaderNodeTexImage'); node.label = 'bake target'; node.image = img
        node.location = (1200, -400); nt.nodes.active = node
        zones.set_channel(m, 'n' if ch == 'n' else ch)
    scene.cycles.samples = 24 if ch == 'n' else 128
    scene.render.bake.margin = 16; scene.render.bake.margin_type = 'EXTEND'; scene.render.bake.use_clear = True
    scene.render.bake.normal_space = 'TANGENT'
    scene.render.bake.normal_r = 'POS_X'; scene.render.bake.normal_g = 'NEG_Y'; scene.render.bake.normal_b = 'POS_Z'
    win = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=win, scene=scene, view_layer=layer, active_object=target, object=target,
                                   selected_objects=[target], selected_editable_objects=[target]):
        bpy.ops.object.bake(type='NORMAL' if ch == 'n' else 'EMIT')
    px = np.empty(SIZE * SIZE * 4, np.float32); img.pixels.foreach_get(px)
    arr = px.reshape(SIZE, SIZE, 4)[::-1].copy(); arr[..., 3] = 1.0
    if ch == 'n':
        # Safety net: a tangent normal must face out of its surface. Tilt is capped at ~81 degrees (z >= 0.15) so no
        # texel can shade inside-out (review pass 3 found Bevel-node inversions round buried caps, now removed at
        # the source; verify_art fails any texel under z 0.1 inside the used UVs).
        n = arr[..., :3] * 2.0 - 1.0
        low = n[..., 2] < 0.15
        if low.any():
            xy = n[..., :2][low]; ln = np.maximum(np.linalg.norm(xy, axis=1, keepdims=True), 1e-6)
            n[..., :2][low] = xy / ln * np.sqrt(1 - 0.15 ** 2)
            n[..., 2][low] = 0.15
            arr[..., :3] = (n + 1.0) * 0.5
        record['normal_clamped_texels'] = int(low.sum())
    out = common.IMG / (name + '.png')
    pngio.write_png(out, arr)
    record['textures'][out.name] = common.sha(out)
    print('WS_BAKED', ch, round(time.time() - t, 1), 's', 'mean', [round(float(x), 3) for x in arr[..., :3].reshape(-1, 3).mean(0)], flush=True)
for m in mats:
    zones.set_channel(m, 'preview')
record.update(master=common.rel(common.ART / 'wunderstrahl.blend'), master_sha256=common.sha(common.ART / 'wunderstrahl.blend'),
              atlas=common.rel(common.KIT / 'atlas.json'), atlas_sha256=common.sha(common.KIT / 'atlas.json'), size=SIZE,
              normal_convention='tangent space, DirectX (green = -Y)', emission_scale=zones.EMISSION_SCALE,
              samples=dict(n=24, other=128), device=device, triangles=len(target.data.polygons))
common.write_json(record_path, record)
if 'n' in CHANNELS:
    bpy.ops.wm.save_as_mainfile(filepath=str(common.ART / 'emitter_bake.blend'))
print('WS_05_BAKE', CHANNELS, 'device', device, flush=True)
