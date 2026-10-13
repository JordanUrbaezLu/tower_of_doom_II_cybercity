"""render_pull.py - SEE the upgrade card reveal (THE PULL, docs/187) the way the game draws it.

Runs the REAL tod_upgrade.lua + TodPull.lua under a TIMED LUI mock (mock_lui_anim.lua):
the server's exact beat schedule (_tod_upgrade_ui.gsc reveal_deal / reveal_slot) is
replayed into the models, tweens are interpolated, their completion handlers fire on
time, and frames are drawn with the shipped art over an in-game sky backdrop.

  python tools/ui_mockup/render_pull.py                 # today's installed art
  python tools/ui_mockup/render_pull.py --v2            # + placeholder card-v2 layers
  python tools/ui_mockup/render_pull.py --deal 4:4,3:1  # slot A LUCK LEGENDARY, B BOUNTY COMMON
  python tools/ui_mockup/render_pull.py --art-dir <unzipped drop> --name drop   # a DROP, before installing it
  python tools/ui_mockup/render_pull.py --class 4       # as a Warrior (CoD.TodClass; 2 = Archer, the mock's default)
  python tools/ui_mockup/render_pull.py --deal 6:2:1,3:1 --reach A:fail   # THE REACH (docs/201): A strains for EPIC, SO CLOSE
  python tools/ui_mockup/render_pull.py --deal 6:4:1,3:1 --reach A:win    # BREAK THROUGH: A crashes on into LEGENDARY
  python tools/ui_mockup/render_pull.py --heat 2 --heat-after 3           # THE HOT STREAK: dealt HEATING UP, it goes ON FIRE

Writes tmp/ui_mockup/pull/<mode>/frame_*.png, contact.png and reveal.gif.
An approximation (linear tweens, no blend modes), not a pixel match: it answers
layout, colour, choreography and timing, which is what a reveal is judged on.
"""
import argparse, math, os, sys
from PIL import Image, ImageDraw, ImageFilter
import lupa.lua51 as lua51

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMG_DIR = os.path.join(REPO, 'source_data', 'tod_ui_images', '_images')
PH_DIR = os.path.join(REPO, 'tmp', 'ui_mockup', 'placeholder_card2')
BACKDROP = os.path.join(REPO, 'docs', 'sky_preview', 'evil_ingame_city.png')
SCALE = 1

# ---- the server's schedule (seconds) - LOCKSTEP with _tod_upgrade_ui.gsc TOD_PULL_* ----
OPEN, HITCH, TAIL = 0.38, 0.19, 0.25
RUNG = {1: 0.44, 2: 0.48, 3: 0.58, 4: 0.82}
BEAT = {1: 0.26, 2: 0.40, 3: 0.65, 4: 1.00}
REACH, REACH_SETTLE = 0.62, 0.26   # TOD_PULL_REACH / TOD_PULL_REACH_SETTLE (docs/201 section 4)
STREAK_FB_DEAL = 0.15              # TOD_STREAK_FB_DEAL: present_choice's streak report lands this long after the reveal


