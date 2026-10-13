"""render_companion_plate.py - SEE the companion status plate (PK08, 2026-10-05, W2G) the way the game draws it.

Runs the REAL TodCompanionPlate.lua and TodSpinReel.lua (+ the glyph typeface modules) under the timed LUI
mock (mock_lui_anim.lua), drives both with the exact events _tod_partners.gsc sends -
    tod_ptn_hud   ( companion + 1, state, value, len, flags )      push_hud: the plate
    tod_ptn_items ( s1, s2, s3, companion + 1 )                    push_items: the item chips on its edge
- advances the clock through the tweens (the hit ghost's hold + drain, the destroyed hold, the pulse and
blink loops really run), and draws each state at 1080P (1.5 px per canvas unit) over an in-game backdrop,
with the bottom-right HUD it sits in (the gun plate + the gun-bay icon, the ability / PaP tiles, the descent
gauge's rail) drawn from the shipped art at their AetheriumLoadout / tod_upgrade.lua rects. The OLD readout
(three server hudelems: a stock-font label over two white quads, docs: _tod_partners.gsc status_hud before
PK08) is drawn the way the engine placed it, for the before / after.

  python tools/ui_mockup/render_companion_plate.py              # -> art/generated/W2G-icons-plate/hud_plate_*.png
  python tools/ui_mockup/render_companion_plate.py --out DIR     #    + hud_plate_contact.png (1:1 crops)

An approximation (linear tweens, no bloom, no blend modes), not a pixel match: it answers layout, size,
colour and the choreography, which is what a readout is judged on. Exits 1 when an image the plate draws
cannot be found (a white square in game).
"""
import argparse, os, sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_pull as rp   # noqa: E402  (draw, find_image, the typeface)
import lupa.lua51 as lua51  # noqa: E402

