"""THE ELITES' EFFECTS (PK26, 2026-10-05): the Doppelghast's death charge + death blast, its juke smear and claw glow,
and the Mangler's death break-up. GENERATED - never hand-edit the .efx; change the tables below and re-run.

  python tools/fxgen/elites/make_fx.py                    write share/raw/fx/tod/elites/<the five effects>.efx
  python tools/fxgen/elites/make_fx.py --check            regenerate in memory, validate, FAIL (exit 1) if a written effect
                                                          differs, is missing, or a stray .efx sits in the folder
  python tools/fxgen/elites/make_fx.py --out-root DIR     write / check under DIR instead of the repo root (a stage); the
                                                          LOCKSTEP numbers are read from DIR's _tod_elite_fx.gsc first
  python tools/fxgen/elites/make_fx.py --selftest         the validators against planted faults (exit 1 if one is missed)
  python tools/fxgen/elites/make_fx.py --vendor           re-extract the donor elements from the private tools root
                                                          (refuses if a stock file's sha256 moved)

THE GAPS (tmp/asset_prod/packs/PK26-elite-vfx.json, all verified against the shipping scripts 2026-10-05):
  * The Doppelghast's death blast hurts (TOD_DOPPEL_DEATH_DAMAGE in TOD_DOPPEL_DEATH_RADIUS) 3 s after it dies, and the
    only tell was a blood spray at +0.1 s: nothing for ~2.9 s, then generic gore. Its BO6 clip names three events
    (dth_01 notetracks: frame 2 a squib, frame 5 "ghoul_death" on j_spine4, frame 90 "ghoul_death_explo_needle") that BO6
    cannot export (Saluki has no particle type), so these are composed from BO3 emitters.
  * A dead Mangler lay still for 0.8 s and vanished (corpse_cleanup: wait 3, Delete, no effect).
  * The Doppelghast's juke (juke_*_short_01 frame 11 FxOnObjectNoStop ghoul_juke) and its swipe (stn_melee_01 frames
    2-22 FxOnObject amalgam_melee_hand) had none of their BO6 effects: the juke read as a plain sidestep and the swipe had
    no visual windup.

THE FIVE EFFECTS (effect path = tod/elites/<name>; _tod_elite_fx.gsc precaches and plays them; the zone names them):
  fx_tod_doppel_death_charge  ONE-SHOT TIMELINE on a carrier that follows the corpse's torso (the script moves it each
                              server frame; a ragdoll is client-only, so nothing is linked to the body): CHARGE_MS long,
                              escalating - a red core swelling toward white, a HEARTBEAT that accelerates (one flash per
                              BEATS step), sparks rushing INTO the torso in three thickening waves, red arcs crawling the
                              body, soot curling off it, a red light that throbs with the beats. "This will explode."
  fx_tod_doppel_death_blast   ONE-SHOT on the FLOOR under the corpse at the blast (frame 90): a white-red flash, a hot
                              fireball, needles thrown out (the BO6 "explo_needle"), embers, a charcoal puff, a light flash
                              - and THE HURT ZONE: a wave of beads racing out along the floor that stops EXACTLY at
                              TOD_DOPPEL_DEATH_RADIUS, a ring of beads glowing at that edge, a flat shock under it.
  fx_tod_doppel_juke          ONE-SHOT TIMELINE on a carrier linked to j_spine4 for the juke: from the clip's frame 11
                              (JUKE_ON_MS) a dark smear left along the dodge (a charcoal smoke ribbon, soot afterimages, a
                              faint red ribbon core so it reads in the dark) and a few red sparks shed; done by ~1.1 s.
  fx_tod_doppel_claw          LOOPING on a carrier linked to the striking claw (CLAW_TAG) for the swipe (stn_melee_01 frames
                              2-22: the script deletes it after CLAW_MS): a red-hot glow on the claw, a red ribbon trailing
                              the swipe, sparks shed, a small red light.
  fx_tod_mangler_death        ONE-SHOT at the Mangler's torso as the 66-frame death clip ends: the wreck breaks up - an
                              orange-white flash, a fireball, hot scrap clumps and spark tails thrown, a fan of steam jets
                              venting for ~1.3 s, the cannon's orange arcs crackling, sparks sputtering for ~1.8 s, dark
                              smoke rising, a light that flashes and smoulders. The Mangler's own cannon palette.

FRAMES. The death charge, the blast and the Mangler burst are authored in the STOCK IMPACT FRAME: local X = UP (the floor
normal), played on carriers at angles ( -90, 0, 0 ) - the same frame as the Rune Prison's impacts through
tod_ability_fx::burst_at. Measured from the stock library: a cylinder spawn's axis 0 is local X (the rocket torch's
sparks ring its +X thrust; the stock dust impact rings), and a rotatedSprite at pitch 0 faces local X (the jetpack disc;
the slam's ground shockwave is pitched -90 because that effect plays Z-up). So in this frame axis 0 rings and pitch-0
rotated sprites lie FLAT ON THE FLOOR. The juke and the claw ride bones: they use only sphere spawns, world velocities
and world-run particles, so the bone's orientation never matters.

THE BUILDER IS THE SKY FLEET'S, through the lucky set's helpers (imported READ-ONLY, as tools/haven/make_fx.py does):
every element is a stock element (a sky-fleet template, or one of the DONOR elements below, copied element for element
into donor/ from the private tools root, each source file's sha256 and each vendored file's sha256 in
donor/provenance.json, so a generation never depends on the machine's tools root) with every visible number
rewritten here. Lights are the map's one recipe (the perk glow's light_small: white def, hue on colorGraph, shadowless,
every lighting state, at most two alive).

LOCKSTEP (read, never copied): CHARGE_MS / JUKE_ON_MS / CLAW_MS / CLAW_TAG from _tod_elite_fx.gsc (the --out-root tree's
first, then the repo's), TOD_DOPPEL_DEATH_RADIUS from _tod_doppelghast.gsc. validate() fails when the blast's ring does
not stop on the radius.

RULES THE WRITTEN FILES PASS (validate()): the effect path <= 63 characters; no gfx_debug_missing_fx; no model / runner
/ child effect / element sound; whole-millisecond times; a LOOPING effect is the only kind with a forever loop, and a
ONE-SHOT timeline ends by itself (finite loops only) within its stated length; alphas 0..1, sizes >= 0; every light
shadowless, in all four lighting states, radius 1..400, at most two alive; the particle budget (PARTICLE_BUDGET peak per
effect); THE 1P RULE - in an effect that can play at a player's face (all but the juke) every sprite wider than NEAR_MAX
fades near the camera; THE HURT ZONE - the blast's wave stops and its edge ring sits within RING_TOL of the radius.
--selftest plants nine faults and requires a catch on each.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import pathlib
import re
import sys

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
LUCKY = ROOT / 'tools/lucky/make_fx.py'
DONOR_DIR = HERE / 'donor'
PROVENANCE = DONOR_DIR / 'provenance.json'
PRIVATE_FX = pathlib.Path(r'C:\BO3Tools\TOD2Cybercity\share\raw\fx')
REL_DIR = 'share/raw/fx/tod/elites'
PREFIX = 'tod/elites/'
MODULE = 'scripts/zm/zm_tod2_cybercity/_tod_elite_fx.gsc'
DOPPEL = 'scripts/zm/zm_tod2_cybercity/_tod_doppelghast.gsc'
MAX_PATH = 63
PARTICLE_BUDGET = 160
NEAR_MAX = 32                 # the widest sprite allowed to reach a player's camera unfaded (the 1p rule)
RING_TOL = 4.0                # the hurt-zone ring must sit within this many units of TOD_DOPPEL_DEATH_RADIUS


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = load(LUCKY, 'lucky_fx_lib_elites')     # the lucky set's helpers + the sky builder (read-only)
S, E = L.S, L.E
spread, xyz, in_world, near_fade, steady, box = L.spread, L.xyz, L.in_world, L.near_fade, L.steady, L.box

# ---- the vendored DONOR elements (stock BO3; --vendor re-extracts them) ---------------------------------------------------
# key: (stock effect, (visual type, first material) of the element taken)
DONORS = {
    'debris':     ('dlc3/stalingrad/fx_raz_dest_weak_point_exp', ('billboardSprite', 'gfx_debris_clumps_em_i8')),
    'spark_tail': ('dlc3/stalingrad/fx_raz_dest_weak_point_exp', ('tail', 'gfx_spark_blink_anim_em')),
    'flame':      ('dlc3/stalingrad/fx_raz_dest_weak_point_exp', ('billboardSprite', 'gfx_fire_flame_base_2_anim_em')),
    'steam':      ('dlc3/stalingrad/fx_raz_cage_steam', ('billboardSprite', 'gfx_smk_puff_volume_varied_lit')),
    'shock_flat': ('dlc1/zmb_weapon/fx_wpn_spike_grnd_hit', ('rotatedSprite', 'gfx_shockwave_anim_em')),
}


def donor_file(stock):
    return DONOR_DIR / (stock.replace('/', '__') + '.efx')


def vendor(force=False):
    """Copy the chosen elements out of the private tools root, one file per stock effect (its header + the elements in
    their stock order, re-serialised by efx_lib), and record each stock file's sha256. Refuses when a stock file no
    longer matches the recorded sha (a mod-tools update moved it: look before you take it) unless --force."""
    DONOR_DIR.mkdir(parents=True, exist_ok=True)
    old = json.loads(PROVENANCE.read_text(encoding='utf-8')) if PROVENANCE.exists() else {}
    prov = {}
    by_stock = {}
    for key, (stock, want) in DONORS.items():
        by_stock.setdefault(stock, []).append((key, want))
    for stock, wants in sorted(by_stock.items()):
        src = PRIVATE_FX / (stock + '.efx')
        raw = src.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if stock in old and old[stock]['source_sha256'] != sha and not force:
            sys.exit('ELITE FX: the stock %s changed since it was vendored (%s -> %s); review it, then --vendor --force'
                     % (stock, old[stock]['source_sha256'][:12], sha[:12]))
        text = raw.decode('utf-8')
        if 'gfx_debug_missing_fx' in text:
            sys.exit('ELITE FX: donor %s is a stub' % stock)
        fx = E.parse(text)
        take = []
        for key, want in wants:
            idx = next((i for i, e in enumerate(fx.elements) if e.visual[0] == want[0] and e.visual[1] and e.visual[1][0] == want[1]), None)
            if idx is None:
                sys.exit('ELITE FX: %s has no %s %s element' % (stock, want[0], want[1]))
            take.append((idx, key))
        take.sort()
        out = E.Effect(fx.version, list(fx.header), [fx.elements[i] for i, _ in take])
        body = out.text()
        donor_file(stock).write_bytes(body.encode('utf-8'))
        prov[stock] = {'source_sha256': sha, 'vendored_sha256': hashlib.sha256(body.encode('utf-8')).hexdigest(),
                       'elements': {key: i for i, key in take}}
    PROVENANCE.write_text(json.dumps(prov, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    print('ELITE FX DONORS VENDORED: %d stock effects -> %s' % (len(prov), DONOR_DIR.relative_to(ROOT)))
    return 0


def donor_problems():
    """The vendored donors are the bytes provenance.json recorded (a hand edit or a partial vendor fails here)."""
    bad = []
    if not PROVENANCE.exists():
        return ['donor/provenance.json missing - run --vendor']
    prov = json.loads(PROVENANCE.read_text(encoding='utf-8'))
    for stock in sorted({s for s, _ in DONORS.values()}):
        p = donor_file(stock)
        if stock not in prov or not p.exists():
            bad.append('donor %s missing - run --vendor' % stock)
        elif hashlib.sha256(p.read_bytes()).hexdigest() != prov[stock]['vendored_sha256']:
            bad.append('donor %s changed since it was vendored' % stock)
    return bad


def register_donors():
    """Teach the sky builder our donor keys: template() resolves DON / <absolute path> to the absolute path."""
    for key, (stock, want) in DONORS.items():
        fx = E.load(donor_file(stock))
        idx = next(i for i, e in enumerate(fx.elements) if e.visual[0] == want[0] and e.visual[1][0] == want[1])
        S.TPL[key] = (str(donor_file(stock)), idx)
        S.EXPECT[key] = want


def el(tkey, name, **kw):
    """The lucky set's el(), minus the water-only draw flags and element sounds some donors carry (scripts own sounds)."""
    e = L.el(tkey, name, **kw)
    if e.has('extraFlags'):
        e.set_flags('extraFlags', remove=('overwaterOnly', 'underwaterOnly'))
    for key in ('elemSpawnSound', 'elemFollowSound'):
        if e.has(key):
            e.get(key).body = []
    return e


