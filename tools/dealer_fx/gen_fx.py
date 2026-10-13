"""THE DEALER's effects (W2B, asset pack PK11, docs/199 s4), GENERATED - never hand-edit the .efx.

  python tools/dealer_fx/gen_fx.py [--root DIR]           write share/raw/fx/tod/dealer/fx_tod_dealer_*.efx under DIR (default
                                                         the repo) and retire any fx_tod_dealer_*.efx this tool no longer makes
  python tools/dealer_fx/gen_fx.py --check [--root DIR]   regenerate in memory, validate, FAIL (exit 1) if a written effect
                                                         differs byte for byte, is missing, or a stray .efx sits in the folder
  python tools/dealer_fx/gen_fx.py --report               the per-effect element / particle / light summary

User 2026-09-30: "a persisting black shadow coming off of his character"; docs/199 s4: "a burst at the face (fragments,
sparks, the right eye's wire dies)"; the body that "blinks out of existence" at his death (PK11). THE EIGHT EFFECTS
(effect path = tod/dealer/<name>; _tod_dealer_finale.gsc #precaches and plays every one on a tag_origin CARRIER - never a
bare PlayFX, never PlayFXOnTag on the actor; LOCKSTEP: the EFFECTS table here, its TOD_DEALER_FX_* defines, and the zone's
fx lines written by tools/dealer_boss/wire.py):

  fx_tod_dealer_aura          STATE ONE, LOOPING on a carrier LINKED to his j_spine4 (bone axes: +X up the spine, so the
                              torso's height runs along local X): black lit smoke peeling off the coat and rising (the
                              "black shadow"), a dark veil off the lower coat and hem, faint oxblood soul wisps inside it,
                              a few red embers drifting up. No light: he is a shadow.
  fx_tod_dealer_aura_cracked  STATE TWO (swapped in at the MASK CRACK): the same shadow, hotter - more and brighter embers,
                              oxblood souls burning red, red soul-flame licking out of the cracked chest and collar, and
                              ONE small shadowless red light riding him (the "hotter red variant" of the brief).
  fx_tod_dealer_aura_trail    BOTH STATES, LOOPING on a carrier linked to his tag_origin at the floor (angles 0: +Z up):
                              a low pool of black mist round his feet that he leaves behind as he moves (the Keeper's mist
                              trail's role), with thin dark tendrils curling up out of it.
  fx_tod_dealer_arrive        ONE-SHOT at the gate he rises through (+Z up), ~1.3 s = TOD_DEALER_PORTAL_SECS: black mist
                              floods the floor, a black column tears up through the spot and swallows the moment he
                              appears, a red neon flare blooms in its heart, a dark shock ring runs over the floor, embers
                              and sparks are thrown out, one short red light, and the column thins to reveal him.
  fx_tod_dealer_mask_shatter  ONE-SHOT on a carrier linked to his tag_eye (+X = out of the face): a red-white crack flash,
                              charcoal mask shards and chips thrown off the face and falling, a red spark burst, a black
                              smoke puff from the wound, one short red light.
  fx_tod_dealer_eye_die       ONE-SHOT, ~2 s, at the RIGHT eye socket (the dead X of the cracked mask): five sputtering
                              spark spits, each weaker, a red glint dying with them, a thread of black smoke.
  fx_tod_dealer_death         ONE-SHOT at the floor under him (+Z up), ~2.5 s: a red flash at the chest, the mask's shards
                              thrown and falling, a BLACK SOUL COLUMN tearing up out of him, red souls racing up inside it,
                              a fountain of embers, a dark shock ring and a black dust wave over the floor, one short light.
  fx_tod_dealer_dissolve      LOOPING on a carrier at his body for the last ~3.6 s of the corpse (+Z up): the body burns
                              away into black ash and embers with a dull red burn and a dim red light, and at 1.85 s a
                              last black billow swallows the body the moment the script deletes it (no blink-out).

THE BUILDER IS THE SKY FLEET'S (tools/sky_ships/gen_fx.py mk() / effect() / graph(), through the lucky set's helpers and its
validate(): tools/lucky/make_fx.py), both imported READ-ONLY under this tool's own module names (never modified; no
bytecode written). Its templates are the fleet's vendored donors; the Dealer's DARK smoke, embers, sparks, shards, shock
ring and flare are stock BO3 elements read READ-ONLY from the workspace's private tools root (the jump title's lane,
tools/jump_title/gen_fx.py) and PINNED by sha256 (DONORS below): a changed donor fails generation instead of silently
changing the look. Every visible number is rewritten here. Engine rules the numbers depend on (lucky set, read off stock):
sizes / offsets / velocities in world units; velGraph0 = the effect's LOCAL frame, velGraph1 = the WORLD's (every rise here
is world +Z, so smoke rises on any bone's tilt); gravity = percent of world gravity (positive falls); a looping element's
loop count 0 = forever; fadeOutRange = the NEAR-camera fade (the flashes fade inside ~60-180 u, nothing big or bright at a
camera). BLACK SMOKE NEEDS A LIT MATERIAL: an additive (_em) sprite cannot darken anything, so every "black" element is a
_lit smoke template (gfx_*_high_dark_lit / gfx_fog_*_lit) with a near-black colour; the red is emissive.

THE COST (validate(): <= 200 live particles per effect, every light shadowless, in all four lighting states, radius <= 400,
one at a time): two loops ride him at once (aura + trail), ~70 particles and one small light at most; the bursts are short.
"""
import argparse
import hashlib
import importlib.util
import math
import pathlib
import sys