def schedule(a, b, reach=None):
    """a, b = (dom, rar, cur) or None; reach = (slot 'A' / 'B', win) or None. -> [(t_seconds, field, value)]
    Mirrors reveal_deal / reveal_slot: a REACH is a second todUpgHold beat at the same rung; a BREAK THROUGH resolves
    with the next climb, a SO CLOSE with a third beat at that rung (then the flip)."""
    ev = []
    t = 0.0
    solo = 0 if b else 1
    for f, v in (('todUpgAD', 0), ('todUpgAR', 0), ('todUpgAL', a[2]), ('todUpgBD', 0), ('todUpgBR', 0),
                 ('todUpgBL', b[2] if b else 0), ('todUpgSolo', solo), ('todUpgLuck', 3), ('todUpgFocus', 0),
                 ('todUpgTime', 15), ('todUpgHold', 0), ('todUpgShow', 1)):
        ev.append((t, f, v))
    t += OPEN
    beat = [0]

    def pull_beat():
        beat[0] += 1
        ev.append((t, 'todUpgHold', beat[0]))

    for slot, card in (('A', a), ('B', b)):
        if not card:
            continue
        dom, rar, cur = card
        reach_at, reach_win = 0, False
        if reach and reach[0] == slot:
            reach_win = reach[1]
            reach_at = rar - 1 if reach_win else rar
        for k in range(1, rar + 1):
            if k == 1:
                pull_beat()
            else:
                ev.append((t, 'todUpg%sR' % slot, k - 1))
            t += RUNG[k] - HITCH
            pull_beat()
            if k == reach_at:
                t += HITCH            # the plain thump, then the REACH beat and the swell
                pull_beat()
                t += REACH
                if reach_win:
                    continue          # BREAK THROUGH: the next rung's push resolves it
                pull_beat()           # SO CLOSE: the third beat at this rung, the sag, then the flip
                t += REACH_SETTLE + HITCH
                continue
            t += HITCH
        ev.append((t, 'todUpg%sD' % slot, dom))
        t += BEAT[rar]
    t += TAIL
    ev.append((t, 'todUpgHold', 0))
    ev.append((t, 'todUpgFocus', 1))
    assert beat[0] <= 15, 'todUpgHold is 4 bits: this deal needs %d beats' % beat[0]
    return ev, t


# ---- drawing ------------------------------------------------------------------------
_cache = {}
_sized = {}         # (name, w, h) -> resized image: most frames reuse the same sizes
ART_DIR = None      # --art-dir: an unzipped art drop, searched FIRST (preview a drop before installing it)


def find_image(name):
    if name in _cache:
        return _cache[name]
    hit = None
    for d in ([ART_DIR] if ART_DIR else []) + [IMG_DIR, PH_DIR]:
        p = os.path.join(d, name + '.png')
        if os.path.exists(p):
            hit = Image.open(p).convert('RGBA')
            break
    _cache[name] = hit
    return hit


FONT = os.path.join(REPO, 'fonts', 'tod_tower1.ttf')
_fonts = {}


def draw_text(canvas, it):
    """A plain LUI.UIText (bind tokens shown as [KEY], colour codes dropped), in the map's TTF."""
    import re
    from PIL import ImageFont
    s = re.sub(r'\^\d', '', it['text'])
    s = re.sub(r'\[\{\+([a-z_]+)\}\]', lambda m: '[' + m.group(1).upper() + ']', s)
    x0, y0, x1, y1 = [v * SCALE for v in (it['x0'], it['y0'], it['x1'], it['y1'])]
    size = max(6, int((y1 - y0) * 0.8))
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size) if os.path.exists(FONT) else ImageFont.load_default()
    f = _fonts[size]
    d = ImageDraw.Draw(canvas)
    w = d.textlength(s, font=f)
    x = {'center': (x0 + x1 - w) / 2, 'right': x1 - w}.get(it.get('align', 'left'), x0)
    col = tuple(int(255 * max(0.0, min(1.0, c))) for c in (it['r'], it['g'], it['b'])) + (int(255 * max(0.0, min(1.0, it['a']))),)
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((x, y0 + (y1 - y0 - size) / 2), s, fill=col, font=f)
    canvas.alpha_composite(layer)


