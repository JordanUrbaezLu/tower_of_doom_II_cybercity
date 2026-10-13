"""render_arena_hud.py - SEE the Battle Arena's readout (docs/185 v2.1 / v2.2) the way the game draws it.

Runs the REAL TodArena.lua (+ TodGlyphText / TodGlyphRow / the generated metrics) under the timed
LUI mock (mock_lui_anim.lua), drives it with the exact events _tod_arena.gsc sends -
    tod_arena ( show, level, levels, wave, waves, left, flags )
- advances the clock through the tweens, and draws each state with the shipped typeface over the
arena's own review render (art/battle_arena/review/arrival.png / pit.png). The HUD V2 status plate's
badge cluster is drawn with it (v2.2): the GENERATED arena badge where the round badge sits, the level
number laid out by the real TodGlyphRow with tod_upgrade.lua's own arithmetic, the luck plate beside it.

  python tools/ui_mockup/render_arena_hud.py            # -> art/battle_arena/review/hud_*.png + hud_contact.png
  python tools/ui_mockup/render_arena_hud.py --out DIR  # somewhere else

An approximation (linear tweens, no bloom), not a pixel match: it answers layout, size, colour and
the flash / tick choreography, which is what a readout is judged on.
"""
import argparse, os, re, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import render_pull  # noqa: E402  (its draw(): the typeface images, colour, alpha, alignment)
import lupa.lua51 as lua51  # noqa: E402

if not hasattr(render_pull, 'ART_DIR'):
    render_pull.ART_DIR = None
REVIEW = os.path.join(REPO, 'art', 'battle_arena', 'review')
PLATE_LUA = os.path.join(REPO, 'ui', 'uieditor', 'menus', 'hud', 'tod_upgrade.lua')

# LOCKSTEP _tod_arena.gsc TOD_ARENA_HUD_* (the gate checks the Lua against the GSC; this mirrors the Lua)
WAVE, CLEARED, BOSS, LEVEL = 1, 2, 4, 8

# name -> (backdrop, [ (event, advance_ms) ... ])  the last state is what is drawn
STATES = [
    ('breath',   'arrival', [((1, 3, 10, 0, 3, 0, 0), 300)]),
    ('wave_in',  'pit',     [((1, 3, 10, 0, 3, 0, 0), 300), ((1, 3, 10, 1, 3, 12, WAVE), 40)]),      # mid-flash
    ('wave',     'pit',     [((1, 3, 10, 0, 3, 0, 0), 300), ((1, 3, 10, 1, 3, 12, WAVE), 700)]),     # settled
    ('hot',      'pit',     [((1, 3, 10, 1, 3, 12, WAVE), 700), ((1, 3, 10, 1, 3, 3, 0), 250)]),
    ('cleared',  'pit',     [((1, 3, 10, 1, 3, 1, 0), 300), ((1, 3, 10, 1, 3, 0, CLEARED), 700)]),
    ('keeper',   'pit',     [((1, 10, 10, 3, 3, 9, WAVE), 700), ((1, 10, 10, 3, 3, 9, BOSS), 300)]),
    ('level',    'pit',     [((1, 7, 10, 3, 3, 1, 0), 300), ((1, 7, 10, 3, 3, 0, LEVEL), 700)]),
]

# the status plate's cluster, as tod_upgrade.lua places it (canvas): the badge, the luck plate, ten segments
BADGE = (16, 10, 88, 82)
PLATE = (94, 16, 330, 76)
SEG_Y = (52, 64)


def plate_numbers():
    """tod_upgrade.lua's own TOD_ARENA_NUM_CAP / _BASE (the level's cap and baseline), read from the source."""
    m = re.search(r'local TOD_ARENA_NUM_CAP, TOD_ARENA_NUM_BASE = ([\d.]+), ([\d.]+)', open(PLATE_LUA, encoding='utf-8').read())
    if not m:
        raise SystemExit('render_arena_hud: tod_upgrade.lua has no TOD_ARENA_NUM_CAP / _BASE')
    return float(m.group(1)), float(m.group(2))


