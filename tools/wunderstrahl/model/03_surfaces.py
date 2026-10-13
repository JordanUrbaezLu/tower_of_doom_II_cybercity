"""MCP step 03: author the Wunderstrahl surfaces ON THE DG-2'S OWN UV LAYOUTS (art pass, deterministic).

Material first, damage second (CLAUDE.md model-surface rules). Every texel of the four hard-surface atlases is
classified from the DG-2's own maps (specular chroma = brass / copper / steel, dielectric colour = black paint /
red paint / grey cable / pink-white label / ivory insulator) and from the 3D part it belongs to (rasterised UV
triangles give each texel its part, its gun-space position and its normal). Each class becomes a Wunderstrahl role:

  receiver + frame  dark gunmetal (satin, broad mottling); former large brass parts keep brass only where the
                    plating has worn through on raised edges; small fittings (screws, nuts, ferrules) stay brass
  coils + claws     aged copper (uneven tarnish, brown-black oxide in recesses - no green/blue patina)
  radiator fins     gunmetal with straw-to-bronze heat tint toward the hot top/front, soot in the fin roots
  battery box       black enamel, chipped to steel on edges, dust in recesses
  stock             dark lacquered composite (deep charcoal-brown, faint fibre), worn to a warm under-layer where
                    hands and edges rub (Treyarch's own wear placement drives it), rubber butt pad
  switch cover      signal-yellow enamel; the red-and-white braided cables become charcoal braid with a mustard
                    tracer; the grey cable charcoal rubber; insulators glazed ivory ceramic
  (a 'hazard' role exists for a pink-and-white decal part; the DG-2 has none - its striped texels are the braid)
Treyarch's normal maps are kept byte-for-byte (copied under our names); their curvature and the DG-2 occlusion
maps place edge wear and recess dirt. Emission lives only in the glow parts (core, bulbs, rear lamp).
Review pass 2 (2026-10-06): the DG-2's two brass coil springs (the bellows ahead of the receiver, the coil over its
top) are the brief's coils - aged copper now, not gunmetal; the stock is a deeper charcoal-brown, ~15% less glossy,
with the wood grain cut back; the laser filament brightens toward the muzzle with soft energy knots along it.
Send ONLY=body,frame (etc.; default all four atlases) to stay inside the 180 s MCP answer window; the small glow
maps (core, lamps, glass) are rewritten on every call (deterministic, ~1 s).
Outputs: model_export/tod_wunderstrahl/_images/i_tod2_ws_*.png + art/wunderstrahl/surfaces.json.
"""
import importlib, json, shutil, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, texgen, pngio
for m in (common, texgen, pngio):
    importlib.reload(m)
T = texgen
t0 = time.time()
ONLY = globals().get('ONLY', 'body,frame,coil,stock').split(',')
common.IMG.mkdir(parents=True, exist_ok=True); common.SCRATCH.mkdir(parents=True, exist_ok=True)
view = common.load_model(common.SRC_VIEW)
SRC = common.SRC_IMG


def src(name):
    return pngio.read_png(SRC / ('i_wpn_t7_zmb_dg2_%s.png' % name))


