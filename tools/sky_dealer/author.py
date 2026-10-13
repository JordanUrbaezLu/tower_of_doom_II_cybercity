"""Build editable sky geometry inside the dedicated real MCP studio, no render."""
import json
import pathlib
import runpy
import sys
import time
import bpy
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'tmp/sky_dealer'
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.modules.pop('pass_config', None)  # fresh pass paths even in the reused MCP studio
from pass_config import sha, source_hashes
OUT.mkdir(parents=True, exist_ok=True)
config_path = OUT / 'author_config.json'
config = json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
assert not (set(config) - {'sign_style', 'moon_style', 'sign_state'}), 'Unknown author_config key'   # sign_state: docs/196 s6 (the dull bake)
started = time.time_ns()
expected_sources = source_hashes()
old_args = sys.argv[:]
try:
    for name, module in list(sys.modules.items()):
        source = getattr(module, '__file__', None)
        if source and pathlib.Path(source).resolve().is_relative_to(ROOT / 'tools/sky3d'):
            sys.modules.pop(name, None)
    sys.argv = ['build_city.py', '--', '--width', '4096', '--samples', '96',
                '--seed', '7', '--cam-h', '220', '--detail', '1',
                '--out', str(OUT / 'raw_4096.exr'),
                '--save-blend', str(OUT / 'dealer.blend'), '--no-render',
                '--screens-dir', str(ROOT / 'art/sky3d/billboards')]
    for name, value in config.items():
        sys.argv += ['--' + name.replace('_', '-'), str(value)]
    runpy.run_path(str(ROOT / 'tools/sky3d/build_city.py'), run_name='__main__')
finally:
    sys.argv = old_args
receipt = {'blend': str(OUT / 'dealer.blend'), 'blend_sha256': sha(OUT / 'dealer.blend'),
           'source_hashes': source_hashes(), 'options': config,
           'objects': len(bpy.context.scene.objects), 'native_visual_verified': False}
assert receipt['source_hashes'] == expected_sources, 'Sources changed while authoring; regenerate the master'
title = OUT / 'raw_4096.title.json'
receipt['title_report'] = ({'path': str(title), 'sha256': sha(title)}
                           if title.is_file() and title.stat().st_mtime_ns >= started else None)
scene = bpy.context.scene
trees = [scene.world.node_tree] if scene.world and scene.world.use_nodes else []
trees += [mat.node_tree for ob in scene.objects if hasattr(ob.data, 'materials')
          for mat in ob.data.materials if mat and mat.use_nodes]
art_inputs, seen = {}, set()
while trees:
    tree = trees.pop()
    if tree.as_pointer() in seen:
        continue
    seen.add(tree.as_pointer())
    for node in tree.nodes:
        image = getattr(node, 'image', None)
        if image and image.filepath:
            p = pathlib.Path(bpy.path.abspath(image.filepath)).resolve()
            if p.is_file():
                art_inputs[str(p)] = sha(p)
        group = getattr(node, 'node_tree', None)
        if group:
            trees.append(group)
for font in bpy.data.fonts:
    p = pathlib.Path(bpy.path.abspath(font.filepath)).resolve()
    if font.users and p.is_file():
        art_inputs[str(p)] = sha(p)
receipt['art_inputs'] = art_inputs
(OUT / 'author.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print('CONSISTENCY_AUTHORED', len(bpy.context.scene.objects))