def draw(items, backdrop):
    canvas = backdrop.copy()
    for it in items:
        x0, y0, x1, y1 = [v * SCALE for v in (it['x0'], it['y0'], it['x1'], it['y1'])]
        w, h = int(round(x1 - x0)), int(round(y1 - y0))
        if w > 0 and h > 0 and not it['img'] and it.get('text'):
            draw_text(canvas, it)
            continue
        if w <= 0 or h <= 0 or not it['img']:
            continue
        r, g, b, a = it['r'], it['g'], it['b'], it['a']
        if it['img'] == '$white':
            im = Image.new('RGBA', (w, h), (255, 255, 255, 255))
        else:
            src = find_image(it['img'])
            if src is None:
                ImageDraw.Draw(canvas).rectangle([x0, y0, x1, y1], outline=(255, 0, 255, 255), width=1)
                continue
            key = (it['img'], w, h)
            im = _sized.get(key)
            if im is None:
                im = src.resize((w, h), Image.BILINEAR)
                if len(_sized) > 4000:
                    _sized.clear()
                _sized[key] = im
        ch = im.split()
        f = lambda band, k: band.point(lambda v: int(v * max(0.0, min(1.0, k))))
        im = Image.merge('RGBA', (f(ch[0], r), f(ch[1], g), f(ch[2], b), f(ch[3], a)))
        if abs(it['zrot']) > 0.01:
            im = im.rotate(-it['zrot'], resample=Image.BILINEAR, expand=True)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            x0, y0 = cx - im.size[0] / 2, cy - im.size[1] / 2
        px, py = int(round(x0)), int(round(y0))
        if it.get('cx0') is not None:
            # clipped by a stencil ancestor (the Black Market reel window)
            c0, c1 = int(round(it['cx0'] * SCALE)), int(round(it['cx1'] * SCALE))
            d0, d1 = int(round(it['cy0'] * SCALE)), int(round(it['cy1'] * SCALE))
            l, t = max(px, c0), max(py, d0)
            r_, b_ = min(px + im.size[0], c1), min(py + im.size[1], d1)
            if r_ <= l or b_ <= t:
                continue
            im = im.crop((l - px, t - py, r_ - px, b_ - py))
            px, py = l, t
        if px >= canvas.size[0] or py >= canvas.size[1] or px + im.size[0] <= 0 or py + im.size[1] <= 0:
            continue
        if px < 0 or py < 0:
            im = im.crop((max(0, -px), max(0, -py), im.size[0], im.size[1]))
            px, py = max(0, px), max(0, py)
        canvas.alpha_composite(im, (px, py))
    return canvas


def backdrop():
    if os.path.exists(BACKDROP):
        bg = Image.open(BACKDROP).convert('RGBA').resize((1280 * SCALE, 720 * SCALE))
    else:
        bg = Image.new('RGBA', (1280 * SCALE, 720 * SCALE), (14, 12, 26, 255))
    return bg


# ---- placeholder card-v2 layers (layout proof until the docs/191 art lands) --------
RCOL = {'common': (233, 238, 245), 'rare': (58, 168, 255), 'epic': (181, 92, 255), 'legendary': (255, 194, 61)}


