"""RT-palette reference sheet: red Fallen (measured, pre-synthwave base copies) beside the shipped synthwave
pieces, plus the role swatch table and a simulated Fallen tube. Review art only (not shipped)."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = r'C:\Users\jorda\Repositories\tower_of_doom_II_cybercity'
os.chdir(REPO)
sys.path.insert(0, os.path.join(REPO, 'tools', 'artgen'))
import synthwave as sw   # read-only use (Svg / tube render); CORE is patched in-process only

B3 = 'tmp/redesign/R3-synthwave-system/base/source_data/tod_ui_images/_images/'
B4 = 'tmp/redesign/R4-synthwave-hud/base/source_data/tod_ui_images/_images/'
C = 'source_data/tod_ui_images/_images/'
OUT = os.path.join(REPO, 'art', 'generated', 'RT-palette')
os.makedirs(OUT, exist_ok=True)

F = lambda s, b=False: ImageFont.truetype(r'C:\Windows\Fonts\%s' % ('arialbd.ttf' if b else 'arial.ttf'), s)
MONO = lambda s: ImageFont.truetype(r'C:\Windows\Fonts\consola.ttf', s)
BG = (30, 30, 32, 255)

FALLEN = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fallen.json')))


def ld(p, sc=1.0, nearest=False):
    im = Image.open(p).convert('RGBA')
    if sc != 1.0:
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.NEAREST if nearest else Image.LANCZOS)
    return im


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


W = 2600
canvas = Image.new('RGBA', (W, 6000), BG)
d = ImageDraw.Draw(canvas)
y = 24
d.text((30, y), 'RT-PALETTE  -  the red "Fallen" UI (measured from the pre-synthwave base PNGs)  vs  the shipped synthwave', font=F(34, True), fill=(240, 242, 248))
y += 48
d.text((30, y), 'Left of each pair = RED ERA (tmp/redesign/R3|R4 .../base).  Right = SYNTHWAVE as shipped (source_data).  Over #1E1E20. Scale noted per row.',
       font=F(20), fill=(170, 176, 190))
y += 44

PAIRS = [
    ('pause left panel, header + YOUR UPGRADES  (x0.55)', B3, 'i_tod_pm_panel_left.png', (0, 0, 1468, 330), 0.55),
    ('pause button idle / focus  (x0.55)', B3, ['i_tod_pm_btn.png', 'i_tod_pm_btn_focus.png'], None, 0.55),
    ('row card / dark twin  (x0.5)', B3, ['i_tod_pm_row.png', 'i_tod_pm_row_violet.png'], None, 0.5),
    ('legend box  (x0.55)', B3, 'i_tod_pm_legend_box.png', None, 0.55),
    ('scoreboard local row / points  (x0.45)', B3, ['i_tod_sb_player_row_local.png', 'i_tod_sb_points.png'], None, 0.45),
    ('prompt chassis / locked  (x0.6)', B4, ['i_tod_prompt_chassis.png', 'i_tod_prompt_chassis_locked.png'], None, 0.6),
    ('HUD round badge / rampage / tile idle / ready / PaP / medallion  (x1)', B4,
     ['i_tod_h2_round_badge.png', 'i_tod_h2_round_badge_rampage.png', 'i_tod_h2_tile.png', 'i_tod_h2_tile_ready.png',
      'i_tod_h2_tile_pap.png', 'i_tod_h2_medallion_ring.png'], None, 1.0),
    ('luck plate / rampage  (x0.5)', B4, ['i_tod_h2_luck_plate.png', 'i_tod_h2_luck_plate_rampage.png'], None, 0.5),
    ('pips on / off / dark  (x2 nearest)  + reset mark', B3,
     ['i_tod_pm_pip_on.png', 'i_tod_pm_pip_off.png', 'i_tod_pm_pip_on_violet.png', 'i_tod_pm_reset_mark.png'], None, 2.0),
]


def strip(base, names, crop, sc, horiz):
    names = names if isinstance(names, list) else [names]
    ims = []
    for n in names:
        im = Image.open(base + n).convert('RGBA')
        if crop:
            im = im.crop(crop)
        nearest = sc >= 2
        ims.append(im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.NEAREST if nearest else Image.LANCZOS))
    if horiz:
        w = sum(i.width for i in ims) + 10 * (len(ims) - 1)
        h = max(i.height for i in ims)
        s = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        x = 0
        for i in ims:
            s.alpha_composite(i, (x, 0)); x += i.width + 10
    else:
        w = max(i.width for i in ims)
        h = sum(i.height for i in ims) + 8 * (len(ims) - 1)
        s = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        yy = 0
        for i in ims:
            s.alpha_composite(i, (0, yy)); yy += i.height + 8
    return s


for label, base, names, crop, sc in PAIRS:
    horiz = isinstance(names, list) and len(names) > 2 or (isinstance(names, list) and 'prompt' in label)
    a = strip(base, names, crop, sc, horiz)
    b = strip(C, names, crop, sc, horiz)
    d.text((30, y), label, font=F(22, True), fill=(220, 224, 236))
    y += 30
    d.text((30, y), 'RED ERA', font=F(16, True), fill=(255, 92, 118))
    d.text((60 + a.width, y), 'SYNTHWAVE (shipped)', font=F(16, True), fill=(255, 43, 209))
    y += 22
    canvas.alpha_composite(a, (30, y))
    canvas.alpha_composite(b, (60 + a.width, y))
    y += max(a.height, b.height) + 26

# ---------------------------------------------------------------------------------------------- swatches
y += 10
d.line((30, y, W - 30, y), fill=(80, 84, 96), width=2)
y += 16
d.text((30, y), 'PAL ROLES:  synthwave value  ->  FALLEN value  (evidence = image + pixels it was measured on)', font=F(28, True), fill=(240, 242, 248))
y += 44
for row in FALLEN['pal']:
    role, meaning, s_hex, f_hex, ev = row['role'], row['meaning'], row['synthwave'], row['fallen'], row['evidence']
    d.text((30, y + 8), role, font=F(22, True), fill=(235, 238, 246))
    mw, mline, my = meaning.split(' '), '', y + 36
    for wd in mw:
        t = (mline + ' ' + wd).strip()
        if d.textlength(t, font=F(15)) > 330:
            d.text((30, my), mline, font=F(15), fill=(150, 156, 172)); my += 18; mline = wd
        else:
            mline = t
    d.text((30, my), mline, font=F(15), fill=(150, 156, 172))
    for i, (hx_, tag) in enumerate(((s_hex, 'SYNTH'), (f_hex, 'FALLEN'))):
        x0 = 380 + i * 270
        try:
            col = rgb(hx_) if hx_.startswith('#') else None
        except Exception:
            col = None
        if col:
            d.rectangle((x0, y + 4, x0 + 80, y + 54), fill=col + (255,), outline=(90, 90, 96))
        d.text((x0 + 92, y + 10), tag, font=F(14, True), fill=(150, 156, 172))
        d.text((x0 + 92, y + 28), hx_, font=MONO(20), fill=(235, 238, 246))
    # evidence wraps
    words, line, ly = ev.split(' '), '', y + 4
    for wd in words:
        t = (line + ' ' + wd).strip()
        if d.textlength(t, font=F(15)) > W - 980:
            d.text((950, ly), line, font=F(15), fill=(190, 196, 210)); ly += 19; line = wd
        else:
            line = t
    d.text((950, ly), line, font=F(15), fill=(190, 196, 210))
    y = max(y + 64, ly + 26, my + 28)

# ---------------------------------------------------------------------------------------------- tube sim
y += 10
d.line((30, y, W - 30, y), fill=(80, 84, 96), width=2)
y += 16
d.text((30, y), 'THE LIT LINE:  red-era focused button (measured, x4 nearest)  |  Svg.tube in FALLEN red + CORE  |  synthwave magenta tube (same code)',
       font=F(24, True), fill=(240, 242, 248))
y += 40
red_crop = Image.open(B3 + 'i_tod_pm_btn_focus.png').convert('RGBA').crop((480, 0, 560, 40))
bgc = Image.new('RGBA', red_crop.size, BG); bgc.alpha_composite(red_crop)
canvas.alpha_composite(bgc.resize((320, 160), Image.NEAREST), (30, y))


def sim(color, core, fill_top, fill):
    sw.CORE[color] = core
    s = sw.Svg(80, 40)
    s.rect(0, 0, 80, 40, fill)
    s.path(sw.poly_d([(0, 4), (80, 4), (80, 40), (0, 40)]), fill=fill_top, opacity=1.0)
    s.tube(sw.line_d((-4, 4), (84, 4)), color, 3.0, glow=1.0)
    im = s.render()
    b = Image.new('RGBA', im.size, BG); b.alpha_composite(im)
    return b.resize((320, 160), Image.NEAREST)


canvas.alpha_composite(sim('#F2203A', FALLEN['core']['red'], '#22070E', '#22070E'), (380, y))
canvas.alpha_composite(sim('#FF2BD1', '#FFD9F6', '#180B30', '#180B30'), (730, y))
d.text((30, y + 168), 'RED ERA: line #FF5C76 2px,', font=F(15), fill=(190, 196, 210))
d.text((30, y + 188), 'halo #E52642, wash #A51B30, fill #22070E', font=F(15), fill=(190, 196, 210))
d.text((380, y + 168), 'FALLEN sim: #F2203A + CORE %s' % FALLEN['core']['red'], font=F(15), fill=(190, 196, 210))
d.text((380, y + 188), 'w 3 -> centre #FF5E73 (target #FF5C76)', font=F(15), fill=(190, 196, 210))
d.text((730, y + 168), 'SYNTHWAVE: #FF2BD1 + CORE #FFD9F6', font=F(15), fill=(190, 196, 210))
d.text((730, y + 188), 'centre renders #FF8AEB', font=F(15), fill=(190, 196, 210))

# measured profile print
def prof(img, x, y0, y1):
    a = np.asarray(img.convert('RGBA'))
    return ['#%02X%02X%02X' % tuple(a[yy, x, :3]) for yy in range(y0, y1)]

y += 230
canvas = canvas.crop((0, 0, W, y + 20))
canvas.convert('RGB').save(os.path.join(OUT, '_reference.png'), optimize=True)
print('wrote', os.path.join(OUT, '_reference.png'), canvas.size)