def pitch(e, deg):
    """A rotated sprite's facing: pitch 0 faces local X (the floor normal in the impact frame)."""
    e.set('spawnAnglePitch', [deg, 0])
    return e


def offset_frame(e):
    """Velocity in the spawn OFFSET's frame (runRelToOffset: X = radially out from the spawn's centre / axis)."""
    e.set_flags('flags', add=('runRelToOffset',), remove=('runRelToEffect', 'runRelToWorld', 'runRelToSpawn'))
    return e


def r3(v):
    return round(v, 3)


# ---- LOCKSTEP: the numbers the scripts own --------------------------------------------------------------------------------
def gsc_text(rel, out_root):
    for base in (out_root, ROOT):
        p = base / rel
        if p.exists():
            return p.read_text(encoding='utf-8')
    raise SystemExit('ELITE FX: cannot read %s (neither under %s nor the repo)' % (rel, out_root))


def gsc_num(text, name):
    m = re.search(r'#define\s+%s\s+(-?[\d.]+)' % name, text)
    if not m:
        raise SystemExit('ELITE FX: #define %s not found' % name)
    return float(m.group(1))


def gsc_str(text, name):
    m = re.search(r'#define\s+%s\s+"([^"]+)"' % name, text)
    if not m:
        raise SystemExit('ELITE FX: #define %s not found' % name)
    return m.group(1)


