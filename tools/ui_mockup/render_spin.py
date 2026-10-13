"""render_spin.py - SEE the Black Market spin (docs/188) the way the game draws it.

Runs the REAL TodSpinReel.lua under the timed LUI mock (mock_lui_anim.lua) and replays
_tod_shop.gsc's exact event schedule into the reel's scriptNotify subscription: the open,
the 30 reel steps on their cubic slow-down (+ the LEGENDARY hitch), the landing, the slot
row, the choice / socket / scrap, the read, the close. Tweens are interpolated and their
completion handlers fire on time, so every chain the reel runs really runs.

  python tools/ui_mockup/render_spin.py                          # EPIC PLATING into an empty slot
  python tools/ui_mockup/render_spin.py --rar 3 --item 5         # LEGENDARY NANO REPAIR
  python tools/ui_mockup/render_spin.py --slots 5,26,33 --scrap  # full slots: choose SCRAP
  python tools/ui_mockup/render_spin.py --slots 5,26,0 --item 6  # ARC CHAIN upgrades slot 2
  python tools/ui_mockup/render_spin.py --rar 1 --near short      # THE NEAR MISS (docs/201): STOPPED SHORT on a LEGENDARY
  python tools/ui_mockup/render_spin.py --rar 0 --near past       # SLIPPED PAST: the reel creeps across a LEGENDARY
  python tools/ui_mockup/render_spin.py --heat 3 --heat-after 0   # THE HOT STREAK: rolled ON FIRE, the streak ends on it
  python tools/ui_mockup/render_spin.py --gift 1                   # THE DEALER'S GIFT (docs/209): the reel gives a TALON

A packed tile / slot is item * 4 + rarity (item 1..9 PLATING OVERCLOCK HOLLOW-POINT
LONG-SIGHT NANO-REPAIR ARC-CHAIN SALVAGE QUICK-REBOOT LUCKY-CHARM, rarity 0..3).
Writes tmp/ui_mockup/spin/<name>/frame_*.png, contact.png and reveal.gif.
An approximation (linear tweens, no blend modes), not a pixel match: it answers layout,
colour, choreography and timing.
"""
import argparse
import os
import sys

from PIL import Image
import lupa.lua51 as lua51

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_pull as rp   # noqa: E402  (draw, backdrop, find_image)

