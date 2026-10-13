"""
tools/sky3d/finish_sky.py — the raw Blender equirect (linear EXR) -> the game's sky asset (docs/166)

THE EXPOSURE CONTRACT (docs/104 §4, unchanged): the sky file is a LIGHT SOURCE. The bake integrates it
through skyStops, and the drawn pipeline always solved its gain so that
    score = mean(linear RGB over the whole sphere) x 1024
lands on --target-score (historically 0.16; the current pipeline holds non-sign city score at 0.64).
An explicit --fixed-gain instead preserves an already reviewed radiance scale:
local dimming then stays local, and the city/whole-sky scores become measured
results rather than normalization targets. This option is off by default.
This holds average energy only: changed direction/color still changes GI and reflections and needs
a fresh lighting bake. Peaks: the
drawn sky soft-clipped every display value above a knee so the engine's bloom does not halo every
window white (docs/104 §4k); here the knee is expressed relative to the picture's mean — --knee K
starts the soft clip at K x mean, --knee-max M is the asymptote at M x mean — because a rendered
picture has its own absolute scale. The EXR is half-float ZIP16 with channels A,B,G,R, the exact
layout the drawn pipeline shipped and the mod tools converter accepts.

⚠️ 2026-09-28 — skyStops ALSO SCALES THE SKY YOU SEE (Treyarch: skyStops "will live update to Radiant"; only the
bounced light needs a rebake). What is on screen is ~ EXR x 2^skyStops (x exposure). Two "brighter sky" passes
(2026-09-26 score 0.16->0.32 with skyStops 2.85->1.85, 2026-09-27 0.32->0.64 with 1.85->0.85) each CANCELLED ON
SCREEN, and the user saw no change twice. NEVER compensate a brighter picture with a lower skyStops if the goal is a
brighter visible sky. The sky_intensity_factor 10 in the worldspawn is UNVERIFIED above 1 (no stock map uses >1).

RUN (Blender's Python: numpy + the EXR reader come with it)
  "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe" -b --factory-startup -P tools/sky3d/finish_sky.py -- \
      --in <raw.exr> [--target-score 0.16] [--knee 10] [--knee-max 32] [--roll 0] [--mirror] \
      [--out source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr | --no-asset] \
      [--preview-dir docs/sky_preview] [--tag sky3d] [--preview-gain 0.01285] [--bloom 0] [--tint r,g,b] [--sat 1.0]
  --sat S     (v6) saturation about luminance, in linear light, before the knee and the gain solve (the mean is re-held):
              1.0 = as rendered; docs/166 §8 records the value the ship used
  --fixed-gain G    optional finite positive gain applied after the normal target-score solve.
              Retains the nominal --target-score in stats, but does not normalize to it.
              Use only with a reviewed baseline gain; changed energy still needs a full bake.
  --roll D    turns the picture D degrees (+ = content moves to higher azimuth / right) before anything else
  --mirror    flips it left-right (the in-game checklist item: if the sign reads backwards, re-finish with this)
  --bloom S   optional soft glow (radius ~1% of width) added at strength S before the knee; 0 = off (the game blooms itself)
  --preview-gain G   the display mapping of the PNG previews, display = (linear x M / G) ^ (1/2.2). Default 0.0176 = the
              gain Cybercity I's approved night sky shipped with (docs/104): its canvas value 1.0 became EXR 0.0176 and
              read as display white in game, so this is the one calibrated absolute mapping we have (bloom excepted).
  --display-mult M   (v4) the in-game worldspawn sky_intensity_factor0/1 — the game multiplies the visible sky box by it
              and the bake does not see it (docs/162 05 §4.4); the previews apply the same factor so they predict the game.
  --white W   (v4) the RAW value that is display white (build_city.py authors in W units: 1.0). With it the knee is in W:
              --knee-w K (0.70) starts the soft clip, --knee-max-w M (1.0) is its asymptote. The gain is still solved to
              --target-score (the world's light does not move); the log prints where W lands in the EXR and on screen.
  --sign-mask P   (v7b, docs/166 §9.7) the title gate's AOV (build_city.py writes <raw>.sign.exr beside the raw; that is the
              default). Inside it the sign gets ITS OWN knee, --sign-knee-w (2.0 W) -> --sign-knee-max-w (4.0 W), instead of the
              city's 0.7 -> 1.0 W, so the hero sign's neon out-shines everything else. The gain is solved on the pixels
              OUTSIDE the sign: the city scores --target-score and the sign is ADDED light (the whole sky 0.6865 on the v7b
              ship; verify_tower_design.js pins that as SKY_SCORE). --whole-sky-gain = the old whole-sphere solve (the city
              gives up the sign's ~7 %, and that gate fails until SKY_SCORE moves). --no-sign-mask = the v7 finish.
"""
import bpy, math, sys, os, time, zlib, struct, json
import numpy as np