C3 = lambda *v: T.rgb(*v)
ROLES = {   # sRGB diffuse / sRGB specular F0 / gloss (0..1 over glossRange 0..12); worn edge; recess dirt
    'gunmetal': dict(d=C3(22, 22, 24), s=C3(130, 130, 134), g=.60, ed=C3(26, 26, 28), es=C3(190, 189, 192), eg=.78,
                     dd=C3(14, 13, 12), ds=.55, dg=.28),
    'brassedge': dict(d=C3(22, 22, 24), s=C3(130, 130, 134), g=.60, ed=C3(30, 24, 12), es=C3(232, 198, 124), eg=.80,
                      dd=C3(14, 13, 12), ds=.55, dg=.28),
    'brass': dict(d=C3(26, 20, 10), s=C3(198, 158, 84), g=.62, ed=C3(30, 24, 12), es=C3(238, 206, 134), eg=.82,
                  dd=C3(20, 17, 10), ds=.45, dg=.30),
    'copper': dict(d=C3(24, 15, 11), s=C3(178, 108, 78), g=.52, ed=C3(28, 18, 13), es=C3(226, 152, 114), eg=.72,
                   dd=C3(40, 23, 16), ds=.32, dg=.26),
    # the coil springs: copper aged harder - brown-black tarnish down in the folds, crests rubbed back to bright metal
    'copper_aged': dict(d=C3(22, 14, 10), s=C3(164, 96, 68), g=.46, ed=C3(30, 19, 14), es=C3(240, 172, 130), eg=.80,
                        dd=C3(30, 18, 13), ds=.22, dg=.20),
    'enamel': dict(d=C3(17, 17, 18), s=C3(56, 56, 56), g=.55, ed=C3(26, 26, 28), es=C3(160, 160, 164), eg=.68,
                   dd=C3(36, 33, 29), ds=.85, dg=.22),
    'heatsink': dict(d=C3(20, 18, 16), s=C3(110, 110, 114), g=.50, ed=C3(24, 22, 20), es=C3(170, 168, 168), eg=.66,
                     dd=C3(11, 10, 9), ds=.45, dg=.22),
    'composite': dict(d=C3(30, 26, 23), s=C3(58, 58, 58), g=.61, ed=C3(66, 56, 47), es=C3(54, 54, 54), eg=.36,
                      dd=C3(18, 15, 13), ds=.90, dg=.42),
    'composite_dark': dict(d=C3(24, 20, 18), s=C3(56, 56, 56), g=.55, ed=C3(58, 48, 40), es=C3(54, 54, 54), eg=.38,
                           dd=C3(16, 13, 11), ds=.90, dg=.38),
    'rubber': dict(d=C3(30, 29, 28), s=C3(48, 48, 48), g=.30, ed=C3(42, 40, 38), es=C3(50, 50, 50), eg=.40,
                   dd=C3(22, 21, 20), ds=.90, dg=.22),
    'braid': dict(d=C3(36, 33, 30), s=C3(52, 52, 52), g=.32, ed=C3(54, 50, 45), es=C3(54, 54, 54), eg=.38,
                  dd=C3(24, 22, 20), ds=.90, dg=.24),
    'yellow_enamel': dict(d=C3(212, 158, 26), s=C3(58, 58, 58), g=.60, ed=C3(26, 26, 28), es=C3(168, 168, 170), eg=.70,
                          dd=C3(96, 70, 22), ds=.85, dg=.30),
    'ceramic': dict(d=C3(178, 166, 144), s=C3(62, 62, 62), g=.80, ed=C3(196, 186, 166), es=C3(64, 64, 64), eg=.84,
                    dd=C3(92, 82, 66), ds=.90, dg=.50),
    'hazard': dict(d=C3(222, 170, 36), s=C3(58, 58, 58), g=.50, ed=C3(26, 26, 28), es=C3(168, 168, 170), eg=.68,
                   dd=C3(80, 64, 30), ds=.85, dg=.30),
}
def ramp(L, stops):
    """Piecewise-linear colour ramp. stops: [(position, sRGB array)] in increasing position."""
    L = np.clip(L, 0, 1)
    out = np.zeros(L.shape + (3,), np.float32) + stops[0][1]
    for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
        t = np.clip((L - p0) / max(p1 - p0, 1e-6), 0, 1)[..., None]
        out = np.where((L >= p0)[..., None], c0 + (c1 - c0) * t, out)
    return out


# Heat tint on steel, hottest first: straw -> bronze -> brown -> plain steel (never into the blue/violet temper band).
HEAT = [(0.0, C3(214, 176, 96)), (0.35, C3(178, 118, 66)), (0.65, C3(124, 90, 80)), (1.0, C3(110, 110, 114))]


def compose(role, wear, dirt, sdet, gdet, mottle, d_override=None, s_override=None):
    r = ROLES[role]
    d = T.lerp(r['d'] if d_override is None else d_override, r['ed'], wear)
    s = T.lerp(r['s'] if s_override is None else s_override, r['es'], wear)
    g = r['g'] + (r['eg'] - r['g']) * wear
    metalish = float(np.mean(r['s'])) > .3
    s = s * (1.0 + (0.9 if metalish else 0.25) * sdet)[..., None] * (1.0 + 0.10 * (mottle - 0.5))[..., None]
    g = g + 0.85 * gdet + 0.06 * (mottle - 0.5)
    d = T.lerp(d, r['dd'], dirt * 0.85)
    s = s * (1.0 - (1.0 - r['ds']) * dirt)[..., None]
    g = g + (r['dg'] - g) * dirt
    return np.clip(d, 0, 1), np.clip(s, 0, 1), np.clip(g, 0, 1)


