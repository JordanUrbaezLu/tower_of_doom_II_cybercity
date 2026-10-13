"""THE HORDE'S EYES (PK04, 2026-10-04): the charcoal horde's red eye glow + the golden zombie's gold one.
GENERATED - never hand-edit the .efx; change the tables below and re-run.

  python tools/fxgen/horde_eyes/make_fx.py                    write share/raw/fx/tod/cyber/<the two effects>.efx
  python tools/fxgen/horde_eyes/make_fx.py --check            regenerate in memory, validate, FAIL (exit 1) if a written
                                                              effect differs, is missing, or a stray .efx sits in the folder
  python tools/fxgen/horde_eyes/make_fx.py --out-root DIR     write / check under DIR instead of the repo root (a stage)
  python tools/fxgen/horde_eyes/make_fx.py --selftest         the validators against planted faults (exit 1 if one is missed)

THE GAP. Every ordinary zombie runs stock zombie_spawn_init, which sets the actor clientfield "zombie_has_eyes" 0.5 s
after the spawn (a riser: once it shows). The client (_zm.csc createZombieEyesInternal) then plays
level._effect["eye_glow"] = "zombie/fx_glow_eye_orange" (zm_usermap.csc:72) on the bone j_eyeball_le - unless
level._override_eye_fx or the actor's _eyeglow_fx_override names another effect. Nothing in this map did, so ORANGE
particles floated over the charcoal horde's pure-red HDR-16 eyes on every zombie (docs/cyber_elites/README.md: "red eyes
and no orange"; CLAUDE.md: "Do not restore the original orange eyes"), and over the golden zombie's gold eyes too.

THE DONOR IS THE STOCK ORANGE, RECOLOURED - NOT THE STOCK RED. Measured (read the vendored files in donor/):
  * fx_glow_eye_orange is Treyarch's effect for THESE heads. The horde's head is a stock BO3 head
    (c_zom_dlc4_zombie_charred_head: Revelations' charred zombies wear this very effect), and the bone frame matches
    it: on every head the horde wears (charred / golden / tod_cyber_sprinter_head1-3, read with PyCoD) the right eye
    sits at local X -2.402 from j_eyeball_le and the face looks down local -Y. The orange's two light-cone LINES fly
    at local velocity (0, -0.5, +0.05) = straight out of the face. Its look: a tight hot core (1.5 @ alpha 1.0), a
    faint wide halo (7 @ 0.18 x a dark colour) and four forward light cones - the BO3 zombie-eye read players know.
  * fx_glow_eye_red is a different design ("wraith_looping", six sprites, no cones): a dim core twice the size
    (3 @ 0.30) under two broad halos (6 @ 0.10, 8 @ 0.15) whose red-channel energy is 3.3x the orange halo's. On top
    of an HDR-16 red eye that is a red haze over the whole face, not a glint - the "too big / too bright" the pack
    brief warned of - and its right-eye sprites sit 0.15-0.45 u outside this head's eye.
  * THE MAP ALREADY SHIPS THIS RECIPE: zombie/fx_glow_eye_white (the Necromancer's helpers' eyes, zoned since
    2026-09-26 and seen in play on these very charcoal heads) is the orange element for element, re-coloured (every
    channel = the orange's red: core .886 @ 1.0, halo .416 @ .18, cones .318 / .408 / .059).
  So both effects here keep the orange's geometry, materials, flags, spawn timing and cones exactly, and change only:
  the colour (every key), the core alpha, the halo size/alpha, the right-eye X (-2.55 -> -2.40, the measured eye) and
  the left-eye X (-0.05 -> 0, centred), a soft far fade where the donor's core and halo popped off at their
  spawn-range edge, and a near fade on the halo (16 + 48 u, the stock red's idea) so a zombie in your face is a pair
  of glints, not a red haze across the screen.

THE HORDE RED (fx_tod_charcoal_eye_glow_red): hue EXACTLY 0 in every colour key (green == blue, both <= 8 % of red), so
  nothing in it can drift toward orange. Core (1, .04, .04) @ 0.85 = 55 % of the orange core's luminance (the eye
  material already blooms; green / blue kept at 4 % so a stacked core stays RED, not pink); halo 6 @ 0.16 of
  (.62, .015, .015) = the orange halo's RED-channel energy, about half its luminance and 27 % of the stock red's
  halo energy; cones the orange's at the same red level.
  KNOBS if the user finds it too strong / weak in game: the halo alpha (0.16) first, then the core alpha (0.85).
THE GOLDEN GOLD (fx_tod_golden_eye_glow): the golden eye material's own hue (tools/lucky/make_golden.py EYE_TINT
  1 .76 .18 = 42 deg; every key 39-41 deg, held to 38-48, never the orange band 5-30), at the stock orange's luminance (the
  golden zombie already wears a gold aura and a self-glow; the user found a brighter gold "way too intense").

UNITS / ENGINE NOTES (read off the stock library, 2026-10-04): sizes are world units (a size read as a radius or a
width scales every effect here alike). spawnRange, fadeInRange and fadeOutRange are all (START, WIDTH) pairs: in the
stock zombie + dlc1 effects the 83 elements fading "1700 300" spawn over "0 2000" / "100 1900" / "500 1500" - every one
ends at 2000, and the orange's cones fade "3700 300" inside "0 4000". fadeInRange is the FAR fade (the element fades
out between start and start + width from the camera), fadeOutRange the NEAR one (it fades in from start to start +
width). spawnLooping (interval ms, count): count 0 = forever.

RULES THE WRITTEN FILES PASS (validate()): exactly the donor's eight elements in order, each with its donor's material
(gfx_light_incandescent_hot_em sprites / gfx_light_ray_cone_em lines) and no other visual, no gfx_debug_missing_fx, no
child effect / sound / model, looping elements loop forever, alphas in 0..1, sizes > 0, every far fade ends exactly at
its spawn-range edge (no pop) and clears the near fade, the effect path <= 63 characters (memory
fx-name-63-char-limit-crashes), the colour rule of its effect (above). --selftest plants seven faults and requires a
catch on each: the stock orange under both colour rules, one orange key in the red, one orange key in the gold, a
dropped element, a gfx_debug_missing_fx material, a 64+ character path, a far fade past the spawn edge.
"""
import argparse
import colorsys
import hashlib
import pathlib
import re
import sys

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
DONOR = HERE / 'donor' / 'fx_glow_eye_orange.efx'
# the stock file, vendored byte for byte from <tools root>/share/raw/fx/zombie/ (identical in the Steam mod tools and
# the private root, 2026-10-04); hashed with CRLF line endings whatever the checkout wrote (.gitattributes is eol=lf)
DONOR_SHA_CRLF = 'b5cfcdd6092442d97bd3d74d09cf82be3c96d41241fae91800e67893708a78cc'
REL_DIR = 'share/raw/fx/tod/cyber'
PREFIX = 'tod/cyber/'
MAX_PATH = 63
EOL = '\r\n'            # every map-owned .efx in share/raw/fx/tod is CRLF (the stock files are too)

