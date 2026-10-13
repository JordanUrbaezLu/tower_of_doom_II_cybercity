"""THE SKY FLEET effects (docs/192), GENERATED - never hand-edit the .efx. v3 (user 2026-09-29: "I can't see any flames
coming out of the back of the jets ... some time warp black hole pulses ... some of the spaceships should come through
like a wormhole ... fighter jets probably just need fire and flames and exhaust" + shooting stars).

  python tools/sky_ships/gen_fx.py           write share/raw/fx/tod/sky/*.efx + art/sky_ships/fx_tables.json
  python tools/sky_ships/gen_fx.py --check   FAIL if any written effect / the table differs from a fresh generation

Every effect is COMPOSED from stock BO3 elements (their materials, flipbook atlases and element types), each one
rewritten to explicit sky-scale numbers: sizes and lengths in units of a reference radius R, colours, lifetimes and
spawn rates. The stock donors are snapshots in art/sky_ships/fx_donors/ (never read from the Mod Tools root), so a
fresh generation is byte-identical anywhere.

EFFECTS CANNOT SCALE (SetScale does not reach them), so every size-bound effect ships in SIZE BUCKETS and the
director picks the bucket that matches the drawn size (the flames sit on the model's nozzle TAGS, so their POSITION
follows the scaled ship exactly and only their size is quantised: at most +-19 %).

  fx_sky_flame_<kind>_<b>   a drive's flame, played LOOPING on the nozzle tag (tag +X = aft). b = 0..4 = the
                            BUCKETS below x the kind's reference radius. Kinds:
                              plasma_capital  the dreadnought's main drives: cyan plasma, a long plasma trail and a
                                              TIME-WARP PULSE (a ring + a lens ripple) every 1.8 s
                              plasma          cyan plasma (the gunship; the dreadnought's small thrusters)
                              fire            the fighter's afterburner: white-hot core, fire, shock diamonds, a
                                              contrail ribbon
                              fire_heavy      the hauler's drives: fire, sparks and a long smoke trail
  fx_sky_glint_<hue>_<s|m|l> a far engine (too small for a flame): a bright point with a faint streak behind it
  fx_sky_worm_<phase>_<b>   the WORMHOLE a ship arrives / leaves through (camera-facing, radius = 1000 x bucket):
                              open   the rift forming: a violet point that swells, swirl, lightning, a lens ring
                                     (looping until the director stops it)
                              burst  the ship bursts through: flash, electric shockwave, distortion ring, streaks
                              close  the rift collapsing: it shrinks to a point, pop, ripple
  fx_sky_star_<a|b|c>       a shooting star (a runner flying along the effect's +X, a thin glowing trail ribbon)
  fx_sky_fireball_<o|g>     a rare fireball (orange / green): a slow burning head, embers + smoke, breaks up at the end
  fx_sky_strobe_s/m/l, fx_sky_beacon_s/m/l   the blinking lights (v2, unchanged)
  fx_sky_sat_xs/s/m/l                        v4 a satellite: a steady warm-white point crossing the upper sky
"""
import json, re, sys, pathlib, copy
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import efx_lib as E

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/sky_fx_detail'))
from native_detail import refine as refine_surface_detail, verify as verify_surface_detail
DON = ROOT / 'art/sky_ships/fx_donors'
GLOW_DONOR = ROOT / 'share/raw/fx/acc/light/fx_perk_glow_amber.efx'
OUT = ROOT / 'share/raw/fx/tod/sky'
TABLES = ROOT / 'art/sky_ships/fx_tables.json'
FAR = 64000

BUCKETS = [1.0, 0.5, 0.25, 0.125, 0.0625]           # flame size buckets (x the kind's reference radius)
WORM_BUCKETS = [2.0, 1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125]   # wormhole radius buckets (x WORM_R); a rift is ~1 deg wide
                                                    # on screen, drawn anywhere from a map corner to the far wall
WORM_R = 1000
GLINT = [('s', 60), ('m', 140), ('l', 320)]          # far-engine point sizes (units)
SATS = [('xs', 18), ('s', 48), ('m', 110), ('l', 250)]   # v4 satellite point sizes (units); the director picks by the drawn distance
                                                     # (xs: pressed against the near wall from the crown hall, ~3,700 u away)
KINDS = {                                            # flame kind -> reference nozzle radius (units at bucket 0)
    'plasma_capital': 410, 'plasma': 150, 'fire': 78, 'fire_heavy': 180,
}
STARS = {'a': (9000, 350), 'b': (7000, 600), 'c': (5500, 900)}       # shooting stars: speed (u/s), life (ms)
FIREBALL = (2900, 2400)                                             # fireball: speed, life

# ---- colour ---------------------------------------------------------------------------------------------------------
CY_CORE, CY_MID, CY_OUT = (0.78, 0.96, 1.0), (0.30, 0.80, 1.0), (0.14, 0.52, 1.0)
OR_CORE, OR_MID, OR_OUT = (1.0, 0.90, 0.72), (1.0, 0.56, 0.20), (0.92, 0.30, 0.08)
VIOLET, WARP = (0.58, 0.36, 1.0), (0.52, 0.62, 1.0)