class Clock:
    """The scripts' numbers this generator builds against."""
    def __init__(self, out_root):
        mod, dop = gsc_text(MODULE, out_root), gsc_text(DOPPEL, out_root)
        self.charge_ms = int(gsc_num(mod, 'TOD_ELITE_FX_CHARGE_MS'))
        self.juke_on_ms = int(gsc_num(mod, 'TOD_ELITE_FX_JUKE_ON_MS'))
        self.juke_ms = int(round(gsc_num(mod, 'TOD_ELITE_FX_JUKE_SECS') * 1000))
        self.claw_ms = int(round(gsc_num(mod, 'TOD_ELITE_FX_CLAW_SECS') * 1000))
        self.claw_tag = gsc_str(mod, 'TOD_ELITE_FX_CLAW_TAG')
        self.mangler_ms = int(round(gsc_num(mod, 'TOD_ELITE_FX_MANGLER_SECS') * 1000))
        self.blast_ms = int(round(gsc_num(mod, 'TOD_ELITE_FX_BLAST_SECS') * 1000))
        self.radius = gsc_num(dop, 'TOD_DOPPEL_DEATH_RADIUS')


# ---- colour (linear RGB) -------------------------------------------------------------------------------------------------
# THE DOPPELGHAST: the charcoal horde's palette (CLAUDE.md: gray / black / red only; the eyes' pure red, hue 0)
BLOOD = (0.50, 0.025, 0.02)        # deep red: the charge's first breath
RED = (1.0, 0.09, 0.05)            # the elite red
HOT = (1.0, 0.34, 0.16)            # red-hot
WHITE_HOT = (1.0, 0.88, 0.80)      # the instant before it goes
EMBER = (1.0, 0.40, 0.14)
SOOT = (0.075, 0.07, 0.07)         # charcoal smoke (a LIT material: it reads as a dark shape, lit red by the charge light)
SMEAR = (0.45, 0.02, 0.02)         # the juke's faint emissive smear (just enough to read in the dark)
# THE MANGLER: its cannon's orange (hb/mangler/fx_hb_mangler_cannon_idle colorGraph 1 .28 .025)
M_ORANGE = (1.0, 0.28, 0.025)
M_HOT = (1.0, 0.60, 0.28)
M_WHITE = (1.0, 0.90, 0.74)
M_SCRAP = (0.42, 0.20, 0.10)       # cooling scrap (an emissive debris clump: dim, never a second fire)
STEAM = (0.60, 0.60, 0.62)         # lit steam
SMOKE = (0.13, 0.12, 0.12)         # lit dark smoke
# THE LIGHTS (the perk glow's recipe; a light exists where someone can see what it lights)
LIGHT_RANGE = L.LIGHT_RANGE


def light_el(name, color, radius, intensity, life, curve=None, every=None, delay=0, org=(0, 0, 0)):
    """One dynamic light (tools/haven/make_fx.py heart_light, generalised): looping (every = interval; two crossfading
    through their overlap) or one-shot (every None: a single light of `life` ms whose intensity is `curve`)."""
    donor = E.load(S.GLOW_DONOR)
    e = [x for x in donor.elements if x.name == 'light_small'][0].copy()
    e.name = name
    e.set_flags('flags', remove=('spawnFrustumCull',))
    e.set('spawnRange', (0, LIGHT_RANGE))
    e.set('spawnOrgX', (org[0], 0))
    e.set('spawnOrgY', (org[1], 0))
    e.set('spawnOrgZ', (org[2], 0))
    e.set('spawnDelayMsec', (delay, 0))
    e.set('lifeSpanMsec', (life, 0))
    if every is None:
        e.set_flags('editorFlags', remove=('looping',))
        e.set('spawnLooping', (1, 0))
        e.set('spawnOneShot', (1, 0))
        if curve is None:
            curve = [(0, 0), (0.1, 1), (0.5, 0.6), (1, 0)]
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
            for line in it.body:
                key = line.strip().split(' ')[0]
                tabs = line[:len(line) - len(line.lstrip())]
                if key == '_color':
                    line = tabs + '_color 1 1 1'
                elif key == 'radius':
                    line = tabs + 'radius %d' % radius
                body.append(line)
            it.body = body
    e.lucky_template = 'light'
    return e


# =========================================================================================================================
# THE DOPPELGHAST'S DEATH CHARGE (one-shot timeline on the torso carrier; local X = up)
# =========================================================================================================================
def beats(total_ms):
    """The heartbeat: ten gaps that shrink by a constant 0.8, scaled so the last beat lands 30 ms before the end."""
    gaps = [0.8 ** i for i in range(10)]
    k = (total_ms - 30) / sum(gaps)
    out, t = [0], 0.0
    for g in gaps:
        t += g * k
        out.append(int(round(t)))
    return out


