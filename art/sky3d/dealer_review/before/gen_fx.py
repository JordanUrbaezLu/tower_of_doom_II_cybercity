"""THE FIRST JUMP'S CRASH - its effects (docs/196 §4), GENERATED - never hand-edit the .efx.

  python tools/jump_title/gen_fx.py           write share/raw/fx/tod/jump/fx_jt_*.efx
  python tools/jump_title/gen_fx.py --check   FAIL if any written effect differs from a fresh generation

Stock effects, READ-ONLY from the mod tools (never written), re-scaled for the sky and written map-owned:
  fx_jt_boom    THE crash, ~6,000 u from the rider: explosions/fx_exp_generic_aerial_lg (Treyarch's mid-air
                blast: the white-hot burst, the fire billows, the tendrils, the spark cloud, the shock ring) x3.2,
                plus the mothership death's falling sparks and metal gibs (killstreaks/fx_mship_death_exp).
  fx_jt_blast   a reactor going up a beat later: the same blast x1.6, no shock ring.
  fx_jt_wreck   the burning wreckage falling toward the city: the helicopter streamer's fire and smoke
                (killstreaks/fx_heli_exp_streamer1) on falling arcs, with the mothership's sparks.
  fx_jt_warp    each gunship's arrival: Gorod Krovi's dragon-strike portal flash (lightning, a hot core cooling
                to blue plasma, shock rings, heat distortion) at 60%: they WARP IN, never pop in.
  fx_jt_burn    both engines flaring for the ram (played on each gunship's tag_origin): a white-hot core on
                every nozzle that follows the ship (the fleet's manifest anchors) and a long cyan streak.
  fx_jt_blaze   THE TITLE BLAZING: additive glows in the authored monument's red/violet colors, on its
                title, subtitle, mechanical forehead channel and red sensor eyes (the cyber_hero_title.py contract):
                ramping up the moment the LIT SIGN CARD holds after its flicker at THE REVEAL (the client's
                flicker_ms table, READ here), the crest and sensors flaring a beat apart, full to the swing back,
                fading as the sign leaves the frame.
  (fx_jt_veil, the seven-puff smoke that dimmed a LIT sign, is RETIRED 2026-09-30: the sky's sign is baked DULL now
   (build_city.py --sign-state dull) and the lit sign is a card model, tools/jump_title/make_sign_card.py.)
The blaze plays on a host the client keeps on the sky sign's bearing every frame (the sign is at infinity: a fixed
point would slide across it as the rider flies), so its offsets are angles laid out at SIGN_DIST - the SAME distance
the lit card is sized at (LOCKSTEP _tod_jump_title.csc TOD_JT_SIGN_DIST, make_sign_card.py).
THE SCALE (a stock effect is built for a few hundred units): one spatial factor k and one time factor tau per
element: sizes, offsets, trail and emit distances x k; lifetimes, delays, spawn intervals x tau; velocities x k/tau;
gravity x k/tau^2 - the same explosion, bigger, not a stretched one. And the sky-distance fixes session 9c paid for
(tools/sky_ships/gen_fx.py): spawnRange 0..64000, no fade-in / fade-out range, no frustum cull, a bounding box that
holds the whole scaled effect. Element spawn / follow SOUNDS are emptied (the scene plays its own; a stock MP alias
would be a missing asset). Model elements are dropped (their debris models are not zoned).
"""
import ast, json, math, re, sys, pathlib, os

REPO = pathlib.Path(os.environ.get('TOD_REPO') or pathlib.Path(__file__).resolve().parents[2])
PRIVATE = pathlib.Path(os.environ.get('TOD_PRIVATE_TOOLS', r'C:\BO3Tools\TOD2Cybercity'))   # the workspace's own copy (read-only here)
MODTOOLS = pathlib.Path(os.environ.get('TOD_MODTOOLS', r'C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130'))
STOCK = PRIVATE / 'share/raw/fx' if (PRIVATE / 'share/raw/fx').exists() else MODTOOLS / 'share/raw/fx'
DONOR_GLOW = REPO / 'share/raw/fx/acc/light/fx_perk_glow_amber.efx'   # the additive glow billboard the fleet uses
OUT = REPO / 'share/raw/fx/tod/jump'
MANIFEST = REPO / 'art/sky_ships/manifest.json'
FAR = 64000

# The authored monument is the source of its anchors and linear emission colors. Read only
# literal assignments so generation works outside Blender and never executes scene code.
SIGN_DIST = 9500       # LOCKSTEP: _tod_jump_title.csc TOD_JT_SIGN_DIST (the card and the glows' host ride the bearing at it;
                       # behind both gunships and the crash, the card's corners inside the sealed sky volume)
