"""Verify and install the isolated crown alarm lens transparency repair.

This gate does not sync, build, launch the game, or change any native geometry.
Capture the CURRENT sources in tmp/alarm_lens_repair/baseline, record their
SHA-256 values in baseline_hashes.json, and author the candidate under staged.
Use --staged to review, --install to publish the complete reviewed source set,
and no argument to check the installed sources against the same capture.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'tmp/alarm_lens_repair'
BASE = WORK / 'baseline'
STAGE = WORK / 'staged'
MANIFEST = 'art/crown_alarm/manifest.json'
GDT = 'source_data/tod_crown_alarm.gdt'
PACKAGE = 'zone_source/tod_crown_alarm.zpkg'
LENS = 'model_export/tod_crown_alarm/_images/i_tod_alarm_lens_c.png'
# Advanced transparency requires a linear scalar specularMask. The original
# RGB lens S binding failed conversion; stock black selects nonmetal glass.
LENS_SPEC_TINT = '.220916 .220916 .220916 1'
LENS_SPEC_MAP = '$black_specular'
MASTERS = {
    'art/crown_alarm/crown_alarm.blend',
    'art/crown_alarm/visibility_review/high_fixture.blend',
}
REVIEW = 'art/crown_alarm/lens_review/'
IMAGE_DIR = 'model_export/tod_crown_alarm/_images/'
sys.path.insert(0, str(Path.home() /
    'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_relative(name):
    p = Path(name)
    require(not p.is_absolute() and '..' not in p.parts and p.parts,
            'Unsafe capture/install path: ' + str(name))
    resolved = (ROOT / p).resolve()
    require(resolved.is_relative_to(ROOT.resolve()), 'Path leaves this repository: ' + str(name))
    return p.as_posix()


def capture_hashes():
    data = json.loads((WORK / 'baseline_hashes.json').read_text(encoding='utf-8'))
    if 'files' in data and isinstance(data['files'], dict):
        data = data['files']
    require(isinstance(data, dict) and data, 'Missing baseline file/hash mapping')
    result = {}
    for key, value in data.items():
        name = safe_relative(key)
        if isinstance(value, dict):
            value = value.get('sha256')
        require(isinstance(value, str) and len(value) == 64,
                'Missing SHA-256 for captured path: ' + name)
        require((BASE / name).is_file(), 'Missing baseline file: ' + name)
        require(sha(BASE / name) == value, 'Baseline capture changed: ' + name)
        result[name] = value
    return result


def lens_uv_mask(model, size):
    """Rasterize native lens UVs, including the four texels used by filtering."""
    mask = np.zeros((size, size), dtype=bool)
    triangles = 0
    for mesh in model.meshes:
        for face in mesh.faces:
            if model.materials[face.material_id].name != 'mtl_tod_alarm_lens':
                continue
            uv = np.asarray([corner.uv for corner in face.indices], dtype=np.float64)
            require(uv.shape == (3, 2) and np.isfinite(uv).all() and
                    (uv >= -1e-5).all() and (uv <= 1.00001).all(), 'Invalid native lens UV')
            # The exporter already converts Blender's V-up UV to native V-down.
            # PIL top-to-bottom rows therefore use native V directly.
            points = np.column_stack((uv[:, 0] * size - .5, uv[:, 1] * size - .5))
            a, b, c = points
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            require(abs(den) > 1e-8, 'Degenerate native lens UV triangle')
            lo = np.maximum(np.floor(points.min(axis=0)).astype(int), 0)
            hi = np.minimum(np.ceil(points.max(axis=0)).astype(int), size - 1)
            if (hi >= lo).all():
                xx, yy = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
                q = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / den
                r = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / den
                covered = (q >= -1e-5) & (r >= -1e-5) & (q + r <= 1.00001)
                mask[yy[covered], xx[covered]] = True
            # Thin triangles and outermost corners can have no pixel centre;
            # they still sample bilinear footprints and must stay transparent.
            for point in list(points) + [points.mean(axis=0)]:
                x, y = np.floor(point).astype(int)
                for dx, dy in ((0, 0), (0, 1), (1, 0), (1, 1)):
                    mask[np.clip(y + dy, 0, size - 1), np.clip(x + dx, 0, size - 1)] = True
            triangles += 1
    return mask, triangles


def image_rgba(path):
    with Image.open(path) as image:
        require(image.mode == 'RGBA', 'Lens must retain its real RGBA alpha channel: ' + str(path))
        require(image.width == image.height and image.width in (512, 1024, 2048),
                'Unexpected lens dimensions')
        return np.asarray(image).copy()


def verify_native_lens_tint(target):
    original = (BASE / GDT).read_text(encoding='utf-8')
    candidate = (target / GDT).read_text(encoding='utf-8')
    pattern = r'("mtl_tod_alarm_lens" \( "material.gdf" \)\s*\{)(.*?)(\n\t\})'
    matches = list(re.finditer(pattern, original, re.S))
    require(len(matches) == 1, 'Missing or duplicate original native lens material')
    match = matches[0]
    body = match.group(2)
    for field, value in (('specColorTint', LENS_SPEC_TINT), ('specColorMap', LENS_SPEC_MAP)):
        body, count = re.subn(r'(?m)^([ \t]*"' + field + r'" ")[^"\n]*(")$',
                             lambda row: row.group(1) + value + row.group(2), body)
        require(count == 1, 'Missing or duplicate native lens field: ' + field)
    expected = original[:match.start(2)] + body + original[match.end(2):]
    require(candidate == expected,
            'GDT may change only lens specColorTint and its valid stock black specularMask binding')


def verify(target):
    hashes = capture_hashes()
    require({MANIFEST, GDT, LENS}.issubset(hashes), 'Capture misses lens, manifest or GDT')
    old = json.loads((BASE / MANIFEST).read_text(encoding='utf-8'))
    current = json.loads((target / MANIFEST).read_text(encoding='utf-8'))
    require(len(old['models']) == 15 and len(old['textures']) == 28,
            'Unexpected captured native alarm model/map set')
    native_paths = {GDT, *(row['file'] for row in old['models']),
                    *(IMAGE_DIR + name for name in old['textures'])}
    require(native_paths.issubset(hashes), 'Capture misses native alarm inputs')
    require(MASTERS.issubset(hashes), 'Capture misses an editable alarm master')
    allowed_changes = {LENS, GDT, PACKAGE, MANIFEST, *MASTERS}
    changed = []
    for name, digest in hashes.items():
        candidate = target / name
        # Omitted protected ancillary inputs are not installed. Live copies are
        # also checked at installation, so no source edited by a peer is lost.
        if not candidate.exists() and name not in native_paths | {MANIFEST} | MASTERS:
            candidate = BASE / name if target == STAGE else ROOT / name
        require(candidate.is_file(), 'Missing candidate input: ' + name)
        if sha(candidate) != digest:
            require(name in allowed_changes, 'Unexpected source/material/state change: ' + name)
            changed.append(name)
    require(LENS in changed, 'Lens-alpha candidate has not changed')
    require(PACKAGE in hashes, 'Capture misses the alarm asset package')
    original_package = (BASE / PACKAGE).read_text(encoding='utf-8')
    material_line = 'material,mc/mtl_tod_alarm_lens\n'
    require(material_line not in original_package, 'Baseline already includes the lens definition')
    expected_package = original_package.replace(
        '// Blender-authored physical red alarm beacons.\n',
        '// Blender-authored physical red alarm beacons.\n'
        '// Keep the model glass as a complete native material definition.\n' + material_line, 1)
    require(expected_package != original_package and
            (target / PACKAGE).read_text(encoding='utf-8') == expected_package,
            'Alarm package may only explicitly include the model lens material')
    verify_native_lens_tint(target)
    require(sha(target / GDT) == current['gdt_sha256'], 'Manifest GDT hash is stale')
    expected = json.loads(json.dumps(old))
    expected['textures']['i_tod_alarm_lens_c.png'] = sha(target / LENS)
    expected['gdt_sha256'] = sha(target / GDT)
    # The repair marker is the only added manifest metadata. All geometry,
    # variants, light profile, animation, state and historical evidence remain.
    marker = current.get('lens_repair')
    require(isinstance(marker, dict) and marker.get('native_playtested') is False and
            marker.get('revision') == '2026-10-01 clear glass',
            'Manifest needs lens_repair revision 2026-10-01 clear glass (native_playtested false)')
    require(marker.get('specColorTint') == LENS_SPEC_TINT and
            marker.get('specColorMap') == LENS_SPEC_MAP and
            marker.get('native_specular_mask') == 0.0 and
            marker.get('native_f0_after') == .04 and 'native_f0_before' not in marker,
            'Manifest must record the valid black-mask dielectric contract without an invented native before F0')
    expected['lens_repair'] = marker
    require(current == expected, 'Unexpected manifest geometry/state/material change')
    for name, digest in current['textures'].items():
        require(sha(target / (IMAGE_DIR + name)) == digest, 'Stale texture manifest hash: ' + name)
    before = image_rgba(BASE / LENS)
    after = image_rgba(target / LENS)
    require(before.shape == after.shape, 'Lens dimensions changed')
    require(np.array_equal(before[:, :, :3], after[:, :, :3]),
            'Lens repair changed RGB; native tint must remain unchanged')
    coverage = np.zeros(before.shape[:2], dtype=bool)
    lods = []
    for row in current['models']:
        name = row['file']
        require(sha(target / name) == row['sha256'] == hashes[name],
                'Exported geometry or UV changed: ' + name)
        model = xmodel.Model()
        model.LoadFile_Bin(str(target / name), split_meshes=True)
        require(sum(len(mesh.faces) for mesh in model.meshes) == row['triangles'],
                'Native triangle count changed: ' + name)
        mask, triangles = lens_uv_mask(model, after.shape[0])
        coverage |= mask
        if triangles:
            lods.append({'file': name, 'lens_triangles': triangles,
                         'sampled_texels': int(mask.sum())})
    require(len(lods) == 6 and coverage.any(), 'Lens coverage must include all six housing LODs')
    alpha = after[:, :, 3][coverage]
    old_alpha = before[:, :, 3][coverage]
    require(int(alpha.min()) >= math.ceil(.04 * 255) and
            int(alpha.max()) <= math.floor(.15 * 255),
            'Lens UV alpha must stay within 0.04..0.15, including filtered corners')
    require((alpha <= old_alpha).all() and float((alpha < old_alpha).mean()) >= .95,
            'Lens opacity was not reduced across the used shell')
    require(not (alpha >= 254).any(), 'An opaque native lens surface remains')
    review_files = []
    review_dir = target / REVIEW
    require(review_dir.is_dir(), 'Missing lens review evidence')
    for path in sorted(review_dir.rglob('*')):
        if path.is_file() and path.suffix.lower() != '.blend1':
            name = safe_relative(path.relative_to(target).as_posix())
            require(path.suffix.lower() in ('.png', '.json', '.html', '.md', '.txt', '.jpg', '.mp4', '.blend'),
                    'Unexpected review artifact: ' + name)
            review_files.append(name)
    require(any(name.endswith('.png') for name in review_files), 'Missing rendered lens review')
    report = {
        'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'scope': 'crown alarm transparent lens alpha, valid stock specularMask binding and dielectric tint',
        'target': 'staged' if target == STAGE else 'installed',
        'native_geometry_uv_lights_and_states_unchanged': True,
        'lens_only_native_material_changes': {'specColorTint': LENS_SPEC_TINT, 'specColorMap': LENS_SPEC_MAP},
        'lens_self_emission_unchanged': 0,
        'explicit_model_lens_material_included': True,
        'rgb_identical': True, 'lod_files_unchanged': len(current['models']),
        'unchanged_texture_maps': len(current['textures']) - 1,
        'used_lens_texels': int(coverage.sum()), 'housing_lod_coverage': lods,
        'alpha_byte_range_before': [int(old_alpha.min()), int(old_alpha.max())],
        'alpha_byte_range_after': [int(alpha.min()), int(alpha.max())],
        'alpha_mean_before': float(old_alpha.mean()) / 255,
        'alpha_mean_after': float(alpha.mean()) / 255,
        'lowered_fraction': float((alpha < old_alpha).mean()),
        'changed_captured_files': sorted(changed),
        'lens_sha256': sha(target / LENS), 'manifest_sha256': sha(target / MANIFEST),
        'native_playtested': False, 'guarded_full_build_required': True,
    }
    (WORK / ('staged_validation.json' if target == STAGE else 'installed_validation.json')).write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report, hashes, sorted(set(changed) | set(review_files))


def require_idle():
    process_csv = subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH'], text=True)
    names = {row[0].lower() for row in csv.reader(io.StringIO(process_csv)) if row}
    blocked = {name for name in names if name.startswith('radiant') or name in
               ('blackops3.exe', 'blender.exe', 'cod2map64.exe', 'linker_modtools.exe', 'gdtdb.exe')}
    require(not blocked, 'Game, Blender or native build is active; keep repair staged: ' + ', '.join(sorted(blocked)))


def install():
    require_idle()
    report, hashes, files = verify(STAGE)
    for name, digest in hashes.items():
        require((ROOT / name).is_file() and sha(ROOT / name) == digest,
                'Live captured input changed; refusing overwrite: ' + name)
    # Check immediately before publication as validation may take several seconds.
    require_idle()
    # Publish the reviewed art first; the native manifest is the final receipt.
    # Keep the short native texture/GDT/receipt publication adjacent.
    files.sort(key=lambda name: (
        0 if name.startswith(REVIEW) or name in MASTERS else
        1 if name == LENS else 2 if name == GDT else 3 if name == PACKAGE else 4, name))
    installed = []
    for name in files:
        source, destination = STAGE / name, ROOT / name
        require(source.is_file(), 'Missing reviewed install input: ' + name)
        require(name in {LENS, GDT, PACKAGE, MANIFEST, *MASTERS} or name.startswith(REVIEW),
                'Unreviewed install path: ' + name)
        if destination.is_file() and sha(destination) == sha(source):
            continue
        require_idle()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        require(sha(destination) == sha(source), 'Installed file hash mismatch: ' + name)
        installed.append({'file': name, 'sha256': sha(destination)})
    receipt = {'installed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'installed': installed, 'count': len(installed),
               'validation': report, 'native_playtested': False,
               'guarded_full_build_required': True}
    (WORK / 'installation.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    (ROOT / REVIEW / 'installation.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('ALARM_LENS_REPAIR_INSTALLED', len(installed), 'reviewed files; guarded FULL build required')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--staged', action='store_true')
    group.add_argument('--install', action='store_true')
    args = parser.parse_args()
    if args.install:
        install()
    else:
        report, _, _ = verify(STAGE if args.staged else ROOT)
        print('ALARM_LENS_REPAIR_PASS', json.dumps(report))


if __name__ == '__main__':
    main()