T0 = time.time()
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(k, d=None):
    if k in ARGS:
        i = ARGS.index(k)
        return ARGS[i + 1] if i + 1 < len(ARGS) else d
    return d


def flag(k):
    return k in ARGS


HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
IN = arg('--in')
if not IN or not os.path.exists(IN):
    raise SystemExit(f'--in <raw.exr> is required (got {IN})')
TARGET = float(arg('--target-score', '0.16'))
if flag('--fixed-gain') and arg('--fixed-gain') is None:
    raise SystemExit('--fixed-gain requires a finite positive number')
FIXED_GAIN = float(arg('--fixed-gain')) if arg('--fixed-gain') is not None else None
if FIXED_GAIN is not None and (not math.isfinite(FIXED_GAIN) or FIXED_GAIN <= 0):
    raise SystemExit('--fixed-gain must be finite and positive')
KNEE = float(arg('--knee', '10'))
KNEE_MAX = float(arg('--knee-max', '32'))
ROLL = float(arg('--roll', '0'))
MIRROR = flag('--mirror')
OUT = arg('--out', os.path.join(REPO, 'source_data', 'tod_skybox', '_images', 'i_skybox_tod_cybercity.exr'))
NO_ASSET = flag('--no-asset')
PREVIEW_DIR = arg('--preview-dir', os.path.join(REPO, 'docs', 'sky_preview'))
TAG = arg('--tag', 'sky3d')
PGAIN = float(arg('--preview-gain', '0.0176'))
DM_ARG = arg('--display-mult', '1')
DISPLAY_MULT = None if DM_ARG == 'auto' else float(DM_ARG)   # auto (needs --white): the worldspawn sky_intensity_factor that puts W at display white
WHITE = float(arg('--white')) if arg('--white') else None
KNEE_W = float(arg('--knee-w', '0.70'))
KNEE_MAX_W = float(arg('--knee-max-w', '1.0'))
BLOOM = float(arg('--bloom', '0'))
TINT = [float(v) for v in arg('--tint', '1,1,1').split(',')]
SAT = float(arg('--sat', '1'))   # v6: a saturation grade in linear light (about Rec.709 luminance), before the knee   # docs/104 §4b: tint the sky (= the sky LIGHT) in linear light; the gain solve re-holds the mean
SIGN_MASK = None if flag('--no-sign-mask') else arg('--sign-mask', os.path.splitext(IN)[0] + '.sign.exr')
SIGN_KNEE_W = float(arg('--sign-knee-w', '2.0'))
SIGN_KNEE_MAX_W = float(arg('--sign-knee-max-w', '4.0'))
HOLD_CITY = not flag('--whole-sky-gain')   # v7b: with a sign mask the gain is solved on the pixels OUTSIDE the sign: the city scores
                                           # --target-score, the sign is ADDED light (the whole sky 0.6865 on the v7b ship, which
                                           # tools/art_cohesion/verify_tower_design.js pins as SKY_SCORE). --whole-sky-gain = the old
                                           # whole-sphere solve (the city gives up the sign's ~7 %) - it fails that gate until SKY_SCORE moves.