# ---- templates: (donor file, element index). Each keeps its own material, flipbook atlas and element type. -------------
TPL = {
    'glow':        (None, 0),                                                    # billboard gfx_light_phosphorous_em
    'core_hot':    ('dlc5_cosmo_fx_zmb_blackhole_looping.efx', 3),               # billboard gfx_light_core_hot_em
    'disc':        ('vehicle_fx_exhaust_jetpack_dbl_jmp_core.efx', 4),           # rotatedSprite gfx_light_core_hot_em_i1024
    'ray_core':    ('vehicle_fx_exhaust_jetpack_dbl_jmp_core.efx', 3),           # line gfx_light_ray_thruster_em
    'ray_wide':    ('vehicle_fx_exhaust_jetpack_dbl_jmp_core.efx', 0),           # line gfx_light_ray_wide_soft_em / wide_em
    'ray_thin':    ('vehicle_fx_exhaust_jetpack_dbl_jmp_core.efx', 1),           # line gfx_light_ray_thin_soft_em
    'heat':        ('vehicle_fx_exhaust_jetpack_dbl_jmp_core.efx', 5),           # billboard gfx_distort_heat
    'fire':        ('dlc1_castle_fx_rocket_exhaust_torch.efx', 1),               # line gfx_fire_inferno_burst_tall_1_anim_em
    'spark':       ('dlc1_castle_fx_rocket_exhaust_torch.efx', 0),               # line gfx_spark_single_em
    'smoke':       ('dlc1_castle_fx_rocket_smk_afterburn.efx', 0),               # billboard gfx_fog_slow_*_anim_lit
    'contrail':    ('dlc5_zmhd_fx_geotrail_jet_contrail.efx', 0),                # trail gfx_smk_trail_billow_lit
    'laser_trail': ('dlc5_zmhd_fx_mp_star_shooting_geotrail.efx', 0),            # trail gfx_trail_laser_em
    'runner':      ('dlc5_zmhd_fx_mp_star_shooting.efx', 0),                     # billboard gfx_light_incandescent_hot_lg + attachment
    'orb':         ('dlc5_zmhd_fx_mp_star_shooting.efx', 1),                     # billboard gfx_light_orb_hot_em_i512
    'incand':      ('dlc5_cosmo_fx_zmb_blackhole_looping.efx', 1),               # billboard gfx_light_incandescent_hot_em
    'swirl':       ('dlc3_stalingrad_fx_stalingrad_vortex_forming.efx', 3),      # billboard gfx_dust_heli_swirl_anim_em
    'lightning':   ('dlc3_stalingrad_fx_stalingrad_vortex_forming.efx', 4),      # billboard gfx_lightning_cloud_em
    'arc':         ('dlc3_stalingrad_fx_stalingrad_vortex_start_2.efx', 3),      # billboard gfx_elec_arc_omni_em_i512
    'shock_elec':  ('dlc3_stalingrad_fx_stalingrad_vortex_start_2.efx', 11),     # billboard gfx_shockwave_elec_anim_em_i2048
    'lens_ring':   ('dlc5_cosmo_fx_zmb_blackhole_looping.efx', 22),              # billboard gfx_distort_ring_hvy
    'ripple':      ('dlc3_stalingrad_fx_raygun_l_projectile_blackhole_lg.efx', 12),  # billboard gfx_distort_ring_ripple
    'sparkle':     ('dlc5_cosmo_fx_zmb_blackhole_looping.efx', 0),               # cloud gfx_spark_blink_anim_pcloud_em
    'ring':        ('dlc1_castle_fx_demon_gate_portal_close.efx', 18),           # billboard gfx_ring_thin
}
EXPECT = {                                                                      # the template must still be what we think
    'glow': ('billboardSprite', 'gfx_light_phosphorous_em'), 'core_hot': ('billboardSprite', 'gfx_light_core_hot_em'),
    'disc': ('rotatedSprite', 'gfx_light_core_hot_em_i1024'), 'ray_core': ('line', 'gfx_light_ray_thruster_em'),
    'ray_wide': ('line', 'gfx_light_ray_wide_soft_em'), 'ray_thin': ('line', 'gfx_light_ray_thin_soft_em'),
    'heat': ('billboardSprite', 'gfx_distort_heat'), 'fire': ('line', 'gfx_fire_inferno_burst_tall_1_anim_em'),
    'spark': ('line', 'gfx_spark_single_em'), 'smoke': ('billboardSprite', 'gfx_fog_slow_sm_anim_lit'),
    'contrail': ('trail', 'gfx_smk_trail_billow_lit'), 'laser_trail': ('trail', 'gfx_trail_laser_em'),
    'runner': ('billboardSprite', 'gfx_light_incandescent_hot_lg'), 'orb': ('billboardSprite', 'gfx_light_orb_hot_em_i512'),
    'incand': ('billboardSprite', 'gfx_light_incandescent_hot_em'), 'swirl': ('billboardSprite', 'gfx_dust_heli_swirl_anim_em'),
    'lightning': ('billboardSprite', 'gfx_lightning_cloud_em'), 'arc': ('billboardSprite', 'gfx_elec_arc_omni_em_i512'),
    'shock_elec': ('billboardSprite', 'gfx_shockwave_elec_anim_em_i2048'), 'lens_ring': ('billboardSprite', 'gfx_distort_ring_hvy'),
    'ripple': ('billboardSprite', 'gfx_distort_ring_ripple'), 'sparkle': ('cloud', 'gfx_spark_blink_anim_pcloud_em'),
    'ring': ('billboardSprite', 'gfx_ring_thin'),
}
_cache = {}


def template(key):
    fname, idx = TPL[key]
    if fname is None:
        fx = _cache.setdefault('__glow__', E.load(GLOW_DONOR))
        e = [x for x in fx.elements if x.name == 'glow'][0]
    else:
        fx = _cache.setdefault(fname, E.load(DON / fname))
        e = fx.elements[idx]
    t, mats = e.visual
    want = EXPECT[key]
    assert t == want[0] and mats[0] == want[1], 'template %s is %s %s, not %s' % (key, t, mats, want)
    return e.copy()


def header():
    fx = _cache.setdefault('__glow__', E.load(GLOW_DONOR))
    return list(fx.header)


def curve(rows):
    return [list(r) for r in rows]


def graph(e, key, scale, a, b=None):
    g = e.graph(key)
    g.scale = scale
    g.curves = [curve(a), curve(b if b is not None else a)]


FLAT0 = [(0, 0), (1, 0)]