def runtime():
    L = lua51.LuaRuntime(unpack_returned_tuples=True)
    os.chdir(REPO)
    L.execute(open(os.path.join(HERE, 'mock_lui_anim.lua'), encoding='utf-8').read())
    for f in ('TodUIOwnership', 'TodGlyphMetrics', 'TodGlyphRow', 'TodGlyphText', 'TodArena'):
        L.execute(open(os.path.join(REPO, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', f + '.lua'), encoding='utf-8').read())
    widget = L.eval('CoD.TodArena.new( nil, 0 )')
    cap, base = plate_numbers()
    # the badge's number row: the same pool, tint and arithmetic as tod_upgrade.lua paintRound2 in arena dress
    L.execute('''
        BADGE_HOST = LUI.UIElement.new()
        BADGE_ROW = CoD.TodGlyphRow.make( BADGE_HOST, 4 )
        BADGE_ROW.setRGB( 0.98, 0.11, 0.22 )
        function BADGE_LEVEL( n )
            local s, cap0, base = string.format( "%%d", n ), %f, %f
            local cap = cap0
            local w = BADGE_ROW.measure( s, cap, CoD.TodGlyphRow.digitSet )
            if w > 38 then cap = cap * 38 / w; w = 38 end
            BADGE_ROW.set( s, cap, 52 + w / 2, base - ( cap0 - cap ) / 2, CoD.TodGlyphRow.digitSet )
        end
    ''' % (cap, base))
    return L, widget


def img_item(name, x0, y0, x1, y1):
    return dict(img=name, x0=x0, y0=y0, x1=x1, y1=y1, r=1.0, g=1.0, b=1.0, a=1.0, zrot=0.0)


def cluster_items(L, g, level):
    items = [img_item('i_tod_h2_luck_plate', *PLATE), img_item('i_tod_h2_arena_badge', *BADGE)]
    for i in range(1, 11):
        x = 110 + (i - 1) * 21 + 1
        items.append(img_item('i_tod_h2_luck_off', x, SEG_Y[0], x + 19, SEG_Y[1]))
    g.BADGE_LEVEL(level)
    items += [dict(x) for x in g.DUMP(g.BADGE_HOST).values()]
    return items


def backdrop(name):
    p = os.path.join(REVIEW, name + '.png')
    if os.path.exists(p):
        return Image.open(p).convert('RGBA').resize((1280, 720), Image.LANCZOS)
    return Image.new('RGBA', (1280, 720), (18, 10, 12, 255))


def render(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    frames = []
    missing = set()
    for name, bg, steps in STATES:
        L, widget = runtime()   # a fresh widget per state: the tween clock starts at 0
        g = L.globals()
        for ev, ms in steps:
            g.NOTIFY('tod_arena', L.table(*ev))
            g.ADVANCE(ms)
        level = steps[-1][0][1]
        items = cluster_items(L, g, level) + [dict(x) for x in g.DUMP(widget).values()]
        for it in items:
            if it['img'] and it['img'] != '$white' and render_pull.find_image(it['img']) is None:
                missing.add(it['img'])
        fr = render_pull.draw(items, backdrop(bg))
        ImageDraw.Draw(fr).text((16, 696), 'TodArena.lua + the round badge  state: ' + name, fill=(255, 255, 255, 200))
        fr.convert('RGB').save(os.path.join(out_dir, 'hud_%s.png' % name))
        frames.append((name, fr))
        print('wrote', os.path.join(out_dir, 'hud_%s.png' % name), '(%d drawn elements)' % len(items))
    cw, ch = 640, 360
    cols = 2
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new('RGB', (cw * cols, ch * rows), (0, 0, 0))
    for i, (name, fr) in enumerate(frames):
        sheet.paste(fr.convert('RGB').resize((cw, ch), Image.LANCZOS), ((i % cols) * cw, (i // cols) * ch))
    sheet.save(os.path.join(out_dir, 'hud_contact.png'))
    print('wrote', os.path.join(out_dir, 'hud_contact.png'))
    # the badge corner at 1080p (x1.5), the size the player reads it at
    corner = frames[0][1].crop((0, 0, 340, 100)).resize((510, 150), Image.LANCZOS)
    corner.convert('RGB').save(os.path.join(out_dir, 'hud_badge_corner_1080p.png'))
    print('wrote', os.path.join(out_dir, 'hud_badge_corner_1080p.png'))
    if missing:
        print('MISSING IMAGES (drawn as magenta boxes):', ', '.join(sorted(missing)))
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=REVIEW)
    a = ap.parse_args()
    sys.exit(render(a.out))


if __name__ == '__main__':
    main()