BLAZE_REF_DIST = 11000 # the BLAZE table's sizes were laid out at this distance: they scale with SIGN_DIST
TITLE_CSC = REPO / 'scripts/zm/zm_tod2_cybercity/_tod_jump_title.csc'
BUILD_CITY = REPO / 'tools/sky3d/build_city.py'
TITLE_ART = REPO / 'tools/sky3d/cyber_hero_title.py'


def title_contract(path=TITLE_ART):
    names = {'REFERENCE_WIDTH', 'FEATURE_PIXELS', 'CINEMATIC_COLORS', 'CREST_LIGHT_RADIUS_FRACTION'}
    values = {}
    for node in ast.parse(path.read_text(encoding='utf-8'), filename=str(path)).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    values[target.id] = ast.literal_eval(node.value)
    assert set(values) == names, 'cyber_hero_title.py: missing literal cinematic contract'
    width = values['REFERENCE_WIDTH']
    assert math.isfinite(width) and width > 0, 'cyber title reference width must be positive'
    features, colors = values['FEATURE_PIXELS'], values['CINEMATIC_COLORS']
    required = {'title', 'sub', 'ring', 'eye_l', 'eye_r'}
    assert set(features) == required and set(colors) == required | {'title_core'}, 'cyber title feature/color keys differ'
    assert all(len(v) == 2 and all(math.isfinite(x) for x in v) for v in features.values()), 'cyber title anchors must be finite'
    assert all(len(v) == 3 and all(math.isfinite(x) and 0 <= x <= 1 for x in v) for v in colors.values()), 'cyber title colors must be linear RGB in 0..1'
    crest = values['CREST_LIGHT_RADIUS_FRACTION']
    assert math.isfinite(crest) and 0 < crest < 1, 'cyber crest radius must be a valid width fraction'
    return width, features, colors, crest


REFERENCE_WIDTH, FEATURES, COLORS, CREST_RADIUS = title_contract()
# FEATURE_PIXELS is a design grid: right +, DOWN +, centered on DOOM II. Geometry
# and FX use the same fractions of GATE's width and the approved cyber art.


# THE TIMELINE is the jump script's (_tod_jumppad.gsc, READ here, never copied): the smoke over the sign and the
# blaze are laid out against its beats, so a retimed flight re-times them on the next generation (--check fails
# until then).
JUMPPAD = REPO / 'scripts/zm/zm_tod2_cybercity/_tod_jumppad.gsc'


def jp_secs(name):
    m = re.search(r'(?m)^#define\s+' + name + r'\s+\(?\s*(-?[\d.]+)', JUMPPAD.read_text(encoding='utf-8'))
    assert m, '_tod_jumppad.gsc: #define %s not found' % name
    return float(m.group(1))


IMPACT = jp_secs('TOD_JUMPPAD_CINE_IMPACT_AT')           # the ships meet (the white flash, the fireball)
IGNITE = jp_secs('TOD_JUMPPAD_CINE_IGNITE_AT')           # the sign's glows come on, behind the full white
SWING = (jp_secs('TOD_JUMPPAD_CINE_TURN_AT') + jp_secs('TOD_JUMPPAD_CINE_TURN_SECS')
         + jp_secs('TOD_JUMPPAD_CINE_HOLD_SECS'))        # the camera swings back to the tower (tod_jump_title_end)
BACK = jp_secs('TOD_JUMPPAD_CINE_BACK_SECS')             # ... and the sign has left the frame this much later
# THE REVEAL (s after the ignite; user after the first play: "make sure sign doesnt light up until explosion
# happens"): the fire in front has thinned; the client plays the power surge and FLICKERS THE LIT CARD ON over the
# dull bake (its flicker_ms table: on / off pairs in ms, then steady on - READ here, never copied), then the blaze
# ramps up over the held card; the crest's ring flares at RING_AT and its eyes at EYES_AT (s after the card holds),
# the surge's sparks rain off the letters as it holds. LOCKSTEP _tod_jump_title.csc TOD_JT_REVEAL (test_jump_title.js).
REVEAL = 2.2
RING_AT, EYES_AT = 0.25, 0.65


def flicker_ms(path=TITLE_CSC):
    """-> the client's flicker table (ms on, ms off, ..., then steady on), read from _tod_jump_title.csc."""
    m = re.search(r'function flicker_ms\(\)\s*\{\s*return array\(([^)]*)\);', path.read_text(encoding='utf-8'))
    assert m, '_tod_jump_title.csc: flicker_ms() not found'
    ms = [int(v) for v in m.group(1).split(',')]
    assert ms and len(ms) % 2 == 0 and all(v > 0 for v in ms), 'flicker_ms(): want on/off pairs of positive ms'
    return ms