def make_placeholders():
    os.makedirs(PH_DIR, exist_ok=True)
    W, H = 768, 1152
    body = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=56, fill=(20, 26, 50, 255))
    d.rectangle([96, 176, 672, 624], fill=(0, 0, 0, 0))                     # the see-through window
    d.rectangle([90, 170, 678, 630], outline=(8, 10, 22, 255), width=6)
    d.rounded_rectangle([168, 656, 600, 724], radius=34, fill=(8, 10, 22, 255))
    d.rounded_rectangle([88, 752, 680, 972], radius=14, fill=(8, 11, 26, 255), outline=(60, 70, 110, 255), width=3)
    d.rounded_rectangle([184, 996, 584, 1068], radius=30, fill=(8, 11, 26, 255))
    d.ellipse([640 - 72, 576 - 72, 640 + 72, 576 + 72], fill=(8, 10, 22, 255))
    body.save(os.path.join(PH_DIR, 'i_tod_card2_body.png'))
    for i, (k, c) in enumerate(RCOL.items()):
        fr = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(fr)
        wdt = 14 + 5 * i
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=56, outline=c + (255,), width=wdt)
        d.rounded_rectangle([64, 36, 704, 148], radius=18, fill=c + (255,))
        d.rectangle([92, 172, 676, 628], outline=c + (255,), width=4)
        if i >= 1:
            for (x, y) in ((40, 40), (W - 40, 40), (40, H - 40), (W - 40, H - 40)):
                d.ellipse([x - 12 - 3 * i, y - 12 - 3 * i, x + 12 + 3 * i, y + 12 + 3 * i], fill=c + (255,))
        if i == 3:
            d.polygon([(384, 0), (430, 36), (338, 36)], fill=c + (255,))
        fr.save(os.path.join(PH_DIR, 'i_tod_card2_frame_%s.png' % k))
        cr = Image.new('RGBA', (144, 144), (0, 0, 0, 0))
        d = ImageDraw.Draw(cr)
        d.polygon([(72, 8), (136, 72), (72, 136), (8, 72)], fill=c + (255,), outline=(255, 255, 255, 255))
        cr.save(os.path.join(PH_DIR, 'i_tod_card2_crest_%s.png' % k))
    back = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(back)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=56, fill=(24, 24, 32, 255), outline=(170, 175, 190, 255), width=10)
    d.rectangle([370, 300, 398, 800], fill=(150, 155, 170, 255))
    d.ellipse([234, 400, 534, 700], outline=(150, 155, 170, 255), width=8)
    back.save(os.path.join(PH_DIR, 'i_tod_card_back.png'))
    ban = Image.new('RGBA', (1024, 192), (0, 0, 0, 0))
    d = ImageDraw.Draw(ban)
    d.polygon([(0, 20), (1024, 20), (980, 96), (1024, 172), (0, 172), (44, 96)], fill=(235, 235, 240, 255))
    d.rectangle([60, 50, 964, 142], fill=(200, 200, 210, 255))
    ban.save(os.path.join(PH_DIR, 'i_tod_pull_banner.png'))
    # illustrations: crops of today's cards where they exist, a labelled tile otherwise
    crops = {'dmg_reduction': 'dmg_reduction', 'bounty': 'bounty', 'luck': 'luck', 'grapple': 'grapple', 'retriever': 'retriever'}
    for slug in ('dmg_reduction', 'bounty', 'luck', 'deadeye', 'piercing', 'sprint', 'quick_draw', 'grapple', 'retriever'):
        p = os.path.join(IMG_DIR, 'i_tod_card_%s_regular.png' % crops.get(slug, 'xx'))
        if os.path.exists(p):
            im = Image.open(p).convert('RGBA').crop((132, 226, 636, 606)).resize((576, 448))
        else:
            im = Image.new('RGBA', (576, 448), (20, 40, 90, 255))
            ImageDraw.Draw(im).text((200, 210), slug.upper(), fill=(255, 255, 255, 255))
        im.save(os.path.join(PH_DIR, 'i_tod_card2_art_%s.png' % slug))
    for t in (2, 3):
        p = os.path.join(IMG_DIR, 'i_tod_card_tier_assault_%d.png' % t)
        if os.path.exists(p):   # R5: the old tier cards left with the Map 1 purge
            im = Image.open(p).convert('RGBA').crop((100, 200, 668, 640)).resize((576, 448))
        else:
            im = Image.new('RGBA', (576, 448), (20, 40, 90, 255))
            ImageDraw.Draw(im).text((200, 210), 'TIER %d' % t, fill=(255, 255, 255, 255))
        im.save(os.path.join(PH_DIR, 'i_tod_card2_art_tier_assault_%d.png' % t))


V2_MANIFEST = '''
local fx = CoD.TodCardArt and CoD.TodCardArt.fx or {}
CoD.TodCardArt = {
    fx = fx,
    body = "i_tod_card2_body", back = "i_tod_card_back", banner = "i_tod_pull_banner",
    frame = { "i_tod_card2_frame_common", "i_tod_card2_frame_rare", "i_tod_card2_frame_epic", "i_tod_card2_frame_legendary" },
    crest = { "i_tod_card2_crest_common", "i_tod_card2_crest_rare", "i_tod_card2_crest_epic", "i_tod_card2_crest_legendary" },
    art = { [2] = "i_tod_card2_art_dmg_reduction", [3] = "i_tod_card2_art_bounty", [4] = "i_tod_card2_art_luck",
            [6] = "i_tod_card2_art_deadeye", [26] = "i_tod_card2_art_piercing", [29] = "i_tod_card2_art_sprint",
            [35] = "i_tod_card2_art_quick_draw", [41] = "i_tod_card2_art_grapple", [57] = "i_tod_card2_art_retriever" },
    tier = { assault = { [2] = "i_tod_card2_art_tier_assault_2", [3] = "i_tod_card2_art_tier_assault_3" } },
}
'''