sys.dont_write_bytecode = True        # the sky fleet's / lucky set's folders are read-only here

REPO = pathlib.Path(__file__).resolve().parents[2]
LUCKY = REPO / 'tools/lucky/make_fx.py'
PRIVATE_FX = pathlib.Path(r'C:\BO3Tools\TOD2Cybercity\share\raw\fx')
PREFIX = 'tod/dealer/'
OUT_REL = ('share', 'raw', 'fx', 'tod', 'dealer')


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = load(LUCKY, 'dealer_lucky_fx_lib')   # its own module instance: patching its PREFIX touches nobody else
S, E = L.S, L.E
L.PREFIX = PREFIX
spread, in_world, near_fade = L.spread, L.in_world, L.near_fade

# ---- the Dealer's templates: stock elements from the private tools root, pinned by sha256 -----------------------------------
# key: (donor effect, element name, expected visual type, expected first material, donor sha256)
DONORS = {
    'dark_wisp':   ('dlc1/castle/fx_wolf_ink_walk_body', 'wraith_looping_def9', 'billboardSprite', 'gfx_smk_whisp_anim_high_dark_lit'),
    'dark_billow': ('dlc1/castle/fx_ee_keeper_teleport', 'wraith_oneshot_def5', 'billboardSprite', 'gfx_smk_billow_whisp_anim_high_dark_lit'),
    'dark_fog':    ('dlc1/castle/fx_ee_keeper_teleport', 'wraith_looping_def0', 'billboardSprite', 'gfx_fog_slow_md_anim_lit'),
    'em_wisp':     ('dlc1/castle/fx_keeper_ghost_ambient_torso_os', 'wraith_oneshot_def0', 'billboardSprite', 'gfx_smk_whisp_anim_em'),
    'ember':       ('dlc4/genesis/fx_keeperprot_360_attack', 'wraith_oneshot_def16', 'billboardSprite', 'gfx_debris_embers_em_i1024'),
    'spark_blink': ('dlc1/castle/fx_ee_keeper_teleport', 'wraith_oneshot_def8', 'billboardSprite', 'gfx_spark_blink_anim_em'),
    'spark_omni':  ('zombie/fx_keeper_death_zod_zmb', 'wraith_oneshot_def7', 'billboardSprite', 'gfx_spark_omni_em'),
    'flame':       ('zombie/fx_keeper_death_zod_zmb', 'wraith_oneshot_def4', 'billboardSprite', 'gfx_fire_flame_base_1_anim_em'),
    'shard':       ('dlc1/castle/fx_ee_keeper_body_billowing_zmb', 'wraith_looping_def1', 'billboardSprite', 'gfx_gib_concrete_02_lit'),
    'shock_dark':  ('dlc4/genesis/fx_apothicon_fury_spawn_in_exp', 'wraith_looping_def1', 'billboardSprite', 'gfx_shockwave_anim_lit_nocull'),
    'flare':       ('dlc4/genesis/fx_keeperprot_spawn', 'wraith_oneshot_def2', 'billboardSprite', 'gfx_light_taillight_em_i1024'),
}
DONOR_SHA = {
    'dlc1/castle/fx_wolf_ink_walk_body': None, 'dlc1/castle/fx_ee_keeper_teleport': None,
    'dlc1/castle/fx_keeper_ghost_ambient_torso_os': None, 'dlc4/genesis/fx_keeperprot_360_attack': None,
    'zombie/fx_keeper_death_zod_zmb': None, 'dlc1/castle/fx_ee_keeper_body_billowing_zmb': None,
    'dlc4/genesis/fx_apothicon_fury_spawn_in_exp': None, 'dlc4/genesis/fx_keeperprot_spawn': None,
}
DONOR_SHA_FILE = pathlib.Path(__file__).with_name('donor_sha.txt')   # "<sha256>  <donor>" per line (the pin)