FLICKER_SECS = sum(flicker_ms()) / 1000.0
BLAZE_AT = IGNITE + REVEAL + FLICKER_SECS                 # absolute s from the launch: the card holds lit, the glows start

# THE BLAZE: one glow per row, played on the client's sign host (the text box's bearing, SIGN_DIST out, forward =
# back along the bearing, up = +Z: local Y is the sign's right, local Z its up, sign_offset). It starts the moment
# the lit card HOLDS after its flicker (the client plays it then): the title and subtitle reach full blaze in 0.3 s
# over the lit card, the crest's ring and its sensors flare a beat apart (RING_AT, EYES_AT), full blaze holds to the
# swing back and fades as the sign leaves the frame; the card itself stays lit. render_storyboard.py paints from
# this same table.
BLAZE_LIFE = int(round((SWING + BACK - BLAZE_AT) * 1000))
_L = BLAZE_LIFE / 1000.0
_HOLD = (SWING - BLAZE_AT) / _L                           # full blaze until the swing back starts
_FADE = (SWING + BACK * 0.6 - BLAZE_AT) / _L
FULL = [(0, 0.0), (0.3 / _L, 1.0), (_HOLD, 1.0), (_FADE, 0.35), (1, 0.0)]
RING = [(0, 0.0), ((RING_AT - 0.05) / _L, 0.0), ((RING_AT + 0.1) / _L, 1.0), (_HOLD, 0.9), (_FADE, 0.35), (1, 0.0)]
EYE = [(0, 0.0), ((EYES_AT - 0.05) / _L, 0.0), ((EYES_AT + 0.1) / _L, 1.0), (_HOLD, 1.0), (_FADE, 0.35), (1, 0.0)]
# Preserve the previous soft-halo ratio while fitting the authored mechanical crest.
# The previous ring radius was 135 design units; this radius is measured in the art.
CREST_GLOW_SCALE = CREST_RADIUS * REFERENCE_WIDTH / 135.0
_K = SIGN_DIST / BLAZE_REF_DIST                           # the sizes below were laid out at BLAZE_REF_DIST
BLAZE = [   # element, feature, size, size at the end, colour, alpha over the life
    ('jz_title', 'title', round(11500 * _K), round(11000 * _K), COLORS['title'], FULL),
    ('jz_title_core', 'title', round(6200 * _K), round(5600 * _K), COLORS['title_core'], [(a, v * 0.55) for a, v in FULL]),
    ('jz_sub', 'sub', round(8200 * _K), round(7800 * _K), COLORS['sub'], FULL),
    ('jz_ring', 'ring', round(4800 * CREST_GLOW_SCALE * _K), round(4500 * CREST_GLOW_SCALE * _K), COLORS['ring'], RING),
    ('jz_eye_l', 'eye_l', round(900 * _K), round(800 * _K), COLORS['eye_l'], EYE),
    ('jz_eye_r', 'eye_r', round(900 * _K), round(800 * _K), COLORS['eye_r'], EYE),
]


def gate_geometry():
    """-> (meters per design-grid unit, sign distance D) from the authored width and GATE."""
    src = BUILD_CITY.read_text(encoding='utf-8')
    m = re.search(r'(?s)^GATE = dict\((.*?)\n\s*sat=', src, re.M)
    assert m, 'build_city.py GATE block not found'
    w_deg = float(re.search(r'\bw_deg=([\d.]+)', m.group(1)).group(1))
    d = float(re.search(r'\bD=([\d.]+)', m.group(1)).group(1))
    return 2.0 * d * math.tan(math.radians(w_deg / 2)) / REFERENCE_WIDTH, d


def sign_offset(feature):
    """-> (local Y, local Z) units at SIGN_DIST for an authored feature: Y = the sign's right (the sign faces the
    camera, so its right is the camera's right: +Y when the host faces back along the bearing), Z = up."""
    s, d = gate_geometry()
    du, dv = FEATURES[feature]
    ay = math.atan(du * s / d)
    az = math.atan(-dv * s / d)
    return round(math.tan(ay) * SIGN_DIST), round(math.tan(az) * SIGN_DIST)


# ---- .efx text -------------------------------------------------------------------------------------------------
def split_efx(text):
    """-> (header, [element blocks]) ; each block is '{\\n\\tname ...\\n}\\n'."""
    i = text.index('\n{\n')
    header = text[:i + 1]
    elems = re.findall(r'(?s)\{\n\tname .*?\n\}\n', text[i + 1:])
    return header, elems