def drop_manifest(art_dir):
    """The CoD.TodCardArt the installer WOULD generate if this drop were installed: every
    installer-known name present in the drop or already in _images (LOCKSTEP by import)."""
    sys.path.insert(0, os.path.join(REPO, 'tools', 'card_pull'))
    import install_card_art as ica
    have = []
    for n in ica.PACK_SIZES:
        if os.path.exists(os.path.join(art_dir, n + '.png')) or os.path.exists(os.path.join(IMG_DIR, n + '.png')):
            have.append(n)
    installed = sorted(ica.FX) + sorted(have)
    classes, _gaps = ica.v2_classes(installed, [])
    return ica.lua_manifest(installed, classes)


def runtime(v2, manifest=None, cls=None):
    L = lua51.LuaRuntime(unpack_returned_tuples=True)
    os.chdir(REPO)
    L.execute(open(os.path.join(REPO, 'tools', 'ui_mockup', 'mock_lui_anim.lua'), encoding='utf-8').read())
    if cls is not None:
        L.execute('CoD.TodClass = %d' % cls)
    # RT 2026-10-05: + TodKeycap, so the deal's caps draw through the real widget (they used tod_upgrade's stub)
    for f in ('TodUIOwnership', 'TodHudVeil', 'TodCardArt', 'TodGlyphMetrics', 'TodGlyphRow', 'TodKeycap'):
        L.execute(open(os.path.join(REPO, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', f + '.lua'), encoding='utf-8').read())
    if manifest:
        L.execute(manifest)
    elif v2:
        L.execute(V2_MANIFEST)
    L.execute(open(os.path.join(REPO, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodPull.lua'), encoding='utf-8').read())
    L.execute(open(os.path.join(REPO, 'ui', 'uieditor', 'menus', 'hud', 'tod_upgrade.lua'), encoding='utf-8', errors='replace').read())
    menu = L.eval('LUI.createMenu.tod_upgrade( 0 )')
    return L, menu


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--v2', action='store_true', help='draw placeholder card-v2 layers')
    ap.add_argument('--deal', default='4:4,3:2', help='dom:rar[:cur][,dom:rar[:cur]] (rar 1..4; cur = level held, default 2)')
    ap.add_argument('--fps', type=int, default=20)
    ap.add_argument('--art-dir', help='an unzipped art drop: its PNGs win, and the manifest is what installing it would give')
    ap.add_argument('--class', dest='cls', type=int, help='CoD.TodClass (1 Necromancer, 2 Archer, 3 Breacher, 4 Warrior)')
    ap.add_argument('--name', help='output folder name under tmp/ui_mockup/pull/')
    ap.add_argument('--reach', help='THE REACH (docs/201): A:fail | A:win | B:fail | B:win (SO CLOSE / BREAK THROUGH)')
    ap.add_argument('--heat', type=int, default=0, help='THE HOT STREAK the deal is rolled on, 0..3 (a tod_luck_heat refresh)')
    ap.add_argument('--heat-after', type=int, default=None, help='the heat the deal leaves (its report, after the reveal)')
    a = ap.parse_args()
    global ART_DIR
    manifest = None
    if a.art_dir:
        ART_DIR = os.path.abspath(a.art_dir)
        manifest = drop_manifest(ART_DIR)
    elif a.v2:
        make_placeholders()
    L, menu = runtime(a.v2, manifest, a.cls)
    g = L.globals()
    cards = []
    for i, part in enumerate(a.deal.split(',')):
        bits = [int(x) for x in part.split(':')]
        dom, rar = bits[0], bits[1]
        cur = bits[2] if len(bits) > 2 else 2    # the level held; for the TIER card (24) the tier code: (class-1)*2 + (tier-2)
        cards.append((dom, rar, cur))
    reach = None
    if a.reach:
        slot, kind = a.reach.upper().split(':')
        card = cards[0] if slot == 'A' else (cards[1] if len(cards) > 1 else None)
        if card is None or kind not in ('FAIL', 'WIN'):
            sys.exit('--reach wants A:fail, A:win, B:fail or B:win on a dealt slot')
        # reach_roll's own rules: a BREAK THROUGH needs a RARE+ (it climbs INTO the card's rarity), a SO CLOSE
        # cannot be a LEGENDARY (no rung above it) - and the server also needs the domain to have room for it
        if kind == 'WIN' and card[1] < 2:
            sys.exit('a BREAK THROUGH needs a RARE or better card (it climbs into the real rarity)')
        if kind == 'FAIL' and card[1] >= 4:
            sys.exit('a SO CLOSE cannot be a LEGENDARY: there is no rung above it')
        reach = (slot, kind == 'WIN')
    ev, end = schedule(cards[0], cards[1] if len(cards) > 1 else None, reach)
    # THE HOT STREAK rides the HUD menu's own tod_luck_heat handler (CoD.TodHeat + the luck plate + the panel line):
    # a refresh before the deal, and the deal's own report after the reveal
    ev.insert(0, (0.0, '!notify', ('tod_luck_heat', [a.heat, a.heat + 1 if a.heat else 0, 0])))
    if a.heat_after is not None:
        change = 1 if a.heat_after > a.heat else (2 if a.heat_after < a.heat else 0)
        ev.append((end + STREAK_FB_DEAL, '!notify', ('tod_luck_heat', [a.heat_after, a.heat_after + 1 if a.heat_after else 0, change])))
        ev.sort(key=lambda e: e[0])
    end += 1.6
    mode = a.name or ('drop' if a.art_dir else ('v2' if a.v2 else 'today'))
    if not a.name and (a.reach or a.heat or a.heat_after is not None):
        mode += ('_reach_' + a.reach.replace(':', '_').lower()) if a.reach else ''
        mode += ('_heat%d' % a.heat) if a.heat else ''
    out = os.path.join(REPO, 'tmp', 'ui_mockup', 'pull', mode)
    os.makedirs(out, exist_ok=True)
    bg = backdrop()
    frames = []
    step = 1.0 / a.fps
    t = 0.0
    evi = 0
    n = 0
    while t <= end + 1e-6:
        while evi < len(ev) and ev[evi][0] <= t + 1e-6:
            et, f, v = ev[evi]
            g.ADVANCE(max(0, et * 1000 - g.NOW))
            if f == '!notify':
                g.NOTIFY(v[0], L.table(*v[1]))
            else:
                g.PUSH(f, v)
            evi += 1
        g.ADVANCE(max(0, t * 1000 - g.NOW))
        items = [dict(x) for x in g.DUMP(menu).values()]
        fr = draw(items, bg)
        frames.append(fr)
        fr.convert('RGB').save(os.path.join(out, 'frame_%03d.png' % n))
        n += 1
        t += step
    # contact sheet: 12 evenly spaced frames
    pick = [frames[int(i * (len(frames) - 1) / 11)] for i in range(12)]
    cw, chh = 640, 360
    sheet = Image.new('RGB', (cw * 3, chh * 4))
    for i, fr in enumerate(pick):
        sheet.paste(fr.convert('RGB').resize((cw, chh)), ((i % 3) * cw, (i // 3) * chh))
    sheet.save(os.path.join(out, 'contact.png'))
    gif = [fr.convert('RGB').resize((640, 360)) for fr in frames]
    gif[0].save(os.path.join(out, 'reveal.gif'), save_all=True, append_images=gif[1:], duration=int(1000 / a.fps), loop=0)
    print('%s: %d frames over %.2f s -> %s' % (mode, len(frames), end, os.path.relpath(out, REPO)))


if __name__ == '__main__':
    main()