def charge(c):
    T = c.charge_ms
    B = beats(T)
    els = [
        # the core: a red glow in the torso swelling toward white over the whole charge
        near_fade(el('orb', 'core', oneshot=(1, 0), life=(T, 0), size=(24, [(0, 0.35), (0.55, 0.55), (0.85, 0.8), (1, 1.0)]),
                     color=[(0,) + BLOOD, (0.55,) + RED, (0.9,) + HOT, (1,) + WHITE_HOT],
                     alpha=[(0, 0), (0.06, 0.4), (0.6, 0.55), (0.92, 0.8), (1, 0.85)]), 24, 40),
    ]
    # the heartbeat: one flash per beat, growing, heating (red -> red-hot, a white heart only on the last beats), the gaps
    # shrinking; never wider than the body (the blast's own flash is the big one)
    for i, ms in enumerate(B):
        k = i / (len(B) - 1)
        hot = tuple(RED[j] + (HOT[j] - RED[j]) * k for j in range(3))
        col = tuple(r3(hot[j] + (WHITE_HOT[j] - hot[j]) * max(0.0, k - 0.75) * 2.0) for j in range(3))
        gap = (B[i + 1] - ms) if i + 1 < len(B) else 60
        els.append(near_fade(el('glow', 'beat_%02d' % i, oneshot=(1, 0), life=(max(50, min(150, int(gap * 0.8))), 0), delay=(ms, 0),
                                size=(r3(18 + 18 * k), [(0, 0.7), (0.25, 1), (1, 1.05)]), color=col,
                                alpha=[(0, r3(0.3 + 0.45 * k)), (1, 0)]), 24, 40))
    # sparks rushing INTO the torso, three thickening waves (spawned on a ball round it, flying home along the offset;
    # the last wave's last spark lands as the charge ends - the carrier is deleted at the blast)
    for i, (t0, t1, n) in enumerate(((0, T * 0.34, 6), (T * 0.34, T * 0.66, 12), (T * 0.66, T - 380, 22))):
        els.append(offset_frame(el('incand', 'rush_%d' % (i + 1), oneshot=(n, 0), life=(300, 60), delay=(int(t0), int(t1 - t0)),
                                   offset='sphere', off_r=(48, 12), size=(3.2, [(0, 0.6), (0.6, 1), (1, 0.4)]),
                                   vel={'X': (-150, [(0, 1.0), (1, 0.6)])},
                                   color=[(0,) + HOT, (1,) + WHITE_HOT], alpha=[(0, 0), (0.15, 1), (0.8, 0.9), (1, 0)])))
    # red arcs crawling the body, more and more of them
    for i, (t0, t1, n) in enumerate(((T * 0.08, T * 0.45, 3), (T * 0.45, T * 0.76, 6), (T * 0.76, T - 180, 10))):
        els.append(el('arc', 'arcs_%d' % (i + 1), oneshot=(n, 0), life=(110, 60), delay=(int(t0), int(t1 - t0)), offset='sphere',
                      off_r=(8, 12), size=(r3(16 + 5 * i), [(0, 0.7), (0.5, 1), (1, 0.8)]), color=[(0,) + RED, (1,) + HOT],
                      alpha=[(0, 0.9), (0.5, 0.55), (1, 0)]))
    els += [
        # soot curling off the body (a lit charcoal: dark against the light, red where the charge light catches it)
        near_fade(in_world(el('smoke', 'soot', oneshot=(7, 0), life=(1300, 300), delay=(80, T - 1700), run='world', offset='sphere', off_r=(6, 10),
                              size=(28, [(0, 0.6), (1, 1.6)]), color=SOOT, alpha=[(0, 0), (0.2, 0.3), (1, 0)]),
                           X=spread(10), Y=spread(10), Z=(26, [(0, 0.6), (1, 0.4)], [(0, 1), (1, 0.7)])), 24, 48),
        # embers lifting off it
        in_world(el('incand', 'embers', oneshot=(14, 0), life=(700, 300), delay=(250, T - 1300), run='world', offset='sphere',
                    off_r=(6, 14), size=(2.4, [(0, 1), (1, 0.3)]), color=[(0,) + EMBER, (1,) + RED],
                    alpha=[(0, 1), (0.5, 0.7), (1, 0)], grav=(-6, 4)),
                 X=spread(30), Y=spread(30), Z=(40, [(0, 0.5), (1, 0.3)], [(0, 1), (1, 0.6)])),
    ]
    # the light throbs with the beats and climbs (a single one-shot light; the curve is the heartbeat)
    rows, base = [(0, 0)], 0.12
    for i, ms in enumerate(B):
        k = i / (len(B) - 1)
        t = ms / T
        peak, floor = 0.35 + 0.65 * k, base + 0.38 * k
        nxt = (B[i + 1] / T) if i + 1 < len(B) else 1.0
        rows.append((r3(max(t, rows[-1][0] + 0.001)), r3(peak)))
        rows.append((r3(min(t + (nxt - t) * 0.45, nxt - 0.002)), r3(floor)))
    rows.append((1, 1.0))
    els.append(light_el('light', (1.0, 0.12, 0.06), radius=220, intensity=520, life=T, curve=rows))
    return els


# =========================================================================================================================
# THE DEATH BLAST (one-shot on the floor under the corpse; local X = up)
# =========================================================================================================================
WAVE_START = 20               # the floor wave's beads start this far out
WAVE_LIFE = 240               # ms to reach the radius


def blast(c):
    R = c.radius
    v = (R - WAVE_START) / (WAVE_LIFE / 1000.0)
    return [
        # the flash and the fireball (where the body lies: ~22 over the floor)
        near_fade(el('glow', 'flash', oneshot=(1, 0), life=(190, 0), org=(22, 0, 0), size=(110, [(0, 0.6), (0.25, 1), (1, 1.15)]),
                     color=[(0,) + WHITE_HOT, (1,) + RED], alpha=[(0, 0.95), (0.4, 0.5), (1, 0)]), 60, 90),
        near_fade(el('core_hot', 'fireball', oneshot=(1, 0), life=(240, 0), org=(22, 0, 0), size=(62, [(0, 0.5), (0.3, 1), (1, 0.8)]),
                     color=[(0,) + WHITE_HOT, (0.5,) + HOT, (1,) + RED], alpha=[(0, 1), (0.5, 0.6), (1, 0)]), 40, 80),
        # THE HURT ZONE: a wave of beads racing out along the floor, stopping at the radius
        near_fade(offset_frame(el('glow', 'zone_wave', oneshot=(36, 0), life=(WAVE_LIFE, 0), org=(4, 0, 0), offset='cylinder',
                                  off_r=(WAVE_START, 0), size=(14, [(0, 0.8), (1, 1.1)]), vel={'X': (r3(v), [(0, 1), (1, 1)])},
                                  color=[(0,) + WHITE_HOT, (0.5,) + HOT, (1,) + RED], alpha=[(0, 0.95), (0.7, 0.8), (1, 0)])), 24, 40),
        # ...and its edge glowing where the wave stopped
        near_fade(el('glow', 'zone_edge', oneshot=(40, 0), life=(420, 60), delay=(WAVE_LIFE - 40, 0), org=(3, 0, 0), offset='cylinder',
                     off_r=(r3(R), 0), size=(11, [(0, 0.6), (0.2, 1), (1, 0.9)]), color=[(0,) + HOT, (1,) + RED],
                     alpha=[(0, 0), (0.15, 0.85), (0.6, 0.45), (1, 0)]), 24, 40),
        # a flat shock under it (a rotated sprite facing up, never wider than the zone)
        near_fade(pitch(el('shock_flat', 'shock', oneshot=(1, 0), life=(300, 0), org=(2, 0, 0), size=(r3(R), [(0, 0.2), (0.6, 0.9), (1, 1.0)]),
                           color=HOT, alpha=[(0, 0.55), (0.6, 0.25), (1, 0)]), 0), 24, 40),
        # the needles (BO6's "explo_needle"): thin hot streaks thrown out of the body
        el('spark', 'needles', oneshot=(22, 4), life=(240, 120), org=(22, 0, 0), run='spawn', offset='sphere', off_r=(4, 6),
           size=(2.2, [(0, 1), (1, 0.6)]), size1=(30, [(0, 1), (1, 0.4)]), vel=xyz(spread(760, 0.5)),
           color=[(0,) + WHITE_HOT, (0.5,) + HOT, (1,) + RED], alpha=[(0, 1), (0.6, 0.8), (1, 0)], grav=(40, 20)),
        el('incand', 'embers', oneshot=(20, 6), life=(650, 300), org=(22, 0, 0), run='spawn', size=(3, [(0, 1), (0.6, 0.7), (1, 0)]),
           vel=xyz(spread(300, 0.4)), color=[(0,) + HOT, (1,) + RED], alpha=[(0, 1), (0.5, 0.7), (1, 0)], grav=(45, 15)),
        # a charcoal puff where it was
        near_fade(in_world(el('smoke', 'puff', oneshot=(6, 1), life=(1500, 500), delay=(30, 60), org=(20, 0, 0), run='world', offset='sphere',
                              off_r=(10, 20), size=(56, [(0, 0.5), (0.3, 1), (1, 1.6)]), color=SOOT, alpha=[(0, 0.45), (0.4, 0.3), (1, 0)]),
                           X=spread(70, 0.3), Y=spread(70, 0.3), Z=(40, [(0, 0.4), (1, 0.2)], [(0, 1), (1, 0.4)])), 32, 64),
        light_el('light', (1.0, 0.18, 0.08), radius=300, intensity=800, life=360, curve=[(0, 0), (0.08, 1), (0.4, 0.45), (1, 0)], org=(24, 0, 0)),
    ]