def elem_by_name(elems, name):
    for e in elems:
        if ('\tname "%s";' % name) in e:
            return e
    raise KeyError(name)


def set_line(e, key, value):
    new, n = re.subn(r'(?m)^\t' + re.escape(key) + r'\b[^\n]*;$', '\t' + key + ' ' + value + ';', e, count=1)
    assert n == 1, 'field not found: ' + key
    return new


def get_nums(e, key):
    m = re.search(r'(?m)^\t' + re.escape(key) + r' ([^\n;]*);$', e)
    assert m, 'field not found: ' + key
    return [float(x) for x in m.group(1).split()]


def fmt(v):
    return ('%.6f' % v).rstrip('0').rstrip('.') if abs(v - round(v)) > 1e-9 else '%d' % round(v)


def scale_line(e, key, factors, integer=False):
    """multiply a numeric one-line field (per position; a shorter factor list repeats its last factor)."""
    if not re.search(r'(?m)^\t' + re.escape(key) + r' [^\n]*;$', e):
        return e
    vals = get_nums(e, key)
    out = [v * (factors[min(i, len(factors) - 1)]) for i, v in enumerate(vals)]
    if integer:   # millisecond fields are whole numbers in every stock effect
        return set_line(e, key, ' '.join('%d' % round(v) for v in out))
    return set_line(e, key, ' '.join(fmt(v) for v in out))


def scale_graph(e, key, k):
    """multiply the scale number on a graph's header line (the curves below it are normalised)."""
    def rep(m):
        return '\t' + key + ' ' + fmt(float(m.group(1)) * k) + '\n'
    new, n = re.subn(r'(?m)^\t' + re.escape(key) + r' ([-\d.e]+)\n', rep, e, count=1)
    return new if n else e


def set_graph(e, key, scale, curve_a, curve_b=None):
    curve_b = curve_b if curve_b is not None else curve_a
    keys = lambda c: ''.join('\t\t\t' + ' '.join(fmt(v) for v in kk) + '\n' for kk in c)
    body = '\t' + key + ' ' + fmt(scale) + '\n\t{\n\t\t{\n' + keys(curve_a) + '\t\t}\n\t\t{\n' + keys(curve_b) + '\t\t}\n\t};'
    new, n = re.subn(r'(?s)\t' + re.escape(key) + r' [^\n]*\n\t\{\n.*?\n\t\};', lambda _: body, e, count=1)
    assert n == 1, 'graph not found: ' + key
    return new


def mul_color(e, rgb):
    """multiply every key of the colour graph by rgb (a tint that keeps the donor's own colour ramp)."""
    m = re.search(r'(?s)\tcolorGraph ([^\n]*)\n\t\{\n(.*?)\n\t\};', e)
    assert m, 'colorGraph missing'
    def row(line):
        p = line.split()
        if len(p) != 4:
            return line
        t, r, g, b = (float(x) for x in p)
        return '\t\t\t' + ' '.join(fmt(v) for v in (t, r * rgb[0], g * rgb[1], b * rgb[2]))
    body = '\n'.join(row(l) for l in m.group(2).split('\n'))
    return e[:m.start(2)] + body + e[m.end(2):]


def mul_alpha(e, a):
    m = re.search(r'(?s)\talphaGraph ([^\n]*)\n', e)
    if not m:
        return e
    return scale_graph(e, 'alphaGraph', a)