def donor_path(d):
    return PRIVATE_FX / (d.replace('/', '\\') + '.efx')


def register_templates():
    pins = {}
    if DONOR_SHA_FILE.exists():
        for ln in DONOR_SHA_FILE.read_text(encoding='utf-8').splitlines():
            if ln.strip():
                h, d = ln.split(None, 1)
                pins[d.strip()] = h
    for key, (d, name, vis, mat) in DONORS.items():
        p = donor_path(d)
        if not p.exists():
            sys.exit('DEALER FX: donor %s is missing from the private tools root %s' % (d, PRIVATE_FX))
        raw = p.read_bytes()
        if b'gfx_debug_missing_fx' in raw:
            sys.exit('DEALER FX: donor %s is a gfx_debug_missing_fx stub' % d)
        h = hashlib.sha256(raw).hexdigest()
        if d in pins and pins[d] != h:
            sys.exit('DEALER FX: donor %s changed (sha %s, pinned %s) - read what changed, then re-pin with --pin' % (d, h[:12], pins[d][:12]))
        DONOR_SHA[d] = h
        fx = E.load(p)
        idx = next((i for i, e in enumerate(fx.elements) if e.name == name), None)
        if idx is None:
            sys.exit('DEALER FX: donor %s has no element %s' % (d, name))
        S.TPL[key] = (str(p), idx)
        S.EXPECT[key] = (vis, mat)


def el(tkey, name, **kw):
    """one element from a template (mk() sets every visible number), no element sounds, no water-only draw flags"""
    e = S.mk(tkey, name, **kw)
    if e.has('extraFlags'):
        e.set_flags('extraFlags', remove=('overwaterOnly', 'underwaterOnly'))
    for key in ('elemSpawnSound', 'elemFollowSound'):
        if e.has(key):
            e.get(key).body = []
    for key in ('emission', 'fxOnImpact', 'attachment'):
        if e.has(key):
            e.set(key, '""')
    return e


def light(name, color, radius, intensity, every=450, life=500, curve=None, org=(0, 0, 0), oneshot=False, delay=0):
    """A REAL dynamic light (the haven heart / golden zombie recipe: the stock perk glow's light_small, white in its def,
    the hue on colorGraph, shadowless, in every lighting state). Looping: two crossfading so the curve is what you see.
    One-shot: one flash of `life` ms after `delay`."""
    donor = E.load(S.GLOW_DONOR)
    e = [x for x in donor.elements if x.name == 'light_small'][0].copy()
    e.name = name
    e.set_flags('flags', remove=('spawnFrustumCull',))
    e.set('spawnRange', (0, L.LIGHT_RANGE))
    for ax, v in zip('XYZ', org):
        e.set('spawnOrg' + ax, (v, 0))
    e.set('spawnDelayMsec', (delay, 0))
    e.set('lifeSpanMsec', (life, 0))
    if oneshot:
        e.set_flags('editorFlags', remove=('looping',))
        e.set('spawnLooping', (1, 0))
        e.set('spawnOneShot', (1, 0))
        if curve is None:
            curve = [(0, 0), (0.12, 1), (0.55, 0.6), (1, 0)]
    else:
        e.set('editorFlags', 'looping')
        e.set('spawnLooping', (every, 0))
        if curve is None:
            fade = (life - every) / life
            curve = [(0, 0), (fade, 1), (1 - fade, 1), (1, 0)]
    S.graph(e, 'lightIntensityGraph', intensity, curve)
    S.graph(e, 'lightRadiusGraph', radius, [(0, 1), (1, 1)])
    S.graph(e, 'colorGraph', 1.0, [(0,) + tuple(color), (1,) + tuple(color)])
    S.graph(e, 'alphaGraph', 1.0, [(0, 1), (1, 1)])
    for it in e.items:
        if isinstance(it, E.Block) and it.key == 'dynamicLight2':
            body = []
            for ln in it.body:
                key = ln.strip().split(' ')[0]
                tabs = ln[:len(ln) - len(ln.lstrip())]
                if key == '_color':
                    ln = tabs + '_color 1 1 1'
                elif key == 'radius':
                    ln = tabs + 'radius %d' % radius
                body.append(ln)
            it.body = body
    return e