# The donor's eight elements, in order (index -> role). L = the bone's own eye (j_eyeball_le), R = the other eye.
ROLES = ['core_l', 'core_r', 'halo_l', 'halo_r', 'cone_l', 'cone_r', 'cone_wide_l', 'cone_wide_r']
MATERIAL = {'core': 'gfx_light_incandescent_hot_em', 'halo': 'gfx_light_incandescent_hot_em',
            'cone': 'gfx_light_ray_cone_em', 'cone_wide': 'gfx_light_ray_cone_em'}

EYE_R_X = -2.40         # the other eye, measured: 2.402 u from j_eyeball_le on every head the horde wears (PyCoD)
EYE_L_X = 0.0           # the donor's -0.05 nudged onto the bone itself

# ---- the two effects ---------------------------------------------------------------------------------------------------
# per role: colour (linear RGB, constant over life), alpha, size0 (size1 = the donor's / the same for a sprite),
# spawnRange (start, width), fadeInRange (start, width) = the far fade, fadeOutRange (start, width) = the near fade.
# None keeps the donor's value.
def red_spec():
    core = dict(color=(1.0, 0.04, 0.04), alpha=0.85, size=1.5, spawn=(0, 2000), fade_in=(1700, 300), fade_out=(0, 0))
    halo = dict(color=(0.62, 0.015, 0.015), alpha=0.16, size=6.0, spawn=(0, 3000), fade_in=(2600, 400), fade_out=(16, 48))
    cone = dict(color=(0.42, 0.03, 0.03), alpha=1.0, size=None, spawn=(0, 4000), fade_in=(3700, 300), fade_out=(0, 40))
    wide = dict(color=(0.075, 0.005, 0.005), alpha=1.0, size=None, spawn=(0, 4000), fade_in=(3700, 300), fade_out=(0, 40))
    return {'core': core, 'halo': halo, 'cone': cone, 'cone_wide': wide}


