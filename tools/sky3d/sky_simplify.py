"""Moderate, spatially selective sky simplification policy (2026-09-29).

This module defines authoring policy only. Importing it changes no Blender
scene, source file, native asset, material or random state. build_city owns
integration and rendering. All angles use its Blender convention: az 0 is
the title. The orbital tether is az100/el47. The hero Skyrail station is
az89/el15.64, at643m horizontally; these are separate landmarks.

GROUNDING
The v8 source has 26 BODIES records: 19 planets/moons, 2 black holes,
4 galaxies and 1 comet. The separate visible hero moon makes 27 named
celestial groups. Ten satellite moonlets belong to retained parent planets.
The nine retirements below make 18 groups: exactly one third fewer named
groups, NOT a claim of one third fewer pixels, meshes or individual discs.

FINAL-RENDER AUDIT
cohesion_review/final/cohesion_sky_equirect.png and ingame_up/giant/
celestial_east: the small ringed filler beside the eastern giants, repeated
galaxies, bright flares and long light bars compete with the station. Around
the title, the continuous nebula and roof-to-roof accents fill its backdrop.
The tall city itself is root's separate density task. Preserve strong worlds
and holes; remove secondary forms and clear chosen sectors instead of
uniformly lowering every light's brightness.

INTEGRATION
* Keep BODIES literal definitions intact. gen_lanes.js reads the two hole
  dictionaries for runtime asteroid orbits. Never move/resize/retilt them.
* Generate each original body before retiring its complete object group
  (body/ring/moons/atmosphere/galaxy/comet). This preserves all RNG draws,
  including eagerly evaluated dict.get defaults and the hole stream draws.
  object_is_retired() identifies the current generator's exact object names.
* For secondary arcs/beams/lasers/free sigils, spend all original draws and
  collect their full geometry ranges plus angular samples. select_secondary
  returns the complete features to KEEP. Retire whole features so no light
  bars or roads end abruptly at a quiet-sector boundary. Feed beam endpoints
  and arc/laser samples, not just source-tower centers.
* Retire only the 40 standalone City.sigils candidates, not architectural
  glyphs attached to the named heroes. City.holos is already uncalled (0).
* Use STAR_GATES in world_sky; keep star sizes, color, peak energy, placement
  offsets and existing elevation fades. Gate thresholds select fewer existing
  stars rather than darken them all. Counts are procedural expectations.
* NEBULA_POLICY is a suggested background-only treatment. Apply its spatial
  factor to nebula cloud emission, never the total world, hero bodies, sign,
  dark-space floor, or all lights. Keep the existing finish/exposure contract;
  the root must review the solved finish gain and new directional GI.
* Keep all four functional rail lines, trains and rail stations, both elevated
  highways, the orbital tether/station, Origin storm, title, and runtime fleet.
  Their density/recognizability belongs to the owning city/station tasks.

This policy is a reviewable proposal, not a completed render/build receipt.
"""

from __future__ import annotations

import hashlib
import math


RETIRED_BODY_NAMES = (
    'dusk',       # Tiny duplicate high above the hero moon/title, az18 el64.
    'far_giant',  # Another tiny ringed gas ball in the eastern/back sector.
    'far_ember',  # Small cracked duplicate between title and main black hole.
    'far_a',      # Isolated filler close to the eastern planetary cluster.
    'far_b',      # Zenith filler; clearing it gives the upper sky a rest.
    'far_c',      # Small filler near the orbital station's angular sector.
    'edge',       # Extra galaxy above the eastern pair of gas giants.
    'sombrero',   # Extra galaxy above the main western gas giant.
    'harbinger',  # Static 14-degree comet tail; native shooting stars remain.
)

PROTECTED_BODY_NAMES = (
    'giant', 'cool', 'ruby', 'brown', 'ice',
    'gargantua', 'maelstrom',
)

RETAINED_BODY_NAMES = (
    'giant', 'cool', 'ember', 'brown', 'verdant', 'ringlet',
    'gargantua', 'andromeda', 'whirl', 'ice', 'ruby', 'jade',
    'obsidian', 'sulfur', 'grey', 'dust', 'maelstrom',
)

# None of the retained body definitions/positions/radii are overridden here.
BODY_POSITION_OVERRIDES = {}

CELESTIAL_COUNTS = {
    'planet_moon_groups_in_BODIES': (19, 13),
    'separate_hero_moon': (1, 1),
    'black_holes': (2, 2),
    'galaxies': (4, 2),
    'static_comets': (1, 0),
    'named_groups_total': (27, 18),
    'attached_satellite_moonlets': (10, 10),
}

# Maximum visible complete features. The original loops still run in full.
# Laser before-count is its requested maximum; geometry constraints can
# yield fewer. Ordinary-building density is deliberately not defined here.
SECONDARY_COUNTS = {
    'air_lanes': (10, 6),
    'searchlight_beams': (7, 4),
    'crown_lasers': (4, 2),
    'floating_sigils': (40, 26),
    'legacy_hologram_panels': (0, 0),
}

PRESERVE_COUNTS = {
    'rail_lines': 4,
    'rail_trains_requested': 9,
    'rail_stations_requested': 8,
    'elevated_highways': 2,
    'orbital_tether_station': 1,
    'black_hole_streams': 13,
}

