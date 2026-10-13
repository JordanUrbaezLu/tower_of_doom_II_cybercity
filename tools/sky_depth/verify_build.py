"""Isolated v13 build proof; every earlier pass and its exceptions stay historical.

After review/install:
  python -B tools/sky_depth/verify_build.py --snapshot --title-report <report> --title-version <actual-version>
After the guarded FULL build:
  python -B tools/sky_depth/verify_build.py --build-log tmp/sky_depth/full.log

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
from finish_profile import PROFILE_PATH, check_stats
from quality_profile import PROFILE_PATH as QUALITY_PROFILE_PATH, load_quality, expected_quality
from card_contract import GENERATOR as CARD_GENERATOR, RECEIPT as CARD_RECEIPT, load_card, validate_card_art, verify_native as verify_native_card

spec = importlib.util.spec_from_file_location('sky_build_proof_core', ROOT / 'tools/sky_cohesion/verify_build.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
core.OUT = REVIEW
core.SNAP = REVIEW / 'build_inputs.json'
core.UNLINKED_PEER_SCRIPTS = frozenset()
# This coordinated pass also places the dealer's portrait on three existing
# walls. Include its real runtime sources; its owner's post-build verifier
# separately proves packed material/image names and native database settings.
core.NATIVE_FILES = tuple(sorted(set(core.NATIVE_FILES) | {
    'source_data/tod_dealer_presence.gdt',
    'model_export/tod_dealer_presence/_images/i_tod_dealer_surveillance.png',
}))
sources = set(core.AUTHOR_FILES)
sources.update(p.relative_to(ROOT).as_posix() for p in sky_sources())
sources.update(p.relative_to(ROOT).as_posix() for p in pathlib.Path(__file__).parent.iterdir()
               if p.suffix in ('.py', '.ps1'))
sources.add('tools/sky_cohesion/verify_build.py')
sources.add(PROFILE_PATH.relative_to(ROOT).as_posix())
sources.add(QUALITY_PROFILE_PATH.relative_to(ROOT).as_posix())
sources.add(CARD_GENERATOR.relative_to(ROOT).as_posix())
sources.add('tools/gen_tower_map.js')
sources.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'tools/dealer_presence').iterdir()
               if p.suffix in ('.py', '.ps1', '.js', '.json'))
core.AUTHOR_FILES = tuple(sorted(sources))


def configure_card_inputs():
    card = load_card()
    card['derived_art_inputs'] = validate_card_art(card)
    core.NATIVE_FILES = tuple(sorted(set(core.NATIVE_FILES) | set(card['native_files'])))
    return card


def depth_evidence(author, quality):
    """Bind the preserved baseline, actual geometry and reviewed sampling crops."""
    paths = []
    for name in ('resource_guard.json', 'radiant_guard.json'):
        guard_path = REVIEW/name
        guard = json.loads(guard_path.read_text(encoding='utf-8'))
        core.require(guard['pass_name'] == 'sky_depth_v13', 'Guard evidence belongs to another pass')
        for source, digest in guard['source_hashes'].items():
            core.require(sha(ROOT/source) == digest, 'Guard evidence is stale: '+source)
    for name in ('baseline.json', 'baseline_views.json'):
        path = REVIEW/name
        evidence = json.loads(path.read_text(encoding='utf-8'))
        paths.append(path)
        for entry in evidence['files'].values():
            preserved = ROOT/entry['preserved']
            core.require(sha(preserved) == entry['sha256'], 'Preserved baseline changed: '+str(preserved))
            paths.append(preserved)
    geometry_path = REVIEW/'architecture_check.json'
    geometry = json.loads(geometry_path.read_text(encoding='utf-8'))
    core.require(geometry['status'] == 'pass', 'Architecture source audit did not pass')
    for name, digest in geometry['source_hashes'].items():
        path = ROOT/name
        core.require(sha(path) == digest, 'Geometry audit has stale source: '+name)
        paths.append(path)
    actual = author['depth_geometry']
    core.require(actual['version'] == geometry['version'] and actual['build_calls'] == len(actual['calls']) >= 1189,
                 'Actual production geometry collector is incomplete')
    core.require(actual['service_bays'] > 0 and all(actual['back_pixels'][key] >= 2 for key in ('min_width','min_height')),
                 'Actual production service bays do not resolve at final angular scale')
    paths.append(geometry_path)
    composition_path = REVIEW/'composition_audit.json'
    composition = json.loads(composition_path.read_text(encoding='utf-8'))
    core.require(composition['status'] == 'pass' and composition['all_fields_equal'] is True, 'City layout changed')
    for key in ('before', 'after'):
        core.require(sha(ROOT/composition[key]) == composition[key+'_sha256'], 'Composition audit is stale')
        paths.append(ROOT/composition[key])
    art_path = REVIEW/'art_measurements.json'
    art = json.loads(art_path.read_text(encoding='utf-8'))
    core.require(art['status'] == 'pass' and art['exact_source_preservation'] is True, 'Accepted title art changed')
    for key in ('source', 'baseline_receipt'):
        path = ROOT/art[key]
        core.require(sha(path) == art[key+'_sha256'], 'Title art audit is stale: '+key)
        paths.append(path)
    cases = {}
    for case in ('before', 'after_old', 'after'):
        path = REVIEW/'crops'/(case+'.json')
        crop = json.loads(path.read_text(encoding='utf-8'))
        source_master = REVIEW/'before/tod2_sky.blend' if case == 'before' else STAGE/'depth.blend'
        core.require(crop['case'] == case and core.path_at(crop['master']) == source_master, 'Crop belongs to another pass')
        core.require(crop['master_sha256'] == sha(source_master), 'Crop source master changed')
        core.require(crop['script_sha256'] == sha(pathlib.Path(__file__).with_name('render_quality.py')), 'Crop renderer changed')
        core.require(crop['quality_profile'] == quality and crop['master_resaved'] is False, 'Crop profile/master contract changed')
        want = expected_quality(quality)
        if case != 'after':
            want.update(adaptive_threshold=.025, adaptive_min_samples=16, filter_width=1.5)
        core.require(crop['render_quality'] == want, 'Actual crop reconstruction differs from the expected case')
        core.require(set(crop['images']) == {'mid_city','outer_city','roofscape'}, 'Incomplete crop coverage')
        for view, image in crop['images'].items():
            image_path = ROOT/image['path']
            core.require(sha(image_path) == image['sha256'], 'Crop image changed: '+str(image_path))
            paths.append(image_path)
            if case != 'before':
                previous = cases['before']['images'][view]
                core.require(image['bounds'] == previous['bounds'] and image['pixels'] == previous['pixels'], 'Crop angles/texel scales differ')
        if case != 'before':
            core.require(crop['fixed_inspection_exposure'] == cases['before']['fixed_inspection_exposure'], 'Crop exposure changed')
        cases[case] = crop
        paths.append(path)
    review_path = REVIEW/'crops/review.json'
    reviewed = json.loads(review_path.read_text(encoding='utf-8'))
    core.require(reviewed['status'] == 'accepted' and reviewed['profile_sha256'] == sha(QUALITY_PROFILE_PATH)
                 and reviewed['candidate_master_sha256'] == author['blend_sha256']
                 and reviewed['reviewed_cases'] == ['before','after_old','after'] and bool(reviewed['note'].strip()),
                 'Current master and sampling profile have not completed the visual crop review')
    paths.append(review_path)
    return paths


def take_snapshot(args):
    started = time.time_ns()
    card = configure_card_inputs()
    stats_path, title_path, master = map(core.path_at, (args.stats, args.title_report, args.master))
    stats = json.loads(stats_path.read_text(encoding='utf-8'))
    title = json.loads(title_path.read_text(encoding='utf-8'))
    core.require(title.get('version') == args.title_version, 'Actual title report does not match --title-version')
    core.require(title.get('sign_state') == 'dull', 'Shipping sky must contain the dull before-jump sign')
    core.require(title.get('sign_aov') == 'sign' and title.get('lights_city') is False, 'Title AOV/light contract changed')
    core.require(title.get('reference_width_deg') == 65 and title.get('title_anchor_deg') == [0, 11.0],
                 'Title framing changed; coordinate cinematic anchors before changing this gate')
    core.require(core.path_at(stats['asset']) == ROOT / core.EXR, 'Stats do not describe the installed shipping sky')
    raw, mask = core.path_at(stats['input']), core.path_at(stats['sign_mask'])
    core.require(stats['size'] == [8192, 4096] and
                 all(core.exr_size(p) == stats['size'] for p in (ROOT / core.EXR, raw, mask)), 'Final EXR/AOV dimensions differ')
    profile = check_stats(stats)
    core.require(stats.get('roll') == 0 and stats.get('mirror') is False, 'Measured sky bearing requires roll0, no mirror')
    core.require(math.isfinite(stats['score']) and stats['score'] > 0, 'Invalid final score')
    files = core.runtime_files()
    inputs = {name: core.describe(p) for name, p in sorted(files.items())}
    authors = [ROOT / name for name in core.AUTHOR_FILES] + [stats_path, title_path, master, raw, mask]
    authors += [STAGE / 'author.json', STAGE / 'raw_8192.render.json', REVIEW / 'install.json', REVIEW / 'final/finish.json']
    authors += [CARD_RECEIPT, REVIEW / 'native_card_art.json']
    authors += [REVIEW/name for name in ('art_measurements.json', 'composition_audit.json', 'radiant_guard.json', 'resource_guard.json',
                 'master_audit.json', 'state_renders.json', 'blender_before_jump.png', 'blender_after_reveal.png', 'blender_preview.png')]
    authors += [ROOT/name for name in card['derived_art_inputs']]
    preview_path = REVIEW/'preview.json'
    preview = json.loads(preview_path.read_text(encoding='utf-8'))
    core.require(preview['exr_sha256'] == sha(ROOT/core.EXR), 'Preview does not show the installed dull sky')
    core.require(preview.get('preview_state') == 'after_reveal', 'Saved preview must default to After reveal')
    core.require(preview['native_card_preview']['native_inputs'] == card['input_hashes'], 'Preview native card inputs are stale')
    core.require(preview['native_card_preview']['derived_art_inputs'] == card['derived_art_inputs'], 'Preview derived card art is stale')
    authors += [preview_path, ROOT/'art/sky3d/depth_preview.blend']
    author = json.loads((STAGE/'author.json').read_text(encoding='utf-8'))
    core.require(author.get('options', {}).get('sign_state') == 'dull', 'Master was not authored explicitly for the dull shipping state')
    render = json.loads((STAGE / 'raw_8192.render.json').read_text(encoding='utf-8'))
    quality = load_quality()
    for name, receipt in (('author', author), ('render', render)):
        core.require(receipt['quality_profile'] == quality, name + ' quality configuration changed')
        core.require(receipt['quality_profile_sha256'] == sha(QUALITY_PROFILE_PATH), name + ' quality profile hash changed')
        core.require(receipt['render_quality'] == expected_quality(quality), name + ' actual production quality differs')
    core.require(author['source_hashes'] == source_hashes(), 'Authoring sources changed')
    core.require(author['blend_sha256'] == render['blend_sha256'], 'Render belongs to a different master')
    authors += depth_evidence(author, quality)
    core.require(render['width'] == 8192 and render['samples'] == 160, 'Final render settings differ from the production contract')
    core.require(render['source_hashes'] == source_hashes(), 'Geometry sources changed since rendering')
    core.require(sha(STAGE / 'raw_8192.title.json') == sha(title_path) == render.get('title_report_sha256'),
                 'Title report is not the one paired with the final render')
    core.require(sha(pathlib.Path(__file__).with_name('render_saved.py')) == render['renderer_sha256'], 'Renderer changed since rendering')
    core.require(sha(raw) == render['raw_sha256'] and sha(mask) == render['mask_sha256'], 'Render provenance mismatch')
    core.require(sha(master) == render['blend_sha256'], 'Installed master differs from the rendered scene')
    finish = json.loads((REVIEW / 'final/finish.json').read_text(encoding='utf-8'))
    check_stats(stats, finish)
    core.require(sha(raw) == finish['raw_sha256'] and sha(mask) == finish['mask_sha256'], 'Finish inputs differ from the paired render')
    core.require(sha(REVIEW / 'final/depth_stats.json') == finish['stats_sha256'], 'Staged finish stats changed')
    core.require(sha(ROOT / core.EXR) == finish['asset_sha256'], 'Installed EXR differs from finish receipt')
    core.require(sha(ROOT / 'tools/sky3d/finish_sky.py') == finish['finish_source_sha256'], 'Finish source changed')
    for name, expected in render['art_inputs'].items():
        core.require(sha(pathlib.Path(name)) == expected, 'Rendered image input changed: '+name)
    authors += [pathlib.Path(p) for p in render['art_inputs']]
    authors.append(ROOT / profile['baseline_stats'])
    authors += sorted((REVIEW / 'final').glob('depth_*.png'))
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
            'title_version': args.title_version, 'finish': stats, 'finish_profile': profile,
            'quality_profile': quality, 'quality_profile_sha256': sha(QUALITY_PROFILE_PATH),
            'native_card_inputs': card['input_hashes'], 'sign_state': 'dull',
            'native_card_art_inputs': card['derived_art_inputs'],
            'title': title, 'pass': 'sky_depth_v13'}
    REVIEW.mkdir(parents=True, exist_ok=True)
    core.SNAP.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    print('V13 SKY INPUT SNAPSHOT:', len(inputs), 'runtime inputs,', len(authoring), 'authoring artifacts;', core.SNAP)


def verify(args):
    configure_card_inputs()
    saved = json.loads(core.SNAP.read_text(encoding='utf-8'))
    core.require(saved.get('sign_state') == 'dull' and saved['title'].get('sign_state') == 'dull', 'Snapshot lacks the dull shipping-state contract')
    card = verify_native_card(core, saved['captured_ns'])
    core.verify(args)
    path = REVIEW/'build.json'
    result = json.loads(path.read_text(encoding='utf-8'))
    result['native_title_card'] = card
    path.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('NATIVE TITLE CARD VERIFIED:', card['source_triangles'], 'exported/compiled triangles, material and images packed')


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
        take_snapshot(args) if args.snapshot else verify(args)
    except (ValueError, OSError, KeyError, TypeError, core.sqlite3.Error, core.struct.error) as exc:
        print('V13 SKY BUILD VERIFY FAILED:', exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