D2R = math.pi / 180


def log(*a):
    print(f'[finish {time.time() - T0:6.1f}s]', *a, flush=True)


# ---------------------------------------------------------------- load
img = bpy.data.images.load(os.path.abspath(IN))
W, H = img.size
buf = np.empty(W * H * img.channels, dtype=np.float32)
img.pixels.foreach_get(buf)
rgb = buf.reshape(H, W, img.channels)[::-1, :, :3].astype(np.float32)   # Blender rows start at the bottom; row 0 = zenith here
del buf
bpy.data.images.remove(img)
rgb = np.nan_to_num(rgb, nan=0.0, posinf=0.0, neginf=0.0)
np.maximum(rgb, 0.0, out=rgb)
log(f'loaded {IN}: {W}x{H}, raw mean {rgb.mean():.4e}, max {rgb.max():.3e}')
if H * 2 != W:
    raise SystemExit(f'not a 2:1 equirect: {W}x{H}')
sign = None                                                   # v7b: the title gate's mask (its AOV), 0..1 per pixel
if SIGN_MASK and os.path.exists(SIGN_MASK):
    if os.path.getmtime(SIGN_MASK) + 600 < os.path.getmtime(IN):
        raise SystemExit(f'the sign mask {SIGN_MASK} is older than the raw render — a stale pair (re-render, or --no-sign-mask)')
    mimg = bpy.data.images.load(os.path.abspath(SIGN_MASK))
    if tuple(mimg.size) != (W, H):
        raise SystemExit(f'the sign mask is {tuple(mimg.size)}, the raw is {(W, H)}')
    mb = np.empty(W * H * mimg.channels, dtype=np.float32)
    mimg.pixels.foreach_get(mb)
    sign = np.clip(np.nan_to_num(mb.reshape(H, W, mimg.channels)[::-1, :, 0]), 0.0, 1.0).astype(np.float32)
    del mb
    bpy.data.images.remove(mimg)
    # the AOV is written only where the card is the camera ray's first surface: the fog scatters a few % of those paths first,
    # so the card's interior reads ~0.99, not 1 — normalise on its robust interior value
    core = sign[sign > 0.3]
    norm = float(np.clip(np.percentile(core, 99.5), 0.8, 1.0)) if core.size else 1.0
    sign = np.clip(sign / norm, 0.0, 1.0)
    log(f'sign mask {SIGN_MASK}: {float((sign > 0.5).mean()) * 100:.2f}% of the sphere, interior {norm:.3f} (normalised to 1)')
elif SIGN_MASK:
    log(f'no sign mask at {SIGN_MASK}: the city knee everywhere')

# ---------------------------------------------------------------- orientation
if MIRROR:
    rgb = rgb[:, ::-1, :]
    if sign is not None:
        sign = sign[:, ::-1]
if ROLL:
    rgb = np.roll(rgb, int(round(ROLL / 360.0 * W)), axis=1)
    if sign is not None:
        sign = np.roll(sign, int(round(ROLL / 360.0 * W)), axis=1)

# ---------------------------------------------------------------- optional bloom (the game has its own; off by default)
if BLOOM > 0:
    r = max(2, int(W * 0.01))
    k = np.exp(-0.5 * (np.arange(-3 * r, 3 * r + 1) / r) ** 2).astype(np.float32)
    k /= k.sum()
    hot = np.maximum(rgb - np.percentile(rgb, 99.0), 0.0)
    def blur1(a, axis):
        return np.apply_along_axis(lambda v: np.convolve(v, k, mode='same'), axis, a)
    glow = blur1(blur1(hot, 1), 0)
    rgb += BLOOM * glow
    log(f'bloom {BLOOM} radius {r}px')

# ---------------------------------------------------------------- tint (linear), knee + gain solve
if TINT != [1.0, 1.0, 1.0]:
    rgb *= np.asarray(TINT, dtype=np.float32)[None, None, :]
    log(f'tint {TINT} applied in linear light (the mean is re-held by the gain solve below)')