def skyify(e, name, k=1.0, tau=1.0, keep_rel=None):
    """rename, re-scale by (k, tau), open every distance limit, drop sounds and the frustum cull."""
    e = re.sub(r'(?m)^\tname "[^"]*";$', '\tname "%s";' % name, e, count=1)
    flags = re.search(r'(?m)^\tflags ([^\n;]*);$', e).group(1).split()
    flags = [f for f in flags if f not in ('spawnFrustumCull', 'useCollision', 'dieOnTouch')]
    if keep_rel is not None:   # 'runRelToEffect' (follow the host) / 'runRelToWorld' (left in the world)
        flags = [f for f in flags if not f.startswith('runRelTo')] + [keep_rel]
    e = set_line(e, 'flags', ' '.join(flags))
    e = set_line(e, 'spawnRange', '0 %d' % FAR)
    e = set_line(e, 'fadeInRange', '0 0')
    e = set_line(e, 'fadeOutRange', '0 0')
    e = set_line(e, 'spawnFrustumCullRadius', '0')
    for key in ('spawnOrgX', 'spawnOrgY', 'spawnOrgZ', 'spawnOffsetRadius', 'spawnOffsetHeight',
                'trailSplitDist', 'trailRepeatDist', 'trailFadeInDist', 'trailFadeOutDist', 'emitDist', 'emitDistVariance',
                'spotLightStartRadius', 'spotLightEndRadius'):
        e = scale_line(e, key, [k])
    for key in ('lifeSpanMsec', 'spawnDelayMsec'):
        e = scale_line(e, key, [tau], integer=True)
    if re.search(r'(?m)^\teditorFlags [^\n]*\blooping\b', e):   # a one-shot's interval field is not a time
        e = scale_line(e, 'spawnLooping', [tau, 1], integer=True)
    e = scale_line(e, 'gravity', [k / (tau * tau)])
    for key in ('sizeGraph0', 'sizeGraph1'):
        e = scale_graph(e, key, k)
    for key in ('velGraph0X', 'velGraph0Y', 'velGraph0Z', 'velGraph1X', 'velGraph1Y', 'velGraph1Z'):
        e = scale_graph(e, key, k / tau)
    if 'useGaussianCloud' in flags:
        e = scale_graph(e, 'scaleGraph', k)
    # a block's inner lines all start with two tabs: match exactly those (an EMPTY block has none; a lazy
    # '.*?' here once swallowed everything up to the next block's end, the visual included)
    e = re.sub(r'\telemSpawnSound\n\t\{\n(?:\t\t[^\n]*\n)*\t\};', '\telemSpawnSound\n\t{\n\t};', e, count=1)
    e = re.sub(r'\telemFollowSound\n\t\{\n(?:\t\t[^\n]*\n)*\t\};', '\telemFollowSound\n\t{\n\t};', e, count=1)
    return e


def is_model(e):
    return bool(re.search(r'(?m)^\tmodel\n\t\{', e)) or bool(re.search(r'(?m)^\trunner\n\t\{', e))


VISUAL = ('billboardSprite', 'orientedSprite', 'rotatedSprite', 'line', 'tail', 'trail', 'cloud', 'lensFlare')


def has_visual(e):
    """the element draws something (a sprite / line / trail / cloud block naming a material)."""
    return any(re.search(r'(?m)^\t' + v + r'\n\t\{\n\t\t"[^"]+"', e) for v in VISUAL)


def validate(name, text):
    """-> the problems in one written effect (the traps paid for while building these)."""
    bad = []
    head, elems = split_efx(text)
    if 'efUseBoundingBox' not in head or '\tefBoundingBoxMin' not in head:
        bad.append(name + ': no bounding box (a sky-scale effect is culled without one)')
    if not elems:
        bad.append(name + ': no elements')
    for e in elems:
        en = re.search(r'\tname "([^"]*)"', e).group(1)
        if not has_visual(e):
            bad.append(name + '/' + en + ': draws nothing')
        if is_model(e):
            bad.append(name + '/' + en + ': a model / runner element (its assets are not zoned)')
        for key in ('lifeSpanMsec', 'spawnDelayMsec'):
            m = re.search(r'(?m)^\t' + key + r' ([^;]*);', e)
            if m and any(float(v) != int(float(v)) for v in m.group(1).split()):
                bad.append(name + '/' + en + ': fractional ' + key)
        for key in ('elemSpawnSound', 'elemFollowSound'):
            m = re.search(r'\t' + key + r'\n\t\{\n((?:\t\t[^\n]*\n)*)\t\};', e)
            if m and m.group(1).strip():
                bad.append(name + '/' + en + ': still names a sound (' + key + ')')
        m = re.search(r'(?m)^\tspawnRange ([^;]*);', e)
        if not m or float(m.group(1).split()[1]) < FAR:
            bad.append(name + '/' + en + ': spawn range under %d (it would vanish at sky distance)' % FAR)
        if re.search(r'(?m)^\tflags [^\n]*\bspawnFrustumCull\b', e):
            bad.append(name + '/' + en + ': frustum-culled at spawn')
    if 'gfx_debug_missing_fx' in text:
        bad.append(name + ': a stub element (gfx_debug_missing_fx)')
    return bad


def header_for(header, half):
    h = re.sub(r'(?m)^\tefBoundingBoxMin [^\n]*;$', '\tefBoundingBoxMin %d %d %d;' % (-half, -half, -half), header, count=1)
    h = re.sub(r'(?m)^\tefBoundingBoxMax [^\n]*;$', '\tefBoundingBoxMax %d %d %d;' % (half, half, half), h, count=1)
    if '\tefBoundingBoxMin' not in h:   # the "wraith" headers carry no box: add one after efPriority
        h = re.sub(r'(?m)^(\tefPriority [^\n]*;)$', r'\1\n\tefBoundingBoxMin %d %d %d;\n\tefBoundingBoxMax %d %d %d;'
                   % (-half, -half, -half, half, half, half), h, count=1)
    h = re.sub(r'(?m)^\tefFlags [^\n]*;$', '\tefFlags efUseBoundingBox;', h, count=1)
    for i in range(3):
        h = re.sub(r'(?m)^\tlodDefault%d [^\n]*;$' % i, '\tlodDefault%d 0 %d;' % (i, FAR), h, count=1)
    return h


