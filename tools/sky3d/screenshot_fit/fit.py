"""fit.py - WHERE IS THE SKY'S SIGN IN GAME? Measured from one screenshot (docs/196 §3).

  node tools/sky3d/screenshot_fit/export_brushes.js --eye <x,y,z of the case>
  python tools/sky3d/screenshot_fit/fit.py tools/sky3d/screenshot_fit/case_20260929.json

A case file names the screenshot, the eye it was taken from (the log's [TOD_AI] PLAYER pos + 60 standing), the
HUD rectangles to ignore, the view search ranges, and painted features of the sign matched between the reference
painting (art/sky3d/sign/tod2_title_gate_reference.png px) and the screenshot (px). Three steps:
  1. THE VIEW: the .map's brushes are ray-cast from the eye and scored against the screenshot's sky / geometry
     mask over the yaw x pitch x hfov grid -> the heading (only geometry fixes the heading: the sky is at
     infinity and moves with the unknown).
  2. THE SIGN: the matched features, turned into directions with session 22's card geometry (build_city.py GATE:
     w_deg, D, box_el; the card json: box_px, pads), are least-squares fitted for (sign yaw - view yaw, pitch,
     hfov) -> the sign's world yaw.
  3. THE CHECK: tmp/screenshot_fit/compare.png = the screenshot above the rebuilt view with the panorama's centre
     column at the measured yaw. It must reproduce the screenshot.
Then compare the measured yaw with test_jumppad's rule: -(SSI sun azimuth + skyRotation) - roll.
"""
import json, math, pathlib, re, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.optimize import least_squares

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import view as V  # noqa: E402

REPO = V.REPO
OUT = REPO / 'tmp/screenshot_fit'


def card():
    """session 22's title-gate card: (m per canvas px, D m, box_el deg, box centre canvas px, pads)."""
    src = (REPO / 'tools/sky3d/build_city.py').read_text(encoding='utf-8')
    gate = re.search(r'(?s)^GATE = dict\((.*?)\n\s*sat=', src, re.M).group(1)
    num = lambda k: float(re.search(r'\b' + k + r'=([\d.]+)', gate).group(1))
    meta = json.loads((REPO / 'art/sky3d/sign/tod2_title_gate.json').read_text())
    s = 2 * num('D') * math.tan(math.radians(num('w_deg') / 2)) / meta['ref_width_px']
    return s, num('D'), num('box_el'), meta['box_px'], (meta.get('pad_x', 0), meta.get('pad_top', 0))


def feature_dir(rx, ry, C):
    """reference painting px -> (azimuth deg, + = the painting's right; elevation deg) from the render camera."""
    s, D, el, (u0, v0), (px, pt) = C
    e = math.radians(el)
    u, v = rx + px, ry + pt
    q = (np.array([0, math.cos(e), math.sin(e)]) * D + np.array([1, 0, 0]) * (u - u0) * s
         + np.array([0, -math.sin(e), math.cos(e)]) * (v0 - v) * s)
    return math.degrees(math.atan2(q[0], q[1])), math.degrees(math.atan2(q[2], math.hypot(q[0], q[1])))


def project(yaw, pitch, hfov, W, H, dirs):
    tx = math.tan(math.radians(hfov / 2))
    ty = tx * H / W
    p, y = math.radians(pitch), math.radians(yaw)
    F = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), -math.sin(p)])
    R = np.array([math.sin(y), -math.cos(y), 0.0])
    U = np.cross(R, F)
    return np.array([(W / 2 + (d @ R) / (d @ F) / tx * W / 2, H / 2 - (d @ U) / (d @ F) / ty * H / 2) for d in dirs])


def world_dir(yaw, el):
    y, e = math.radians(yaw), math.radians(el)
    return np.array([math.cos(e) * math.cos(y), math.cos(e) * math.sin(y), math.sin(e)])