# =========================================================================================================================
# THE JUKE (one-shot timeline on a carrier linked to j_spine4)
# =========================================================================================================================
def juke(c):
    on = c.juke_on_ms
    span = 420                    # the dash (clip frames 11-24)
    every = 40
    n = span // every + 1
    return [
        # the dark smear left along the dodge: a charcoal smoke ribbon + soot afterimages
        L.ribbon(el('contrail', 'smear', oneshot=(1, 0), life=(700, 0), delay=(on, 0), run='world',
                    size=(30, [(0, 0.8), (0.4, 1.0), (1, 1.3)]), color=SOOT, alpha=[(0, 0.55), (0.5, 0.3), (1, 0)]), 8, 160),
        in_world(el('smoke', 'ghosts', loop=(every, n), life=(420, 80), delay=(on, 0), run='world', offset='sphere', off_r=(4, 8),
                    size=(34, [(0, 0.8), (1, 1.4)]), color=SOOT, alpha=[(0, 0.42), (0.5, 0.2), (1, 0)]),
                 X=spread(8), Y=spread(8), Z=(6, [(0, 0), (1, 0)], [(0, 1), (1, 1)])),
        # a faint red core so it reads in the dark (emissive, low)
        L.ribbon(el('laser_trail', 'core', oneshot=(1, 0), life=(520, 0), delay=(on, 0), run='world',
                    size=(12, [(0, 1), (0.5, 0.6), (1, 0.15)]), color=[(0,) + RED, (1,) + SMEAR], alpha=[(0, 0.5), (0.5, 0.25), (1, 0)]), 8, 120),
        # (one every 40 ms living 240: where the dodge ends and the body stops, ~6 overlap - 6 x 0.14 stays a glow, not a blob)
        el('glow', 'smear_glow', loop=(every, n), life=(240, 0), delay=(on, 0), run='world', size=(26, [(0, 1), (1, 1.2)]),
           color=SMEAR, alpha=[(0, 0.14), (1, 0)]),
        # sparks shed off the body as it cuts sideways
        in_world(el('spark', 'sparks', oneshot=(10, 2), life=(260, 120), delay=(on, span), run='world', offset='sphere', off_r=(6, 8),
                    size=(1.5, [(0, 1), (1, 0.6)]), size1=(14, [(0, 1), (1, 0.4)]), color=[(0,) + HOT, (1,) + RED],
                    alpha=[(0, 1), (0.6, 0.7), (1, 0)], grav=(50, 20)),
                 X=spread(160, 0.5), Y=spread(160, 0.5), Z=(120, [(0, -0.2), (1, -0.3)], [(0, 0.8), (1, 0.4)])),
    ]


# =========================================================================================================================
# THE CLAW (looping on a carrier linked to the striking claw; the script deletes it after CLAW_MS)
# =========================================================================================================================
def claw(c):
    return [
        # the claw's glow: small (the hit lands 60-90 u from the target's eye, where 7 u is already a fist-sized blaze), and
        # gone inside 16..52 u of a camera
        near_fade(el('orb', 'glow', loop=(90, 0), life=(180, 0), run='effect', size=(7, [(0, 0.95), (1, 1.05)]), color=HOT,
                     alpha=steady(0.5)), 16, 36),
        near_fade(el('incand', 'core', loop=(60, 0), life=(120, 0), run='effect', size=(3.5, [(0, 0.8), (0.4, 1.2), (1, 0.8)]),
                     color=[(0,) + WHITE_HOT, (1,) + HOT], alpha=[(0, 0), (0.3, 1), (0.7, 0.8), (1, 0)]), 8, 16),
        # the swipe's ribbon: a red-hot streak trailing the claw through the arc
        near_fade(L.ribbon(el('laser_trail', 'trail', loop=(220, 0), life=(220, 0), run='world',
                              size=(5, [(0, 1), (0.5, 0.6), (1, 0.1)]), color=[(0,) + HOT, (0.5,) + RED, (1,) + BLOOD],
                              alpha=[(0, 0.65), (0.5, 0.35), (1, 0)]), 6, 64), 12, 20),
        in_world(el('spark', 'sparks', loop=(70, 0), life=(200, 80), run='world', offset='sphere', off_r=(2, 4),
                    size=(1.2, [(0, 1), (1, 0.6)]), size1=(9, [(0, 1), (1, 0.4)]), color=[(0,) + HOT, (1,) + RED],
                    alpha=[(0, 1), (0.6, 0.7), (1, 0)], grav=(40, 20)),
                 X=spread(70, 0.5), Y=spread(70, 0.5), Z=(40, [(0, -0.3), (1, -0.6)], [(0, 0.5), (1, 0.2)])),
        light_el('light', (1.0, 0.14, 0.06), radius=96, intensity=140, life=500, every=450),
    ]