def stock(rel):
    return split_efx((STOCK / rel).read_text(encoding='utf-8'))


# ---- the effects -----------------------------------------------------------------------------------------------
def glow_elem(base, name, *, org, size, size_end, color, alpha, life, looping_ms, oneshot, follow, spread=0.0,
              delay=0):
    """the fleet's additive glow billboard (tools/sky_ships/gen_fx.py element()), plus a spawn delay."""
    e = base
    e = e.replace('\tname "glow";', '\tname "' + name + '";', 1)
    ed = 'looping' if looping_ms else ''
    e = set_line(e, 'editorFlags', (ed + ' useRandSize0 boundingSphere').strip())
    flags = 'spawnRelative spawnOffsetSphere' + (' runRelToEffect' if follow else ' runRelToWorld')
    e = set_line(e, 'flags', flags)
    e = set_line(e, 'spawnRange', '0 %d' % FAR)
    e = set_line(e, 'fadeInRange', '0 0')
    e = set_line(e, 'fadeOutRange', '0 0')
    e = set_line(e, 'spawnFrustumCullRadius', '0')
    e = set_line(e, 'spawnLooping', '%d 0' % (looping_ms or 1))
    e = set_line(e, 'spawnLoopingSpawnCount', '1 0')
    e = set_line(e, 'spawnOneShot', '%d 0' % oneshot)
    e = set_line(e, 'spawnDelayMsec', '%d 0' % delay)
    e = set_line(e, 'lifeSpanMsec', '%d %d' % life)
    e = set_line(e, 'spawnOrgX', '%s 0' % fmt(org[0]))
    e = set_line(e, 'spawnOrgY', '%s 0' % fmt(org[1]))
    e = set_line(e, 'spawnOrgZ', '%s 0' % fmt(org[2]))
    e = set_line(e, 'spawnOffsetRadius', '%s %s' % (fmt(spread), fmt(spread * 0.5)))
    e = set_line(e, 'spawnOffsetHeight', '0.1 0.1')
    e = set_line(e, 'gravity', '0 0')
    for axis in ('X', 'Y', 'Z'):
        e = set_graph(e, 'velGraph0' + axis, 0, [(0, 0), (1, 0)])
        e = set_graph(e, 'velGraph1' + axis, 0, [(0, 0), (1, 0)])
    e = set_graph(e, 'sizeGraph0', 1, [(0, size), (1, size_end)], [(0, size * 0.9), (1, size_end * 0.9)])
    e = set_graph(e, 'sizeGraph1', 1, [(0, size), (1, size_end)], [(0, size * 0.9), (1, size_end * 0.9)])
    e = set_graph(e, 'colorGraph', 1, [(0,) + tuple(color), (1,) + tuple(color)])
    e = set_graph(e, 'alphaGraph', 1, alpha)
    return e


def donor_glow():
    text = DONOR_GLOW.read_text(encoding='utf-8')
    header, _ = split_efx(text)
    m = re.search(r'\{\n\tname "glow";.*?\n\}\n', text, re.S)
    assert m, 'donor glow element missing'
    return header, m.group(0)