def gold_spec():
    core = dict(color=(1.0, 0.72, 0.16), alpha=0.55, size=1.5, spawn=(0, 2000), fade_in=(1700, 300), fade_out=(0, 0))
    halo = dict(color=(0.55, 0.39, 0.08), alpha=0.10, size=6.0, spawn=(0, 3000), fade_in=(2600, 400), fade_out=(16, 48))
    cone = dict(color=(0.36, 0.26, 0.05), alpha=1.0, size=None, spawn=(0, 4000), fade_in=(3700, 300), fade_out=(0, 40))
    wide = dict(color=(0.07, 0.05, 0.01), alpha=1.0, size=None, spawn=(0, 4000), fade_in=(3700, 300), fade_out=(0, 40))
    return {'core': core, 'halo': halo, 'cone': cone, 'cone_wide': wide}


EFFECTS = {
    # effect name (= file stem): (element-name prefix, spec builder, colour rule)
    'fx_tod_charcoal_eye_glow_red': ('tod_eye_red', red_spec, 'red'),
    'fx_tod_golden_eye_glow': ('tod_eye_gold', gold_spec, 'gold'),
}
GOLD_HUE = (38.0, 48.0)     # degrees; the golden eye tint is 42.4, the stock orange core 15.6
ORANGE_BAND = (5.0, 30.0)


# ---- the donor ---------------------------------------------------------------------------------------------------------
def lf(text):
    return text.replace('\r\n', '\n')


def read_donor():
    raw = DONOR.read_bytes()
    crlf = lf(raw.decode('latin-1')).replace('\n', '\r\n').encode('latin-1')
    got = hashlib.sha256(crlf).hexdigest()
    if got != DONOR_SHA_CRLF:
        raise SystemExit('HORDE EYES: the vendored donor %s is not the stock fx_glow_eye_orange (sha %s)' % (DONOR.name, got))
    return lf(raw.decode('latin-1'))


def blocks(text):
    """The top-level { ... } element blocks of an .efx (LF text), each returned with its braces."""
    out, depth, start = [], 0, None
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                out.append(text[start:i + 1])
    return out


def fmt(x):
    return '%.6f' % x


def set_line(b, key, value):
    pat = re.compile(r'(\n\t' + re.escape(key) + r' )[^\n;]*;')
    if not pat.search(b):
        raise SystemExit('HORDE EYES: element has no %s line' % key)
    return pat.sub(lambda m: m.group(1) + value + ';', b, count=1)


def graph_span(b, key):
    m = re.search(r'\n\t' + re.escape(key) + r' ([^\n]*)\n\t\{\n(.*?)\n\t\};', b, re.S)
    if not m:
        raise SystemExit('HORDE EYES: element has no %s graph' % key)
    return m