REPO = rp.REPO
W = os.path.join(REPO, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets')
OUT = os.path.join(REPO, 'art', 'generated', 'W2G-icons-plate')
K = 1.5   # 1080p

ACTIVE, REBUILD, DEPLOYING = 1, 2, 3
CHIPS = [1 * 4 + 3, 6 * 4 + 2, 0]          # PLATING LEGENDARY, ARC CHAIN EPIC, an empty slot

# name -> (companion 1..4, [(event args, advance ms) ...], caption). The last state is what is drawn.
STATES = [
    ('online',     2, [((2, ACTIVE, 100, 0, 0), 700)], 'the Dealer\'s gift arrives: ONLINE, cyan, the bar powered up'),
    ('hit',        2, [((2, ACTIVE, 100, 0, 0), 700), ((2, ACTIVE, 65, 0, 0), 140)], 'a hit: the white ghost holds the lost health'),
    ('damaged',    1, [((1, ACTIVE, 100, 0, 0), 700), ((1, ACTIVE, 30, 0, 0), 700)], 'at 35 percent or less: DAMAGED, amber, the ring pulses'),
    ('destroyed',  3, [((3, ACTIVE, 30, 0, 0), 700), ((3, REBUILD, 45, 45, 0), 160)], 'destroyed: red flash, the portrait shakes and darkens'),
    ('rebuilding', 3, [((3, ACTIVE, 30, 0, 0), 700), ((3, REBUILD, 45, 45, 0), 1500)] + [((3, REBUILD, n, 45, 0), 1000) for n in range(44, 22, -1)],
     'BACK IN 23: the amber bar fills to the second it returns'),
    ('deploying',  4, [((4, DEPLOYING, 100, 0, 0), 300)], 'on its way: DEPLOYING, violet, the portrait blinks'),
    ('holding',    4, [((4, ACTIVE, 80, 0, 0), 700), ((4, ACTIVE, 80, 0, 1), 300)], 'frozen with its owner (a spin, a card deal): HOLDING'),
]
LOADOUT = [  # the bottom-right HUD the plate sits in (AetheriumLoadout.lua HUD_DX 4, tod_upgrade.lua V2 rail)
    ('i_tod_h2_gauge_tower', 1232, 110, 1264, 560),
    ('i_tod_h2_gun_plate', 1002, 606, 1266, 678),
    ('i_tod_hud_gun_skull', 1008, 632, 1104, 676),
    ('i_tod_h2_tile_pap', 1004, 568, 1050, 600),
    ('i_tod_h2_tile', 1164, 568, 1210, 600), ('i_tod_h2_ab_cloak', 1169, 572, 1193, 596),
    ('i_tod_h2_tile', 1214, 568, 1260, 600), ('i_tod_h2_ab_soul_bomb', 1219, 572, 1243, 596),
]


def img_item(name, x0, y0, x1, y1, a=1.0, rgb=(1.0, 1.0, 1.0)):
    return dict(img=name, x0=x0, y0=y0, x1=x1, y1=y1, r=rgb[0], g=rgb[1], b=rgb[2], a=a, zrot=0.0, text='')


def runtime():
    L = lua51.LuaRuntime(unpack_returned_tuples=True)
    os.chdir(REPO)
    L.execute(open(os.path.join(HERE, 'mock_lui_anim.lua'), encoding='utf-8').read())
    for f in ('TodUIOwnership', 'TodHudVeil', 'TodCardArt', 'TodGlyphMetrics', 'TodGlyphRow', 'TodGlyphText',
              'TodSpinReel', 'TodCompanionPlate'):
        p = os.path.join(W, f + '.lua')
        if not os.path.exists(p):
            if f == 'TodCompanionPlate':
                raise SystemExit('render_companion_plate: %s is missing' % p)
            continue
        L.execute(open(p, encoding='utf-8').read())
    plate = L.eval('CoD.TodCompanionPlate.new( 0, 0 )')
    reel = L.eval('CoD.TodSpinReel.new( 0, 0 )')
    return L, plate, reel


def backdrop():
    p = rp.BACKDROP
    if os.path.exists(p):
        return Image.open(p).convert('RGBA').resize((int(1280 * K), int(720 * K)), Image.LANCZOS)
    return Image.new('RGBA', (int(1280 * K), int(720 * K)), (14, 12, 26, 255))


def old_readout(canvas, comp_name, text_suffix, frac):
    """The pre-PK08 readout as the engine drew it: NewClientHudElem right / bottom aligned at x -28, label y -138
    (fontScale 1.1, the default font), a 112 x 4 track coloured (0.10, 0.15, 0.20) and a cyan fill at y -130, all
    at alpha 0.85, in the 640 x 480 virtual screen (x 3 px, y 2.25 px per unit at 1080p). The chips sat above it."""
    d = ImageDraw.Draw(canvas, 'RGBA')
    sx, sy = 1920 / 640.0, 1080 / 480.0
    right = 1920 - 28 * sx
    by = 1080 - 130 * sy
    d.rectangle([right - 112 * sx, by - 4 * sy, right, by], fill=(26, 38, 51, 217))
    d.rectangle([right - 112 * sx, by - 4 * sy, right - 112 * sx * (1 - frac), by], fill=(26, 191, 255, 217))
    try:
        f = ImageFont.truetype('arial.ttf', int(10 * 1.1 * sy))
    except Exception:
        f = ImageFont.load_default()
    s = comp_name + text_suffix
    w = d.textlength(s, font=f)
    ly = 1080 - 138 * sy
    d.text((right - w, ly - int(10 * 1.1 * sy)), s, font=f, fill=(255, 255, 255, 217))


def render(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rp.SCALE = K
    missing, frames = set(), []
    for name, comp, steps, caption in STATES:
        L, plate, reel = runtime()   # a fresh pair per state: the tween clock starts at 0
        g = L.globals()
        g.NOTIFY('tod_ptn_items', L.table(CHIPS[0], CHIPS[1], CHIPS[2], comp))
        for ev, ms in steps:
            g.NOTIFY('tod_ptn_hud', L.table(*ev))
            g.ADVANCE(ms)
        items = [img_item(*x) for x in LOADOUT]
        items += [dict(x) for x in g.DUMP(plate).values()] + [dict(x) for x in g.DUMP(reel).values()]
        for it in items:
            if it['img'] and it['img'] != '$white' and rp.find_image(it['img']) is None:
                missing.add(it['img'])
        fr = rp.draw(items, backdrop())
        ImageDraw.Draw(fr).text((24, 1040), 'TodCompanionPlate.lua + TodSpinReel.lua chips, 1080p  state: %s - %s'
                                % (name, caption), fill=(255, 255, 255, 220))
        path = os.path.join(out_dir, 'hud_plate_%s.png' % name)
        fr.save(path)
        frames.append((name, caption, fr))
    # the OLD readout, for the before / after (online and rebuilding)
    olds = []
    for name, suffix, frac in (('online', '', 1.0), ('rebuilding', ' - REBUILDING', 22 / 45.0)):
        fr = backdrop()
        L = rp.draw([img_item(*x) for x in LOADOUT if x[0] != 'i_tod_hud_gun_skull'] +
                    [img_item('i_tod_hud_gun_skull', 1008, 632, 1104, 676)], fr)
        old_readout(L, 'TALON' if name == 'online' else 'R.A.P.S.', suffix, frac)
        olds.append(('OLD ' + name, L))
    # the contact sheet: the bottom-right of each 1080p frame at 1:1
    crop = (1360, 640, 1920, 1080)
    cw, ch = crop[2] - crop[0], crop[3] - crop[1]
    cells = [('OLD (hudelems) ' + n.split()[1], im.crop(crop)) for n, im in olds] + \
            [(n + ': ' + c, im.crop(crop)) for n, c, im in frames]
    cols = 3
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new('RGBA', (cols * (cw + 12) + 12, rows * (ch + 40) + 48), (24, 22, 32, 255))
    d = ImageDraw.Draw(sheet)
    d.text((12, 12), 'COMPANION STATUS PLATE at 1080p, 1:1 (bottom-right of the screen). First row: the OLD hudelem readout; '
                     'then every state of the new plate, rendered from the shipping Lua.', fill=(230, 230, 240, 255))
    for i, (label, im) in enumerate(cells):
        x, y = 12 + (i % cols) * (cw + 12), 48 + (i // cols) * (ch + 40)
        d.text((x, y), label[:96], fill=(200, 205, 220, 255))
        sheet.alpha_composite(im, (x, y + 18))
    sheet.save(os.path.join(out_dir, 'hud_plate_contact.png'))
    if missing:
        print('render_companion_plate: MISSING images (white squares in game): ' + ', '.join(sorted(missing)))
        return 1
    print('render_companion_plate: %d states -> %s (hud_plate_*.png, hud_plate_contact.png)' % (len(frames), out_dir))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    sys.exit(render(a.out))


if __name__ == '__main__':
    main()