def author(key, mesh_index, size, srckey, seed):
    w, h = size
    mesh = view.meshes[mesh_index]
    label, pos, nrm, info = T.rasterize([mesh], w, h)
    raw_cov = label >= 0
    label, (pos, nrm) = T.dilate(label, [pos, nrm], iters=10)
    cov = label >= 0
    diag = np.full(len(info) + 1, 99.0, np.float32)
    for p in info:
        diag[p['id']] = p['diag']
    diagmap = np.where(cov, diag[np.clip(label, 0, None)], 99.0)
    C = src(srckey + '_c')[..., :3]; S = src(srckey + '_s')[..., :3]; G = src(srckey + '_g')[..., 0]
    N = src(srckey + '_n')[..., :3]
    O = T.resize(src(srckey + '_o')[..., 0], h, w)
    # Island borders sample Treyarch's padding (a yellow fill in the specular maps, flat normals): classified as
    # they are, every seam grew a thin brass outline and a bright 'worn edge'. Read every source signal from the
    # island INTERIOR only: erode each island 2 texels, then refill its border (and the padding) from the interior.
    lab0 = np.where(raw_cov, label, -1)
    interior = raw_cov.copy()
    for d in (1, 2):
        for dy, dx in ((0, d), (0, -d), (d, 0), (-d, 0), (d, d), (-d, -d), (d, -d), (-d, d)):
            interior &= np.roll(lab0, (dy, dx), axis=(0, 1)) == lab0
    seed = np.where(interior, lab0, -1)
    _, (C, S, G, N) = T.dilate(seed, [C, S, G, N], iters=8)
    slum = T.luminance(S); clum = T.luminance(C)
    metal = T.smoothstep(.30, .46, slum)
    copper = metal * T.smoothstep(.045, .085, S[..., 0] - S[..., 1])
    brass = metal * (1 - copper) * T.smoothstep(.08, .20, (S[..., 0] + S[..., 1]) * .5 - S[..., 2])
    steel = np.clip(metal - copper - brass, 0, 1)
    diel = 1 - metal
    # The pink-and-white label is found first, PER PART: a part is the label when a real share of its texels are
    # bright pinkish paint (a grey cable's painted highlights never qualify); all its painted texels become stripes.
    lbl = np.clip(label, 0, None)
    pink = diel * T.smoothstep(.31, .38, clum) * T.smoothstep(.06, .12, C[..., 0] - C[..., 1])
    cnt = np.bincount(lbl[raw_cov], minlength=len(info) + 2)
    frac = np.bincount(lbl[raw_cov], weights=pink[raw_cov], minlength=len(info) + 2) / np.maximum(cnt, 1)
    label_part = (frac > .22)[lbl] & cov
    label_w = diel * label_part if key == 'body' else np.zeros_like(diel)
    red = diel * (1 - label_w) * T.smoothstep(.12, .24, C[..., 0] - np.maximum(C[..., 1], C[..., 2]))
    light = diel * (1 - red) * (1 - label_w) * T.smoothstep(.30, .42, clum)
    dark = np.clip(diel - red - light - label_w, 0, 1)
    small = T.smoothstep(2.2, 1.4, diagmap)
    # wear / dirt signals from Treyarch's own maps + the normal-map curvature + broad occlusion
    curv = T.blur(T.curvature(N), 1)
    cv = curv[raw_cov]
    e_lo, e_hi = np.percentile(cv, 90), np.percentile(cv, 99.4)
    c_lo, c_hi = np.percentile(-cv, 90), np.percentile(-cv, 99.4)
    edge = T.smoothstep(e_lo, e_hi, curv); crease = T.smoothstep(c_lo, c_hi, -curv)
    fine = T.value_noise(h, w, 96, seed + 1, 3); medium = T.value_noise(h, w, 22, seed + 2, 3)
    mottle = T.value_noise(h, w, 5, seed + 3, 3)
    sdet = slum - T.blur(slum, 18); gdet = G - T.blur(G, 18)
    painted_wear = T.smoothstep(np.percentile(sdet[raw_cov], 88), np.percentile(sdet[raw_cov], 99.5), sdet)
    wear = np.clip(np.maximum(edge * T.smoothstep(.30, .62, fine), painted_wear * .8), 0, 1)
    # The DG-2 occlusion maps are dark over whole panels; only their darkest relative band is a real recess.
    o_lo, o_hi = np.percentile(O[raw_cov], 6), np.percentile(O[raw_cov], 35)
    dirt = np.clip(crease * .85 + T.smoothstep(o_hi, o_lo, O) * .55, 0, 1) * (.55 + .45 * medium)
    sdet_n = np.clip(sdet * 2.2, -.3, .3); gdet_n = np.clip(gdet * .9, -.18, .18)
    weights = {}
    if key in ('body', 'frame'):
        radiator = T.smoothstep(22.4, 21.6, pos[..., 0]) * T.smoothstep(1.8, 1.2, pos[..., 2]) if key == 'body' else 0
        coil = 0
        if key == 'frame':
            # The DG-2's two brass coil springs (measured, coil_probe): the bellows of 22 ring segments ahead of the
            # receiver (x 20.98-25.71, radius ~1.13 round the beam axis) and the coil over the receiver's top
            # (x 6.10-13.76, z 3.66-4.90). The brief's coils are aged copper; only their brass texels change.
            rad = np.hypot(pos[..., 1], pos[..., 2] - 3.1414)
            bellows = (T.smoothstep(20.85, 20.98, pos[..., 0]) * T.smoothstep(25.84, 25.71, pos[..., 0]) *
                       T.smoothstep(1.32, 1.22, rad))
            topcoil = (T.smoothstep(5.97, 6.10, pos[..., 0]) * T.smoothstep(13.89, 13.76, pos[..., 0]) *
                       T.smoothstep(3.52, 3.64, pos[..., 2]) * T.smoothstep(1.05, .97, np.abs(pos[..., 1])))
            coil = np.clip(bellows + topcoil, 0, 1) * brass
        weights['gunmetal'] = steel + (dark if key == 'body' else 0)
        weights['brassedge'] = brass * (1 - small) * (1 - coil)
        weights['brass'] = brass * small * (1 - coil)
        weights['copper'] = copper
        if key == 'frame':
            weights['copper_aged'] = coil
        weights['heatsink'] = red * radiator
        weights['braid'] = red * (1 - radiator)
        weights['rubber'] = light
        weights['hazard'] = label_w
        if key == 'frame':
            weights['enamel'] = dark
    elif key == 'coil':
        weights['copper'] = copper
        weights['brassedge'] = brass * (1 - small)
        weights['brass'] = brass * small
        weights['gunmetal'] = steel
        weights['yellow_enamel'] = red
        weights['ceramic'] = light
        weights['composite_dark'] = dark
    elif key == 'stock':
        # The whole stock is the composite (its round bosses are moulded, not metal), with a rubber butt pad.
        pad = T.smoothstep(-10.45, -10.62, pos[..., 0])
        weights['composite'] = np.clip(1 - pad, 0, 1)
        weights['rubber'] = pad
        # Handled wear: Treyarch's lighter worn wood + edges + the wrist and comb where hands and cheek rub.
        lw = T.smoothstep(np.percentile(clum[raw_cov], 70), np.percentile(clum[raw_cov], 97), clum)
        handled = (T.smoothstep(-3.5, -1.0, pos[..., 0]) * T.smoothstep(5.5, 3.0, pos[..., 0]) +
                   T.smoothstep(-4.0, -6.0, pos[..., 0]) * T.smoothstep(1.4, 2.2, pos[..., 2]))
        wear = np.clip(np.maximum(wear, lw * .75) + np.clip(handled, 0, 1) * .35 * T.smoothstep(.35, .7, medium), 0, 1)
        grain = np.clip((clum - T.blur(clum, 5)) * 3.0 + (clum - T.blur(clum, 40)) * 1.2, -.25, .25)
    total = sum(np.asarray(v, np.float32) for v in weights.values()) + 1e-6
    D = np.zeros((h, w, 3), np.float32); Sp = np.zeros((h, w, 3), np.float32); Gl = np.zeros((h, w), np.float32)
    for role, wt in weights.items():
        wt = np.asarray(wt, np.float32) / total
        if not np.any(wt > 1e-3):
            continue
        d_o = s_o = None
        if role == 'heatsink':
            heat = .55 * T.smoothstep(-2.6, 1.0, pos[..., 2]) + .45 * T.smoothstep(14.0, 21.8, pos[..., 0])
            heat = np.clip(heat + .12 * (medium - .5), 0, 1)
            s_o = ramp(1.0 - T.smoothstep(.35, 1.0, heat), HEAT)
        if role == 'hazard':
            stripe = T.smoothstep(.55, .72, clum)
            d_o = T.lerp(C3(24, 24, 24), C3(222, 170, 36), stripe)
        if role in ('composite', 'composite_dark') and key == 'stock':
            # a moulded composite, not walnut: the source grain survives only as a faint fibre in the lacquer
            d_o = np.clip(ROLES[role]['d'] * (1.0 + .22 * grain)[..., None], 0, 1)
        if role in ('rubber', 'braid'):
            d_o = np.clip(ROLES[role]['d'] * (.80 + .45 * T.norm01(clum, raw_cov))[..., None], 0, 1)
        if role == 'braid':
            # the red-and-white braided cables become charcoal braid; their white tracer becomes a mustard tracer
            rb = (np.asarray(wt) > .5)
            if rb.any():
                lo_, hi_ = np.percentile(clum[rb], 78), np.percentile(clum[rb], 96)
                tracer = T.smoothstep(lo_, hi_, clum) * T.smoothstep(.16, .05, C[..., 0] - C[..., 2])
                d_o = T.lerp(d_o, C3(150, 116, 38), np.clip(tracer, 0, 1) * .75)
        w_use, dirt_use = wear, dirt
        if role == 'copper_aged':
            # tarnish gathers in the folds (creases + occlusion), the crests are rubbed bright (convex curvature)
            w_use = np.clip(wear * 1.35 + edge * .30, 0, 1)
            dirt_use = np.clip(dirt * 1.5 + crease * .35, 0, 1)
        d, s, g = compose(role, w_use, dirt_use, sdet_n, gdet_n, mottle, d_o, s_o)
        D += d * wt[..., None]; Sp += s * wt[..., None]; Gl += g * wt
    # Unused texels: neutral dark (keeps mips from bleeding bright source art into the edges).
    D[~cov] = C3(20, 20, 20); Sp[~cov] = C3(60, 60, 60); Gl[~cov] = .4
    out = {}
    for suffix, arr in (('c', D), ('s', Sp), ('g', np.repeat(Gl[..., None], 3, axis=2))):
        rgba = np.concatenate([arr, np.ones((h, w, 1), np.float32)], axis=2)
        p = common.IMG / ('i_tod2_ws_%s_%s.png' % (key, suffix))
        pngio.write_png(p, rgba); out[suffix] = p
    nsrc = SRC / ('i_wpn_t7_zmb_dg2_%s_n.png' % srckey)
    ndst = common.IMG / ('i_tod2_ws_%s_n.png' % key)
    shutil.copyfile(nsrc, ndst); out['n'] = ndst
    # review masks (scratch only)
    dbg = np.zeros((h, w, 3), np.float32)
    palette = {'gunmetal': (.35, .35, .38), 'brassedge': (.55, .45, .2), 'brass': (1, .8, .2), 'copper': (.9, .45, .3),
               'copper_aged': (.6, .25, .12),
               'enamel': (.12, .12, .12), 'heatsink': (1, .5, 0), 'composite': (.35, .22, .15), 'composite_dark': (.2, .13, .1),
               'rubber': (.5, .5, .5), 'braid': (.6, .3, .6), 'yellow_enamel': (1, 1, 0), 'ceramic': (1, 1, 1), 'hazard': (1, .2, .2)}
    for role, wt in weights.items():
        dbg += (np.asarray(wt, np.float32) / total)[..., None] * np.array(palette[role], np.float32)
    pngio.write_png(common.SCRATCH / ('roles_%s.png' % key), T.resize(dbg, h // 4, w // 4))
    pngio.write_png(common.SCRATCH / ('wear_%s.png' % key), T.resize(np.stack([wear, dirt, edge], 2), h // 4, w // 4))
    stats = {role: float((np.asarray(wt, np.float32) / total)[raw_cov].mean()) for role, wt in weights.items()}
    return dict(size=[w, h], parts=len(info), coverage=float(raw_cov.mean()), roles=stats,
                curvature_pct=[float(e_lo), float(e_hi)], files={k: common.rel(v) for k, v in out.items()})


prev = common.ART / 'surfaces.json'
record = dict(materials=(common.read_json(prev).get('materials', {}) if prev.exists() else {}))
for key, mi, size, sk, seed in [('body', 2, (2048, 2048), 'body', 11), ('frame', 4, (2048, 2048), 'metal', 23),
                                ('coil', 1, (2048, 2048), 'pipe', 37), ('stock', 0, (2048, 1024), 'wood', 41)]:
    if key not in ONLY:
        continue
    t = time.time()
    record['materials'][key] = author(key, mi, size, sk, seed)
    print('WS_SURFACE', key, round(time.time() - t, 1), 's', json.dumps(record['materials'][key]['roles']), flush=True)

# ---------------- glow parts ----------------
P = common.PALETTE
core_rgb, hot_rgb, amber_rgb = C3(*P['core']), C3(*P['core_hot']), C3(*P['amber'])


# The laser filament (DG-2 power rod: u runs along it, u = 0 at its MUZZLE end x 17.6 - measured, corr(u, x) = -1;
# v around it): fine lengthwise striations, a clear brightness gradient up toward the muzzle and soft energy knots
# spaced along the rod, so it reads as light being driven forward; the emissive falloff keeps the centre line hottest.
cw, ch = 512, 256
u = (np.arange(cw) + .5) / cw; v = (np.arange(ch) + .5) / ch
U, V = np.meshgrid(u, v)
stri = .5 + .5 * np.sin(V * np.pi * 2 * 18.0 + np.sin(U * 9.0) * .6)
stri = T.smoothstep(.72, 1.0, stri)
grad = T.smoothstep(1.0, 0.0, U)                                   # 0 at the breech end, 1 at the muzzle end
# energy knots: irregularly spaced, stretched to different lengths and strengths (evenly spaced pale knots read as
# stacked beads - review pass 3), denser and brighter toward the muzzle
KNOTS = [(.045, .022, .9), (.12, .045, .7), (.205, .018, 1.0), (.29, .06, .55), (.385, .028, .8), (.47, .05, .6),
         (.575, .02, .75), (.66, .07, .45), (.78, .035, .5), (.9, .055, .35)]
knots = sum(s_ * np.exp(-((U - c_) / w_) ** 2) for c_, w_, s_ in KNOTS)
knots = np.clip(knots, 0, 1) * (.6 + .4 * grad) * (.85 + .15 * np.sin(V * np.pi * 2 * 3.0 + U * 5.0))
L = np.clip((.46 + .44 * grad) * (.80 + .20 * stri) + .22 * knots, 0, 1)
core_e = ramp(L, [(0, amber_rgb * .55), (.40, amber_rgb), (.62, core_rgb), (.86, core_rgb), (1.0, hot_rgb)])
core_c = np.clip(core_e * .55, 0, 1)
for name, arr in (('i_tod2_ws_core_e', core_e), ('i_tod2_ws_core_c', core_c),
                  ('i_tod2_ws_core_s', np.full((ch, cw, 3), 56 / 255, np.float32)),
                  ('i_tod2_ws_core_g', np.full((ch, cw, 3), .72, np.float32))):
    pngio.write_png(common.IMG / (name + '.png'), np.concatenate([arr, np.ones((ch, cw, 1), np.float32)], 2))
shutil.copyfile(SRC / 'i_wpn_t7_zmb_dg2_power_n.png', common.IMG / 'i_tod2_ws_core_n.png')

# Lamps (three bulbs + the rear indicator) on the DG-2 glass-texture layout: the bulbs keep the source's filament
# streak and cap pattern as warm-yellow emission over a glowing amber floor; the rear lamp band glows yellow.
gl_c = src('glass_c'); gl_e = src('glass_e')
lw_, lh_ = 512, 512
gc = T.resize(gl_c, lh_, lw_); ge = T.resize(gl_e, lh_, lw_)
Le = T.luminance(ge[..., :3]); Le = T.norm01(Le, None, 1, 99.7)
rows = (np.arange(lh_) + .5) / lh_
band_bulb = (rows < .465)[:, None] * np.ones((1, lw_), bool)
band_glow = ((rows >= .465) & (rows < .74))[:, None] * np.ones((1, lw_), bool)
# The rear indicator lamp (band_glow) is a dark warm GLASS shell round a glowing core: the source's own across-the-
# tube gradient is kept at full range (dark rims, bright middle) instead of being lifted flat (review pass 3: it
# read as opaque glowing plastic), and its diffuse is dark amber glass, not bright yellow.
Lg = T.norm01(np.where(band_glow, Le, np.nan), band_glow, 2, 99.5) if band_glow.any() else Le
lamp_L = np.where(band_bulb, .40 + .60 * Le, np.where(band_glow, .06 + .94 * np.nan_to_num(Lg) ** 1.4, .25 + .2 * Le))
lamp_e = ramp(lamp_L, [(0, amber_rgb * .35), (.40, amber_rgb * .80), (.66, core_rgb), (.90, core_rgb), (1.0, hot_rgb)])
lamp_c = np.clip(T.lerp(C3(120, 84, 30), C3(180, 140, 60), T.luminance(gc[..., :3]) * 2.0), 0, 1)
lamp_c = np.where(band_glow[..., None], np.clip(T.lerp(C3(34, 24, 9), C3(70, 50, 18), T.luminance(gc[..., :3]) * 2.0), 0, 1),
                  lamp_c)
gloss = np.clip(.86 - .25 * T.norm01(T.luminance(gc[..., :3]), None, 5, 95) * .6, 0, 1)
for name, arr in (('i_tod2_ws_lamp_e', lamp_e), ('i_tod2_ws_lamp_c', lamp_c),
                  ('i_tod2_ws_lamp_s', np.full((lh_, lw_, 3), 56 / 255, np.float32)),
                  ('i_tod2_ws_lamp_g', np.repeat(gloss[..., None], 3, 2))):
    pngio.write_png(common.IMG / (name + '.png'), np.concatenate([arr, np.ones((lh_, lw_, 1), np.float32)], 2))
shutil.copyfile(SRC / 'i_wpn_t7_zmb_dg2_glass_n.png', common.IMG / 'i_tod2_ws_lamp_n.png')

# The glass tube: clear, faintly warm, alpha .12 with fingerprint/dust smudges (from the source smudge pattern) up to
# ~.30 - the filament reads through it from every side. Specular comes from stock $black_specular (F0 .04).
smudge = T.norm01(1.0 - T.luminance(gc[..., :3]), None, 5, 98)
smudge = T.smoothstep(.35, .95, smudge) * (.6 + .4 * T.value_noise(lh_, lw_, 14, 91, 2))
alpha = np.clip(.12 + .18 * smudge, 0, 1)
glass_rgb = np.clip(T.lerp(C3(196, 186, 162), C3(120, 110, 92), smudge), 0, 1)
pngio.write_png(common.IMG / 'i_tod2_ws_glass_c.png', np.concatenate([glass_rgb, alpha[..., None]], 2))
glass_g = np.clip(.92 - .35 * smudge, 0, 1)
pngio.write_png(common.IMG / 'i_tod2_ws_glass_g.png', np.concatenate([np.repeat(glass_g[..., None], 3, 2), np.ones((lh_, lw_, 1), np.float32)], 2))

files = sorted(p for p in common.IMG.glob('i_tod2_ws_*.png') if not p.name.startswith('i_tod2_ws_emitter'))
record['textures'] = {p.name: common.sha(p) for p in files}
record['sources'] = {p.name: common.sha(p) for p in sorted(SRC.glob('i_wpn_t7_zmb_dg2_*.png'))}
record['palette'] = common.PALETTE
record['notes'] = ('Normal maps are the DG-2 originals copied byte-for-byte under Wunderstrahl names; every other '
                   'map is authored here. Gloss maps are relative to glossRange 0..12 (opaque) / 0..8 (glass).')
common.write_json(common.ART / 'surfaces.json', record)
print('WS_03_SURFACES done', len(files), 'maps', round(time.time() - t0, 1), 's', flush=True)