def main():
    case = json.loads(pathlib.Path(sys.argv[1]).read_text())
    eye = case['eye']
    shot = np.asarray(Image.open(REPO / case['shot']).convert('RGB')).astype(float)
    FH, FW = shot.shape[:2]
    br = V.load_brushes(OUT / 'brushes.json')

    # 1. THE VIEW
    r, g, b = shot[..., 0], shot[..., 1], shot[..., 2]
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    std = np.sqrt(np.maximum(ndi.uniform_filter(lum ** 2, 7) - ndi.uniform_filter(lum, 7) ** 2, 0))
    sky = ndi.binary_opening(((b - g) > 6) | (g > r * 0.55) | (r > 70) | (std > 4), iterations=1)
    valid = np.ones_like(sky)
    valid[case.get('ignore_below_y', FH):] = False
    for x0, y0, x1, y1 in case.get('hud_masks', []):
        valid[y0:y1, x0:x1] = False
    S = 8
    W, H = FW // S, FH // S
    sk = ndi.zoom(sky.astype(float), (H / FH, W / FW), order=1) > 0.5
    va = ndi.zoom(valid.astype(float), (H / FH, W / FW), order=0) > 0.5
    y0, y1, ys = case['search']['yaw']
    best = (-1, None)
    for hf in case['search']['hfov']:
        for p in case['search']['pitch']:
            for yw in np.arange(y0, y1 + 1e-6, ys):
                t, _ = V.cast(eye, V.rays(W, H, yw, p, hf), br, tile=8)
                sc = (((~np.isfinite(t)) == sk) & va).sum() / va.sum()
                if sc > best[0]:
                    best = (sc, (float(yw), p, hf))
    score, (vyaw, vpitch, vhfov) = best
    print('THE VIEW: yaw %.1f pitch %.1f hfov %.1f (mask agreement %.3f)' % (vyaw, vpitch, vhfov, score))

    # 2. THE SIGN
    C = card()
    pts = case['points']
    feats = [feature_dir(*p['ref'], C) for p in pts]
    target = np.array([p['shot'] for p in pts], float)

    def resid(x):
        rel, pitch, hfov = x
        dirs = [world_dir(vyaw + rel - az, el) for az, el in feats]
        return (project(vyaw, pitch, hfov, FW, FH, dirs) - target).ravel()
    sol = least_squares(resid, [0.0, vpitch, vhfov])
    rel = sol.x[0]
    rms = math.sqrt((sol.fun ** 2).mean())
    sign_yaw = (vyaw + rel) % 360
    print('THE SIGN: centre %.1f deg %s of the view -> WORLD YAW %.1f (fit pitch %.1f hfov %.1f, rms %.1f px over %d points)'
          % (abs(rel), 'right' if rel < 0 else 'left', sign_yaw, sol.x[1], sol.x[2], rms, len(pts)))

    # 3. THE CHECK
    OUT.mkdir(parents=True, exist_ok=True)
    w, h = 948, int(948 * FH / FW)
    fpitch, fhfov = sol.x[1], sol.x[2]     # the sign fit pins pitch + hfov far better than the mask grid does
    im, _ = V.render(eye, vyaw, fpitch, fhfov, w, h, br, V.load_sky(case.get('sky')), sign_yaw)
    top = Image.fromarray(np.clip((shot - 5) * 3.0, 0, 255).astype('uint8')).resize((w, h))
    sheet = Image.new('RGB', (w, 2 * h + 40), (0, 0, 0))
    sheet.paste(top, (0, 0))
    sheet.paste(Image.fromarray(im), (0, h + 40))
    ImageDraw.Draw(sheet).text((6, h + 12), 'rebuilt: yaw %.1f pitch %.1f hfov %.1f, the sign centre at world yaw %.1f'
                                 % (vyaw, fpitch, fhfov, sign_yaw), fill=(255, 255, 0))
    sheet.save(OUT / 'compare.png')
    print('THE CHECK:', (OUT / 'compare.png').relative_to(REPO), '- the rebuilt view must reproduce the screenshot')


if __name__ == '__main__':
    main()
