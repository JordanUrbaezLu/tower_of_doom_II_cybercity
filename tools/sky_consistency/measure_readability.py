"""Measure celestial highlight clipping in existing before/after preview PNGs.

Reads source literals, PNGs and finish metadata; writes a JSON report only.
No image edits, Blender connection, scene changes, native installs or builds.
The numbers describe display PNGs, not native BO3 lighting or visual approval.
"""
import argparse
import ast
import datetime
import json
import math

import numpy as np
from PIL import Image

from pass_config import ROOT, REVIEW, sha

INNER_RADIUS = 0.85
KINDS = {'gas', 'cracked', 'moon'}


def literal(node):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'dict':
        assert not node.args and all(k.arg is not None for k in node.keywords)
        return {k.arg: literal(k.value) for k in node.keywords}
    if isinstance(node, (ast.List, ast.Tuple)):
        return [literal(item) for item in node.elts]
    return ast.literal_eval(node)


def assignments(path, names):
    result = {}
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in names:
                result[target.id] = literal(node.value)
    assert result.keys() == set(names), 'Expected source literals missing: ' + str(set(names)-result.keys())
    return result


def direction(az, el):
    az, el = math.radians(az), math.radians(el)
    return np.array([math.sin(az)*math.cos(el), math.cos(az)*math.cos(el), math.sin(el)])


def celestial_disks():
    """Mirror authored body_frame placement algebra without importing bpy."""
    source = assignments(ROOT/'tools/sky3d/build_city.py', ('BODIES', 'MOON_DISC'))
    policy = assignments(ROOT/'tools/sky3d/sky_simplify.py', ('RETIRED_BODY_NAMES', 'BODY_POSITION_OVERRIDES'))
    assert not policy['BODY_POSITION_OVERRIDES'], 'Account for position overrides before measuring'
    retired = set(policy['RETIRED_BODY_NAMES'])
    result = []
    for body in source['BODIES']:
        if body['kind'] not in KINDS or body['name'] in retired:
            continue
        result.append({key: body[key] for key in ('name', 'kind', 'az', 'el', 'r')})
        # make_bodies: P=D*dh, R=D*tan(r), moon=P+right*mx*R+up*my*R.
        # Work in units of D so no camera height/world distance is assumed.
        dh = direction(body['az'], body['el'])
        up = np.array([0., 0., 1.]) - dh*dh[2]
        up /= np.linalg.norm(up)
        right = np.cross(dh, up)
        right /= np.linalg.norm(right)
        radius = math.tan(math.radians(body['r']))
        for index, (mx, my, mr) in enumerate(body.get('moons', [])):
            center = dh + right*(mx*radius) + up*(my*radius)
            distance = float(np.linalg.norm(center))
            unit = center/distance
            result.append({'name': body['name']+'_m'+str(index), 'kind': 'satellite_moon',
                           'parent': body['name'], 'az': math.degrees(math.atan2(unit[0], unit[1])),
                           'el': math.degrees(math.asin(unit[2])),
                           'r': math.degrees(math.asin(radius*mr/distance))})
    result.append(dict(name='primary', kind='moon', **source['MOON_DISC']))
    assert sum(row['kind'] != 'satellite_moon' for row in result) == 14
    assert sum(row['kind'] == 'satellite_moon' for row in result) == 10
    return result


def disk_mask(width, height, az, el, radius):
    """Pixel centers follow finish_sky: u=az/(2*pi)+.5, v=.5-el/pi.

    Dot-product angular distance makes a true spherical disk, includes azimuth
    wrap, and avoids the high-elevation distortion of a raw (az,el) circle.
    """
    a = ((np.arange(width)+.5)/width-.5)*(2*math.pi)
    e = (.5-(np.arange(height)+.5)/height)*math.pi
    az, el, radius = map(math.radians, (az, el, radius))
    cosine = np.sin(e)[:, None]*math.sin(el) + np.cos(e)[:, None]*math.cos(el)*np.cos(a-az)[None, :]
    return cosine >= math.cos(radius)