if SAT != 1.0:
    Y = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    rgb -= Y[..., None]
    rgb *= SAT
    rgb += Y[..., None]
    np.maximum(rgb, 0.0, out=rgb)
    del Y
    log(f'saturation x{SAT:g} about luminance, in linear light')
m0 = float(rgb.mean())
if WHITE is not None:
    kn, km = KNEE_W * WHITE, KNEE_MAX_W * WHITE                                 # v4: the knee in display-white units
    log(f'raw mean {m0:.4e} = {m0 / WHITE:.3f} W; knee {KNEE_W} W -> {KNEE_MAX_W} W')
else:
    kn, km = KNEE * m0, KNEE_MAX * m0
def soft_knee(a, k0, k1):
    r = k1 - k0
    return np.where(a > k0, k0 + r * (1.0 - np.exp(-(a - k0) / r)), a).astype(np.float32)


frac_hot = float((rgb > kn).mean())
skn = skm = None
if sign is not None:
    if WHITE is None:
        raise SystemExit('--sign-mask needs --white (the sign knee is in W)')
    skn, skm = SIGN_KNEE_W * WHITE, SIGN_KNEE_MAX_W * WHITE
sum_all = sum_out = w_out = 0.0
sign_peak = 0.0
for y0 in range(0, H, 256):                                   # in row blocks: an 8192 sky is 400 MB a copy
    blk = rgb[y0:y0 + 256]
    kb = soft_knee(blk, kn, km)
    if sign is not None:
        mblk = sign[y0:y0 + 256]
        if mblk.any():
            sk = soft_knee(blk, skn, skm)
            sign_peak = max(sign_peak, float(sk[mblk > 0.5].max()) if (mblk > 0.5).any() else 0.0)
            kb += mblk[..., None] * (sk - kb)
        wo = 1.0 - mblk
        sum_out += float(np.einsum('ijk,ij->', kb, wo, dtype=np.float64))
        w_out += float(wo.sum(dtype=np.float64)) * 3.0
    sum_all += float(kb.sum(dtype=np.float64))
    rgb[y0:y0 + 256] = kb
m1_all = sum_all / rgb.size
m1_city = sum_out / w_out if sign is not None else m1_all
m1 = m1_city if (sign is not None and HOLD_CITY) else m1_all   # v7b: --hold-city = the sign is added light; default = the whole-sky contract
gain = TARGET / 1024.0 / m1
if FIXED_GAIN is not None:
    log(f'fixed gain {FIXED_GAIN:.17g} replaces target-score gain {gain:.17g}; city and whole-sky scores are measured, not held')
    gain = FIXED_GAIN
rgb *= gain
mean = float(rgb.mean())
if sign is not None:
    log(f'sign: its own knee {SIGN_KNEE_W:g} W -> {SIGN_KNEE_MAX_W:g} W (the city {KNEE_W:g} -> {KNEE_MAX_W:g}), peak {sign_peak / WHITE:.2f} W; '
        f'the sign carries {(m1_all / m1_city - 1) * 100:+.1f}% of the sky\'s light; '
        f'{"fixed baseline gain; nominal solve basis " if FIXED_GAIN is not None else "gain solved on "}'
        f'{"the city OUTSIDE the sign (the sign is added light)" if HOLD_CITY else "the whole sky (--whole-sky-gain)"}: '
        f'the whole sky scores {mean * 1024:.3f}, the city {m1_city * gain * 1024:.3f}')
