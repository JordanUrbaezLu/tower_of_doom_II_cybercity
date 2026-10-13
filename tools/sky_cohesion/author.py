"""Build editable sky geometry inside the dedicated real MCP studio, no render."""
import json
import pathlib
import runpy
import sys
import bpy
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'tmp/sky_cohesion'
old_args = sys.argv[:]
try:
    for name in ('cyber_title', 'cyber_architecture'):
        sys.modules.pop(name, None)
    sys.argv = ['build_city.py', '--', '--width', '4096', '--samples', '96',
                '--seed', '7', '--cam-h', '220', '--detail', '1',
                '--out', str(OUT / 'raw_4096.exr'),
                '--save-blend', str(OUT / 'cohesion.blend'), '--no-render',
                '--screens-dir', str(ROOT / 'art/sky3d/billboards')]
    runpy.run_path(str(ROOT / 'tools/sky3d/build_city.py'), run_name='__main__')
finally:
    sys.argv = old_args
print('COHESION_AUTHORED', len(bpy.context.scene.objects))