# Circular azimuth bands with soft edges. The sign's elevation10..35 core
# protects the new user priority: a dominant, intimidating title landmark.
# These affect optional sky accents/clouds only, never a named hero building.
QUIET_SECTORS = (
    dict(name='title_frame', az=0.0, half_width=35.0,
         el_min=10.0, el_max=35.0, feather_az=10.0, feather_el=10.0,
         nebula_floor=0.40),
    dict(name='station_backdrop', az=100.0, half_width=18.0,
         el_min=28.0, el_max=70.0, feather_az=9.0, feather_el=9.0,
         nebula_floor=0.42),
    dict(name='skyrail_station_frame', az=89.0, half_width=24.0,
         el_min=10.0, el_max=23.0, feather_az=8.0, feather_el=6.0,
         nebula_floor=0.60),
    dict(name='rear_depth_gap', az=170.0, half_width=17.0,
         el_min=40.0, el_max=76.0, feather_az=10.0, feather_el=8.0,
         nebula_floor=0.58),
)

STAR_GATES = {
    # Surviving procedural candidates are proportional to (1 - keep).
    # Preserve fine distant stars: they provide depth without big silhouettes.
    'faint': dict(before_keep=0.50, after_keep=0.50, expected_retained=1.0),
    'medium': dict(before_keep=0.60, after_keep=0.72, expected_retained=0.70),
    'large_flares': dict(before_keep=0.85, after_keep=0.90,
                         expected_retained=2.0 / 3.0),
}

NEBULA_POLICY = {
    'gain': 1.45,                     # Unchanged, not uniform dimming.
    'cores_before': ((75.0, 55.0, 1.2), (-40.0, 60.0, 0.7), (170.0, 70.0, 0.5)),
    'cores_after': ((75.0, 55.0, 1.2), (-40.0, 60.0, 0.7)),
    'spatial_factor': 'nebula_factor', # A soft background-only quiet mask.
    'retain_palette': True,
    'retain_space_floor': True,
    'retain_finish_target_and_exposure': True,
}


def body_visible(name):
    """Visibility only; do not skip the original authoring RNG draws."""
    return name not in RETIRED_BODY_NAMES


def object_is_retired(object_name):
    """Complete current-generator body groups, not loose substring matches."""
    prefixes = ('gas_', 'cracked_', 'moon_', 'ring_', 'atmo_',
                'galaxy_', 'comet_', 'coma_', 'tail_')
    for name in RETIRED_BODY_NAMES:
        if object_name in tuple(prefix + name for prefix in prefixes):
            return True
        if object_name.startswith('moon_' + name + '_m'):
            return True
    return False


def _smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _sector_weight(az, el, sector):
    difference = abs((az - sector['az'] + 180.0) % 360.0 - 180.0)
    horizontal = 1.0 - _smoothstep(
        (difference - sector['half_width']) / sector['feather_az'])
    below = 1.0 - _smoothstep((sector['el_min'] - el) / sector['feather_el'])
    above = 1.0 - _smoothstep((el - sector['el_max']) / sector['feather_el'])
    return horizontal * below * above


def quiet_weight(az, el):
    """0 outside quiet sectors, 1 in a protected framing sector."""
    if not math.isfinite(az) or not math.isfinite(el):
        raise ValueError('Angular visibility samples must be finite')
    return max(_sector_weight(az, el, sector) for sector in QUIET_SECTORS)


def nebula_factor(az, el):
    """Reference CPU mask for translating the same policy into shader nodes."""
    if not math.isfinite(az) or not math.isfinite(el):
        raise ValueError('Nebula directions must be finite')
    return 1.0 - max(_sector_weight(az, el, sector) * (1.0 - sector['nebula_floor'])
                     for sector in QUIET_SECTORS)


def select_secondary(kind, candidates):
    """Return deterministic IDs to KEEP, retiring most intrusive whole forms.

    Candidate dicts: ``id`` (unique int/string), ``samples`` [(az,el), ...]
    along the complete feature. A feature with ``protected=True`` is always
    kept (use only for a necessary station/title component, not decoration).
    Optional ``importance`` in [0,1] favors an especially useful accent.
    No candidates are mutated and no random generator is used.
    """
    if kind not in SECONDARY_COUNTS:
        raise KeyError(kind)
    desired = SECONDARY_COUNTS[kind][1]
    ids = [item['id'] for item in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError('Secondary feature IDs must be unique')
    protected, ranked = [], []
    for item in candidates:
        if item.get('protected', False):
            protected.append(item['id'])
            continue
        samples = item.get('samples')
        if not samples:
            raise ValueError('Provide complete angular feature samples')
        values = [quiet_weight(float(az), float(el)) for az, el in samples]
        # An arc briefly crossing the sign matters even if its centroid does
        # not; average overlap distinguishes long overlays from edge touches.
        intrusion = 0.70 * max(values) + 0.30 * sum(values) / len(values)
        importance = max(0.0, min(1.0, float(item.get('importance', 0.0))))
        tie = hashlib.blake2s((kind + ':' + str(item['id'])).encode(), digest_size=8).digest()
        ranked.append((intrusion - importance * 0.25, tie, item['id']))
    ranked.sort(key=lambda entry: (entry[0], entry[1]))
    keep_count = max(0, desired - len(protected))
    return frozenset(protected + [entry[2] for entry in ranked[:keep_count]])
