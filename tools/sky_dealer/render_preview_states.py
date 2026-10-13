"""Render both saved preview states without altering or resaving the preview asset."""
import pathlib
import json
import sys
import bpy
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from native_card_preview import select, BEFORE, AFTER
from pass_config import sha
expected = ROOT / 'art/sky3d/dealer_preview.blend'
assert pathlib.Path(bpy.data.filepath).resolve() == expected
digest = sha(expected)
files = {}
try:
    for state, name in (('before_jump', BEFORE), ('after_reveal', AFTER)):
        select(state)
        scene = bpy.data.scenes[name]
        path = ROOT / 'art/sky3d/dealer_review' / ('blender_' + state + '.png')
        previous = (scene.render.filepath, scene.render.image_settings.file_format,
                    scene.render.image_settings.color_mode, scene.render.image_settings.color_depth)
        try:
            scene.render.filepath = str(path)
            scene.render.image_settings.file_format = 'PNG'
            scene.render.image_settings.color_mode = 'RGB'
            scene.render.image_settings.color_depth = '8'
            bpy.ops.render.render(write_still=True, scene=name)
            files[state] = {'path': str(path), 'sha256': sha(path)}
        finally:
            scene.render.filepath, scene.render.image_settings.file_format, scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = previous
finally:
    select('after_reveal')
assert sha(expected) == digest, 'State preview must not modify the saved asset'
(ROOT / 'art/sky3d/dealer_review/state_renders.json').write_text(json.dumps({
    'blend_sha256': digest, 'images': files, 'native_visual_verified': False,
    'note': 'Blender render using actual native card inputs and an approximate display conversion; no native bloom.'}, indent=2)+'\n', encoding='utf-8')
print('PREVIEW_STATES_RENDERED', files)
