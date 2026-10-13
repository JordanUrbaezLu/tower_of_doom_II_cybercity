"""Candidate render quality, verified on angular-scale crops before production.

This changes sampling/reconstruction only. No native texture-size increase,
sharpening filter, new emission or exposure adjustment is involved.
"""
import json
from pathlib import Path

PROFILE_PATH = Path(__file__).with_suffix('.json')


def load_quality():
    p = json.loads(PROFILE_PATH.read_text(encoding='utf-8'))
    assert p['schema'] == 1 and p['profile'] == 'sky_depth_v13'
    assert (p['width'], p['height'], p['samples']) == (8192, 4096, 160)
    assert p['use_adaptive_sampling'] is True
    assert 0 < p['adaptive_threshold'] <= .025
    assert 16 <= p['adaptive_min_samples'] <= p['samples']
    assert .75 <= p['filter_width'] <= 1.5
    assert p['pixel_filter_type'] == 'BLACKMAN_HARRIS'
    assert p['use_denoising'] and p['denoiser'] == 'OPTIX'
    assert p['denoising_input_passes'] == 'RGB_ALBEDO_NORMAL'
    return p


def expected_quality(profile=None):
    return {k: v for k, v in (profile or load_quality()).items()
            if k not in ('schema', 'profile')}


def actual_quality(scene):
    return dict(width=scene.render.resolution_x, height=scene.render.resolution_y,
                samples=scene.cycles.samples,
                use_adaptive_sampling=scene.cycles.use_adaptive_sampling,
                adaptive_threshold=round(scene.cycles.adaptive_threshold, 8),
                adaptive_min_samples=scene.cycles.adaptive_min_samples,
                filter_width=round(scene.cycles.filter_width, 8),
                pixel_filter_type=scene.cycles.pixel_filter_type,
                use_denoising=scene.cycles.use_denoising,
                denoiser=scene.cycles.denoiser,
                denoising_input_passes=scene.cycles.denoising_input_passes)


def apply_quality(scene, production=False):
    p = load_quality()
    for key in ('use_adaptive_sampling', 'adaptive_threshold', 'adaptive_min_samples', 'use_denoising',
                'denoiser', 'denoising_input_passes'):
        setattr(scene.cycles, key, p[key])
    scene.cycles.filter_width = p['filter_width']
    scene.cycles.pixel_filter_type = p['pixel_filter_type']
    # Release geometry/device data after a completed frame on the 16GB host.
    scene.render.use_persistent_data = False
    if production:
        scene.render.resolution_x, scene.render.resolution_y = p['width'], p['height']
        scene.cycles.samples = p['samples']
    return actual_quality(scene)