# =========================================================================================================================
# THE MANGLER BREAKS UP (one-shot at its torso; local X = up)
# =========================================================================================================================
def mangler(c):
    return [
        near_fade(el('glow', 'flash', oneshot=(1, 0), life=(200, 0), org=(12, 0, 0), size=(104, [(0, 0.6), (0.25, 1), (1, 1.1)]),
                     color=[(0,) + M_WHITE, (1,) + M_ORANGE], alpha=[(0, 0.9), (0.4, 0.45), (1, 0)]), 50, 80),
        near_fade(el('core_hot', 'pop', oneshot=(1, 0), life=(170, 0), org=(12, 0, 0), size=(56, [(0, 1), (1, 0.5)]),
                     color=M_WHITE, alpha=[(0, 1), (1, 0)]), 40, 70),
        # a burst of fire out of the opened chest
        near_fade(el('flame', 'fire', oneshot=(5, 1), life=(420, 200), org=(10, 0, 0), run='spawn', offset='sphere', off_r=(4, 8),
                     size=(26, [(0, 0.6), (0.3, 1), (1, 0.5)]), vel={'X': (110, [(0, 0.4), (1, 0.6)], [(0, 1), (1, 0.8)]),
                                                                     'Y': spread(120, 0.4), 'Z': spread(120, 0.4)},
                     color=[(0,) + M_WHITE, (0.4,) + M_HOT, (1,) + M_ORANGE], alpha=[(0, 1), (0.6, 0.6), (1, 0)]), 30, 50),
        # hot scrap clumps thrown up and out, falling back
        el('debris', 'scrap', oneshot=(10, 2), life=(950, 350), org=(10, 0, 0), run='spawn', size=(8, [(0, 1), (1, 0.8)]),
           vel={'X': (320, [(0, 0.35), (1, 0.2)], [(0, 1), (1, 0.6)]), 'Y': spread(380, 0.6), 'Z': spread(380, 0.6)},
           color=[(0,) + M_HOT, (0.25,) + M_SCRAP, (1, 0.2, 0.1, 0.06)], alpha=[(0, 1), (0.8, 0.9), (1, 0)], grav=(100, 15),
           spin=((0, 360), (-360, 720))),
        # spark tails flung every way
        el('spark_tail', 'sparks', oneshot=(26, 6), life=(650, 350), org=(12, 0, 0), run='spawn',
           size=(2.4, [(0, 1), (1, 0.5)]), vel={'X': (420, [(0, 0.1), (1, 0.05)], [(0, 1), (1, 0.6)]), 'Y': spread(520, 0.5), 'Z': spread(520, 0.5)},
           color=[(0,) + M_WHITE, (0.5,) + M_HOT, (1,) + M_ORANGE], alpha=[(0, 1), (0.7, 0.8), (1, 0)], grav=(80, 20)),
        # steam venting out of the burst body for ~1.3 s
        near_fade(el('steam', 'steam', loop=(60, 22), life=(520, 260), delay=(80, 0), org=(8, 0, 0), run='spawn', offset='sphere', off_r=(4, 10),
                     size=(30, [(0, 0.5), (0.4, 1), (1, 1.6)]), vel={'X': (240, [(0, 0.5), (1, 0.15)], [(0, 1), (1, 0.3)]), 'Y': spread(220, 0.3), 'Z': spread(220, 0.3)},
                     color=STEAM, alpha=[(0, 0.5), (0.4, 0.35), (1, 0)]), 24, 48),
        # the cannon's arcs crackling over the wreck
        el('arc', 'arcs', loop=(160, 9), life=(120, 70), delay=(200, 0), org=(8, 0, 0), offset='sphere', off_r=(6, 18),
           size=(18, [(0, 0.7), (0.5, 1), (1, 0.8)]), color=[(0,) + M_HOT, (1,) + M_ORANGE], alpha=[(0, 0.9), (0.5, 0.5), (1, 0)]),
        # sparks sputtering out of it after the burst
        in_world(el('spark', 'sputter', loop=(110, 16), count=(1, 1), life=(320, 150), delay=(300, 0), org=(8, 0, 0), run='world',
                    offset='sphere', off_r=(4, 10), size=(1.6, [(0, 1), (1, 0.6)]), size1=(12, [(0, 1), (1, 0.4)]),
                    color=[(0,) + M_WHITE, (1,) + M_ORANGE], alpha=[(0, 1), (0.6, 0.7), (1, 0)], grav=(70, 20)),
                 X=spread(150, 0.5), Y=spread(150, 0.5), Z=(220, [(0, 0.3), (1, 0.1)], [(0, 1), (1, 0.5)])),
        # dark smoke rising off the wreck
        near_fade(in_world(el('smoke', 'smoke', oneshot=(6, 1), life=(2100, 500), delay=(100, 600), org=(8, 0, 0), run='world', offset='sphere',
                              off_r=(6, 14), size=(54, [(0, 0.6), (0.3, 1), (1, 2.0)]), color=SMOKE, alpha=[(0, 0), (0.15, 0.4), (1, 0)]),
                           X=spread(14), Y=spread(14), Z=(30, [(0, 0.6), (1, 0.5)], [(0, 1), (1, 0.8)])), 32, 64),
        light_el('light', (1.0, 0.42, 0.12), radius=260, intensity=650, life=1600, org=(16, 0, 0),
                 curve=[(0, 0), (0.04, 1), (0.15, 0.45), (0.3, 0.6), (0.42, 0.3), (0.55, 0.42), (0.7, 0.18), (1, 0)]),
    ]


# ---- the table: name, builder, LOOPING?, bounding-box half size, may-play-at-a-face? ---------------------------------------
EFFECTS = [
    ('fx_tod_doppel_death_charge', charge, False, 180, True),    # sparks start ~60 u out; soot rises ~40; the corpse barely moves
    ('fx_tod_doppel_death_blast', blast, False, 360, True),      # needles ~300 u; the zone ring at the radius
    ('fx_tod_doppel_juke', juke, False, 340, False),             # ~1 s of world-run smear behind a ~270 u/s dodge; plays 250+ u away
    ('fx_tod_doppel_claw', claw, True, 260, True),               # the claw sweeps ~130 u round the body; the ribbon stays on the arc
    ('fx_tod_mangler_death', mangler, False, 420, True),         # scrap ~350 u, sparks ~400 u
]
NAMES = [row[0] for row in EFFECTS]


def build(c):
    register_donors()
    out, meta = {}, {}
    for name, fn, looping, half, face in EFFECTS:
        els = fn(c)
        out[name] = S.effect(els, *box(half))
        meta[name] = dict(looping=looping, half=half, face=face)
    return out, meta


# ---- validation ----------------------------------------------------------------------------------------------------------
def _whole(vals):
    return all(abs(v - round(v)) < 1e-9 for v in vals)