# ---- colour (linear RGB) -------------------------------------------------------------------------------------------------
BLACK = (0.030, 0.011, 0.011)          # lit smoke: black with a whisper of oxblood (his lining)
BLACK_HOT = (0.050, 0.010, 0.009)      # state two's smoke, a shade redder
OXBLOOD = (0.42, 0.03, 0.025)          # his lining / the mask's red
OX_HOT = (0.86, 0.07, 0.035)
EMBER = (1.0, 0.24, 0.06)
EMBER_HOT = (1.0, 0.34, 0.10)
EMBER_DEEP = (0.55, 0.04, 0.02)
NEON = (1.0, 0.10, 0.09)               # the mask's neon X
FLASH = (1.0, 0.42, 0.30)              # a red-white crack flash
CHARCOAL = (0.12, 0.115, 0.125)        # the mask's graphite (lit: the room's light falls on the shards)
LIGHT_RED = (1.0, 0.13, 0.07)


def rise(e, v, jitter=0.35, decay=0.6):
    """world +Z drift: v*(1 - jitter)..v*(1 + jitter) at spawn, easing to `decay` of that"""
    return in_world(e, Z=(2 * v, [(0, 0.5 * (1 - jitter)), (1, 0.5 * (1 - jitter) * decay)], [(0, 0.5 * (1 + jitter)), (1, 0.5 * (1 + jitter) * decay)]))


def drift(e, v, decay=1.0, z=None):
    """a symmetric world X/Y drift (and optionally Z)"""
    axes = {'X': spread(v, decay), 'Y': spread(v, decay)}
    if z is not None:
        axes['Z'] = z
    return in_world(e, **axes)


def embers(name, hot, **kw):
    col = [(0, 1.0, 0.42, 0.14), (0.45,) + (EMBER_HOT if hot else EMBER), (1,) + EMBER_DEEP]
    return el('ember', name, color=col, alpha=[(0, 1), (0.7, 0.85), (1, 0)], spin=((0, 360), (-180, 360)), **kw)


# =========================================================================================================================
# THE AURA (looping, on j_spine4: +X runs up the spine; the coat hangs from X ~ -64 (the hem) to the shoulders at ~ +10)
# =========================================================================================================================
def aura(cracked):
    blk = BLACK_HOT if cracked else BLACK
    els = [
        # the black shadow peeling off the whole coat and rising (~23 alive, 0.55 peak each)
        rise(drift(el('dark_wisp', 'shadow', loop=(55 if cracked else 65, 0), life=(1100, 400), run='spawn',
                      org=(-58, -9, -9), org_rand=(64, 18, 18),
                      size=(42, [(0, 0.38), (0.35, 0.75), (1, 1.0)], [(0, 0.3), (0.35, 0.62), (1, 0.85)]),
                      color=blk, alpha=[(0, 0), (0.15, 0.55), (0.55, 0.38), (1, 0)], grav=(-2, 1),
                      spin=((0, 360), (-20, 40))), 8), 30),
        # a darker, slower veil off the lower coat and the hem (~12 alive, broad and soft)
        rise(drift(el('dark_billow', 'veil', loop=(190, 0), life=(1700, 400), run='spawn',
                      org=(-66, -14, -14), org_rand=(28, 28, 28),
                      size=(76, [(0, 0.45), (0.4, 0.8), (1, 1.0)]),
                      color=blk, alpha=[(0, 0), (0.2, 0.42), (0.6, 0.28), (1, 0)], spin=((0, 360), (-12, 24))), 10), 14),
        # the souls inside the shadow: faint oxblood wisps (burning red once the mask cracks)
        rise(el('em_wisp', 'souls', loop=(150 if cracked else 230, 0), life=(950, 250), run='spawn',
                org=(-44, -7, -7), org_rand=(50, 14, 14), size=(26, [(0, 0.45), (1, 1.0)]),
                color=(OX_HOT if cracked else OXBLOOD), alpha=[(0, 0), (0.25, 0.4 if cracked else 0.32), (1, 0)]), 40),
        # embers drifting up out of the coat (sparse in state one)
        rise(drift(embers('embers', cracked, loop=(120 if cracked else 280, 0), life=(1300, 500), run='spawn',
                          org=(-56, -12, -12), org_rand=(66, 24, 24), size=(2.2, [(0, 1), (1, 0.35)]),
                          grav=(-3, 2)), 14), 44 if cracked else 36, jitter=0.45),
    ]
    if cracked:
        els += [
            # the wound: red soul-flame licking out of the cracked chest and collar
            rise(el('flame', 'leak', loop=(240, 0), life=(520, 160), run='spawn', org=(-2, -6, -6), org_rand=(18, 12, 12),
                    size=(16, [(0, 0.5), (0.4, 1), (1, 0.6)]), color=[(0,) + OX_HOT, (1, 1.0, 0.25, 0.06)],
                    alpha=[(0, 0), (0.2, 0.45), (1, 0)]), 46),
            # one small shadowless red light riding him (it reads on the floor and the steps round him)
            light('glow', LIGHT_RED, 110, 160, org=(8, 0, 0)),
        ]
    return els


