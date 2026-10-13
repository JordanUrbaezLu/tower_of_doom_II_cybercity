"""THE HAVENS' screen tint, previewed exactly as the HUD draws it (docs/202).

Composites the SHIPPED tint texture (model_export/tod_haven/_images/i_tod_haven_vignette.png)
over a stand-in dark scene with the widget's OWN colours, alphas and timings, read out of
TodHaven.lua (the wired copy, else the staged one), so the review can never drift from the
widget. Straight alpha blending, as a LUI UIImage draws: rgb = texture x setRGB, alpha =
texture alpha x setAlpha.

    python -B tools/haven/render_tint_preview.py

Writes art/haven/review/vignette_states.png, four panels top to bottom:
  1 OUTSIDE   nothing drawn
  2 INSIDE    the steady tint (IDLE_A)
  3 CROSSING  the flash's peak, PULSE_IN_MS in: the steady tint has only started to rise
  4 HIT CUT   inside, at the peak of a cut hit's flicker (HIT_A)
and vignette_corner_2x.png (the top-left corner of panel 2 at twice size).
The scene behind is a placeholder, not the game.
"""
import math, pathlib, re
import numpy as np
from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/haven/review'
TEX = ROOT / 'model_export/tod_haven/_images/i_tod_haven_vignette.png'
LUA = next(p for p in (ROOT / 'ui/uieditor/widgets/HUD/AetheriumWidgets/TodHaven.lua',
                       ROOT / 'art/haven/staged/TodHaven.lua') if p.exists())

src = LUA.read_text(encoding='utf-8')
def rgb(name):
    m = re.search(r'local %s = \{ ([\d.]+), ([\d.]+), ([\d.]+) \}' % name, src); assert m, name
    return tuple(float(v) for v in m.groups())
def num(name):
    """`local A, B, C = 1, 2, 3` -> the value in NAME's position on its declaring line."""
    m = re.search(r'^local ([\w, ]*\b%s\b[\w, ]*)=([^\n]+)' % name, src, re.M); assert m, name
    names = [n.strip() for n in m.group(1).split(',')]
    vals = [v.strip() for v in m.group(2).split('--')[0].split(',')]
    assert len(names) == len(vals), m.group(0)
    return float(vals[names.index(name)])
TINT, HOT = rgb('TINT'), rgb('HOT')
IDLE_A, PULSE_A, HIT_A = num('IDLE_A'), num('PULSE_A'), num('HIT_A')
TINT_IN_MS, PULSE_IN_MS = num('TINT_IN_MS'), num('PULSE_IN_MS')

tex = np.asarray(Image.open(TEX).convert('RGBA'), dtype=np.float32) / 255.0
H, W = tex.shape[:2]

def scene():
    """A dark stand-in for the game behind the HUD: a cool gradient, a warm and a cold blur."""
    y = np.linspace(0, 1, H)[:, None, None]
    base = np.array([24, 22, 36], np.float32) * (1 - y) + np.array([40, 32, 52], np.float32) * y
    img = np.broadcast_to(base, (H, W, 3)).copy()
    yy, xx = np.mgrid[0:H, 0:W]
    for (cx, cy, r, col) in ((300, 410, 150, (175, 82, 72)), (880, 300, 115, (82, 104, 196)), (640, 560, 260, (70, 60, 92))):
        w = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2.0 * r * r)))[..., None] * 0.85
        img = img * (1 - w) + np.array(col, np.float32) * w
    return img / 255.0

def layer(dst, colour, alpha):
    a = tex[..., 3:4] * alpha
    return dst * (1 - a) + tex[..., :3] * np.array(colour, np.float32) * a

bg = scene()
states = [
    ('outside', bg),
    ('inside', layer(bg, TINT, IDLE_A)),
    ('crossing', layer(layer(bg, TINT, IDLE_A * PULSE_IN_MS / TINT_IN_MS), HOT, PULSE_A)),
    ('hit', layer(layer(bg, TINT, IDLE_A), HOT, HIT_A)),
]
to_img = lambda a: Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB')
panels = [to_img(a).resize((W // 2, H // 2), Image.LANCZOS) for _, a in states]
gap = 6
sheet = Image.new('RGB', (W // 2, len(panels) * (H // 2) + (len(panels) - 1) * gap), (0, 0, 0))
for i, p in enumerate(panels):
    sheet.paste(p, (0, i * (H // 2 + gap)))
sheet.save(OUT / 'vignette_states.png', optimize=True)
corner = to_img(states[1][1]).crop((0, 0, 420, 260)).resize((840, 520), Image.LANCZOS)
corner.save(OUT / 'vignette_corner_2x.png', optimize=True)
print('HAVEN_TINT_PREVIEW', LUA.relative_to(ROOT).as_posix(), 'TINT', TINT, 'HOT', HOT,
      'IDLE_A', IDLE_A, 'PULSE_A', PULSE_A, 'HIT_A', HIT_A, 'crossing tint', round(IDLE_A * PULSE_IN_MS / TINT_IN_MS, 3))