def mk(tkey, name, *, life, loop=None, oneshot=None, count=(1, 0), delay=(0, 0), org=(0, 0, 0), org_rand=(0, 0, 0),
       offset='none', off_r=(0, 0), off_h=(0, 0), size=(1, [(0, 1), (1, 1)]), size1=None, vel=None, color=(1, 1, 1),
       alpha=[(0, 1), (1, 1)], run='effect', pivot=None, spin=None, grav=(0, 0), attach=None, death=None):
    """One element from template tkey, every visible number set here. size / size1 = (scale, curveA[, curveB]);
    vel = {axis: (scale, curveA[, curveB])} (missing axes zero); color = rgb or [(t, r, g, b), ...];
    alpha = [(t, a), ...] or (curveA, curveB); run = 'effect' (follows the tag) | 'world' (left behind) | 'spawn'."""
    e = template(tkey)
    e.name = name
    ed = [f for f in e.flags('editorFlags') if f not in ('looping', 'playAttached')]
    if loop is not None:
        ed.insert(0, 'looping')
        e.set('spawnLooping', list(loop))
        e.set('spawnLoopingSpawnCount', list(count))
        e.set('spawnOneShot', [1, 0])
    else:
        e.set('spawnLooping', [1, 0])
        e.set('spawnLoopingSpawnCount', [1, 0])
        e.set('spawnOneShot', list(oneshot or (1, 0)))
    if attach:
        ed.insert(1 if loop is not None else 0, 'playAttached')
    for f in ('useRandSize0', 'useRandSize1', 'useRandVel0', 'useRandAlpha'):
        if f not in ed:
            ed.append(f)
    e.set('editorFlags', ' '.join(ed))
    keep = [f for f in e.flags('flags') if f in ('noComputeSprites', 'useRotationAxis')]
    fl = ['spawnRelative', {'none': 'spawnOffsetNone', 'sphere': 'spawnOffsetSphere', 'cylinder': 'spawnOffsetCylinder'}[offset],
          {'effect': 'runRelToEffect', 'world': 'runRelToWorld', 'spawn': 'runRelToSpawn'}[run]]
    if size1 is not None:
        fl.append('nonUniformScale')
    if pivot is not None:
        fl.append('useBillboardPivot')
    e.set('flags', ' '.join(fl + keep))
    E.open_for_sky(e, FAR)
    e.set('spawnFrustumCullRadius', 0)
    e.set('lifeSpanMsec', list(life))
    e.set('spawnDelayMsec', list(delay))
    for ax, v, rv in zip('XYZ', org, org_rand):
        e.set('spawnOrg' + ax, [v, rv])
    e.set('spawnOffsetRadius', list(off_r))
    e.set('spawnOffsetHeight', list(off_h))
    e.set('gravity', list(grav))
    graph(e, 'sizeGraph0', size[0], size[1], size[2] if len(size) > 2 else None)
    s1 = size1 if size1 is not None else size
    graph(e, 'sizeGraph1', s1[0], s1[1], s1[2] if len(s1) > 2 else None)
    vel = vel or {}
    for ax in 'XYZ':
        if ax in vel:
            v = vel[ax]
            graph(e, 'velGraph0' + ax, v[0], v[1], v[2] if len(v) > 2 else None)
        else:
            graph(e, 'velGraph0' + ax, 0, FLAT0)
        graph(e, 'velGraph1' + ax, 0, FLAT0)
    rows = color if isinstance(color, list) else [(0,) + tuple(color), (1,) + tuple(color)]
    graph(e, 'colorGraph', 1, rows)
    if isinstance(alpha, tuple):
        graph(e, 'alphaGraph', 1, alpha[0], alpha[1])
    else:
        graph(e, 'alphaGraph', 1, alpha)
    if pivot is not None:
        e.set('billboardPivot', list(pivot))
    if spin is not None:                                   # (initial rotation range deg, roll speed deg/s range)
        e.set('initialRot', [spin[0][0], spin[0][1]])
        e.set('angleVelRoll', [spin[1][0], spin[1][1]])
    e.set('attachment', '"' + attach + '"' if attach else '""')
    e.set('fxOnDeath', '"' + death + '"' if death else '""')
    return e


def effect(elements, lo, hi):
    fx = E.Effect(3, header(), elements)
    fx.set_bounds(lo, hi)
    return fx.text()