def set_graph_const(b, key, values, scale=None):
    """Every key row of both curves becomes `time v1 v2 ...` (constant over life); optionally the graph's scale."""
    m = graph_span(b, key)
    body = m.group(2)
    rows = []
    for line in body.split('\n'):
        nums = line.split()
        if len(nums) >= 2 and re.fullmatch(r'-?[0-9.]+', nums[0]):
            indent = line[:len(line) - len(line.lstrip('\t'))]
            line = indent + ' '.join([nums[0]] + [fmt(v) for v in values])
        rows.append(line)
    head = m.group(1) if scale is None else fmt(scale)
    new = '\n\t' + key + ' ' + head + '\n\t{\n' + '\n'.join(rows) + '\n\t};'
    return b[:m.start()] + new + b[m.end():]


def graph_rows(b, key):
    m = graph_span(b, key)
    return m.group(1), [[float(x) for x in ln.split()] for ln in m.group(2).split('\n')
                        if ln.strip() and re.fullmatch(r'-?[0-9.]+', ln.split()[0])]


def line_vals(b, key):
    m = re.search(r'\n\t' + re.escape(key) + r' ([^\n;]*);', b)
    return m.group(1).split() if m else None


def role_kind(role):
    return role.rsplit('_', 1)[0]


# ---- build --------------------------------------------------------------------------------------------------------------
def build_effect(stem, donor_text):
    prefix, spec_fn, _rule = EFFECTS[stem]
    spec = spec_fn()
    src = blocks(donor_text)
    if len(src) != len(ROLES):
        raise SystemExit('HORDE EYES: the donor has %d elements, expected %d' % (len(src), len(ROLES)))
    out = []
    for role, b in zip(ROLES, src):
        kind = role_kind(role)
        s = spec[kind]
        b = set_line(b, 'name', '"%s_%s"' % (prefix, role))
        b = set_line(b, 'spawnRange', '%s %s' % (fmt(s['spawn'][0]), fmt(s['spawn'][1])))
        b = set_line(b, 'fadeInRange', '%s %s' % (fmt(s['fade_in'][0]), fmt(s['fade_in'][1])))
        b = set_line(b, 'fadeOutRange', '%s %s' % (fmt(s['fade_out'][0]), fmt(s['fade_out'][1])))
        x = EYE_R_X if role.endswith('_r') else EYE_L_X
        org = line_vals(b, 'spawnOrgX')
        b = set_line(b, 'spawnOrgX', '%s %s' % (fmt(x), org[1]))
        b = set_graph_const(b, 'colorGraph', s['color'])
        b = set_graph_const(b, 'alphaGraph', (s['alpha'],))
        if s['size'] is not None:
            b = set_graph_const(b, 'sizeGraph0', (1.0,), scale=s['size'])
            b = set_graph_const(b, 'sizeGraph1', (1.0,), scale=s['size'])
        out.append(b)
    text = 'iwfx 2\n\n' + '\n\n'.join(out) + '\n\n'
    return text.replace('\n', EOL)


def all_effects():
    donor = read_donor()
    return {stem: build_effect(stem, donor) for stem in EFFECTS}


# ---- validate ---------------------------------------------------------------------------------------------------------
VISUAL_KEYS = ('billboardSprite', 'orientedSprite', 'tail', 'line', 'trail', 'cloud', 'sparkCloud', 'sparkFountain',
               'model', 'light', 'spotLight', 'omniLight', 'decal', 'runner', 'sound', 'lensFlare', 'vectorField',
               'particleCloud', 'geoTrail', 'beam', 'laser')


def visuals(b):
    found = []
    for k in VISUAL_KEYS:
        for m in re.finditer(r'\n\t' + k + r'\n\t\{\n(.*?)\n\t\};', b, re.S):
            found.append((k, re.findall(r'"([^"]*)"', m.group(1))))
    return found


def hue_deg(rgb):
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    return h * 360.0, s, v


def colour_problems(rule, rgb, where):
    r, g, b = rgb
    if rule == 'red':
        if r <= 0 or g > 0.08 * r + 1e-9 or abs(g - b) > 0.0015:
            return ['%s colour %s is not pure red (hue 0: green == blue, both <= 8%% of red)' % (where, rgb)]
    elif rule == 'gold':
        h, s, _v = hue_deg(rgb)
        if not (GOLD_HUE[0] <= h <= GOLD_HUE[1]) or s < 0.6:
            return ['%s colour %s hue %.1f / sat %.2f is not the golden eye\'s gold (%g-%g deg)' % (where, rgb, h, s, *GOLD_HUE)]
    if ORANGE_BAND[0] <= hue_deg(rgb)[0] <= ORANGE_BAND[1] and hue_deg(rgb)[1] > 0.2:
        return ['%s colour %s sits in the ORANGE band' % (where, rgb)]
    return []