# =========================================================================================================================
# THE TRAIL (looping, on his tag_origin at the floor, angles 0: +Z up)
# =========================================================================================================================
def trail():
    return [
        # the black pool round his feet, left behind as he glides (~11 alive; ~0.12 mean alpha each where they stack)
        rise(drift(el('dark_fog', 'pool', loop=(150, 0), life=(1300, 300), run='spawn', org=(-26, -26, 2), org_rand=(52, 52, 6),
                      size=(96, [(0, 0.5), (0.4, 0.85), (1, 1.05)]), color=BLACK,
                      alpha=[(0, 0), (0.25, 0.24), (0.7, 0.15), (1, 0)], spin=((0, 360), (-10, 20))), 14), 5),
        # thin dark tendrils curling up out of it
        rise(drift(el('dark_wisp', 'tendrils', loop=(150, 0), life=(900, 300), run='spawn', org=(-18, -18, 0), org_rand=(36, 36, 14),
                      size=(26, [(0, 0.35), (0.5, 0.8), (1, 1.0)]), color=BLACK,
                      alpha=[(0, 0), (0.2, 0.5), (1, 0)], spin=((0, 360), (-30, 60))), 6), 22),
    ]


# =========================================================================================================================
# THE ARRIVAL (one-shot at the gate, +Z up): he appears at t=0 inside the column; the column thins by ~1.3 s
# =========================================================================================================================
def arrive():
    return [
        rise(drift(el('dark_fog', 'flood', oneshot=(7, 0), life=(1500, 400), run='spawn', org=(-40, -40, 0), org_rand=(80, 80, 8),
                      size=(120, [(0, 0.3), (0.3, 0.9), (1, 1.15)]), color=BLACK,
                      alpha=[(0, 0), (0.12, 0.55), (0.6, 0.3), (1, 0)], spin=((0, 360), (-15, 30))), 30, decay=0.4), 6),
        rise(el('dark_billow', 'cloak', oneshot=(6, 0), life=(900, 200), run='spawn', org=(-10, -10, 8), org_rand=(20, 20, 64),
                size=(56, [(0, 0.6), (0.2, 0.9), (1, 1.1)]), color=BLACK, alpha=[(0, 0), (0.06, 0.8), (0.6, 0.45), (1, 0)],
                spin=((0, 360), (-30, 60))), 40),
        rise(drift(el('dark_billow', 'column', oneshot=(12, 2), delay=(0, 400), life=(1200, 400), run='spawn',
                      org=(-14, -14, 0), org_rand=(28, 28, 96), size=(64, [(0, 0.35), (0.3, 0.8), (1, 1.1)]), color=BLACK,
                      alpha=[(0, 0), (0.12, 0.7), (0.6, 0.4), (1, 0)], spin=((0, 360), (-30, 60))), 10), 110, jitter=0.4, decay=0.3),
        rise(el('em_wisp', 'heart', oneshot=(8, 2), delay=(0, 350), life=(800, 250), run='spawn', org=(-10, -10, 16), org_rand=(20, 20, 70),
                size=(34, [(0, 0.4), (1, 1.0)]), color=OX_HOT, alpha=[(0, 0), (0.2, 0.5), (1, 0)]), 50),
        near_fade(el('flare', 'flare', oneshot=(1, 0), delay=(120, 0), life=(520, 0), org=(0, 0, 56),
                     size=(190, [(0, 0.15), (0.18, 1), (1, 0.6)]), color=NEON, alpha=[(0, 0), (0.12, 0.78), (0.5, 0.3), (1, 0)]), 60, 120),
        el('shock_dark', 'ring', oneshot=(1, 0), delay=(80, 0), life=(560, 0), org=(0, 0, 6),
           size=(300, [(0, 0.1), (0.5, 0.8), (1, 1.0)]), color=(0.02, 0.004, 0.004), alpha=[(0, 0.85), (1, 0)]),
        drift(embers('embers', True, oneshot=(26, 6), delay=(100, 200), life=(1100, 500), run='spawn', org=(-16, -16, 10),
                     org_rand=(32, 32, 70), size=(2.2, [(0, 1), (1, 0.4)]), grav=(18, 10)), 60, decay=0.5,
              z=(150, [(0, 0.25), (1, 0.05)], [(0, 0.75), (1, 0.2)])),
        drift(el('spark_blink', 'sparks', oneshot=(14, 4), delay=(110, 60), life=(600, 250), run='spawn', org=(0, 0, 50),
                 size=(1.4, [(0, 1), (1, 0.5)]), color=[(0, 1.0, 0.45, 0.2), (1, 1.0, 0.08, 0.04)], alpha=[(0, 1), (0.6, 0.9), (1, 0)],
                 grav=(45, 10)), 140, decay=0.6, z=(160, [(0, -0.2), (1, -0.1)], [(0, 0.8), (1, 0.4)])),
        light('flash', LIGHT_RED, 260, 420, life=600, org=(0, 0, 50), oneshot=True, delay=100),
    ]


