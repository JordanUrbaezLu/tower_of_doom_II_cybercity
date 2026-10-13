"""companion_maps/compose.py - author the companion texture maps that no readable source holds (W2A, 2026-10-05).

WHY (tmp/design_review/findings.md, user 2026-10-04: "the ai companions dont look correct at all. Raps looks lazy and
talon isnt even the talon shape or image"): in the world the Civil Protector wore a 4x4 flat blue swatch on 41% of its
body, and the Talon / Cerberus sampled 35 per-part maps that were never found, so their hulls rendered flat. A full
search (2026-10-05: the T7 Assets V2.7/V2.8 archives, the private and the shared tools roots, Hellbound, TOD1, ACC)
found NONE of those originals. This tool authors each one from the best REAL evidence there is, every recipe below
recorded and reproducible:

  1. Battle-damaged twins. The pack ships the "_dead_" normal maps of the very same UV layouts: the live detail plus
     ONE shared crumple tile. The tile is MEASURED (attack drone: body_dead_n - the clean body normal it ships;
     AMWS: the per-pixel median of four armored parts' dead maps) and subtracted - the panel lines, rings and rivets
     are the original artists' (Talon wing set, Cerberus hull / turret / tread covers / launcher / armored swingarm).
  2. Occlusion and reveal masks are fitted, not guessed: a least-squares model trained on the one part that ships
     BOTH real maps and clean geometry (the attack drone body: its _o and its reveal mask _m against a Cycles bake
     and the clean normal) is applied to the bakes of every other part (bake.py: same UVs, same reach).
  3. Parts with no evidence at all (minigun, turret grenade pod, the Protector's upper shell / arm / chassis) get a
     Cycles Bevel normal of the real low-poly surface, plus - where the part has a real colour map - the panel
     relief that map carries (upper_c, arm_c), at the strength of the Protector's own real normal maps.
  4. The Civil Protector's GOLD finish is the donor's own gold material (black 40% albedo, gold specular tint,
     gloss up to 17) with its real gloss / spec / normal / occlusion maps where the pack has them (leg, limbs, foot)
     and authored ones where it does not; gloss and spec carry the real wear of the steel finish's own maps.
  5. Reveal (wear) masks take their wear from a REAL clean gloss map of the same layout where the pack has one (five
     Cerberus armour parts: scratches, chipped edges, dust exactly where the original artists painted them), else a
     soft multi-scale grain - never fine speckle (review: salt-and-pepper marble that shimmers once mipped).
  6. The R.A.P.S.'s rust-spots decal shell (17% of the model, dropped until now) gets its missing colour map from the
     real T7 rust grunge decal's spots (raps()).

RUN  python tools/companion_maps/compose.py            -> art/companion_maps/authored/<original image name>.png
     python tools/companion_maps/compose.py --check    -> regenerate in memory, byte-compare every authored PNG,
                                                          and prove the wiring: the partner GDT points at each one and
                                                          the installed copy is the same pixels (exit 1 on any drift)
     [--out DIR] [--bakes DIR] [--gdt FILE] [--images DIR] [--manifest FILE]  (a scratch overlay / stage tree)
Inputs: bake.py's PNGs (art/companion_maps/bakes/), the installer's T7 pack cache (tmp/partner_assets/, re-extracted
from ~/Downloads/T7 Assets V2.8.rar on demand) and stock maps under C:/BO3Tools/TOD2Cybercity/model_export (READ ONLY).
Deterministic: fixed seeds, no clocks; the same inputs give the same bytes.
"""
from pathlib import Path
import argparse, hashlib, json, os, sys, zlib, io
# the OpenBLAS kernel the maps were authored with (2026-10-13): numpy's per-CPU kernel moves the last bits of
# the fits; build_map.ps1 / run_build_gates.py pin the same, this covers a hand-run --check too
os.environ.setdefault('OPENBLAS_CORETYPE', 'Haswell')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '24')
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, median_filter, zoom, sobel

ROOT = Path(__file__).resolve().parents[2]
PRIV = Path('C:/BO3Tools/TOD2Cybercity')
STOCK = PRIV / 'model_export' / 'black_ops_3'
PACKS = [ROOT / 'tmp/partner_assets/T7 Assets V2.8', Path.home() / 'Downloads/_t7stage/T7 Assets V2.8']

ap = argparse.ArgumentParser()
ap.add_argument('--check', action='store_true')
ap.add_argument('--out', type=Path, default=ROOT / 'art/companion_maps/authored')
ap.add_argument('--bakes', type=Path, default=ROOT / 'art/companion_maps/bakes')
ap.add_argument('--gdt', type=Path, default=ROOT / 'source_data/tod_partners.gdt')
ap.add_argument('--images', type=Path, default=ROOT / 'model_export/tod_partner/_images')
ap.add_argument('--manifest', type=Path, default=ROOT / 'model_export/tod_partner/manifest.json')
ap.add_argument('--only', default='')
ap.add_argument('--preview', type=Path, default=None, help='also write a contact sheet of every output here')
A = ap.parse_args()

# ------------------------------------------------------------------------------------------------ sources
_INDEX = None
USED = {}          # source name -> sha256 (recorded in _authored.json)