def validate(stem, text, rule):
    probs = []
    path = PREFIX + stem
    if len(path) > MAX_PATH:
        probs.append('%s: effect path is %d chars (> %d)' % (path, len(path), MAX_PATH))
    t = lf(text)
    if not t.startswith('iwfx 2\n'):
        probs.append('%s: not an iwfx 2 file' % stem)
    if 'gfx_debug_missing_fx' in t:
        probs.append('%s: names the gfx_debug_missing_fx stub' % stem)
    els = blocks(t)
    if len(els) != len(ROLES):
        probs.append('%s: %d elements, expected the donor\'s %d' % (stem, len(els), len(ROLES)))
        return probs
    for role, b in zip(ROLES, els):
        where = '%s/%s' % (stem, role)
        vis = visuals(b)
        want = MATERIAL[role_kind(role)]
        if len(vis) != 1 or vis[0][1] != [want]:
            probs.append('%s: visuals %s, expected one %s' % (where, vis, want))
        for k in ('fxOnImpact', 'fxOnDeath', 'emission', 'attachment'):
            v = line_vals(b, k)
            if v is None or v != ['""']:
                probs.append('%s: %s is %s (no child effects allowed)' % (where, k, v))
        if re.search(r'\n\telemSpawnSound\n\t\{\n\t\t"', b) or re.search(r'\n\telemFollowSound\n\t\{\n\t\t"', b):
            probs.append('%s: carries an element sound' % where)
        loop = line_vals(b, 'spawnLooping')
        if 'looping' in (line_vals(b, 'editorFlags') or []) and (loop is None or loop[1] != '0'):
            probs.append('%s: a looping element with a loop COUNT %s (0 = forever)' % (where, loop))
        _s, rows = graph_rows(b, 'colorGraph')
        for row in rows:
            if len(row) != 4:
                probs.append('%s: colour row %s' % (where, row))
                continue
            probs += colour_problems(rule, tuple(row[1:]), where)
        _s, rows = graph_rows(b, 'alphaGraph')
        for row in rows:
            if not (0.0 <= row[1] <= 1.0):
                probs.append('%s: alpha %s outside 0..1' % (where, row[1]))
        for k in ('sizeGraph0', 'sizeGraph1'):
            scale, rows = graph_rows(b, k)
            if float(scale) <= 0 or any(r[1] <= 0 for r in rows):
                probs.append('%s: %s not positive' % (where, k))
        sr = [float(x) for x in line_vals(b, 'spawnRange')]          # (start, width)
        fi = [float(x) for x in line_vals(b, 'fadeInRange')]         # (start, width): the far fade
        fo = [float(x) for x in line_vals(b, 'fadeOutRange')]        # (start, width): the near fade
        far = sr[0] + sr[1]
        if abs(fi[0] + fi[1] - far) > 1e-6 or fi[1] <= 0:
            probs.append('%s: the far fade %s does not end at the spawn range edge %g (the element pops off)' % (where, fi, far))
        if fo[0] + fo[1] >= fi[0]:
            probs.append('%s: the near fade %s overlaps the far fade %s' % (where, fo, fi))
    return probs