# =========================================================================================================================
# THE MASK SHATTER (one-shot on tag_eye: +X = out of the face, +Z up the head)
# =========================================================================================================================
def mask_shatter():
    return [
        near_fade(el('spark_omni', 'flash', oneshot=(1, 0), life=(160, 0), size=(26, [(0, 0.6), (0.3, 1), (1, 0.8)]),
                     color=FLASH, alpha=[(0, 1), (1, 0)]), 40, 80),
        el('shard', 'shards', oneshot=(9, 3), life=(950, 300), run='spawn', org=(1, -3, -3), org_rand=(2, 6, 6),
           vel={'X': (150, [(0, 0.6), (1, 0.5)], [(0, 1.0), (1, 0.8)]), 'Y': spread(110, 0.8), 'Z': spread(90, 0.8)},
           grav=(70, 20), size=(2.6, [(0, 1), (1, 0.9)]), color=CHARCOAL, alpha=[(0, 1), (0.8, 1), (1, 0)],
           spin=((0, 360), (-720, 1440))),
        el('shard', 'chips', oneshot=(14, 4), life=(800, 300), run='spawn', org=(1, -3, -3), org_rand=(2, 6, 6),
           vel={'X': (210, [(0, 0.6), (1, 0.5)], [(0, 1.0), (1, 0.8)]), 'Y': spread(150, 0.8), 'Z': spread(120, 0.8)},
           grav=(80, 20), size=(1.3, [(0, 1), (1, 0.8)]), color=CHARCOAL, alpha=[(0, 1), (0.8, 1), (1, 0)],
           spin=((0, 360), (-900, 1800))),
        el('spark_blink', 'sparks', oneshot=(24, 6), life=(480, 240), run='spawn',
           vel={'X': (170, [(0, 0.4), (1, 0.2)], [(0, 1.0), (1, 0.5)]), 'Y': spread(120, 0.6), 'Z': spread(120, 0.6)},
           grav=(40, 10), size=(1.1, [(0, 1), (1, 0.5)]), color=[(0, 1.0, 0.35, 0.12), (1,) + EMBER_DEEP], alpha=[(0, 1), (0.7, 0.9), (1, 0)]),
        rise(el('dark_wisp', 'puff', oneshot=(5, 1), delay=(20, 0), life=(1300, 300), run='spawn', org=(2, -2, -2), org_rand=(2, 4, 4),
                vel={'X': (24, [(0, 0.5), (1, 0.2)], [(0, 1.0), (1, 0.3)])}, size=(16, [(0, 0.4), (1, 1.3)]), color=BLACK,
                alpha=[(0, 0), (0.1, 0.65), (1, 0)], spin=((0, 360), (-40, 80))), 14),
        light('flash_light', LIGHT_RED, 150, 380, life=260, oneshot=True, curve=[(0, 1), (0.4, 0.6), (1, 0)]),
    ]


# =========================================================================================================================
# THE RIGHT EYE DIES (one-shot ~2 s at the right socket, on tag_eye: +X out of the face)
# =========================================================================================================================
SPUTTER = [(0, 12, 0.9), (230, 8, 0.72), (540, 6, 0.55), (980, 4, 0.38), (1520, 3, 0.22)]   # (delay ms, sparks, glint alpha)