def index():
    global _INDEX
    if _INDEX is None:
        _INDEX = {}
        for base in PACKS:
            me = base / 'model_export'
            if me.exists():
                for p in sorted(me.rglob('*.png')):
                    _INDEX.setdefault(p.stem, p)
        for p in sorted(STOCK.glob('*/_images/*')):
            if p.suffix.lower() in ('.tif', '.tiff', '.png'):
                _INDEX.setdefault(p.stem, p)
    return _INDEX


def source(name):
    p = index().get(name)
    if p is None:
        sys.path.insert(0, str(ROOT / 'tools' / 'partner'))
        import partner_materials as pm          # the installer's own 7-Zip extraction (read-only on the archive)
        pm.extract([name + '.png'])
        global _INDEX
        _INDEX = None
        p = index().get(name)
    if p is None:
        raise SystemExit('compose: source map not found anywhere readable: ' + name)
    if name not in USED:
        USED[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return p


def _load(p, size=None, mode='RGB'):
    im = Image.open(p)
    im.load()
    im = im.convert(mode)
    if size and im.size != size:
        im = im.resize(size, Image.LANCZOS)
    return np.asarray(im, np.float32) / 255.0


def rgb(name, size=None):
    return _load(source(name), size, 'RGB')


def lum(name, size=None):
    a = rgb(name, size)
    return a @ np.array([0.299, 0.587, 0.114], np.float32)


def normal_xy(name, size=None):
    """A T7 normal map's X/Y in [-1,1] (T7 convention: green = +rows / DirectX)."""
    return rgb(name, size)[..., :2] * 2.0 - 1.0


def bake(model, group, kind, size=None):
    p = A.bakes / ('%s_%s_%s.png' % (model, group, kind))
    if not p.exists():
        raise SystemExit('compose: missing bake %s - run tools/companion_maps/bake.py' % p)
    key = 'bake:' + p.name
    if key not in USED:
        USED[key] = hashlib.sha256(p.read_bytes()).hexdigest()
    a = _load(p, size, 'RGB')
    if kind == 'bevel':
        xy = a[..., :2] * 2 - 1
        xy[..., 1] *= -1.0          # Blender bakes +V up; the T7 maps store green the other way (measured: r < 0)
        return xy
    return a[..., 0]


# ------------------------------------------------------------------------------------------------ helpers
def seed(name):
    return zlib.crc32(name.encode()) & 0x7fffffff


def noise(shape, name, sigma, octaves=4):
    """Tileable fractal noise, mean 0 std 1, deterministic per output name."""
    rs = np.random.RandomState(seed(name))
    acc = np.zeros(shape, np.float64)
    amp = 1.0
    for o in range(octaves):
        acc += amp * gaussian_filter(rs.standard_normal(shape), sigma / (2 ** o), mode='wrap')
        amp *= 0.5
    acc -= acc.mean()
    return (acc / (acc.std() + 1e-9)).astype(np.float32)


def renorm(xy):
    xy = np.clip(xy, -0.98, 0.98)
    z = np.sqrt(np.clip(1.0 - xy[..., 0] ** 2 - xy[..., 1] ** 2, 0.02, 1.0))
    v = np.dstack([xy, z])
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def normal_png(xy):
    return renorm(xy) * 0.5 + 0.5


def fit_k(dead, dmg):
    k = float((dead * dmg).sum() / (dmg * dmg).sum())
    return min(1.15, max(0.85, k))


def height(xy, scale=1.0):
    """Frankot-Chellappa integration of a T7 normal map (green = +rows) into a relative height field."""
    n = renorm(xy)
    p = -n[..., 0] / n[..., 2]          # dh/dcol
    q = -n[..., 1] / n[..., 2]          # dh/drow
    h, w = p.shape
    wx = np.fft.fftfreq(w) * 2 * np.pi
    wy = np.fft.fftfreq(h) * 2 * np.pi
    WX, WY = np.meshgrid(wx, wy)
    d = WX ** 2 + WY ** 2
    d[0, 0] = 1.0
    H = (-1j * WX * np.fft.fft2(p) - 1j * WY * np.fft.fft2(q)) / d
    H[0, 0] = 0
    return np.real(np.fft.ifft2(H)).astype(np.float32) * scale


def cavity(xy, sigma):
    h = height(xy)
    c = h - gaussian_filter(h, sigma, mode='wrap')
    return c / (np.abs(c).mean() * 4 + 1e-6)


def features(ao, xy):
    """The per-pixel description both regressions use: occlusion bake, normal-derived cavity and edge."""
    edge = 1.0 - renorm(xy)[..., 2]
    cav = cavity(xy, 6.0)
    return np.stack([np.ones_like(ao), ao, ao * ao, np.minimum(cav, 0), np.maximum(cav, 0), edge,
                     gaussian_filter(edge, 2.0, mode='wrap')], -1)


def bevel_hp(xy, sigma=5.0):
    """Keep only a bevel bake's narrow edge rounding: Cycles' Bevel ignores the file's custom normals, so on a
    smoothed shell the raw bake also carries broad tilts (the custom-vs-smooth difference) that must not ship."""
    hp = xy - gaussian_filter(xy, (sigma, sigma, 0), mode='wrap')
    mag = np.sqrt((hp ** 2).sum(-1, keepdims=True))
    return hp * np.minimum(1.0, 0.45 / np.maximum(mag, 1e-6))


def detail_from_colour(l, target_rms):
    """Panel relief a colour map carries (bright edge wear and lit lips = raised), as T7 normal X/Y, scaled so the
    UNFILTERED relief would have target_rms (the real Protector normals' high-frequency rms).
    Edge-preserving: a median pass flattens the paint grime inside each panel and a soft threshold drops the weakest
    slopes, so a panel reads as a flat plate between crisp seams (the style of the real limbs_n / leg_n). Review of the
    first pass: on the mirror-polished gold the raw relief's grime read as hammered foil across the chest. The scale is
    taken BEFORE the clean-up, so removing the grime never boosts what is left (rust-patch edges into blobs)."""
    h = gaussian_filter(l, 1.0, mode='wrap') - gaussian_filter(l, 10.0, mode='wrap')
    h = h / (h.std() + 1e-6)
    raw = np.dstack([-sobel(h, axis=1, mode='wrap'), -sobel(h, axis=0, mode='wrap')]) / 8.0
    scale = target_rms / max(hf_rms(raw), 1e-6)
    h = median_filter(h, size=5, mode='wrap')
    gx = sobel(h, axis=1, mode='wrap') / 8.0
    gy = sobel(h, axis=0, mode='wrap') / 8.0
    mag = np.hypot(gx, gy)
    t = float(np.quantile(mag, 0.70))
    keep = np.clip((mag - t) / max(t, 1e-6), 0.0, 1.0)
    return np.dstack([-gx * keep, -gy * keep]) * scale


def hf_rms(xy):
    hp = xy - gaussian_filter(xy, (6, 6, 0), mode='wrap')
    return float(np.sqrt((hp ** 2).mean()))


# ------------------------------------------------------------------------------------------------ the measured models
class Models:
    """Everything fitted from REAL pairs, once per run (deterministic least squares)."""

    def __init__(self):
        self.info = {}
        # damage layers ---------------------------------------------------------------------------------------
        self.d_attack = (normal_xy('i_veh_t7_drone_attack_body_dead_n', (512, 512))
                         - normal_xy('i_veh_t7_drone_attack_body_litecolor_test_n', (512, 512)))
        four = ['armored_hull', 'armored_turret', 'armored_treadcovers', 'launcher']
        self.d_amws = np.median(np.stack([normal_xy('i_veh_t7_drone_amws_%s_dead_n' % p, (512, 512)) for p in four]), 0)
        # the armored swingarm's dead map carries the same crumple at twice the scale: find its offset (FFT peak)
        d = normal_xy('i_veh_t7_drone_amws_armored_swingarm_dead_n', (512, 512))
        t2 = zoom(self.d_amws, (2, 2, 1), order=1)
        pad = np.zeros_like(t2)
        pad[:512, :512] = d
        cc = sum(np.real(np.fft.ifft2(np.fft.fft2(t2[..., c]) * np.conj(np.fft.fft2(pad[..., c])))) for c in range(2))
        iy, ix = np.unravel_index(int(np.argmax(cc)), cc.shape)
        self.d_amws2 = np.roll(np.roll(t2, -iy, 0), -ix, 1)[:512, :512]
        self.info['armored_swingarm_crumple_offset_at_2x'] = [int(iy), int(ix)]
        # the attack drone body: real _o / reveal against its bake and clean normal ----------------------------
        n_body = normal_xy('i_veh_t7_drone_attack_body_litecolor_test_n', (512, 512))
        ao_body = bake('talon', 'body', 'ao', (512, 512))
        m_body = bake('talon', 'body', 'mask', (512, 512)) > 0.5
        o_real = lum('i_veh_t7_drone_attack_body_dead_o', (512, 512))
        r_real = lum('i_veh_t7_drone_attack_body_litecolor_test_m', (512, 512))
        F = features(ao_body, n_body)[m_body]
        self.w_o, *_ = np.linalg.lstsq(F, o_real[m_body], rcond=None)
        o_pred = np.clip(features(ao_body, n_body) @ self.w_o, 0, 1)
        # recorded at 10 decimals: the raw value moves in its 16th digit between CPUs (2026-10-13 migration;
        # only the %.2f "how" text reads it, so no pixel depends on the dropped digits)
        self.info['occlusion_fit_r'] = round(float(np.corrcoef(o_pred[m_body], o_real[m_body])[0, 1]), 10)
        # reveal: from the PREDICTED occlusion (what every other part will have) + the same geometry terms
        F2 = np.concatenate([features(o_pred, n_body), (o_pred ** 3)[..., None]], -1)[m_body]
        self.w_r, *_ = np.linalg.lstsq(F2, r_real[m_body], rcond=None)
        r_pred = np.clip(np.concatenate([features(o_pred, n_body), (o_pred ** 3)[..., None]], -1) @ self.w_r, 0, 1)
        res = (r_real - r_pred)[m_body]
        self.r_mottle = float(res.std())
        self.info['reveal_fit_r'] = round(float(np.corrcoef(r_pred[m_body], r_real[m_body])[0, 1]), 10)
        self.info['reveal_residual_std'] = self.r_mottle
        # real reveal contrast: the target histogram the authored masks are matched to (levels, not shape)
        self.r_quant = np.quantile(r_real[m_body], np.linspace(0, 1, 101))
        # Protector: the strength of its real normal relief (limbs_n / leg_n high-frequency rms)
        self.prot_hf = 0.5 * (hf_rms(normal_xy('i_c_t7_zom_zod_robot_limbs_n', (1024, 1024)))
                              + hf_rms(normal_xy('i_c_t7_zom_zod_robot_leg_n', (1024, 1024))))
        self.info['protector_normal_hf_rms'] = self.prot_hf
        self.info['w_occlusion'] = [float(x) for x in self.w_o]
        self.info['w_reveal'] = [float(x) for x in self.w_r]

    def occlusion(self, ao, xy):
        return np.clip(features(ao, xy) @ self.w_o, 0.0, 1.0)

    def reveal(self, o, xy, name, wear=None):
        """The fit (cavities, recesses, edges) plus the part's wear, then the real mask's levels by rank.
        wear: the REAL wear of this very layout where the pack has it (real_wear(): scratches, chips and dust from the
        part's own clean _g map, the original artists' placement). Without it, a soft multi-scale grain at 0.3 of the
        fit's residual: review rejected the first pass's 2.5 px speckle at 0.4 (salt-and-pepper marble on the hulls, and
        it shimmers once mipped), and full-strength broad noise read as camouflage blotches."""
        f = np.concatenate([features(o, xy), (o ** 3)[..., None]], -1)
        r = f @ self.w_r
        if wear is not None:
            r = r - self.r_mottle * WEAR_WEIGHT * wear
        else:
            sig = 5.0 * o.shape[0] / 512.0
            r = r + 0.3 * self.r_mottle * noise(o.shape, name, sig, 3)
        # histogram-match to the real mask's levels (the fit regresses toward the mean; the real mask is bimodal)
        ranks = np.argsort(np.argsort(r.ravel())).reshape(r.shape) / float(r.size - 1)
        return np.interp(ranks, np.linspace(0, 1, 101), self.r_quant).astype(np.float32)


# The real wear's weight against the fit, in units of the fit's residual. A/B rendered at 1.6 / 1.2 / 0.8: all three
# place the wear where the artists did; 0.8 keeps the most quiet paint between the scuffs (restrained edge / contact
# wear, the checklist's 'avoid evenly scratched panels'), so it ships.
WEAR_WEIGHT = 0.8


# ------------------------------------------------------------------------------------------------ recipes
SEM = {}            # output name -> (semantic, coreSemantic, compressionMethod)
OUT = {}            # output name -> float array (H, W[, 3]) in [0,1]
HOW = {}            # output name -> one line: what it was made from
NORMAL, OCC, REVEAL, GLOSS = ('normalMap', 'Normal', 'compressed'), ('occlusionMap', 'Linear1ch', 'compressed'), \
    ('revealMap', 'Linear1ch', 'compressed'), ('glossMap', 'Linear1ch', 'compressed')
DIFFUSE, SPEC = ('diffuseMap', 'sRGB3chAlpha', 'compressed high color'), ('specularMap', 'sRGB3ch', 'compressed')
# lit_advanced's specColorMap is a SCALAR mask (every stock lit_advanced material, 215 of 215); only the _fullspec
# techsets read a colour spec map. A wrong semantic is a linker usage mismatch = an EMPTY material (flat grey).
SPECMASK = ('specularMask', 'Linear1ch', 'compressed')


def emit(name, arr, sem, how):
    OUT[name] = np.clip(arr, 0.0, 1.0).astype(np.float32)
    SEM[name] = sem
    HOW[name] = how


def real_wear(name, size=(512, 512)):
    """The wear a REAL clean gloss map of the same layout carries, as one zero-mean field (std 1): bright thin
    features (scratches, chipped edges - bare metal reads glossy) and broad matte patches (dust, grime). Panel-scale
    shading is removed first so only the artists' wear is kept, never the part's lighting."""
    g = lum(name, size)
    hp = g - gaussian_filter(g, 6.0, mode='wrap')
    scratch = np.maximum(hp, 0) / (hp.std() + 1e-6)
    lo = gaussian_filter(g, 2.0, mode='wrap') - gaussian_filter(g, 24.0, mode='wrap')
    dust = np.maximum(-lo, 0) / (lo.std() + 1e-6)
    w = 0.6 * np.clip(scratch, 0, 4) + 0.4 * np.clip(dust, 0, 4)
    w = w - w.mean()
    return (w / (w.std() + 1e-6)).astype(np.float32)


def t7_part(M, model, group, stem, n_xy, how_n, reveal_names, wear_from=None):
    ao = bake(model, group, 'ao', (512, 512))
    o = M.occlusion(ao, n_xy)
    emit(stem + '_n', normal_png(n_xy), NORMAL, how_n)
    emit(stem + '_o', o, OCC, 'occlusion: the attack-drone fit (r=%.2f) on this part\'s Cycles bake + its normal'
         % M.info['occlusion_fit_r'])
    wear = real_wear(wear_from) if wear_from else None
    for r in reveal_names:
        emit(r, M.reveal(o, n_xy, r, wear), REVEAL, 'reveal: the attack-drone mask fit (r=%.2f) + %s, levels matched '
             'to the real mask' % (M.info['reveal_fit_r'], ('the real wear of ' + wear_from) if wear_from
                                   else 'soft multi-scale grain'))
    return o


def talon(M):
    d = normal_xy('i_veh_t7_drone_attack_wing_gun_dead_n', (512, 512))
    k = fit_k(d, M.d_attack)
    n = d - k * M.d_attack
    t7_part(M, 'talon', 'wing_gun', 'i_veh_t7_drone_attack_wing_gun', n,
            'normal: wing_gun_dead_n minus the measured attack-drone crumple (k=%.3f)' % k,
            ['i_veh_t7_drone_attack_wing_gun_tile_r'])


def cerberus(M):
    # These five parts ship a CLEAN gloss map of the very same layout in the pack (i_veh_t7_drone_amws_<part>_g, used by
    # no definition we clone): its scratches / chips / dust place the reveal's wear where the original artists put it.
    for p in ['armored_hull', 'armored_turret', 'armored_treadcovers', 'launcher']:
        d = normal_xy('i_veh_t7_drone_amws_%s_dead_n' % p, (512, 512))
        k = fit_k(d, M.d_amws)
        t7_part(M, 'cerberus', p, 'i_veh_t7_drone_amws_' + p, d - k * M.d_amws,
                'normal: %s_dead_n minus the measured AMWS crumple (k=%.3f)' % (p, k),
                ['i_veh_t7_drone_amws_%s_tile_r' % p], 'i_veh_t7_drone_amws_%s_g' % p)
    d = normal_xy('i_veh_t7_drone_amws_armored_swingarm_dead_n', (512, 512))
    t7_part(M, 'cerberus', 'armored_swingarm', 'i_veh_t7_drone_amws_armored_swingarm', d - M.d_amws2,
            'normal: armored_swingarm_dead_n minus the AMWS crumple at 2x scale (offset %s)'
            % M.info['armored_swingarm_crumple_offset_at_2x'], ['i_veh_t7_drone_amws_armored_swingarm_tile_r'],
            'i_veh_t7_drone_amws_armored_swingarm_g')
    # no source at all: the real surface's own bevel (rounded machined edges)
    for group, stem, rv in [('minigun', 'i_veh_t7_drone_amws_minigun', 'i_veh_t7_drone_amws_minigun_tile_r'),
                            ('turret_grenade', 'i_veh_t7_drone_amws_armored_turret_grenade',
                             'i_veh_t7_drone_amws_armored_turret_grenade_r')]:
        size = 512 if group == 'minigun' else 256
        n = bevel_hp(bake('cerberus', group, 'bevel', (size, size)))
        ao = bake('cerberus', group, 'ao', (size, size))
        o = M.occlusion(ao, n)
        emit(stem + '_n', normal_png(n), NORMAL, 'normal: Cycles Bevel of the real low-poly surface (no source exists)')
        if group == 'minigun':
            emit(stem + '_o', o, OCC, 'occlusion: the attack-drone fit on the Cycles bake + bevel normal')
        emit(rv, M.reveal(o, n, rv), REVEAL, 'reveal: the attack-drone mask fit + mottle, levels matched')
    # parts that DO ship a real normal and occlusion: only their reveal is authored, from those real maps
    for p, nn in [('swingarm', 'i_veh_t7_drone_amws_swingarm_n'), ('wheels', 'i_t7_drone_amws_wheels_n')]:
        o = lum('i_veh_t7_drone_amws_%s_o' % p, (512, 512))
        n = normal_xy(nn, (512, 512))
        r = 'i_veh_t7_drone_amws_%s_tile_r' % p
        emit(r, M.reveal(o, n, r), REVEAL, 'reveal: the attack-drone mask fit on the REAL %s_o + %s' % (p, nn))
    # the ammo belt's tiling gloss: worn steel links (scratched highs, grime lows), tileable
    g = 0.52 + 0.10 * noise((256, 256), 'belt_g', 10.0) + 0.06 * noise((256, 256), 'belt_g2', 1.5, 2)
    emit('i_veh_t7_drone_amws_minigun_tile_g', g, GLOSS, 'gloss: tileable worn-steel noise (no source exists)')
    # the light panel: the real dead set with its cracked-glass layer filtered out (cracks are 1-2 px lines)
    def declack(a, size=7):
        return median_filter(a, size=size, mode='wrap')
    n = normal_xy('i_veh_t7_drone_amws_base_emissive_dead_n', (256, 256))
    n = np.dstack([declack(n[..., 0]), declack(n[..., 1])])
    emit('i_veh_t7_drone_amws_base_emissive_n', normal_png(n), NORMAL,
         'normal: base_emissive_dead_n, cracked-glass lines median-filtered out (bezels kept)')
    emit('i_veh_t7_drone_amws_base_emissive_o', declack(lum('i_veh_t7_drone_amws_base_emissive_darkcolor_dead_o',
         (256, 256))), OCC, 'occlusion: base_emissive_darkcolor_dead_o, crack lines filtered out')
    g = declack(lum('i_veh_t7_drone_amws_base_emissive_darkcolor_dead_g', (256, 256)), 9)
    emit('i_veh_t7_drone_amws_base_emissive_g', 0.25 + 0.75 * g, GLOSS,
         'gloss: base_emissive_darkcolor_dead_g, crack glints filtered out, lifted (an intact lens)')
    e = rgb('i_veh_t7_drone_amws_base_emissive_dead_e', (256, 256))
    emit('i_veh_t7_drone_amws_base_emissive_e', e, DIFFUSE,
         'emissive: the stock AMWS light layout (base_emissive_dead_e) - strips, dots, chevrons')
    # the scrolling status strip: soft scan pulses along U (its UVs are a line at v=0; the material scrolls them)
    u = np.linspace(0, 1, 128, endpoint=False)
    band = 0.15 + 0.85 * np.clip(np.cos((u * 3 % 1 - 0.5) * np.pi) ** 6, 0, 1)
    emit('i_veh_t7_drone_amws_base_emissive_scroll_e', np.repeat(np.tile(band, (32, 1))[..., None], 3, -1),
         DIFFUSE, 'emissive: three soft scan pulses for the scrolling status strip (no source exists)')
    for s in ('sensor01', 'sensor02'):
        name = 'i_veh_t7_drone_amws_%s_lens_g' % s
        emit(name, 0.88 + 0.05 * noise((128, 128), name, 12.0) - 0.04 * np.abs(noise((128, 128), name + 'b', 3.0)),
             GLOSS, 'gloss: polished lens with faint smudges (no source exists)')


def raps(M):
    """The Gorod Krovi R.A.P.S. has every per-model map in the pack. Its one gap is the colour map of its rust-spots
    decal shell (mtl_t7_veh_dlc_decal_rust_spots_01, 2110 triangles - 17% of the model - dropped until W2A): the pack
    defines the decal (rust tint 0.60 0.36 0.28 at 58%, its reveal mask mixmap_06_r, normal, gloss) but no source holds
    i_t7_decal_grunge_splatter_c. The tint carries the colour, so the map is a light grey splatter mask: the REAL T7
    rust grunge decal's own spots (i_t7_cru_decal_grunge_rust_01_c alpha, its luminance as the grey variation),
    made to wrap (the shell's UVs tile -1.5..2.2) by a half-offset cross-fade at the one seam that does not."""
    src = np.asarray(Image.open(source('i_t7_cru_decal_grunge_rust_01_c')).convert('RGBA')
                     .resize((512, 512), Image.LANCZOS), np.float32) / 255.0
    h = src.shape[0]
    band = 32
    y = np.arange(h, dtype=np.float32)
    edge = np.minimum(y, h - 1 - y)
    m = (0.5 + 0.5 * np.cos(np.clip(edge / band, 0, 1) * np.pi))[:, None, None]
    a = src * (1 - m) + np.roll(src, h // 2, 0) * m
    l = a[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32)
    grey = 0.70 + 0.30 * (l - l.min()) / max(float(np.ptp(l)), 1e-6)
    emit('i_t7_decal_grunge_splatter_c', np.dstack([grey, grey, grey, a[..., 3]]), DIFFUSE,
         'decal colour: the real T7 rust grunge (cru_decal_grunge_rust_01_c) spots as alpha over a light grey (the '
         'definition\'s own rust tint colours it), wrapped vertically by a half-offset cross-fade')


GOLD_GLOSS_FLOOR = 0.55     # the SoE gold reads polished: worn / dirty areas only take it down to here


def protector(M):
    S = 1024
    # ---- the upper shell (helmet + chest): no normal / gloss / spec anywhere; its real colour map carries the panels
    l = lum('i_c_t7_zom_zod_robot_upper_c', (S, S))
    n = detail_from_colour(l, M.prot_hf)
    emit('i_c_t7_zom_zod_robot_upper_n', normal_png(n), NORMAL,
         'normal: the panel relief of the real upper_c (its islands overlap 5x: no geometry bake), at the rms of '
         'the real limbs / leg _n')
    # No occlusion map: the donor's gold shell samples $occlusion, as do its leg / limbs; the grime lives in gloss/spec.
    wear = gaussian_filter(l, 0.8, mode='wrap') - gaussian_filter(l, 6.0, mode='wrap')
    wear = wear / (wear.std() + 1e-6)
    dark = gaussian_filter(l, 20.0, mode='wrap') - gaussian_filter(l, 2.0, mode='wrap')
    grime = np.clip(dark / (dark.std() + 1e-6) * 0.35, 0, 1)
    g = 0.86 + 0.05 * np.clip(wear, -2, 2) - 0.30 * grime + 0.03 * noise((S, S), 'upper_g', 6.0)
    emit('i_c_t7_zom_zod_robot_upper_gold_g', np.clip(g, GOLD_GLOSS_FLOOR, 1.0), GLOSS,
         'gloss: polished gold, lowered where the real upper_c is grimy (darker than around), lifted on its worn edges')
    s = np.clip(0.88 + 0.06 * np.clip(wear, -2, 2) - 0.25 * grime, 0.6, 1.0)
    emit('i_c_t7_zom_zod_robot_upper_gold_s', s, SPECMASK,
         'spec: the gold tint\'s strength - full on clean plate, dimmed in grime, brighter on worn edges')
    # the eye / chest lights: the upper_c orbs themselves (saturated, bright), as the lit_emissive colour map
    c = rgb('i_c_t7_zom_zod_robot_upper_c', (S, S))
    mx, mn = c.max(-1), c.min(-1)
    lit = np.clip((mx - 0.18) * 3.0, 0, 1) * np.clip((mx - mn) * 3.0, 0, 1)
    lit = gaussian_filter(lit, 1.0, mode='wrap')
    emit('i_c_t7_zom_zod_robot_upper_m', c * lit[..., None] * 2.2, DIFFUSE,
         'emissive: the real upper_c status orbs (blue / red), isolated by brightness + saturation')
    # ---- leg / limbs / foot: the REAL steel-finish gloss and spec carry the wear; the gold tint stays the donor's
    for part, size in [('leg', (S, S)), ('limbs', (S, S)), ('foot', (S, S // 2))]:
        greal = lum('i_c_t7_zom_zod_robot_%s_g' % part, size)
        sreal = lum('i_c_t7_zom_zod_robot_%s_s' % part, size)
        emit('i_c_t7_zom_zod_robot_%s_gold_g' % part, GOLD_GLOSS_FLOOR + (1 - GOLD_GLOSS_FLOOR) * greal, GLOSS,
             'gloss: the real %s_g remapped to polished gold (floor %.2f)' % (part, GOLD_GLOSS_FLOOR))
        s = sreal / max(float(np.quantile(sreal, 0.9)), 1e-3)
        emit('i_c_t7_zom_zod_robot_%s_gold_s' % part, np.clip(0.62 + 0.38 * s, 0.62, 1.0), SPECMASK, 'spec: the real %s_s brightness as the gold tint\'s strength (painted / dirty parts dimmer)' % part)
    # ---- the silver arm (the gold donor's own skin maps arm_gold -> arm2): real colour, authored n / g / s
    l = lum('i_c_t7_zmb_zod_robot_arm_c', (S, S))
    c = rgb('i_c_t7_zmb_zod_robot_arm_c', (S, S))
    n = bevel_hp(bake('protector', 'arm', 'bevel', (S, S)))
    n = n + detail_from_colour(l, M.prot_hf)
    emit('i_c_t7_nrc_robot_grunt_chassis_arm_n', normal_png(n), NORMAL,
         'normal: Cycles Bevel of the arm + the relief of the real arm_c, at the real Protector normal rms')
    ao = bake('protector', 'arm', 'ao', (S, S))
    o = M.occlusion(ao, n)
    red = np.clip((c[..., 0] - np.maximum(c[..., 1], c[..., 2]) - 0.08) * 6, 0, 1)
    rust = np.clip((c[..., 0] - c[..., 2] - 0.025) * 12, 0, 1) * (1 - red)
    plate = np.clip((l - 0.12) * 5, 0, 1) * (1 - red) * (1 - rust)
    g = 0.42 + 0.22 * plate - 0.20 * rust - 0.10 * red - 0.25 * np.clip(0.8 - o, 0, 1) + 0.03 * noise((S, S), 'arm_g', 5)
    emit('i_c_t7_nrc_robot_grunt_chassis_arm_g', np.clip(g, 0.08, 0.9), GLOSS,
         'gloss: from the real arm_c - bare plates glossier, rust / dust / red paint duller, cavities dull')
    steel = np.array([0.46, 0.49, 0.53], np.float32)
    s = steel * (0.75 + 0.25 * plate)[..., None] * np.clip(o, 0.5, 1)[..., None]
    s = s * (1 - red - rust)[..., None] + np.array([0.06, 0.06, 0.06]) * red[..., None] \
        + np.array([0.10, 0.08, 0.06]) * rust[..., None]
    emit('i_c_t7_nrc_robot_grunt_chassis_arm_s', s, SPEC,
         'spec: blue-steel (the real leg_s steel), dielectric on the red paint and rust of the real arm_c')
    # ---- the grunt chassis pelvis / torso (no map at all): dark gunmetal, grime in recesses, worn edges
    for part, sz in [('pelvis', 512), ('torso', 256)]:
        n = bevel_hp(bake('protector', part, 'bevel', (sz, sz)))
        n = n + 0.05 * np.dstack([noise((sz, sz), part + 'nx', 1.2, 2), noise((sz, sz), part + 'ny', 1.2, 2)])
        ao = bake('protector', part, 'ao', (sz, sz))
        o = M.occlusion(ao, n)
        edge = np.clip((1 - renorm(n)[..., 2]) * 6, 0, 1) * np.clip(o * 1.4 - 0.4, 0, 1)
        grime = np.clip((0.8 - o) * 2.5, 0, 1)
        mott = noise((sz, sz), part + 'c', sz / 20.0)
        base = np.array([0.105, 0.11, 0.12], np.float32)          # sRGB ~ (27, 28, 31): dark gunmetal paint
        col = base * (1 + 0.10 * mott)[..., None] * (1 - 0.45 * grime)[..., None] \
            + np.array([0.20, 0.20, 0.21]) * (0.35 * edge)[..., None]
        stem = 'i_c_t7_nrc_robot_grunt_chassis_' + part
        emit(stem + '_c', col, DIFFUSE, 'colour: dark gunmetal paint, grime in recesses (bake), edge wear (bevel)')
        emit(stem + '_n', normal_png(n), NORMAL, 'normal: Cycles Bevel of the chassis + fine casting grain')
        emit(stem + '_g', np.clip(0.40 + 0.25 * edge - 0.22 * grime + 0.04 * mott, 0.1, 0.85), GLOSS,
             'gloss: satin paint, polished on worn edges, dull in grime')
        s = np.array([0.30, 0.31, 0.33]) * (1 - 0.5 * grime)[..., None] + np.array([0.25, 0.26, 0.28]) * edge[..., None]
        if part == 'pelvis':    # pelvis2 is lit_advanced: a scalar spec mask; torso2 is lit_advanced_fullspec: colour
            emit(stem + '_s', s.mean(-1), SPECMASK, 'spec: painted metal, bare steel showing on worn edges (mask)')
        else:
            emit(stem + '_s', s, SPEC, 'spec: painted metal, bare steel showing on worn edges')


# ------------------------------------------------------------------------------------------------ output
def pil_mode(arr):
    return 'L' if arr.ndim == 2 else ('RGBA' if arr.shape[2] == 4 else 'RGB')


def png_bytes(name, arr):
    a = np.round(np.clip(arr, 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray(a, pil_mode(a))
    bio = io.BytesIO()
    im.save(bio, format='PNG', compress_level=9)
    return bio.getvalue()


def main():
    M = Models()
    only = set(x for x in A.only.split(',') if x)
    for fn in (talon, cerberus, protector, raps):
        if not only or fn.__name__ in only:
            fn(M)
    for name, arr in OUT.items():
        h, w = arr.shape[:2]
        assert h % 4 == 0 and w % 4 == 0 and max(h, w) <= 1024, (name, arr.shape)
        assert len('i_tod_ptn_' + name[2:]) < 64, name
    record = {'tool': 'tools/companion_maps/compose.py', 'models': M.info,
              'sources_sha256': dict(sorted(USED.items())),
              'images': {n: {'semantic': SEM[n][0], 'coreSemantic': SEM[n][1], 'compressionMethod': SEM[n][2],
                             'size': list(OUT[n].shape[1::-1]), 'how': HOW[n],
                             'sha256': hashlib.sha256(png_bytes(n, OUT[n])).hexdigest()} for n in sorted(OUT)}}
    rec_bytes = (json.dumps(record, indent=1, sort_keys=True) + '\n').encode()
    bad = []
    if A.check:
        for n in sorted(OUT):
            p = A.out / (n + '.png')
            if not p.exists() or p.read_bytes() != png_bytes(n, OUT[n]):
                bad.append('authored map differs from its recipe: ' + str(p))
        if (A.out / '_authored.json').read_bytes() != rec_bytes:
            bad.append('art/companion_maps/authored/_authored.json is stale')
        bad += wiring()
        for b in bad:
            print('COMPANION_MAPS_FAIL:', b)
        if bad:
            sys.exit(1)
        print('COMPANION_MAPS_PASS: %d authored maps match their recipes and are wired (GDT block + installed pixels)'
              % len(OUT))
        return
    A.out.mkdir(parents=True, exist_ok=True)
    for n in sorted(OUT):
        (A.out / (n + '.png')).write_bytes(png_bytes(n, OUT[n]))
    (A.out / '_authored.json').write_bytes(rec_bytes)
    print('compose: wrote %d authored maps to %s' % (len(OUT), A.out))
    print(json.dumps(M.info, indent=1))
    if A.preview:
        sheet(A.preview)


def wiring():
    """Every authored map reaches the game: the installer copied it (same pixels) and the GDT declares it."""
    bad = []
    gdt = A.gdt.read_text(encoding='utf-8') if A.gdt.exists() else ''
    man = json.loads(A.manifest.read_text()) if A.manifest.exists() else {}
    srcs = man.get('images', {})
    for n in sorted(OUT):
        ours = 'i_tod_ptn_' + n[2:]
        if '"%s" ( "image.gdf" )' % ours not in gdt:
            bad.append('no GDT image block for %s (run tools/partner/install_assets.py)' % ours)
            continue
        if not srcs.get(ours, {}).get('from', '').endswith('companion_maps/authored/%s.png' % n):
            bad.append('manifest does not record %s as authored from %s.png' % (ours, n))
        p = A.images / (ours + '.png')
        if not p.exists():
            bad.append('installed image missing: ' + str(p))
            continue
        got = np.asarray(Image.open(p).convert(pil_mode(OUT[n])))
        want = np.round(np.clip(OUT[n], 0, 1) * 255).astype(np.uint8)
        if got.shape != want.shape or not np.array_equal(got, want):
            bad.append('installed %s is not the authored pixels' % p.name)
        sem = SEM[n][0]
        blk = gdt.split('"%s" ( "image.gdf" )' % ours, 1)[1].split('\t}', 1)[0]
        if '"semantic" "%s"' % sem not in blk:
            bad.append('%s is not declared %s' % (ours, sem))
    return bad


def sheet(path):
    from PIL import ImageDraw
    names = sorted(OUT)
    S, cols = 192, 8
    rows = (len(names) + cols - 1) // cols
    im = Image.new('RGB', (cols * S, rows * (S + 14)), (24, 24, 28))
    d = ImageDraw.Draw(im)
    for i, n in enumerate(names):
        a = np.round(np.clip(OUT[n], 0, 1) * 255).astype(np.uint8)
        t = Image.fromarray(a).convert('RGB').resize((S, S))
        x, y = (i % cols) * S, (i // cols) * (S + 14)
        im.paste(t, (x, y + 14))
        d.text((x + 2, y + 1), n.replace('i_veh_t7_drone_', '').replace('i_c_t7_', '')[-30:], fill=(255, 230, 120))
    im.save(path)


if __name__ == '__main__':
    main()