def peak_particles(e):
    life = sum(e.nums('lifeSpanMsec'))
    if 'looping' in e.flags('editorFlags'):
        interval, count = e.nums('spawnLooping')
        per = max(1, sum(e.nums('spawnLoopingSpawnCount')))
        alive = math.ceil(life / max(1.0, interval))
        if count > 0:
            alive = min(alive, count)
        return int(alive * per)
    return int(sum(e.nums('spawnOneShot')))


def end_ms(e):
    """When a one-shot timeline's element is surely gone (inf = it loops forever)."""
    delay = sum(e.nums('spawnDelayMsec'))
    life = sum(e.nums('lifeSpanMsec'))
    if 'looping' in e.flags('editorFlags'):
        interval, count = e.nums('spawnLooping')
        if count <= 0:
            return math.inf
        return delay + interval * count + life
    return delay + life


def widest(e):
    g = e.graph('sizeGraph0')
    return g.scale * max(row[1] for c in g.curves for row in c)


def validate(name, text, meta, c, limit_ms=None):
    bad = []
    path = PREFIX + name
    if len(path) > MAX_PATH:
        bad.append('%s: effect path %d chars (> %d: cut at runtime)' % (path, len(path), MAX_PATH))
    if 'gfx_debug_missing_fx' in text:
        bad.append(name + ': a stub element (gfx_debug_missing_fx)')
    try:
        fx = E.parse(text)
    except Exception as ex:
        return bad + ['%s: does not parse (%s)' % (name, ex)]
    if not any(ln.strip().startswith('efFlags') and 'efUseBoundingBox' in ln for ln in fx.header):
        bad.append(name + ': no bounding box')
    seen, total, last = set(), 0, 0
    for e in fx.elements:
        en = name + '/' + e.name
        if e.name in seen:
            bad.append(en + ': a second element with this name')
        seen.add(e.name)
        t, mats = e.visual
        if t == 'model':
            bad.append(en + ': a model element')
        elif t == 'runner' or any(e.has(k) and e.get(k).strip().strip('"') for k in ('attachment', 'fxOnDeath', 'fxOnImpact', 'emission')):
            bad.append(en + ': names a child effect (this set has none)')
        elif t in L.LIGHTS:
            body = ' '.join(m.strip() for m in mats)
            if 'shadowUpdate Never' not in body or 'PRIMARY_NOSHADOWMAP 1' not in body:
                bad.append(en + ': a light that casts shadows')
            if not all(('lightingstate%d 1' % k) in body for k in (1, 2, 3, 4)):
                bad.append(en + ': a light missing from a lighting state')
            ig, rg = e.graph('lightIntensityGraph'), e.graph('lightRadiusGraph')
            peak_r = rg.scale * max(row[1] for cc in rg.curves for row in cc)
            peak_i = ig.scale * max(row[1] for cc in ig.curves for row in cc)
            if not (0 < peak_i and 0 < peak_r <= L.LIGHT_RADIUS_MAX):
                bad.append('%s: light intensity %s / radius %s (radius 1..%d)' % (en, peak_i, peak_r, L.LIGHT_RADIUS_MAX))
            if peak_particles(e) > 2:
                bad.append('%s: %d lights alive at once (at most two, crossfading)' % (en, peak_particles(e)))
            for cc in ig.curves:
                ts = [row[0] for row in cc]
                if ts[0] != 0 or ts[-1] != 1 or any(b <= a for a, b in zip(ts, ts[1:])):
                    bad.append(en + ': the light curve is not 0..1 strictly increasing in time')
                    break
        elif t not in L.VISUAL or not mats:
            bad.append(en + ': draws nothing')
        if 'gfx_debug_missing_fx' in mats:
            bad.append(en + ': a stub material')
        for key in ('lifeSpanMsec', 'spawnDelayMsec', 'spawnLooping'):
            if not _whole(e.nums(key)):
                bad.append(en + ': fractional ' + key)
        edf = e.flags('editorFlags')
        if 'looping' in edf:
            interval, count = e.nums('spawnLooping')
            if interval < 1 or count < 0:
                bad.append('%s: looping every %s ms for %s loops' % (en, interval, count))
            if count == 0 and not meta['looping']:
                bad.append(en + ': loops forever inside a ONE-SHOT timeline (it would never end)')
        for key in ('elemSpawnSound', 'elemFollowSound'):
            if e.has(key) and any(line.strip() for line in e.get(key).body):
                bad.append(en + ': names a sound (' + key + ')')
        if t not in L.LIGHTS and e.nums('spawnRange')[1] < S.FAR:
            bad.append(en + ': spawn range under %d' % S.FAR)
        if any(e.nums('fadeInRange')):
            bad.append(en + ': a far fade-in range')
        fl = e.flags('flags')
        if 'spawnFrustumCull' in fl or 'useCollision' in fl or 'isMatureContent' in fl:
            bad.append(en + ': frustum-culled / collides / mature-only')
        for it in e.items:
            if isinstance(it, E.Graph):
                if not math.isfinite(it.scale) or any(not math.isfinite(v) for cc in it.curves for row in cc for v in row):
                    bad.append('%s: %s is not finite' % (en, it.key))
                if it.key == 'alphaGraph' and any(not (0 <= row[1] * it.scale <= 1) for cc in it.curves for row in cc):
                    bad.append(en + ': alpha outside 0..1')
                if it.key in ('sizeGraph0', 'sizeGraph1') and any(row[1] * it.scale < 0 for cc in it.curves for row in cc):
                    bad.append('%s: negative %s' % (en, it.key))
        # THE 1P RULE: a sprite wider than NEAR_MAX in an effect that can play at a player's face fades near the camera
        if meta['face'] and t in ('billboardSprite', 'orientedSprite', 'rotatedSprite') and widest(e) > NEAR_MAX:
            start, width = e.nums('fadeOutRange')
            if start < 24 or width <= 0:
                bad.append('%s: a %g-unit sprite with no near-camera fade (the 1p rule)' % (en, widest(e)))
        total += peak_particles(e)
        last = max(last, end_ms(e))
    if total > PARTICLE_BUDGET:
        bad.append('%s: ~%d live particles at peak (budget %d)' % (name, total, PARTICLE_BUDGET))
    if not meta['looping'] and limit_ms is not None and last > limit_ms:
        bad.append('%s: the timeline runs %s ms, past its carrier\'s %d ms' % (name, last, limit_ms))
    return bad