REPO = rp.REPO
W = os.path.join(REPO, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets')

# LOCKSTEP with _tod_shop.gsc (TOD_SPIN_* and the waits in spin())
STEPS, MIN_MS, MAX_MS, LEG_HITCH = 30, 50, 700, 850
NEAR_HANG, PAST_HOLD = 400, 850          # THE NEAR MISS (docs/201): TOD_SPIN_NEAR_HANG_MS / TOD_SPIN_PAST_HOLD_MS
STREAK_FB = 1.3                          # TOD_SPIN_STREAK_FB_SECS: the streak's change reaches the HUD this long after the land
OPEN_WAIT, LAND_WAIT, READ_SECS = 0.95, 1.0, 1.4   # OPEN_WAIT = TOD_SPIN_POUR_SECS (the slam + the luck pour)
REFUND = [10, 20, 35, 50]
# THE DEALER'S GIFT (docs/209; LOCKSTEP _tod_shop.gsc TOD_GIFT_* and the waits in gift())
GIFT_MAX = 450                           # TOD_GIFT_STEP_MAX_MS
GIFT_BASE, GIFT_CODE, GIFT_SLOTS, GIFT_POOL = 44, 8, 4, 5   # TOD_GIFT_TILE_BASE / _CODE_GIFT / _SLOTS_MODE / _POOL_MODE
GIFT_OPEN, GIFT_READ = 0.5, 3.2


def step_ms(k, rar, nkind=0):
    t = (k - 1) / float(STEPS - 1)
    ms = MIN_MS + (MAX_MS - MIN_MS) * t * t * t
    if k == STEPS:
        if rar == 3:
            ms += LEG_HITCH
        elif nkind == 1:
            ms += NEAR_HANG
        elif nkind == 2:
            ms += PAST_HOLD
    ms = int(ms / 50 + 0.5) * 50
    return max(ms, 50)


def gift_step_ms(k):
    t = (k - 1) / float(STEPS - 1)
    ms = MIN_MS + (GIFT_MAX - MIN_MS) * t * t * t
    ms = int(ms / 50 + 0.5) * 50
    return max(ms, 50)


def gift_schedule(seed, comp, luck):
    """-> [(t_seconds, event, [args])], end time. Mirrors _tod_shop.gsc gift(): no luck pour, a companion reel,
    the landing with the gift code, the companion handed over (tod_ptn_items), its three empty slots, the read.
    comp = 0..3 (CIVIL PROTECTOR, TALON, R.A.P.S., CERBERUS)."""
    prize = GIFT_BASE + comp + 1
    ev = [(0.0, 'tod_ptn_items', [0, 0, 0, 0]),                     # he has no companion yet
          (0.0, 'tod_spin_open', [seed, prize, 0, luck * 64 + STEPS]),
          (0.0, 'tod_spin_slots', [0, 0, 0, GIFT_POOL])]                # THE POOL rides the open (spin_open)
    t = GIFT_OPEN
    for k in range(1, STEPS + 1):
        ms = gift_step_ms(k)
        ev.append((t, 'tod_spin_step', [k, ms]))
        t += ms / 1000.0
    ev.append((t, 'tod_spin_land', [prize, GIFT_CODE]))
    ev.append((t, 'tod_ptn_items', [0, 0, 0, comp + 1]))           # _tod_partners gift_companion -> push_items
    ev.append((t, 'tod_spin_slots', [0, 0, 0, GIFT_SLOTS]))
    t += GIFT_READ
    ev.append((t, 'tod_spin_end', [0]))
    return ev, t


def schedule(seed, item, rar, luck, slots, tease, scrap, comp, nkind=0, heat=0, heat_after=None):
    """-> [(t_seconds, event, [args])], end time. Mirrors _tod_shop.gsc spin(). tease = the teased tile (item * 4 +
    rarity); nkind 1 STOPPED SHORT / 2 SLIPPED PAST packs it with the heat as the server does (docs/201)."""
    prize = item * 4 + rar
    packed = heat * 256 + (nkind * 64 + tease if tease else 0)
    ev = [(0.0, 'tod_ptn_items', list(slots) + [comp + 1]),          # the loadout push (_tod_partners push_items)
          (0.0, 'tod_spin_open', [seed, prize, packed, luck * 64 + STEPS]),
          (0.0, 'tod_spin_slots', list(slots) + [0])]                  # spin_open sends the slots with the open (pass 3)
    t = OPEN_WAIT
    for k in range(1, STEPS + 1):
        ms = step_ms(k, rar, nkind)
        ev.append((t, 'tod_spin_step', [k, ms]))
        t += ms / 1000.0
    held = empty = -1
    for i in (2, 1, 0):
        if slots[i] == 0:
            empty = i
        elif slots[i] // 4 == item:
            held = i
    code = 2 if held >= 0 else (1 if empty >= 0 else 3)
    ev.append((t, 'tod_spin_land', [prize, code]))
    ev.append((t, 'tod_spin_slots', list(slots) + [0]))
    if heat_after is not None:                                       # THE HOT STREAK: the spin's result moves it
        ev.append((t + STREAK_FB, 'tod_luck_heat', [heat_after, 0, 1 if heat_after > heat else (2 if heat_after < heat else 0)]))
    t += LAND_WAIT
    idx = held if code == 2 else empty
    if code == 3:
        weakest = min(range(3), key=lambda i: slots[i] % 4)
        focus = 3 if scrap else weakest
        idx = -1 if scrap else weakest
        t += 0.8   # the choice grace + a moment to read
        for h in range(0, 11):
            ev.append((t + h * 0.05, 'tod_spin_slots', list(slots) + [h * 100 + focus * 10 + 1]))
        t += 0.6
    if idx >= 0:
        new = list(slots)
        new[idx] = prize
        ev.append((t, 'tod_spin_slots', new + [idx * 10 + 2]))
    else:
        ev.append((t, 'tod_spin_slots', list(slots) + [REFUND[rar] * 100 + 30 + 3]))
    t += READ_SECS
    ev.append((t, 'tod_spin_end', [0]))
    return ev, t


def runtime():
    L = lua51.LuaRuntime(unpack_returned_tuples=True)
    os.chdir(REPO)
    L.execute(open(os.path.join(REPO, 'tools', 'ui_mockup', 'mock_lui_anim.lua'), encoding='utf-8').read())
    for f in ('TodUIOwnership', 'TodHudVeil', 'TodCardArt', 'TodGlyphMetrics', 'TodGlyphRow', 'TodGlyphText', 'TodSpinReel'):
        p = os.path.join(W, f + '.lua')
        if os.path.exists(p):
            L.execute(open(p, encoding='utf-8').read())
    reel = L.eval('CoD.TodSpinReel.new( 0, 0 )')
    return L, reel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--item', type=int, default=1, help='1..9 (1 PLATING ... 9 LUCKY CHARM)')
    ap.add_argument('--rar', type=int, default=2, help='0 COMMON, 1 RARE, 2 EPIC, 3 LEGENDARY')
    ap.add_argument('--luck', type=int, default=80)
    ap.add_argument('--slots', default='0,0,0', help='the companion\'s three slots, packed item*4+rarity (0 = empty)')
    ap.add_argument('--tease', type=int, default=0, help='the teased tile, item*4+rarity (0 = none; --near picks a LEGENDARY one)')
    ap.add_argument('--near', choices=['short', 'past'], help='THE NEAR MISS (docs/201): STOPPED SHORT or SLIPPED PAST')
    ap.add_argument('--heat', type=int, default=0, help='THE HOT STREAK the spin rolls with, 0..3')
    ap.add_argument('--heat-after', type=int, default=None, help='the heat after the spin (the chip follows it)')
    ap.add_argument('--scrap', action='store_true', help='full slots: choose SCRAP instead of the weakest slot')
    ap.add_argument('--seed', type=int, default=4242)
    ap.add_argument('--comp', type=int, default=1, help='companion 0 CIVIL PROTECTOR, 1 TALON, 2 R.A.P.S., 3 CERBERUS')
    ap.add_argument('--fps', type=int, default=20)
    ap.add_argument('--name', default=None)
    ap.add_argument('--gift', type=int, default=None, help="THE DEALER'S GIFT (docs/209): the companion the reel gives, 0..3")
    a = ap.parse_args()
    slots = [int(x) for x in a.slots.split(',')]
    nkind = {'short': 1, 'past': 2}.get(a.near, 1 if a.tease else 0)
    tease = a.tease or ((a.item % 9 + 1) * 4 + 3 if nkind else 0)   # a LEGENDARY of the next item by default
    if a.gift is not None:
        ev, end = gift_schedule(a.seed, a.gift, a.luck)
        name = a.name or ('gift_%s' % ['protector', 'talon', 'raps', 'cerberus'][a.gift])
    else:
        ev, end = schedule(a.seed, a.item, a.rar, a.luck, slots, tease, a.scrap, a.comp, nkind, a.heat, a.heat_after)
        name = a.name or ('spin_%s_item%d%s%s' % (['common', 'rare', 'epic', 'legendary'][a.rar], a.item,
                                                 ('_' + a.near) if a.near else '', ('_heat%d' % a.heat) if a.heat else ''))
    end += 0.6
    out = os.path.join(REPO, 'tmp', 'ui_mockup', 'spin', name)
    os.makedirs(out, exist_ok=True)
    L, reel = runtime()
    g = L.globals()
    bg = rp.backdrop()
    frames = []
    step = 1.0 / a.fps
    t, evi, n = 0.0, 0, 0
    while t <= end + 1e-6:
        while evi < len(ev) and ev[evi][0] <= t + 1e-6:
            et, name_, args = ev[evi]
            g.ADVANCE(max(0, et * 1000 - g.NOW))
            g.NOTIFY(name_, L.table(*args))
            evi += 1
        g.ADVANCE(max(0, t * 1000 - g.NOW))
        items = [dict(x) for x in g.DUMP(reel).values()]
        fr = rp.draw(items, bg)
        frames.append(fr)
        fr.convert('RGB').save(os.path.join(out, 'frame_%03d.png' % n))
        n += 1
        t += step
    pick = [frames[int(i * (len(frames) - 1) / 11)] for i in range(12)]
    cw, chh = 640, 360
    sheet = Image.new('RGB', (cw * 3, chh * 4))
    for i, fr in enumerate(pick):
        sheet.paste(fr.convert('RGB').resize((cw, chh)), ((i % 3) * cw, (i // 3) * chh))
    sheet.save(os.path.join(out, 'contact.png'))
    gif = [fr.convert('RGB').resize((640, 360)) for fr in frames]
    gif[0].save(os.path.join(out, 'reveal.gif'), save_all=True, append_images=gif[1:], duration=int(1000 / a.fps), loop=0)
    print('%s: %d frames over %.2f s -> %s' % (name, len(frames), end, os.path.relpath(out, REPO)))


if __name__ == '__main__':
    main()