def eye_die():
    els = []
    for i, (d, n, a) in enumerate(SPUTTER):
        els.append(el('spark_blink', 'spit%d' % (i + 1), oneshot=(n, max(1, n // 3)), delay=(d, 40), life=(300, 160), run='spawn',
                      vel={'X': (70, [(0, 0.5), (1, 0.3)], [(0, 1.0), (1, 0.6)]), 'Y': spread(50, 0.6), 'Z': spread(50, 0.6)},
                      grav=(40, 10), size=(1.2, [(0, 1), (1, 0.4)]), color=[(0, 1.0, 0.3, 0.1), (1, 0.9, 0.05, 0.03)],
                      alpha=[(0, 1), (0.6, 0.9), (1, 0)]))
        els.append(el('spark_omni', 'glint%d' % (i + 1), oneshot=(1, 0), delay=(d, 0), life=(110, 0), size=(9, [(0, 0.7), (0.3, 1), (1, 0.6)]),
                      color=(1.0, 0.15, 0.08), alpha=[(0, a), (1, 0)]))
    els.append(rise(el('dark_wisp', 'thread', oneshot=(6, 1), delay=(0, 1700), life=(900, 200), run='spawn',
                       vel={'X': (6, [(0, 0.5), (1, 0.2)], [(0, 1.0), (1, 0.4)])}, size=(5, [(0, 0.5), (1, 1.6)]), color=BLACK,
                       alpha=[(0, 0), (0.15, 0.5), (1, 0)]), 14))
    return els


# =========================================================================================================================
# THE DEATH (one-shot at the floor under him, +Z up; his chest is ~56 up, his head ~70)
# =========================================================================================================================
def death():
    return [
        near_fade(el('spark_omni', 'flash', oneshot=(1, 0), life=(220, 0), org=(0, 0, 56), size=(60, [(0, 0.6), (0.3, 1), (1, 0.8)]),
                     color=FLASH, alpha=[(0, 1), (1, 0)]), 60, 120),
        drift(el('shard', 'shards', oneshot=(14, 4), life=(1100, 300), run='spawn', org=(-6, -6, 64), org_rand=(12, 12, 12),
                 grav=(80, 20), size=(2.4, [(0, 1), (1, 0.9)]), color=CHARCOAL, alpha=[(0, 1), (0.85, 1), (1, 0)],
                 spin=((0, 360), (-720, 1440))), 150, decay=0.8, z=(220, [(0, 0.25), (1, 0.2)], [(0, 0.75), (1, 0.6)])),
        rise(drift(el('dark_billow', 'column', oneshot=(16, 3), delay=(0, 900), life=(1500, 400), run='spawn', org=(-14, -14, 20),
                      org_rand=(28, 28, 50), size=(70, [(0, 0.4), (0.3, 0.85), (1, 1.2)]), color=BLACK,
                      alpha=[(0, 0), (0.12, 0.72), (0.55, 0.45), (1, 0)], spin=((0, 360), (-30, 60))), 10), 95, jitter=0.4),
        rise(el('em_wisp', 'souls', oneshot=(9, 3), delay=(80, 700), life=(1000, 300), run='spawn', org=(-10, -10, 30),
                org_rand=(20, 20, 40), size=(34, [(0, 0.4), (1, 1.0)]), color=OX_HOT, alpha=[(0, 0), (0.2, 0.45), (1, 0)]), 130),
        drift(embers('embers', True, oneshot=(40, 10), delay=(0, 500), life=(1500, 700), run='spawn', org=(-18, -18, 20),
                     org_rand=(36, 36, 60), size=(2.0, [(0, 1), (1, 0.35)]), grav=(14, 10)), 70, decay=0.5,
              z=(240, [(0, 0.3), (1, 0.15)], [(0, 0.7), (1, 0.35)])),
        el('shock_dark', 'shock', oneshot=(1, 0), delay=(40, 0), life=(650, 0), org=(0, 0, 4),
           size=(380, [(0, 0.08), (0.5, 0.8), (1, 1.0)]), color=(0.02, 0.004, 0.004), alpha=[(0, 0.8), (1, 0)]),
        drift(el('dark_fog', 'dust', oneshot=(9, 2), life=(1300, 300), run='spawn', org=(-30, -30, 0), org_rand=(60, 60, 8),
                 size=(110, [(0, 0.4), (1, 1.2)]), color=BLACK, alpha=[(0, 0), (0.1, 0.5), (0.6, 0.25), (1, 0)],
                 spin=((0, 360), (-20, 40))), 220, decay=0.05),
        light('flash_light', LIGHT_RED, 300, 460, life=500, org=(0, 0, 50), oneshot=True),
    ]


# =========================================================================================================================
# THE DISSOLVE (looping on a carrier at his body; the script deletes the corpse at DISSOLVE_DELETE_MS, the carrier after)
# =========================================================================================================================
DISSOLVE_DELETE_MS = 2000      # LOCKSTEP _tod_dealer_finale.gsc TOD_DEALER_DISSOLVE_SECS (the last billow covers the delete)


def dissolve():
    return [
        rise(drift(el('dark_wisp', 'ash', loop=(45, 0), life=(1300, 400), run='spawn', org=(-34, -34, -4), org_rand=(68, 68, 14),
                      size=(24, [(0, 0.4), (0.4, 0.8), (1, 1.1)]), color=BLACK, alpha=[(0, 0), (0.18, 0.6), (0.6, 0.35), (1, 0)],
                      spin=((0, 360), (-30, 60))), 10), 44),
        rise(drift(embers('embers', True, loop=(55, 0), life=(1400, 500), run='spawn', org=(-34, -34, -4), org_rand=(68, 68, 14),
                          size=(1.8, [(0, 1), (1, 0.3)]), grav=(-3, 2)), 16), 55, jitter=0.5),
        rise(el('em_wisp', 'burn', loop=(140, 0), life=(750, 200), run='spawn', org=(-28, -28, -2), org_rand=(56, 56, 8),
                size=(22, [(0, 0.5), (1, 1.0)]), color=OX_HOT, alpha=[(0, 0), (0.25, 0.35), (1, 0)]), 30),
        rise(drift(el('dark_billow', 'last', oneshot=(10, 2), delay=(DISSOLVE_DELETE_MS - 150, 100), life=(1300, 300), run='spawn',
                      org=(-24, -24, -4), org_rand=(48, 48, 30), size=(60, [(0, 0.5), (0.3, 0.9), (1, 1.2)]), color=BLACK,
                      alpha=[(0, 0), (0.08, 0.8), (0.5, 0.45), (1, 0)], spin=((0, 360), (-30, 60))), 20), 60),
        light('burn_light', LIGHT_RED, 130, 140, org=(0, 0, 8)),
    ]


# name, builder, bounds half-size (a moving host's box reaches back over what it leaves behind)
EFFECTS = [
    ('fx_tod_dealer_aura', lambda: aura(False), 400),
    ('fx_tod_dealer_aura_cracked', lambda: aura(True), 400),
    ('fx_tod_dealer_aura_trail', trail, 400),
    ('fx_tod_dealer_arrive', arrive, 300),
    ('fx_tod_dealer_mask_shatter', mask_shatter, 260),
    ('fx_tod_dealer_eye_die', eye_die, 120),
    ('fx_tod_dealer_death', death, 360),
    ('fx_tod_dealer_dissolve', dissolve, 260),
]
NAMES = [e[0] for e in EFFECTS]


def build():
    register_templates()
    out = {}
    for name, fn, half in EFFECTS:
        out[name] = S.effect(fn(), (-half, -half, -half), (half, half, half))
    return out


def report(fx):
    for n in NAMES:
        p = E.parse(fx[n])
        peak = sum(L.peak_particles(e) for e in p.elements)
        lights = [e for e in p.elements if e.visual[0] in L.LIGHTS]
        loop = any('looping' in e.flags('editorFlags') for e in p.elements)
        print('  %-28s %-8s %2d elements, peak ~%3d particles, %d light(s)%s' % (
            n, 'looping' if loop else 'one-shot', len(p.elements), peak, len(lights),
            '' if not lights else ' r=' + ','.join('%d' % (e.graph('lightRadiusGraph').scale) for e in lights)))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--pin', action='store_true', help='record the donors\' sha256 (after reading what changed)')
    ap.add_argument('--root', default=str(REPO))
    a = ap.parse_args(argv)
    fx = build()
    if a.pin:
        DONOR_SHA_FILE.write_text(''.join('%s  %s\n' % (h, d) for d, h in sorted(DONOR_SHA.items())), encoding='utf-8')
        print('pinned', len(DONOR_SHA), 'donors ->', DONOR_SHA_FILE)
    bad = []
    for n in NAMES:
        bad += L.validate(n, fx[n], NAMES)
    if bad:
        print('DEALER FX INVALID:\n  ' + '\n  '.join(bad))
        return 1
    out = pathlib.Path(a.root).joinpath(*OUT_REL)
    if a.report:
        report(fx)
    if a.check:
        stale = []
        for n in NAMES:
            p = out / (n + '.efx')
            if not p.exists() or p.read_text(encoding='utf-8') != fx[n]:
                stale.append(n)
        strays = [p.name for p in out.glob('fx_tod_dealer_*.efx') if p.stem not in NAMES] if out.exists() else []
        if stale or strays:
            print('DEALER FX STALE: %s%s - run: python tools/dealer_fx/gen_fx.py' % (', '.join(stale), (' strays ' + ', '.join(strays)) if strays else ''))
            return 1
        print('DEALER FX OK: %d effects, every one valid (bounded particles, shadowless lights, paths <= 63)' % len(NAMES))
        return 0
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob('fx_tod_dealer_*.efx'):
        if p.stem not in NAMES:
            p.unlink()
            print('retired', p.name)
    for n in NAMES:
        p = out / (n + '.efx')
        same = p.exists() and p.read_text(encoding='utf-8') == fx[n]
        if not same:
            p.write_text(fx[n], encoding='utf-8', newline='\n')
        print('%s %s%s (%d B)' % ('unchanged' if same else 'wrote', PREFIX, n, len(fx[n])))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