def build():
    out = {}
    ghead, glow = donor_glow()

    # ---- THE CRASH --------------------------------------------------------------------------------------------
    ahead, aelems = stock('explosions/fx_exp_generic_aerial_lg.efx')
    _, melems = stock('killstreaks/fx_mship_death_exp.efx')
    K = 3.2
    # THE TIME FACTOR PER LAYER (user after the first play: "the kaboom ended early"): the white flash is a quarter
    # second now, so the fire is what the player SEES. The flash-length bursts keep 1.25; the hot glow lingers
    # through the flash's burn-out (x2.4); the fire billows and the tendrils burn ~2.6 s on average (x1.5) and the
    # dark smoke thins by ~2.6 s (x0.8), so the fire has cleared off the title as the smoke over the sign lifts
    # (CLEAR_FROM..CLEAR_DONE after the ignite).
    TAU = {'burst_glow': 1.25, 'burst_glow copy': 1.25, 'burst_glow_linger': 2.4, 'burst_glow_debris': 1.25,
           'exp_smk_core_2': 1.5, 'tendrils_0': 1.5, 'sparks_pcloud_2': 1.25, 'shockwave_fast': 1.25}
    boom = []
    for n, tau in TAU.items():
        boom.append(skyify(elem_by_name(aelems, n), 'jt_' + n.replace(' ', '_'), K, tau))
    boom.append(skyify(elem_by_name(aelems, 'smk_thick_1'), 'jt_smk_thick', K, 0.8))
    # a white-hot core flash under the burst (the donor glow: an additive punch the stock burst lacks at range)
    boom.append(glow_elem(glow, 'jt_core_flash', org=(0, 0, 0), size=9000, size_end=13000, color=(1.0, 0.86, 0.62),
                          alpha=[(0, 1.0), (0.35, 0.8), (1, 0.0)], life=(420, 60), looping_ms=0, oneshot=1, follow=False))
    # THE FIREBALL'S LIGHT: an orange bloom ~110-125 deg across at the crash distance, still at 0.8 when the white
    # burns out and fading as the fire thins ("a huge explosion so you can't see anything")
    boom.append(glow_elem(glow, 'jt_fireball', org=(0, 0, 0), size=9000, size_end=12500, color=(1.0, 0.42, 0.1),
                          alpha=[(0, 0.0), (0.05, 0.8), (0.4, 0.62), (1, 0.0)], life=(2300, 200), looping_ms=0,
                          oneshot=1, follow=False))
    for i, n in enumerate(('wraith_oneshot_def6', 'wraith_oneshot_def0', 'wraith_oneshot_def2')):   # sparks + gibs falling
        boom.append(skyify(elem_by_name(melems, n), 'jt_fall_%d' % i, 4.0, 1.4))
    # THE SHOCKWAVE: Der Eisendrache's moon blast (dlc1/castle/fx_exp_moon_castle) - its two giant flat shock
    # rings, the thin ring and the spark flash - at 6% of the moon's scale and 60% of its time, started WITH the
    # blast (the moon's own 2.5 s run-up of surface explosions, its runners, is not taken).
    _, celems = stock('dlc1/castle/fx_exp_moon_castle.efx')
    for n, tag in (('wraith_oneshot_def0', 'shock'), ('wraith_oneshot_def2', 'shock_fire'), ('wraith_oneshot_def1', 'ring'),
                   ('wraith_looping_def1', 'spark_flash')):
        e = skyify(elem_by_name(celems, n), 'jt_moon_' + tag, 0.06, 0.6)
        d = get_nums(e, 'spawnDelayMsec')
        e = set_line(e, 'spawnDelayMsec', '%d %d' % (max(0, round(d[0] - 2500 * 0.6)), round(d[1])))
        boom.append(e)
    out['fx_jt_boom'] = header_for(ghead, 30000) + ''.join(boom)

    blast = []
    for n in ('burst_glow', 'burst_glow_linger', 'exp_smk_core_2', 'sparks_pcloud_2', 'tendrils_0'):
        blast.append(skyify(elem_by_name(aelems, n), 'jb_' + n.replace(' ', '_'), 1.6, 1.1))
    out['fx_jt_blast'] = header_for(ghead, 16000) + ''.join(blast)

    # ---- THE WRECKAGE: fire and smoke on falling arcs ---------------------------------------------------------
    shead, selems = stock('killstreaks/fx_heli_exp_streamer1.efx')
    wreck = []
    for i, n in enumerate(('wraith_oneshot_def4', 'wraith_oneshot_def5', 'wraith_oneshot_def0', 'wraith_oneshot_def1')):
        e = skyify(elem_by_name(selems, n), 'jw_%d' % i, 3.0, 1.4)
        # thrown out and falling: a downward drift plus gravity (the stock streamer rides a moving helicopter)
        e = set_graph(e, 'velGraph0Z', 1, [(0, -900), (1, -1400)], [(0, -500), (1, -1100)])
        e = set_graph(e, 'velGraph0Y', 1, [(0, 600), (1, 300)], [(0, -600), (1, -300)])
        e = set_line(e, 'gravity', '220 120')
        if get_nums(e, 'spawnOneShot')[0] < 1:   # the stock streamer's billow is emitted by a moving heli: a burst here
            e = set_line(e, 'spawnOneShot', '3 1')
        wreck.append(e)
    wreck.append(skyify(elem_by_name(melems, 'wraith_oneshot_def6'), 'jw_sparks', 3.0, 1.6))
    out['fx_jt_wreck'] = header_for(ghead, 20000) + ''.join(wreck)

    # ---- THE CHARGE: both engines flare --------------------------------------------------------------------------
    ships = {r['ship']: r for r in json.loads(MANIFEST.read_text(encoding='utf-8'))['ships']}
    burn = []
    for i, (x, y, z, rad) in enumerate(ships['gunship']['nozzles']):
        org = (x - rad * 0.6, y, z)
        burn.append(glow_elem(glow, 'jb_core_%d' % i, org=org, size=rad * 7.0, size_end=rad * 5.5, color=(0.85, 0.97, 1.0),
                              alpha=[(0, 1.0), (1, 0.9)], life=(90, 20), looping_ms=30, oneshot=1, follow=True))
        burn.append(glow_elem(glow, 'jb_flare_%d' % i, org=org, size=rad * 14.0, size_end=rad * 10.0, color=(0.3, 0.8, 1.0),
                              alpha=[(0, 0.7), (1, 0.0)], life=(160, 40), looping_ms=40, oneshot=1, follow=True))
        burn.append(glow_elem(glow, 'jb_streak_%d' % i, org=org, size=rad * 4.0, size_end=rad * 9.0, color=(0.35, 0.85, 1.0),
                              alpha=[(0, 0.8), (0.3, 0.5), (1, 0.0)], life=(700, 150), looping_ms=20, oneshot=1,
                              follow=False, spread=rad * 0.3))
    out['fx_jt_burn'] = header_for(ghead, 22000) + ''.join(burn)

    # ---- THE ARRIVAL: each gunship WARPS IN beside the dimmed sign ------------------------------------------------
    # Gorod Krovi's dragon-strike portal flash (dlc3/stalingrad/fx_dragonstrike_portal_flash, a portal tearing open
    # in the sky): lightning beams and bolts, a white-hot core cooling through orange to blue plasma, shock rings,
    # heat distortion, a lingering blue haze. At 60% of its size (its biggest ring ~4,500 u; a gunship is 3,600 u
    # long, ~7,500 u from the rider) and on its own timing (~1 s).
    _, pelems = stock('dlc3/stalingrad/fx_dragonstrike_portal_flash.efx')
    warp = []
    for e in pelems:
        if is_model(e) or not has_visual(e):
            continue
        n = re.search(r'\tname "([^"]*)"', e).group(1)
        warp.append(skyify(e, 'jp_' + n.replace('wraith_', ''), 0.6, 1.0))
    out['fx_jt_warp'] = header_for(ghead, 14000) + ''.join(warp)

    # ---- THE TITLE BLAZING (the BLAZE table, above) ---------------------------------------------------------------
    blaze = [glow_elem(glow, name, org=(0,) + sign_offset(feature), size=size, size_end=size_end, color=rgb,
                       alpha=alpha, life=(BLAZE_LIFE, 0), looping_ms=0, oneshot=1, follow=True)
             for name, feature, size, size_end, rgb, alpha in BLAZE]
    # the surge's sparks raining off the letters as the power holds (the effect starts when the card holds)
    sp = skyify(elem_by_name(melems, 'wraith_oneshot_def6'), 'jz_sparks', 6.0 * _K, 1.5)
    blaze.append(sp)
    out['fx_jt_blaze'] = header_for(ghead, 30000) + ''.join(blaze)
    return out