# =========================================================================================================================
# THE FLAMES. Effect space: +X = aft (the nozzle tag is turned 180 deg about Z), the origin = the nozzle's exit plane.
# Every length is in units of R, the kind's reference radius at bucket 0; the bucket scales all of it.
# =========================================================================================================================
def flame(kind, R):
    els = []
    cap = kind == 'plasma_capital'
    plasma = kind in ('plasma_capital', 'plasma')
    core, mid, out = (CY_CORE, CY_MID, CY_OUT) if plasma else (OR_CORE, OR_MID, OR_OUT)
    long_ = {'plasma_capital': 1.35, 'plasma': 1.0, 'fire': 0.85, 'fire_heavy': 1.1}[kind]
    # the engine's glow: a bright soft ball on the exit, seen from every side
    els.append(mk('glow', 'glow', loop=(50, 0), life=(170, 30), org=(0.2 * R, 0, 0), size=(3.3 * R, [(0, 1), (1, 0.9)], [(0, 0.85), (1, 0.75)]),
                  color=mid, alpha=[(0, 0.8), (0.5, 0.9), (1, 0.7)]))
    # the white-hot disc filling the nozzle (faces aft)
    els.append(mk('disc', 'disc', loop=(25, 0), life=(25, 0), org=(0.05 * R, 0, 0), size=(1.55 * R, [(0, 1), (1, 1)]),
                  vel={'X': (0.25, [(0, 0.5), (1, 0.5)])}, color=core, alpha=[(0, 0.32), (1, 0.34)]))
    # the flame's core: a flickering white ray
    els.append(mk('ray_core', 'core', loop=(25, 0), life=(100, 20), org=(-0.1 * R, 0, 0),
                  size=(1.05 * R, [(0, 0.6), (0.05, 1), (1, 0.3)], [(0, 0.5), (0.05, 0.85), (1, 0.25)]),
                  size1=(4.0 * R * long_, [(0, 0.8), (1, 1)], [(0, 0.65), (1, 0.9)]),
                  vel={'X': (0.25, [(0, 0.5), (1, 0.5)])}, color=[(0,) + core, (1,) + mid],
                  alpha=[(0, 0.55), (0.6, 0.42), (1, 0.15)], pivot=(0, -0.45)))
    # the plume: a wide soft cone
    els.append(mk('ray_wide', 'plume', loop=(60, 10), life=(220, 40), org=(-0.1 * R, 0, 0),
                  size=(2.3 * R, [(0, 0.85), (1, 0.6)]), size1=(7.0 * R * long_, [(0, 1), (1, 1)], [(0, 0.85), (1, 0.85)]),
                  vel={'X': (0.25, [(0, 0.5), (1, 0.5)])}, color=[(0,) + mid, (1,) + out], alpha=[(0, 0.36), (0.5, 0.42), (1, 0)],
                  pivot=(0, -0.45)))
    # a thin inner streak
    els.append(mk('ray_thin', 'streak', loop=(100, 20), life=(200, 50), org=(-0.1 * R, 0, 0),
                  size=(0.75 * R, [(0, 0.35), (1, 1)]), size1=(5.5 * R * long_, [(0, 1), (1, 1)]),
                  vel={'X': (10.0, [(0, 0.5), (1, 0.5)])}, color=[(0,) + core, (1,) + out], alpha=[(0, 0.5), (0.5, 0.55), (1, 0)],
                  pivot=(0, -0.45)))
    # heat shimmer behind the drive
    els.append(mk('heat', 'haze', loop=(90, 20), life=(500, 200), org=(1.3 * R, 0, 0), offset='sphere', off_r=(0.2 * R, 0.1 * R),
                  size=(2.6 * R, [(0, 0.35), (0.3, 0.8), (1, 1)]), vel={'X': (7.0 * R, [(0, 0.5), (0.5, 0.3), (1, 0.2)])},
                  color=(0.6, 0.6, 1.0), alpha=[(0, 1), (1, 0)]))
    if not plasma:
        # real FIRE: the animated flame flipbook along the exhaust
        els.append(mk('fire', 'fire', loop=(90, 20), life=(450, 100), org=(0.05 * R, 0, 0),
                      size=(1.45 * R, [(0, 1), (1, 1)], [(0, 0.85), (1, 0.85)]), size1=(3.7 * R * long_, [(0, 1), (1, 1)], [(0, 0.85), (1, 0.85)]),
                      vel={'X': (0.025, [(0, 0.5), (1, 0.5)])}, color=(1.0, 0.66, 0.38),
                      alpha=[(0, 0), (0.15, 0.55), (0.6, 0.6), (1, 0)], pivot=(0, -0.3)))
    if kind == 'fire':
        # the afterburner's SHOCK DIAMONDS: three hot rings down the flame
        for i, (x, s, a) in enumerate(((1.2, 0.8, 0.26), (2.1, 0.66, 0.2), (3.0, 0.52, 0.15))):
            els.append(mk('disc', 'diamond_%d' % i, loop=(25, 0), life=(25, 0), org=(x * R, 0, 0), size=(s * R, [(0, 1), (1, 1)]),
                          vel={'X': (0.25, [(0, 0.5), (1, 0.5)])}, color=(1.0, 0.86, 0.62), alpha=[(0, a), (1, a)]))
        # sparks flicking off the flame
        els.append(mk('spark', 'sparks', loop=(160, 60), life=(250, 200), run='world', offset='cylinder', off_r=(0.4 * R, 0),
                      size=(0.06 * R, [(0, 1), (1, 0)]), size1=(0.5 * R, [(0, 1), (1, 0.2)]),
                      vel={'X': (14.0 * R, [(0, 0.5), (1, 0.2)]), 'Y': (2.0 * R, [(0, -0.5), (1, -0.1)], [(0, 0.5), (1, 0.1)]),
                           'Z': (2.0 * R, [(0, -0.5), (1, -0.1)], [(0, 0.5), (1, 0.1)])},
                      color=(1.0, 0.7, 0.35), alpha=[(0, 1), (1, 0)]))
        # the CONTRAIL: a ribbon of lit vapour left in the sky
        els.append(mk('contrail', 'contrail', loop=(1, 0), life=(1700, 0), run='world', org=(0.6 * R, 0, 0),
                      size=(2.8 * R, [(0, 0.2), (0.3, 0.45), (1, 1)]), color=(0.86, 0.88, 0.95),
                      alpha=[(0, 0.5), (0.25, 0.3), (0.6, 0.12), (1, 0)]))
    if kind == 'fire_heavy':
        els.append(mk('spark', 'sparks', loop=(90, 40), life=(300, 300), run='world', offset='cylinder', off_r=(0.45 * R, 0),
                      size=(0.07 * R, [(0, 1), (1, 0)]), size1=(0.6 * R, [(0, 1), (1, 0.2)]),
                      vel={'X': (11.0 * R, [(0, 0.5), (1, 0.15)]), 'Y': (2.5 * R, [(0, -0.5), (1, -0.1)], [(0, 0.5), (1, 0.1)]),
                           'Z': (2.5 * R, [(0, -0.5), (1, -0.1)], [(0, 0.5), (1, 0.1)])},
                      color=(1.0, 0.64, 0.3), alpha=[(0, 1), (1, 0)]))
        # a long industrial smoke trail and embers, left in the sky
        els.append(mk('smoke', 'smoke', loop=(150, 40), life=(3600, 900), run='world', org=(1.2 * R, 0, 0), offset='sphere',
                      off_r=(0.3 * R, 0.2 * R), size=(1.3 * R, [(0, 0.5), (0.4, 0.85), (1, 1.6)]),
                      color=(0.34, 0.32, 0.31), alpha=[(0, 0), (0.1, 0.42), (0.6, 0.22), (1, 0)]))
        els.append(mk('glow', 'embers', loop=(80, 20), life=(900, 200), run='world', org=(1.0 * R, 0, 0), offset='sphere',
                      off_r=(0.25 * R, 0.1 * R), size=(1.1 * R, [(0, 1), (1, 1.8)]), color=OR_MID, alpha=[(0, 0.36), (1, 0)]))
    if plasma:
        # the plasma contrail: glow left behind in the sky
        trail_ms = 2600 if cap else 1500
        els.append(mk('glow', 'trail', loop=(60, 0), life=(trail_ms, trail_ms // 5), run='world', org=(1.0 * R, 0, 0), offset='sphere',
                      off_r=(0.2 * R, 0.1 * R), size=(1.7 * R, [(0, 1), (1, 2.6)]), color=tuple(c * 0.85 for c in out),
                      alpha=[(0, 0.34), (0.3, 0.22), (1, 0)]))
    if cap:
        # THE TIME-WARP PULSE: every 1.8 s a ring of warped light rips out of the drive, with a lens ripple
        els.append(mk('shock_elec', 'warp_ring', loop=(1800, 0), life=(900, 0), org=(1.2 * R, 0, 0),
                      size=(6.0 * R, [(0, 0.25), (0.35, 0.7), (1, 1)]), color=WARP, alpha=[(0, 0.85), (0.4, 0.55), (1, 0)]))
        els.append(mk('lens_ring', 'warp_lens', loop=(1800, 0), life=(750, 0), org=(1.2 * R, 0, 0),
                      size=(8.0 * R, [(0, 0.2), (1, 1)]), alpha=[(0, 1), (1, 0)]))
        els.append(mk('glow', 'warp_flash', loop=(1800, 0), life=(260, 0), org=(0.6 * R, 0, 0),
                      size=(4.5 * R, [(0, 0.6), (1, 1)]), color=(0.7, 0.72, 1.0), alpha=[(0, 0.55), (1, 0)]))
    return els


def glint(hue, S):
    col = CY_MID if hue == 'cyan' else OR_MID
    hot = CY_CORE if hue == 'cyan' else OR_CORE
    return [
        mk('glow', 'point', loop=(60, 0), life=(180, 40), size=(S, [(0, 1), (1, 0.9)], [(0, 0.85), (1, 0.8)]), color=col,
           alpha=[(0, 0.95), (1, 0.85)]),
        mk('core_hot', 'hot', loop=(40, 0), life=(120, 20), size=(0.38 * S, [(0, 1), (1, 1)]), color=hot, alpha=[(0, 0.7), (1, 0.6)]),
        mk('glow', 'streak', loop=(70, 0), life=(1300, 200), run='world', size=(0.5 * S, [(0, 1), (1, 1.5)]), color=col,
           alpha=[(0, 0.3), (1, 0)]),
    ]


def satellite(S):
    """v4 A SATELLITE: a slow steady point of light crossing the upper sky (the director flares it now and then with a
    strobe one-shot). A warm-white point with a hot core; no streak (it is not an engine)."""
    return [
        mk('glow', 'point', loop=(60, 0), life=(180, 40), size=(S, [(0, 1), (1, 0.92)], [(0, 0.9), (1, 0.84)]), color=(1.0, 0.96, 0.88),
           alpha=[(0, 0.9), (1, 0.8)]),
        mk('core_hot', 'hot', loop=(40, 0), life=(120, 20), size=(0.35 * S, [(0, 1), (1, 1)]), color=(1.0, 1.0, 1.0), alpha=[(0, 0.75), (1, 0.65)]),
    ]


# =========================================================================================================================
# THE WORMHOLE. Camera-facing (a spherical rift reads the same from any side), radius Rw.
# =========================================================================================================================
def worm_open(Rw):
    return [
        mk('glow', 'seed', oneshot=(1, 0), life=(1700, 0), size=(1.9 * Rw, [(0, 0.03), (0.55, 0.55), (0.85, 0.95), (1, 1)]),
           color=VIOLET, alpha=[(0, 0.2), (0.3, 0.9), (1, 1)]),
        mk('glow', 'aura', loop=(120, 0), life=(420, 60), delay=(700, 0), size=(2.3 * Rw, [(0, 0.95), (1, 1.05)]),
           color=(0.36, 0.42, 1.0), alpha=[(0, 0.32), (1, 0.28)]),
        mk('core_hot', 'core', loop=(60, 0), life=(180, 40), delay=(450, 0), size=(0.42 * Rw, [(0, 1), (1, 1)]),
           color=(0.86, 0.88, 1.0), alpha=[(0, 0.75), (1, 0.6)]),
        mk('swirl', 'swirl', loop=(330, 40), life=(1400, 200), delay=(300, 0), size=(2.05 * Rw, [(0, 0.8), (0.5, 1), (1, 0.9)], [(0, 0.7), (0.5, 0.9), (1, 0.8)]),
           color=(0.46, 0.36, 1.0), alpha=[(0, 0), (0.25, 0.55), (0.75, 0.5), (1, 0)], spin=((0, 360), (40, 80))),
        mk('lightning', 'lightning', loop=(170, 70), life=(150, 40), delay=(250, 0), offset='sphere', off_r=(0.35 * Rw, 0.2 * Rw),
           size=(1.25 * Rw, [(0, 1), (1, 1)], [(0, 0.7), (1, 0.7)]), color=(0.72, 0.9, 1.0), alpha=[(0, 0.95), (1, 0.6)]),
        mk('arc', 'arcs', loop=(110, 40), life=(150, 40), delay=(350, 0), offset='sphere', off_r=(0.55 * Rw, 0.2 * Rw),
           size=(0.95 * Rw, [(0, 1), (1, 1)], [(0, 0.6), (1, 0.6)]), color=(0.78, 0.62, 1.0), alpha=[(0, 1), (1, 0.5)]),
        mk('lens_ring', 'lens', loop=(900, 0), life=(900, 0), delay=(550, 0), size=(2.5 * Rw, [(0, 0.45), (1, 1)]), alpha=[(0, 1), (1, 0)]),
        mk('ring', 'rim', loop=(700, 0), life=(700, 0), delay=(600, 0), size=(2.1 * Rw, [(0, 1.05), (1, 0.8)]),
           color=(0.62, 0.52, 1.0), alpha=[(0, 0), (0.3, 0.55), (1, 0)]),
    ]


def worm_burst(Rw):
    return [
        mk('glow', 'flash', oneshot=(1, 0), life=(280, 0), size=(3.6 * Rw, [(0, 0.7), (1, 1)]), color=(0.92, 0.88, 1.0), alpha=[(0, 1), (1, 0)]),
        mk('core_hot', 'core', oneshot=(1, 0), life=(190, 0), size=(1.5 * Rw, [(0, 1), (1, 0.6)]), color=(1, 1, 1), alpha=[(0, 1), (1, 0)]),
        mk('shock_elec', 'shock', oneshot=(1, 0), life=(750, 0), size=(5.8 * Rw, [(0, 0.15), (0.4, 0.7), (1, 1)]), color=(0.55, 0.62, 1.0),
           alpha=[(0, 0.95), (0.5, 0.6), (1, 0)]),
        mk('lens_ring', 'lens', oneshot=(1, 0), life=(650, 0), size=(7.0 * Rw, [(0, 0.15), (1, 1)]), alpha=[(0, 1), (1, 0)]),
        mk('lightning', 'bolts', oneshot=(3, 1), life=(220, 60), offset='sphere', off_r=(0.6 * Rw, 0.3 * Rw),
           size=(2.0 * Rw, [(0, 1), (1, 1)]), color=(0.75, 0.9, 1.0), alpha=[(0, 1), (1, 0)]),
        mk('ray_thin', 'rays', oneshot=(12, 4), life=(320, 120), offset='sphere', off_r=(0.2 * Rw, 0.1 * Rw),
           size=(0.12 * Rw, [(0, 1), (1, 0.5)]), size1=(2.4 * Rw, [(0, 0.4), (1, 1)]),
           vel={'X': (2.6 * Rw, [(0, -0.5), (1, -0.5)], [(0, 0.5), (1, 0.5)]), 'Y': (2.6 * Rw, [(0, -0.5), (1, -0.5)], [(0, 0.5), (1, 0.5)]),
                'Z': (2.6 * Rw, [(0, -0.5), (1, -0.5)], [(0, 0.5), (1, 0.5)])},
           color=(0.8, 0.84, 1.0), alpha=[(0, 0.9), (1, 0)], pivot=(0, -0.45)),
    ]


def worm_close(Rw):
    return [
        mk('glow', 'implode', oneshot=(1, 0), life=(650, 0), size=(2.3 * Rw, [(0, 1), (0.7, 0.3), (1, 0.02)]), color=VIOLET,
           alpha=[(0, 0.85), (1, 0.6)]),
        mk('swirl', 'swirl', oneshot=(1, 0), life=(620, 0), size=(2.1 * Rw, [(0, 1), (1, 0.05)]), color=(0.46, 0.36, 1.0),
           alpha=[(0, 0.55), (1, 0)], spin=((0, 360), (160, 240))),
        mk('arc', 'arcs', loop=(90, 30), life=(140, 30), offset='sphere', off_r=(0.5 * Rw, 0.2 * Rw),
           size=(0.8 * Rw, [(0, 1), (1, 1)]), color=(0.78, 0.62, 1.0), alpha=[(0, 1), (1, 0.4)]),
        mk('core_hot', 'pop', oneshot=(1, 0), life=(150, 0), delay=(600, 0), size=(1.2 * Rw, [(0, 1), (1, 0.3)]), color=(0.95, 0.95, 1.0),
           alpha=[(0, 1), (1, 0)]),
        mk('ripple', 'ripple', oneshot=(1, 0), life=(520, 0), delay=(600, 0), size=(3.6 * Rw, [(0, 0.1), (1, 1)]), alpha=[(0, 1), (1, 0)]),
        mk('ring', 'ring', oneshot=(1, 0), life=(420, 0), delay=(610, 0), size=(2.4 * Rw, [(0, 0.1), (1, 1)]), color=(0.7, 0.6, 1.0),
           alpha=[(0, 0.8), (1, 0)]),
    ]


# =========================================================================================================================
# SHOOTING STARS + FIREBALLS: runners flying along +X at a fixed speed; the trail is an attached child effect.
# Sizes are for the sky shell (~8,000-12,000 units from the camera: one pixel ~ 7 units).
# =========================================================================================================================
def star(speed, life):
    L = life
    fade = [(0, 0), (0.08, 1), (0.7, 0.85), (1, 0)]                  # flares in, burns, fades
    return [
        mk('runner', 'head', oneshot=(1, 0), life=(L, 0), size=(26, [(0, 1), (1, 1)]), vel={'X': (speed, [(0, 1), (1, 1)])},
           color=(0.86, 0.93, 1.0), alpha=fade, run='spawn', attach='tod/sky/fx_sky_star_trail'),
        mk('orb', 'glow', oneshot=(1, 0), life=(L, 0), size=(70, [(0, 1), (1, 0.8)]), vel={'X': (speed, [(0, 1), (1, 1)])},
           color=(0.6, 0.75, 1.0), alpha=[(0, 0), (0.08, 0.45), (0.7, 0.35), (1, 0)], run='spawn'),
    ]


def star_trail():
    return [mk('laser_trail', 'trail', loop=(400, 0), life=(420, 0), run='world', size=(15, [(0, 1), (0.3, 0.6), (1, 0.25)]),
               color=[(0, 0.9, 0.95, 1.0), (0.4, 0.55, 0.7, 1.0), (1, 0.2, 0.3, 0.6)], alpha=[(0, 0.75), (0.4, 0.4), (1, 0)])]


def fireball(hue):
    speed, L = FIREBALL
    col = (1.0, 0.72, 0.42) if hue == 'o' else (0.55, 1.0, 0.62)
    return [
        mk('runner', 'head', oneshot=(1, 0), life=(L, 0), size=(62, [(0, 0.6), (0.1, 1), (1, 1.15)]), vel={'X': (speed, [(0, 1), (1, 1)])},
           color=(1.0, 0.95, 0.85), alpha=[(0, 0), (0.06, 1), (0.9, 1), (1, 0)], run='spawn',
           attach='tod/sky/fx_sky_fireball_trail_' + hue, death='tod/sky/fx_sky_fireball_burst_' + hue),
        mk('orb', 'glow', oneshot=(1, 0), life=(L, 0), size=(240, [(0, 0.5), (0.1, 1), (1, 1.2)]), vel={'X': (speed, [(0, 1), (1, 1)])},
           color=col, alpha=[(0, 0), (0.06, 0.6), (0.9, 0.55), (1, 0)], run='spawn'),
    ]


def fireball_trail(hue):
    col = (1.0, 0.55, 0.22) if hue == 'o' else (0.45, 1.0, 0.5)
    return [
        mk('laser_trail', 'streak', loop=(400, 0), life=(900, 0), run='world', size=(46, [(0, 1), (0.4, 0.6), (1, 0.2)]),
           color=[(0,) + col, (1, 0.35, 0.18, 0.1)], alpha=[(0, 0.85), (0.5, 0.45), (1, 0)]),
        mk('incand', 'embers', loop=(35, 10), life=(750, 250), run='world', offset='sphere', off_r=(18, 12),
           size=(46, [(0, 1), (1, 0.35)]), color=col, alpha=[(0, 0.7), (1, 0)]),
        mk('smoke', 'smoke', loop=(70, 20), life=(2600, 700), run='world', offset='sphere', off_r=(20, 15),
           size=(90, [(0, 0.5), (1, 2.4)]), color=(0.36, 0.34, 0.34), alpha=[(0, 0), (0.1, 0.3), (1, 0)]),
    ]


def fireball_burst(hue):
    col = (1.0, 0.7, 0.4) if hue == 'o' else (0.6, 1.0, 0.65)
    return [
        mk('glow', 'flash', oneshot=(1, 0), life=(300, 0), size=(520, [(0, 0.6), (1, 1)]), color=col, alpha=[(0, 1), (1, 0)]),
        mk('runner', 'fragments', oneshot=(3, 1), life=(700, 250), size=(22, [(0, 1), (1, 0.4)]),
           vel={'X': (900, [(0, 0.3), (1, 0.3)], [(0, 0.5), (1, 0.5)]), 'Y': (700, [(0, -0.5), (1, -0.5)], [(0, 0.5), (1, 0.5)]),
                'Z': (700, [(0, -0.5), (1, -0.5)], [(0, 0.5), (1, 0.5)])},
           color=col, alpha=[(0, 1), (1, 0)], run='spawn', attach='tod/sky/fx_sky_fireball_frag'),
        mk('incand', 'sparks', oneshot=(10, 4), life=(500, 250), size=(14, [(0, 1), (1, 0.2)]),
           vel={'X': (600, [(0, -0.5), (1, -0.5)], [(0, 0.5), (1, 0.5)]), 'Y': (600, [(0, -0.5), (1, -0.5)], [(0, 0.5), (1, 0.5)]),
                'Z': (600, [(0, -0.5), (1, -0.5)], [(0, 0.5), (1, 0.5)])},
           color=col, alpha=[(0, 1), (1, 0)], run='spawn'),
    ]


def fireball_frag():
    return [mk('laser_trail', 'trail', loop=(400, 0), life=(380, 0), run='world', size=(12, [(0, 1), (1, 0.2)]),
               color=[(0, 1.0, 0.8, 0.5), (1, 0.4, 0.2, 0.1)], alpha=[(0, 0.8), (1, 0)])]


# ---- v2's blinking lights (unchanged look) ------------------------------------------------------------------------------
def v2_lights():
    out = {}
    for tag, s in (('s', 50), ('m', 120), ('l', 240)):
        halo = mk('glow', 'halo', oneshot=(1, 0), life=(120, 0), size=(s, [(0, 1), (1, 1.15)], [(0, 0.85), (1, 0.98)]),
                  color=(1.0, 0.97, 0.92), alpha=[(0, 1.0), (0.55, 0.75), (1, 0.0)])
        core = mk('glow', 'core', oneshot=(1, 0), life=(90, 0), size=(s * 0.35, [(0, 1), (1, 0.86)], [(0, 0.85), (1, 0.73)]),
                  color=(1.0, 1.0, 1.0), alpha=[(0, 1.0), (1, 0.0)])
        b = int(s * 2)
        out['fx_sky_strobe_' + tag] = effect([halo, core], (-b, -b, -b), (b, b, b))
        pulse = mk('glow', 'pulse', oneshot=(1, 0), life=(450, 0), size=(s * 1.1, [(0, 1), (1, 1.09)], [(0, 0.85), (1, 0.93)]),
                   color=(1.0, 0.08, 0.05), alpha=[(0, 0.25), (0.3, 1.0), (0.6, 0.7), (1, 0.0)])
        rcore = mk('glow', 'rcore', oneshot=(1, 0), life=(380, 0), size=(s * 0.4, [(0, 1), (1, 1)], [(0, 0.85), (1, 0.85)]),
                   color=(1.0, 0.35, 0.3), alpha=[(0, 0.3), (0.3, 1.0), (1, 0.0)])
        out['fx_sky_beacon_' + tag] = effect([pulse, rcore], (-b, -b, -b), (b, b, b))
    return out


def scaled(els, k):
    out = []
    for e in els:
        c = e.copy()
        E.scale_space(c, k)
        out.append(c)
    return out


def build():
    out = {}
    for kind, R in sorted(KINDS.items()):
        base = flame(kind, R)
        for b, k in enumerate(BUCKETS):
            s = R * k
            w = 9 * s + 2000 * k                              # the world-space trails stay behind a moving ship: the box covers them
            out['fx_sky_flame_%s_%d' % (kind, b)] = effect(scaled(base, k), (-4 * s, -w, -w), (24 * s + 6000 * k, w, w))
    for hue in ('cyan', 'orange'):
        for tag, S in GLINT:
            g = 3 * S + 1500                                  # its streak is left in the sky behind a far ship
            out['fx_sky_glint_%s_%s' % (hue, tag)] = effect(glint(hue, S), (-g, -g, -g), (g, g, g))
    for tag, S in SATS:                                       # v4 satellites
        out['fx_sky_sat_' + tag] = effect(satellite(S), (-2 * S, -2 * S, -2 * S), (2 * S, 2 * S, 2 * S))
    for b, k in enumerate(WORM_BUCKETS):
        Rw = WORM_R * k
        box = ((-5 * Rw,) * 3, (5 * Rw,) * 3)
        out['fx_sky_worm_open_%d' % b] = effect(worm_open(Rw), *box)
        out['fx_sky_worm_burst_%d' % b] = effect(worm_burst(Rw), *box)
        out['fx_sky_worm_close_%d' % b] = effect(worm_close(Rw), *box)
    for tag, (v, L) in STARS.items():
        reach = v * L / 1000.0
        out['fx_sky_star_' + tag] = effect(star(v, L), (-200, -200, -200), (reach + 200, 200, 200))
    out['fx_sky_star_trail'] = effect(star_trail(), (-200, -200, -200), (200, 200, 200))
    reach = FIREBALL[0] * FIREBALL[1] / 1000.0
    for hue in ('o', 'g'):
        out['fx_sky_fireball_' + hue] = effect(fireball(hue), (-600, -600, -600), (reach + 1500, 600, 600))
        out['fx_sky_fireball_trail_' + hue] = effect(fireball_trail(hue), (-600, -600, -600), (600, 600, 600))
        out['fx_sky_fireball_burst_' + hue] = effect(fireball_burst(hue), (-1500, -1500, -1500), (1500, 1500, 1500))
    out['fx_sky_fireball_frag'] = effect(fireball_frag(), (-300, -300, -300), (300, 300, 300))
    out.update(v2_lights())
    out['fx_sky_eng_gunship'] = jump_title_gunship()
    return refine_surface_detail(out)


# Session 61's first-jump crash scene (_tod_jump_title.csc) plays this ONE effect on each gunship's tag_origin (its two
# ships hang in front of the sign at full size). It is the fleet's own plasma flame at each exported gunship nozzle, turned
# aft (tag_origin's +X is the ship's nose), so that scene's engines match the fleet's without touching its script.
def jump_title_gunship():
    m = json.loads((ROOT / 'art/sky_ships/manifest.json').read_text(encoding='utf-8'))
    nozzles = [r for r in m['ships'] if r['ship'] == 'gunship'][0]['nozzles']
    els = []
    for i, (x, y, z, r) in enumerate(nozzles):
        for e in scaled(flame('plasma', KINDS['plasma']), r / KINDS['plasma']):
            E.turn_about_z(e)
            E.shift(e, x, y, z)
            e.name = '%s_%d' % (e.name, i)
            els.append(e)
    xs = [n[0] for n in nozzles]
    w = max(abs(n[1]) for n in nozzles) + 9 * KINDS['plasma'] + 2000
    return effect(els, (min(xs) - 24 * KINDS['plasma'] - 6000, -w, -w), (max(xs) + 4 * KINDS['plasma'], w, w))


def tables():
    return {
        'buckets': BUCKETS, 'kinds': KINDS, 'glint': [[t, s] for t, s in GLINT], 'sat': [[t, s] for t, s in SATS],
        'worm_buckets': WORM_BUCKETS, 'worm_r': WORM_R,
        'stars': {k: {'speed': v, 'life_ms': L} for k, (v, L) in STARS.items()},
        'fireball': {'speed': FIREBALL[0], 'life_ms': FIREBALL[1]},
    }


def main():
    verify_surface_detail()
    fx = build()
    tab = json.dumps(tables(), indent=1, sort_keys=True) + '\n'
    for n in fx:
        assert len('tod/sky/' + n) < 63, n
    for n, t in fx.items():                                   # every child effect named must be generated
        for child in re.findall(r'"(tod/sky/[^"]+)"', t):
            assert child.split('/')[-1] in fx, (n, child)
    if '--check' in sys.argv:
        bad = [n for n, t in fx.items() if not (OUT / (n + '.efx')).exists() or (OUT / (n + '.efx')).read_text(encoding='utf-8') != t]
        stray = [p.stem for p in OUT.glob('fx_sky_*.efx') if p.stem not in fx]
        if not TABLES.exists() or TABLES.read_text(encoding='utf-8') != tab:
            bad.append('fx_tables.json')
        if bad or stray:
            print('SKY FX STALE:', ', '.join(bad + ['stray ' + s for s in stray]), '- run python tools/sky_ships/gen_fx.py')
            sys.exit(1)
        print('SKY FX OK', len(fx))
        return
    out_dir = pathlib.Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else OUT
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob('fx_sky_*.efx'):                  # retire whole: an effect this generator no longer makes
        if old.stem not in fx:
            old.unlink()
            print('SKY FX RETIRED', old.name)
    for n, t in fx.items():
        (out_dir / (n + '.efx')).write_text(t, encoding='utf-8', newline='\n')
    (out_dir / 'fx_tables.json' if '--out' in sys.argv else TABLES).write_text(tab, encoding='utf-8', newline='\n')
    print('SKY FX WRITTEN', len(fx), sorted(fx)[:6], '...')


if __name__ == '__main__':
    main()