# ---- selftest: the validators must catch what they exist for ---------------------------------------------------------
def selftest():
    donor = read_donor()
    misses = []
    effects = {stem: build_effect(stem, donor) for stem in EFFECTS}
    for stem, (_p, _f, rule) in EFFECTS.items():
        if validate(stem, effects[stem], rule):
            misses.append('the shipped %s fails its own rules: %s' % (stem, validate(stem, effects[stem], rule)[:2]))
    # 1. the stock orange itself must fail both colour rules
    for rule in ('red', 'gold'):
        if not any('colour' in p for p in validate('fx_glow_eye_orange', donor, rule)):
            misses.append('the %s colour rule passes the stock ORANGE' % rule)
    # 2. one orange key planted into the red effect
    red = lf(effects['fx_tod_charcoal_eye_glow_red'])
    planted = red.replace('1.000000 0.040000 0.040000', '0.886275 0.258824 0.039216', 1)
    if planted == red or not validate('fx_tod_charcoal_eye_glow_red', planted, 'red'):
        misses.append('one orange colour key in the red effect is not caught')
    # 3. a dropped element
    els = blocks(red)
    short = 'iwfx 2\n\n' + '\n\n'.join(els[:-1]) + '\n\n'
    if not validate('fx_tod_charcoal_eye_glow_red', short, 'red'):
        misses.append('a dropped element is not caught')
    # 4. a stub material
    stub = red.replace('"gfx_light_incandescent_hot_em"', '"gfx_debug_missing_fx"', 1)
    if not validate('fx_tod_charcoal_eye_glow_red', stub, 'red'):
        misses.append('a gfx_debug_missing_fx material is not caught')
    # 5. a too-long path
    if not validate('x' * 60, red, 'red'):
        misses.append('a > 63 character effect path is not caught')
    # 6. a gold key drifting into orange
    gold = lf(effects['fx_tod_golden_eye_glow'])
    planted = gold.replace('1.000000 0.720000 0.160000', '1.000000 0.450000 0.100000', 1)
    if planted == gold or not validate('fx_tod_golden_eye_glow', planted, 'gold'):
        misses.append('an orange key in the gold effect is not caught')
    # 7. a far fade past the spawn range
    pop = red.replace('fadeInRange 1700.000000 300.000000', 'fadeInRange 1900.000000 300.000000', 1)
    if pop == red or not validate('fx_tod_charcoal_eye_glow_red', pop, 'red'):
        misses.append('a far fade past the spawn range is not caught')
    return misses


# ---- main -------------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--out-root', default=str(ROOT))
    a = ap.parse_args()
    out_dir = pathlib.Path(a.out_root) / REL_DIR

    if a.selftest:
        misses = selftest()
        for m in misses:
            print('HORDE EYES SELFTEST MISS: ' + m)
        print('HORDE EYES SELFTEST %s (7 planted faults)' % ('FAIL' if misses else 'OK'))
        return 1 if misses else 0

    effects = all_effects()
    probs = []
    for stem, text in effects.items():
        probs += validate(stem, text, EFFECTS[stem][2])
    if probs:
        for p in probs:
            print('HORDE EYES INVALID: ' + p)
        return 1

    if a.check:
        bad = []
        for stem, text in effects.items():
            f = out_dir / (stem + '.efx')
            if not f.is_file():
                bad.append('missing %s' % f)
            elif lf(f.read_bytes().decode('latin-1')) != lf(text):
                bad.append('stale %s (re-run tools/fxgen/horde_eyes/make_fx.py)' % f)
        if out_dir.is_dir():
            for f in sorted(out_dir.glob('*.efx')):
                if f.stem not in effects:
                    bad.append('stray %s (not generated here)' % f)
        misses = selftest()
        bad += ['selftest: ' + m for m in misses]
        for b in bad:
            print('HORDE EYES FX: ' + b)
        if bad:
            print('HORDE EYES FX FAIL')
            return 1
        print('HORDE EYES FX OK (%d effects, %d elements each, colour rules + 7 planted faults)' % (len(effects), len(ROLES)))
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    for stem, text in effects.items():
        (out_dir / (stem + '.efx')).write_bytes(text.encode('latin-1'))
        print('wrote %s (%d B)' % ((out_dir / (stem + '.efx')), len(text)))
    for f in sorted(out_dir.glob('*.efx')):
        if f.stem not in effects:
            print('NOTE: %s is not generated here - remove it or this folder fails --check' % f)
    return 0


if __name__ == '__main__':
    sys.exit(main())