upper = float(rgb[: H // 2].mean())
share = rgb.reshape(-1, 3).sum(0)
share = share / share.sum() * 100
pct = {p: float(np.percentile(rgb, p)) for p in (50, 90, 99, 99.9)}
mx = float(rgb.max())
log(f'knee {"%.2f W" % kn if WHITE is not None else "%gx mean" % KNEE} -> {"%.2f W" % km if WHITE is not None else "%gx mean" % KNEE_MAX}: {frac_hot * 100:.2f}% of samples above the knee')
if WHITE is not None:
    w_exr = WHITE * gain
    if DISPLAY_MULT is None:
        DISPLAY_MULT = max(1.0, min(10.0, PGAIN / w_exr))
        log(f'display-mult auto: sky_intensity_factor {DISPLAY_MULT:.2f} (= {PGAIN:g} / W_exr; the documented range is 0..10)')
    log(f'W (display white) -> EXR {w_exr:.4e}; on screen x{DISPLAY_MULT:g} -> display {min(1.0, (w_exr * DISPLAY_MULT / PGAIN)) ** (1 / 2.2):.2f}; '
        f'the mean displays at {min(1.0, mean * DISPLAY_MULT / PGAIN) ** (1 / 2.2):.2f}')
if DISPLAY_MULT is None:
    DISPLAY_MULT = 1.0
log(f'STATS mean {mean:.4e} (upper half {upper:.4e}) score(x1024) {mean * 1024:.3f} rgb share {share[0]:.0f}/{share[1]:.0f}/{share[2]:.0f} '
    f'gain {gain:.4e} | p50 {pct[50] / mean:.2f}x p90 {pct[90] / mean:.2f}x p99 {pct[99] / mean:.2f}x p99.9 {pct[99.9] / mean:.2f}x max {mx / mean:.1f}x of the mean')
# the wrap: the |col W-1 - col 0| delta against the mean adjacent-column delta (a periodic picture sits inside the noise)
seam = float(np.abs(rgb[:, -1] - rgb[:, 0]).mean())
neigh = float(np.abs(rgb[:, 1:] - rgb[:, :-1]).mean())
log(f'seam: wrap delta {seam:.3e} = {seam / max(neigh, 1e-12):.2f}x the mean adjacent-column delta')

# ---------------------------------------------------------------- EXR writer (half, ZIP16, channels A B G R) — the drawn pipeline's layout
def write_exr_half(path, w, h, rgb):
    names = ['A', 'B', 'G', 'R']
    parts = [b'\x76\x2f\x31\x01', struct.pack('<i', 2)]

    def attr(name, typ, val):
        parts.extend([name.encode() + b'\0' + typ.encode() + b'\0', struct.pack('<i', len(val)), val])

    chl = b''.join(n.encode() + b'\0' + struct.pack('<i', 1) + b'\0\0\0\0' + struct.pack('<ii', 1, 1) for n in names) + b'\0'
    attr('channels', 'chlist', chl)
    attr('compression', 'compression', b'\x03')
    box = struct.pack('<iiii', 0, 0, w - 1, h - 1)
    attr('dataWindow', 'box2i', box)
    attr('displayWindow', 'box2i', box)
    attr('lineOrder', 'lineOrder', b'\x00')
    attr('pixelAspectRatio', 'float', struct.pack('<f', 1.0))
    attr('screenWindowCenter', 'v2f', struct.pack('<ff', 0.0, 0.0))
    attr('screenWindowWidth', 'float', struct.pack('<f', 1.0))
    parts.append(b'\0')
    header = b''.join(parts)
    LINES = 16
    nchunks = (h + LINES - 1) // LINES
    offset = len(header) + nchunks * 8
    table, chunks = [], []
    ones = np.ones((w,), dtype='<f2')
    half = rgb.astype('<f2')
    for ci in range(nchunks):
        y0 = ci * LINES
        y1 = min(h, y0 + LINES)
        rows = []
        for y in range(y0, y1):
            rows.append(ones)                       # A
            rows.append(half[y, :, 2])              # B
            rows.append(half[y, :, 1])              # G
            rows.append(half[y, :, 0])              # R
        raw = np.concatenate(rows).view(np.uint8)
        n = raw.size
        re = np.empty(n, dtype=np.uint8)            # OpenEXR zip: split even/odd bytes, then a byte-delta predictor, then deflate
        h1 = (n + 1) // 2
        re[:h1] = raw[0::2]
        re[h1:] = raw[1::2]
        d = np.empty(n, dtype=np.uint8)
        d[0] = re[0]
        d[1:] = ((re[1:].astype(np.int16) - re[:-1].astype(np.int16) + 128) & 255).astype(np.uint8)
        comp = zlib.compress(d.tobytes(), 6)
        data = comp if len(comp) < n else raw.tobytes()
        table.append(struct.pack('<Q', offset))
        head = struct.pack('<ii', y0, len(data))
        chunks.append(head)
        chunks.append(data)
        offset += 8 + len(data)
    with open(path, 'wb') as f:
        f.write(header)
        f.write(b''.join(table))
        f.write(b''.join(chunks))


if not NO_ASSET:
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    t = time.time()
    write_exr_half(OUT, W, H, rgb)
    log(f'EXR {time.time() - t:.1f}s -> {os.path.relpath(OUT, REPO) if OUT.startswith(REPO) else OUT} ({os.path.getsize(OUT) / 1048576:.1f} MB, half, zip16)')
else:
    log('no asset written (--no-asset)')

# ---------------------------------------------------------------- previews
os.makedirs(PREVIEW_DIR, exist_ok=True)


def to_display(lin):
    return np.clip(np.power(np.clip(lin * DISPLAY_MULT / PGAIN, 0.0, None), 1.0 / 2.2), 0.0, 1.0)


def save_png(path, disp):
    """disp: (h, w, 3) floats 0..1, row 0 = top"""
    h, w = disp.shape[:2]
    im = bpy.data.images.new('prev', w, h, alpha=False)
    px = np.empty((h, w, 4), dtype=np.float32)
    px[..., :3] = disp[::-1]
    px[..., 3] = 1.0
    im.pixels.foreach_set(px.ravel())
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)


# the whole sphere, box-filtered to 2048 wide
k = max(1, W // 2048)
eq = rgb[: (H // k) * k, : (W // k) * k].reshape(H // k, k, W // k, k, 3).mean((1, 3))
save_png(os.path.join(PREVIEW_DIR, f'{TAG}_sky_equirect.png'), to_display(eq))


def view(name, az_deg, pitch_deg, VW=1920, VH=1080):
    """a perspective look at the sphere: cg_fov 65 (4:3 horizontal, Hor+) -> 80.7 deg at 16:9, bilinear, wrap in x"""
    vfov = 2 * math.atan(math.tan(65 * D2R / 2) / (4 / 3))
    hfov = 2 * math.atan(math.tan(vfov / 2) * VW / VH)
    f = (VW / 2) / math.tan(hfov / 2)
    xs = (np.arange(VW) + 0.5 - VW / 2)
    ys = -(np.arange(VH) + 0.5 - VH / 2)
    X, Y = np.meshgrid(xs, ys)
    # camera ray: forward along +Y', right +X', up +Z'; pitch about the right axis, then yaw
    cp, sp = math.cos(pitch_deg * D2R), math.sin(pitch_deg * D2R)
    dx, dy, dz = X, np.full_like(X, f), Y
    dy2 = dy * cp - dz * sp
    dz2 = dy * sp + dz * cp
    L = np.sqrt(dx * dx + dy2 * dy2 + dz2 * dz2)
    dx, dy2, dz2 = dx / L, dy2 / L, dz2 / L
    az = np.arctan2(dx, dy2) + az_deg * D2R
    el = np.arcsin(np.clip(dz2, -1, 1))
    u = (az / (2 * math.pi) + 0.5) * W - 0.5
    v = (0.5 - el / math.pi) * H - 0.5
    u = np.mod(u, W)
    v = np.clip(v, 0, H - 1)
    x0 = np.floor(u).astype(np.int64)
    y0 = np.floor(v).astype(np.int64)
    fx = (u - x0)[..., None].astype(np.float32)
    fy = (v - y0)[..., None].astype(np.float32)
    x1 = (x0 + 1) % W
    y1 = np.minimum(y0 + 1, H - 1)
    s = (rgb[y0, x0] * (1 - fx) + rgb[y0, x1] * fx) * (1 - fy) + (rgb[y1, x0] * (1 - fx) + rgb[y1, x1] * fx) * fy
    save_png(os.path.join(PREVIEW_DIR, f'{TAG}_ingame_{name}.png'), to_display(s))
    return hfov


VIEWS = [('moon', 0, 6), ('city', 126, 4), ('skyline_r', 55, 7), ('harbour', -125, 3), ('behind', 180, 5),
         ('down_r', 60, -48), ('down_l', -140, -40), ('nadir', 0, -80), ('up', 0, 40),
         # v2 (docs/166): the origin tower + its storm, the black hole, the tether station; v4: the giant, the cracked planet, a galaxy
         ('origin', -140, 24), ('gargantua', 75, 50), ('galaxy', -40, 52), ('tether', 100, 30), ('giant', -98, 40), ('brown', -60, 35),
         ('celestial_east', 130, 55),
         ('station', 89, 16),
         # v5: the second black hole, the core's seam into the grid (v7b: the battlecruisers' 'ships' view retired with them)
         ('maelstrom', -12, 66), ('core', -100, -28),
         # v6: the red giant
         ('ruby', -20, 44),
         # v7: the title gate as the crown->tower jump's reveal frames it (docs/166 §9; session 61's camera aims at the text box, el 11)
         ('reveal', 0, 11), ('reveal_cinematic', 0, 13)]
hfov = None
requested_views = set((arg('--views', '') or '').split(',')) - {''}
if requested_views:
    unknown = requested_views - {v[0] for v in VIEWS}
    if unknown:
        raise SystemExit('Unknown preview views: ' + ', '.join(sorted(unknown)))
    VIEWS = [v for v in VIEWS if v[0] in requested_views]
for name, az, pitch in VIEWS:
    hfov = view(name, az + ROLL, pitch)                  # v7: the views are named after CONTENT, so they follow --roll (the sign sits at az -90 after the ship's roll)
log(f'previews -> {PREVIEW_DIR}/{TAG}_sky_equirect.png + {len(VIEWS)} in-game views (1920x1080, hfov {hfov / D2R:.1f} deg, {hfov / (2 * math.pi) * W / 1920:.2f} texel/px)')
stats = dict(input=os.path.abspath(IN), size=[W, H], target_score=TARGET, score=mean * 1024, mean=mean, upper_mean=upper,
             rgb_share=[float(s) for s in share], gain=gain, gain_mode=('fixed' if FIXED_GAIN is not None else 'target_score'),
             fixed_gain=FIXED_GAIN, knee=[KNEE, KNEE_MAX], hot_fraction=frac_hot,
             percentiles_x_mean={str(p): v / mean for p, v in pct.items()}, max_x_mean=mx / mean, seam_ratio=seam / max(neigh, 1e-12),
             roll=ROLL, mirror=MIRROR, sat=SAT, asset=None if NO_ASSET else os.path.abspath(OUT), when=time.strftime('%Y-%m-%d %H:%M:%S'),
             white_raw=WHITE, white_exr=(WHITE * gain if WHITE is not None else None), knee_w=[KNEE_W, KNEE_MAX_W] if WHITE is not None else None,
             display_mult=DISPLAY_MULT, preview_gain=PGAIN,
             sign_mask=(os.path.abspath(SIGN_MASK) if sign is not None else None),
             sign_knee_w=([SIGN_KNEE_W, SIGN_KNEE_MAX_W] if sign is not None else None),
             sign_peak_w=(sign_peak / WHITE if sign is not None else None),
             score_city=(m1_city * gain * 1024 if sign is not None else None), hold_city=HOLD_CITY)
with open(os.path.join(PREVIEW_DIR, f'{TAG}_stats.json'), 'w') as f:
    json.dump(stats, f, indent=1)
log('done')
