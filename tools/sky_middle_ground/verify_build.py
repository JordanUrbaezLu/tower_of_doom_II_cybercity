"""Isolated v10 build proof; v8/v9 receipts and earlier exceptions stay historical.

After review/install:
  python -B tools/sky_middle_ground/verify_build.py --snapshot --title-report <report> --title-version <actual-version>
After the guarded FULL build:
  python -B tools/sky_middle_ground/verify_build.py --build-log tmp/sky_middle_ground/full.log

The explicit title version is an exact expectation, not a family/prefix waiver.
The common sign AOV, camera anchor, exposure and native bake contracts stay strict.
Additional title/station/image-art evidence can be pinned with repeated --receipt.
This script never authors, installs, syncs, builds or launches BO3.
"""
import argparse
import datetime
import importlib.util
import json
import math
import pathlib
import sys
import time

sys.modules.pop('pass_config', None)  # fresh pass paths even in the reused MCP studio
from pass_config import ROOT, STAGE, REVIEW, sky_sources, source_hashes, sha

spec = importlib.util.spec_from_file_location('sky_build_proof_core', ROOT / 'tools/sky_cohesion/verify_build.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
core.OUT = REVIEW
core.SNAP = REVIEW / 'build_inputs.json'
core.UNLINKED_PEER_SCRIPTS = frozenset()
sources = set(core.AUTHOR_FILES)
sources.update(p.relative_to(ROOT).as_posix() for p in sky_sources())
sources.update(p.relative_to(ROOT).as_posix() for p in pathlib.Path(__file__).parent.iterdir()
               if p.suffix in ('.py', '.ps1'))
sources.add('tools/sky_cohesion/verify_build.py')
core.AUTHOR_FILES = tuple(sorted(sources))


def take_snapshot(args):
    started = time.time_ns()
    stats_path, title_path, master = map(core.path_at, (args.stats, args.title_report, args.master))
    stats = json.loads(stats_path.read_text(encoding='utf-8'))
    title = json.loads(title_path.read_text(encoding='utf-8'))
    core.require(title.get('version') == args.title_version, 'Actual title report does not match --title-version')
    core.require(title.get('sign_aov') == 'sign' and title.get('lights_city') is False, 'Title AOV/light contract changed')
    core.require(title.get('reference_width_deg') == 65 and title.get('title_anchor_deg') == [0, 11.0],
                 'Title framing changed; coordinate cinematic anchors before changing this gate')
    core.require(core.path_at(stats['asset']) == ROOT / core.EXR, 'Stats do not describe the installed shipping sky')
    raw, mask = core.path_at(stats['input']), core.path_at(stats['sign_mask'])
    core.require(stats['size'] == [8192, 4096] and
                 all(core.exr_size(p) == stats['size'] for p in (ROOT / core.EXR, raw, mask)), 'Final EXR/AOV dimensions differ')
    core.require(stats.get('hold_city') is True and abs(stats.get('score_city', -1)-.64) < 1e-7, 'City score contract changed')
    core.require(stats.get('roll') == 0 and stats.get('mirror') is False, 'Measured sky bearing requires roll0, no mirror')
    core.require(math.isfinite(stats['score']) and stats['score'] > 0, 'Invalid final score')
    files = core.runtime_files()
    inputs = {name: core.describe(p) for name, p in sorted(files.items())}
    authors = [ROOT / name for name in core.AUTHOR_FILES] + [stats_path, title_path, master, raw, mask]
    authors += [STAGE / 'author.json', STAGE / 'raw_8192.render.json', REVIEW / 'install.json', REVIEW / 'final/finish.json']
    render = json.loads((STAGE / 'raw_8192.render.json').read_text(encoding='utf-8'))
    core.require(render['width'] == 8192 and render['samples'] == 160, 'Final render settings differ from the production contract')
    core.require(render['source_hashes'] == source_hashes(), 'Geometry sources changed since rendering')
    core.require(sha(STAGE / 'raw_8192.title.json') == sha(title_path) == render.get('title_report_sha256'),
                 'Title report is not the one paired with the final render')
    core.require(sha(pathlib.Path(__file__).with_name('render_saved.py')) == render['renderer_sha256'], 'Renderer changed since rendering')
    core.require(sha(raw) == render['raw_sha256'] and sha(mask) == render['mask_sha256'], 'Render provenance mismatch')
    core.require(sha(master) == render['blend_sha256'], 'Installed master differs from the rendered scene')
    finish = json.loads((REVIEW / 'final/finish.json').read_text(encoding='utf-8'))
    core.require(sha(raw) == finish['raw_sha256'] and sha(mask) == finish['mask_sha256'], 'Finish inputs differ from the paired render')
    core.require(sha(REVIEW / 'final/middle_ground_stats.json') == finish['stats_sha256'], 'Staged finish stats changed')
    core.require(sha(ROOT / core.EXR) == finish['asset_sha256'], 'Installed EXR differs from finish receipt')
    core.require(sha(ROOT / 'tools/sky3d/finish_sky.py') == finish['finish_source_sha256'], 'Finish source changed')
    for name, expected in render['art_inputs'].items():
        core.require(sha(pathlib.Path(name)) == expected, 'Rendered image input changed: '+name)
    authors += [pathlib.Path(p) for p in render['art_inputs']]
    authors += sorted((REVIEW / 'final').glob('middle_ground_*.png'))
    authors += [core.path_at(p) for p in args.receipt]
    authoring = {str(p): core.describe(p) for p in sorted(set(authors))}
    existing_cache = core.cache_files()
    core.require(files.keys() == core.runtime_files().keys(), 'Runtime file set changed during snapshot')
    for name, p in files.items():
        core.require(p.stat().st_mtime_ns == inputs[name]['mtime_ns'], 'Runtime source changed during snapshot: '+name)
    data = {'schema': 1, 'map': core.MAP, 'private_root': str(core.MT), 'started_ns': started,
            'captured_ns': time.time_ns(), 'captured_local': datetime.datetime.now().isoformat(),
            'inputs': inputs, 'authoring': authoring, 'existing_sky_cache': existing_cache,
            'stats_path': str(stats_path), 'master_path': str(master), 'title_report': str(title_path),
            'title_version': args.title_version, 'finish': stats, 'title': title, 'pass': 'sky_middle_ground_v10'}
    REVIEW.mkdir(parents=True, exist_ok=True)
    core.SNAP.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    print('V10 SKY INPUT SNAPSHOT:', len(inputs), 'runtime inputs,', len(authoring), 'authoring artifacts;', core.SNAP)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--snapshot', action='store_true')
    action.add_argument('--build-log')
    parser.add_argument('--stats', default='docs/sky_preview/sky3d_stats.json')
    parser.add_argument('--master', default='art/sky3d/tod2_sky.blend')
    parser.add_argument('--title-report')
    parser.add_argument('--title-version')
    parser.add_argument('--receipt', action='append', default=[])
    parser.add_argument('--record-built-art', action='store_true')
    args = parser.parse_args()
    if args.snapshot and (not args.title_report or not args.title_version):
        parser.error('--snapshot requires --title-report and the exact --title-version')
    try:
        take_snapshot(args) if args.snapshot else core.verify(args)
    except (ValueError, OSError, KeyError, TypeError, core.sqlite3.Error, core.struct.error) as exc:
        print('V10 SKY BUILD VERIFY FAILED:', exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