def main():
    fx = build()
    problems = [b for n, t in sorted(fx.items()) for b in validate(n, t)]
    if problems:
        print('JUMP TITLE FX INVALID:\n  ' + '\n  '.join(problems))
        sys.exit(1)
    if '--check' in sys.argv:
        bad = [n for n, t in fx.items() if not (OUT / (n + '.efx')).exists() or (OUT / (n + '.efx')).read_text(encoding='utf-8') != t]
        if bad:
            print('JUMP TITLE FX STALE:', ', '.join(bad), '- run python tools/jump_title/gen_fx.py')
            sys.exit(1)
        print('JUMP TITLE FX OK', len(fx))
        return
    out_dir = OUT
    if '--out' in sys.argv:
        out_dir = pathlib.Path(sys.argv[sys.argv.index('--out') + 1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob('fx_jt_*.efx'):
        if old.stem not in fx:
            old.unlink()
            print('JUMP TITLE FX RETIRED', old.name)
    for n, t in fx.items():
        (out_dir / (n + '.efx')).write_text(t, encoding='utf-8', newline='\n')
        path = 'tod/jump/' + n
        assert len(path) < 63, path
        assert 'gfx_debug_missing_fx' not in t, n + ' carries a stub element'
    print('JUMP TITLE FX WRITTEN', sorted(fx))


if __name__ == '__main__':
    main()
