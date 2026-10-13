"""render_menus.py - draw the pause menu (and the scoreboard) from the REAL LUI scripts.

2026-09-28 (user: "Spend some time designing these menus correctly cause its how players
get all their info"). Runs AetheriumStartMenu.lua / AetheriumScoreboard.lua under the
geometry-recording mock (mock_lui.lua, lupa Lua 5.1), then draws every element with the
shipped art (source_data/tod_ui_images/_images) and the map's TTF (fonts/tod_tower1.ttf)
on the 1280x720 canvas at 2x. Text that is wider than its box is outlined RED and listed:
the engine does not wrap or shrink a UIText, so an overflow in the render is an overflow
in the game.

  python tools/ui_mockup/render_menus.py            # every scenario -> tmp/ui_mockup/*.png
  python tools/ui_mockup/render_menus.py --check    # exit 1 on any text overflow

A LAYOUT proof, not a pixel match: no shader, blur or animation.
"""
import argparse, os, sys, glob
from PIL import Image, ImageDraw, ImageFont
import lupa.lua51 as lua51

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, 'tmp', 'ui_mockup')
SCALE = 2
IMG_DIRS = [os.path.join(REPO, 'source_data', 'tod_ui_images', '_images')]
FONT = os.path.join(REPO, 'fonts', 'tod_tower1.ttf')
_img_cache = {}


def find_image(name):
    if name in _img_cache:
        return _img_cache[name]
    hit = None
    for d in IMG_DIRS:
        p = os.path.join(d, name + '.png')
        if os.path.exists(p):
            hit = Image.open(p).convert('RGBA')
            break
    _img_cache[name] = hit
    return hit


def tint(im, r, g, b, a):
    if (r, g, b, a) == (1, 1, 1, 1):
        return im
    ch = im.split()
    mul = lambda band, f: band.point(lambda v: int(v * max(0.0, min(1.0, f))))
    return Image.merge('RGBA', (mul(ch[0], r), mul(ch[1], g), mul(ch[2], b), mul(ch[3], a)))


def draw(items, path, bg=(12, 13, 16)):
    W, H = 1280 * SCALE, 720 * SCALE
    canvas = Image.new('RGBA', (W, H), bg + (255,))
    over = []
    for it in items:
        x0, y0, x1, y1 = [v * SCALE for v in (it['x0'], it['y0'], it['x1'], it['y1'])]
        w, h = int(round(x1 - x0)), int(round(y1 - y0))
        if w <= 0 or h <= 0:
            continue
        if isinstance(it['img'], str) and it['img']:
            im = find_image(it['img'])
            if im is None:
                d = ImageDraw.Draw(canvas)
                d.rectangle([x0, y0, x1, y1], outline=(255, 0, 255, 255), width=2)
                continue
            im = tint(im.resize((w, h), Image.LANCZOS), it['r'], it['g'], it['b'], it['a'])
            canvas.alpha_composite(im, (int(round(x0)), int(round(y0))))
        if it['text'] not in ('', None):
            it['text'] = str(it['text'])
            size = max(4, int(round(h)))
            font = ImageFont.truetype(FONT, size)
            txt = it['text']
            tw = font.getlength(txt)
            layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            if it['align'] == 'right':
                tx = x1 - tw
            elif it['align'] == 'center':
                tx = (x0 + x1) / 2 - tw / 2
            else:
                tx = x0
            col = tuple(int(255 * max(0, min(1, c))) for c in (it['r'], it['g'], it['b'])) + (int(255 * it['a']),)
            d.text((tx, y0), txt, font=font, fill=col)
            canvas.alpha_composite(layer)
            if tw > (x1 - x0) + 1:
                over.append((txt, round(tw / SCALE, 1), round((x1 - x0) / SCALE, 1)))
                ImageDraw.Draw(canvas).rectangle([x0, y0, x1, y1], outline=(255, 40, 40, 255), width=2)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    canvas.convert('RGB').save(path)
    return over


def lua_runtime():
    L = lua51.LuaRuntime(unpack_returned_tuples=True)
    os.chdir(REPO)
    L.execute(open(os.path.join(REPO, 'tools', 'ui_mockup', 'mock_lui.lua'), encoding='utf-8').read())
    return L


def owned_table(L, rows):
    t = L.table()
    for id_, (lvl, mx, *rest) in rows.items():
        r = L.table()
        r['lvl'] = lvl
        r['max'] = mx
        if rest and rest[0]:
            r['dark'] = True
        t[id_] = r
    return t


