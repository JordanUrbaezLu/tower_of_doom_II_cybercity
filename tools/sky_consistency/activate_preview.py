"""Restore the finished HDR viewport after Blender resets shading on file load.

Run with --python when opening consistency_preview.blend, or through the
dedicated MCP studio. This changes display state only; never resaves the asset.
"""
import hashlib
import json
import pathlib
import bpy

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXPECTED = ROOT / 'art/sky3d/consistency_preview.blend'
assert pathlib.Path(bpy.data.filepath).resolve() == EXPECTED.resolve(), 'Open the finished sky preview first'
sc = bpy.context.scene
assert sc.world and sc.world.use_nodes and sc.camera, 'Finished sky world/camera missing'
images = [n.image for n in sc.world.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
assert len(images) == 1, 'Expected one finished HDR world image'
source = pathlib.Path(bpy.path.abspath(images[0].filepath)).resolve()
assert source == ROOT / 'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr'
expected = json.loads((ROOT / 'art/sky3d/consistency_review/preview.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest() == expected['exr_sha256']
states = expected['native_card_preview']['states']
assert sc.name in states.values(), 'Expected Before jump / After reveal scene'
for name, digest in expected['native_card_preview']['native_inputs'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, 'Preview card input changed: '+name
for name, digest in expected['native_card_preview']['derived_art_inputs'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, 'Preview derived art changed: '+name
assert hashlib.sha256((ROOT/'source_data/tod_skybox.gdt').read_bytes()).hexdigest() == expected['native_card_preview']['sky_gdt_sha256']
before = []
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            sp = area.spaces.active
            before.append(sp.shading.type)
            sp.shading.type = 'RENDERED'
            sp.shading.use_scene_world_render = True
            sp.shading.use_scene_lights_render = True
            sp.overlay.show_overlays = False
            sp.region_3d.view_perspective = 'CAMERA'
            area.tag_redraw()
assert before, 'No 3D viewport to activate'
sc.render.engine = 'BLENDER_EEVEE_NEXT'
receipt = dict(file=str(EXPECTED), exr_sha256=expected['exr_sha256'],
               before=before, viewport='RENDERED', scene_world=True, scene_lights=True,
               active_scene=sc.name, sign_state=sc.get('sign_state'),
               preview_file_resaved=False, native_visual_verified=False)
(ROOT / 'art/sky3d/consistency_review/preview_activation.json').write_text(json.dumps(receipt, indent=2)+'\n')
print('FINISHED_HDR_VIEWPORT_ACTIVE', json.dumps(receipt))