def zone_problems(text, c):
    """THE HURT ZONE: the blast's floor wave stops on TOD_DOPPEL_DEATH_RADIUS and its edge ring sits on it."""
    fx = E.parse(text)
    els = {e.name: e for e in fx.elements}
    bad = []
    w, edge = els.get('zone_wave'), els.get('zone_edge')
    if w is None or edge is None:
        return ['blast: the hurt-zone wave / edge elements are missing']
    for e in (w, edge):
        if 'spawnOffsetCylinder' not in e.flags('flags') or e.nums('spawnOffsetCylindricalAxis')[0] != 0:
            bad.append('blast/%s: not a ring round local X (the floor normal)' % e.name)
        if e.nums('spawnOffsetRadius')[1] != 0 or any(e.nums('spawnOffsetHeight')):
            bad.append('blast/%s: a ring with a random radius / height' % e.name)
    r0 = w.nums('spawnOffsetRadius')[0]
    g = w.graph('velGraph0X')
    mean_v = g.scale * sum((a[1] + b[1]) / 2 * (b[0] - a[0]) for a, b in zip(g.curves[0], g.curves[0][1:]))
    reach = r0 + mean_v * w.nums('lifeSpanMsec')[0] / 1000.0
    if 'runRelToOffset' not in w.flags('flags') or w.nums('lifeSpanMsec')[1] != 0:
        bad.append('blast/zone_wave: the wave must run in the offset frame with a fixed life')
    if abs(reach - c.radius) > RING_TOL:
        bad.append('blast/zone_wave: the wave stops at %.1f u, not the %g-unit hurt radius' % (reach, c.radius))
    if abs(edge.nums('spawnOffsetRadius')[0] - c.radius) > RING_TOL:
        bad.append('blast/zone_edge: the edge ring sits at %g u, not the %g-unit hurt radius' % (edge.nums('spawnOffsetRadius')[0], c.radius))
    shock = els.get('shock')
    if shock is not None and widest(shock) > c.radius + RING_TOL:
        bad.append('blast/shock: the flat shock (%g) overstates the zone' % widest(shock))
    return bad


def limits(c):
    return {'fx_tod_doppel_death_charge': c.charge_ms + 50, 'fx_tod_doppel_death_blast': c.blast_ms,
            'fx_tod_doppel_juke': c.juke_ms, 'fx_tod_mangler_death': c.mangler_ms}


def problems_of(fx, meta, c):
    names = set(fx)
    bad = donor_problems()
    lim = limits(c)
    for n in NAMES:
        bad += validate(n, fx[n], meta[n], c, lim.get(n))
    bad += zone_problems(fx['fx_tod_doppel_death_blast'], c)
    return bad


def selftest(fx, meta, c):
    """Nine planted faults; each must be caught."""
    misses = []

    def caught(label, name, text, m=None, check_zone=False):
        bad = validate(name, text, m or meta[name], c, limits(c).get(name))
        if check_zone:
            bad += zone_problems(text, c)
        if not bad:
            misses.append(label)

    blast_t, claw_t, charge_t = fx['fx_tod_doppel_death_blast'], fx['fx_tod_doppel_claw'], fx['fx_tod_doppel_death_charge']
    caught('a stub material', 'fx_tod_doppel_claw', claw_t.replace('gfx_trail_laser_em', 'gfx_debug_missing_fx'))
    caught('a ring off the hurt radius', 'fx_tod_doppel_death_blast',
           re.sub(r'(name "zone_edge";[\s\S]*?spawnOffsetRadius )[\d.]+', r'\g<1>160', blast_t), check_zone=True)
    caught('a wave that overshoots', 'fx_tod_doppel_death_blast',
           re.sub(r'(name "zone_wave";[\s\S]*?lifeSpanMsec )\d+', r'\g<1>400', blast_t), check_zone=True)
    caught('a forever loop in a one-shot timeline', 'fx_tod_doppel_death_charge',
           re.sub(r'(name "core";\n\teditorFlags )', r'\1looping ', charge_t, count=1).replace('spawnLooping 1 0;', 'spawnLooping 90 0;', 1))
    caught('a shadowed light', 'fx_tod_doppel_claw', claw_t.replace('PRIMARY_NOSHADOWMAP 1', 'PRIMARY_NOSHADOWMAP 0'))
    caught('a light missing a lighting state', 'fx_tod_doppel_claw', claw_t.replace('lightingstate3 1', 'lightingstate3 0'))
    caught('a big flash with no near fade', 'fx_tod_doppel_death_blast',
           re.sub(r'(name "flash";[\s\S]*?fadeOutRange )[\d.]+ [\d.]+', r'\g<1>0 0', blast_t))
    caught('a path over 63 characters', 'fx_tod_doppel_claw_' + 'x' * 40, claw_t, m=meta['fx_tod_doppel_claw'])
    over = charge_t.replace('spawnOneShot 22 0;', 'spawnOneShot 220 0;')
    caught('a particle budget blown', 'fx_tod_doppel_death_charge', over)
    return misses


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--vendor', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--out-root', default=str(ROOT))
    a = ap.parse_args(argv)
    if a.vendor:
        return vendor(a.force)
    out_root = pathlib.Path(a.out_root).resolve()
    c = Clock(out_root)
    fx, meta = build(c)
    bad = problems_of(fx, meta, c)
    if bad:
        print('ELITE FX INVALID:\n  ' + '\n  '.join(bad))
        return 1
    if a.selftest:
        misses = selftest(fx, meta, c)
        if misses:
            print('ELITE FX SELFTEST MISSED: ' + ', '.join(misses))
            return 1
        print('ELITE FX SELFTEST OK: 9 planted faults caught')
        return 0
    out = out_root / REL_DIR
    if a.check:
        stale = []
        for n in NAMES:
            p = out / (n + '.efx')
            if not p.exists():
                stale.append(n + ' missing')
            elif p.read_bytes() != fx[n].encode('utf-8'):
                stale.append(n + ' differs')
        if out.exists():
            stale += ['stray ' + p.name for p in sorted(out.glob('*.efx')) if p.stem not in fx]
        if stale:
            print('ELITE FX STALE: ' + ', '.join(stale) + ' - run python tools/fxgen/elites/make_fx.py')
            return 1
        print('ELITE FX OK: %d effects' % len(fx))
        return 0
    out.mkdir(parents=True, exist_ok=True)
    for n in NAMES:
        (out / (n + '.efx')).write_bytes(fx[n].encode('utf-8'))
        parsed = E.parse(fx[n])
        peak = sum(peak_particles(e) for e in parsed.elements)
        lights = sum(1 for e in parsed.elements if e.visual[0] in L.LIGHTS)
        print('wrote %s%s  (%d elements, peak ~%d particles, %d light, sha %s)' % (PREFIX, n, len(parsed.elements), peak, lights,
                                                                                    hashlib.sha256(fx[n].encode('utf-8')).hexdigest()[:10]))
    print('ELITE FX WRITTEN: %d effects -> %s' % (len(fx), out))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