# class id -> (key, the nine cards it holds in a fair mid-run spread)
CLASSES = {
    1: ('necromancer', {59: (6, 9), 38: (4, 9), 39: (9, 9), 5: (2, 9), 19: (3, 9), 9: (5, 9)}),
    2: ('archer', {29: (5, 9), 41: (9, 9), 6: (7, 9), 57: (3, 9), 35: (4, 9), 26: (1, 9)}),
    3: ('breacher', {25: (2, 9), 58: (9, 9), 60: (6, 9), 61: (4, 9), 36: (3, 9), 45: (5, 9)}),
    4: ('warrior', {37: (4, 9), 7: (9, 9), 62: (6, 9), 63: (2, 9), 48: (5, 9), 12: (3, 9)}),
}
SHARED = {2: (9, 9, True), 3: (4, 9), 4: (6, 9)}

# THE AI COMPANION ROW (2026-09-29): the state the HUD reel records from tod_ptn_items /
# tod_ptn_state (CoD.TodCompanion), one held companion per class for the 'full' renders -
# the worst cases on purpose: the longest name + destroyed + the three longest item names
# (necromancer), one item (archer), no items + on its way (breacher), three items (warrior).
# The 'early' renders hold nothing, with two built. A tile = item * 4 + rarity.
COMPANION = {
    1: 'CoD.TodCompanion = { comp = 1, items = { [1] = { 15, 34, 37 } }, state = 2, value = 45, built = 15 }',
    2: 'CoD.TodCompanion = { comp = 4, items = { [4] = { 4, 0, 0 } }, state = 1, value = 100, built = 8 }',
    3: 'CoD.TodCompanion = { comp = 2, items = { [2] = { 0, 0, 0 } }, state = 3, value = 0, built = 2 }',
    4: 'CoD.TodCompanion = { comp = 3, items = { [3] = { 21, 26, 9 } }, state = 1, value = 55, built = 4 }',
}
NO_COMPANION = 'CoD.TodCompanion = { comp = 0, items = {}, state = 0, value = 0, built = 5 }'


def load_companion(L, snippet):
    """The real TodSpinReel.lua defines CoD.TodCompanionDescribe / CoD.TodCompanionInfo."""
    L.execute(open(os.path.join(REPO, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodSpinReel.lua'),
                   encoding='utf-8', errors='replace').read())
    L.execute(snippet)


def pause_items(L, cls, owned, tier=2, companion=None):
    g = L.globals()
    load_companion(L, companion or NO_COMPANION)
    g.CoD.TodClass = cls
    g.CoD.TodClassTier = tier
    g.CoD.TodOwned = owned_table(L, owned)
    g.DataSources = L.table()
    src = open(os.path.join(REPO, 'ui', 'uieditor', 'menus', 'StartMenu', 'AetheriumStartMenu.lua'), encoding='utf-8', errors='replace').read()
    L.execute(src)
    menu = g.LUI.createMenu.StartMenu_Main(0)
    return [dict(x) for x in L.globals().DUMP(menu).values()]


def scoreboard_items(L, cls, owned, companion=None):
    g = L.globals()
    load_companion(L, companion or NO_COMPANION)
    g.CoD.TodClass = cls
    g.CoD.TodOwned = owned_table(L, owned)
    g.CoD.TodDomainInfo = g.CoD.TodDomainInfo
    src = open(os.path.join(REPO, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'AetheriumScoreboard.lua'), encoding='utf-8', errors='replace').read()
    L.execute(src)
    root = g.LUI.UIElement.new()
    sb = g.CoD.AetheriumScoreboard.new(root, 0)
    root.addElement(root, sb)
    cps = sb.clipsPerState
    for state in ('Visible',):
        st = cps[state] if cps else None
        if st and st.DefaultClip:
            st.DefaultClip()
    return [dict(x) for x in L.globals().DUMP(root).values()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    problems = []
    for cls, (key, cards) in CLASSES.items():
        for label, owned, comp in (('full', {**cards, **SHARED, 24: (2, 3)}, COMPANION[cls]),
                                   ('early', {k: v for k, v in list(cards.items())[:2]}, NO_COMPANION)):
            L = lua_runtime()
            items = pause_items(L, cls, owned, companion=comp)
            path = os.path.join(OUT, 'pause_%s_%s.png' % (key, label))
            over = draw(items, path)
            print('%-40s %d elements, %d overflow' % (os.path.relpath(path, REPO), len(items), len(over)))
            for o in over:
                print('   OVERFLOW %r needs %s of %s' % o)
            problems += over
        L = lua_runtime()
        try:
            items = scoreboard_items(L, cls, {**cards, **SHARED, 24: (2, 3)}, companion=COMPANION[cls])
            path = os.path.join(OUT, 'scoreboard_%s.png' % key)
            over = draw(items, path)
            print('%-40s %d elements, %d overflow' % (os.path.relpath(path, REPO), len(items), len(over)))
            for o in over:
                print('   OVERFLOW %r needs %s of %s' % o)
            problems += over
        except Exception as e:
            print('scoreboard %s: %s' % (key, e))
            problems.append(('scoreboard render failed: %s' % e, 0, 0))
    if a.check and problems:
        sys.exit(1)


if __name__ == '__main__':
    main()