def measures(rgb, mask):
    pixels = rgb[mask]
    assert len(pixels), 'No samples in celestial mask'
    luma = pixels.astype(np.float64) @ np.array([.2126, .7152, .0722])
    return {'sample_pixels': len(pixels),
            'all_channels_ge_250_fraction': float(np.mean(np.all(pixels >= 250, axis=1))),
            'any_channel_eq_255_fraction': float(np.mean(np.any(pixels == 255, axis=1))),
            'luma_display_0_255': {str(p): float(np.percentile(luma, p)) for p in (5, 50, 95)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('preview4096', 'final'), default='final')
    args = parser.parse_args()
    before_path = REVIEW/'before/middle_ground_sky_equirect.png'
    after_path = REVIEW/args.stage/'consistency_sky_equirect.png'
    stats_paths = [REVIEW/'before/middle_ground_stats.json', REVIEW/args.stage/'consistency_stats.json']
    stats = [json.loads(path.read_text(encoding='utf-8')) for path in stats_paths]
    for row in stats:
        assert row['roll'] == 0 and row['mirror'] is False, 'Masks expect unrolled, unmirrored panoramas'
    for key in ('display_mult', 'preview_gain'):
        assert stats[0][key] == stats[1][key], 'Different preview display brackets: ' + key
    arrays = []
    for path in (before_path, after_path):
        with Image.open(path) as image:
            assert image.mode in ('RGB', 'RGBA'), 'Expected RGB display PNG'
            assert image.size == (2048, 1024), 'Expected matching 2048x1024 panorama previews'
            arrays.append(np.asarray(image.convert('RGB')))
    before, after = arrays
    height, width = before.shape[:2]
    assert after.shape == before.shape
    union = np.zeros((height, width), dtype=bool)
    rows = []
    for body in celestial_disks():
        sample_radius = body['r']*INNER_RADIUS
        mask = disk_mask(width, height, body['az'], body['el'], sample_radius)
        union |= mask
        old, new = measures(before, mask), measures(after, mask)
        rows.append(dict(body, sample_radius_deg=sample_radius, before=old, after=new,
                         delta_all_channels_ge_250_fraction=new['all_channels_ge_250_fraction']-old['all_channels_ge_250_fraction'],
                         delta_any_channel_eq_255_fraction=new['any_channel_eq_255_fraction']-old['any_channel_eq_255_fraction'],
                         small_sample_warning=old['sample_pixels'] < 16))
    source_files = [ROOT/'tools/sky3d/build_city.py', ROOT/'tools/sky3d/sky_simplify.py',
                    ROOT/'tools/sky3d/finish_sky.py', ROOT/'tools/sky_consistency/measure_readability.py']
    result = {'schema': 1, 'measured_at': datetime.datetime.now().astimezone().isoformat(), 'stage': args.stage,
              'evidence': 'Read-only display PNG analysis; not a native BO3 screenshot or visual approval',
              'method': 'Unweighted pixel fractions inside spherical angular disks at 85% authored radius. Same current source masks applied to both panoramas; body placement is assumed unchanged. Moonlet centers and radii follow make_bodies/body_frame algebra.',
              'luma': 'Rec.709 coefficients on display RGB values 0..255; these are display luma, not linear radiance',
              'limitations': '2048-wide box-filtered previews; small moonlets have few samples. Ring/foreground overlays inside a disk are included. The primary masks omit atmospheric halos, ring exteriors and stars. Lower clipping indicates more display headroom, not independently verified texture quality.',
              'ray_convention': 'u=(az/(2*pi)+0.5); v=(0.5-el/pi), sampled at pixel centers',
              'inner_radius_fraction': INNER_RADIUS, 'size': [width, height],
              'inputs': {str(p.relative_to(ROOT)): sha(p) for p in [before_path, after_path]+stats_paths+source_files},
              'body_disks': 14, 'satellite_disks': 10, 'bodies': rows,
              'union_of_disks': {'before': measures(before, union), 'after': measures(after, union)},
              'lower_all_channel_clipping_bodies': sum(row['delta_all_channels_ge_250_fraction'] < 0 for row in rows),
              'higher_all_channel_clipping_bodies': sum(row['delta_all_channels_ge_250_fraction'] > 0 for row in rows),
              'lower_any_channel_clipping_bodies': sum(row['delta_any_channel_eq_255_fraction'] < 0 for row in rows),
              'higher_any_channel_clipping_bodies': sum(row['delta_any_channel_eq_255_fraction'] > 0 for row in rows),
              'native_visual_verified': False}
    target = REVIEW/('readability_'+args.stage+'.json')
    target.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('READABILITY_MEASURED', target)
    print(json.dumps({key: value for key, value in result.items() if key in (
        'body_disks', 'satellite_disks', 'union_of_disks', 'lower_all_channel_clipping_bodies',
        'higher_all_channel_clipping_bodies', 'lower_any_channel_clipping_bodies', 'higher_any_channel_clipping_bodies')}, indent=2))


if __name__ == '__main__':
    main()
