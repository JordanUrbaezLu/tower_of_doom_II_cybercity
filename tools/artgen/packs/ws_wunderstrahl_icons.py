"""ws_wunderstrahl_icons.py - THE WUNDERSTRAHL's two HUD icons (docs/219, 2026-10-05).

THE GAP: the laser power-up gun (the DG-2 remodelled, tools/wunderstrahl/model/) needs
  i_tod_pu2_wunderstrahl     the power-up TRAY token (AetheriumPowerupsContainer.lua row "tod_wunderstrahl"), 256 x 256:
                             THE ONE LIBRARY's glyph family - r4_synthwave_hud.py's power-up token, drawn THROUGH r4's
                             own renderer (powerup_icon: the octagon well, the hue tube, neon_glyph ink, the safe-inset
                             fit and its gate). r4 is imported read-only; its PU table and powerup_symbol are extended in
                             THIS process only, so r4's bytes and its --check are untouched. White-hot ink = the gun in
                             profile; the ONE hue accent = the beam leaving the lens with its swirl and two orbs.
                             Hue: the laser's own yellow #FFD640 (a literal identity hue, like a perk's: never themed).
  i_tod_hud_gun_wunderstrahl the gun-bay icon (AetheriumLoadout.lua TOD_GUN_CAT "tod2_wunderstrahl" / TOD_NAME_CAT
                             "WUNDERSTRAHL" -> slug "wunderstrahl"), 288 x 132: gun_bay_icons.py's family - three tones
                             (navy outline, slate shade, pale light), binary alpha, pointing right, drawn as outlined
                             Parts and rendered through gun_bay_icons.render (4x crisp, 4x4 majority) - so the output
                             can only hold the family's three colours.
The gun is the DG-2's silhouette as the Wunderstrahl keeps it (stock, receiver, the top coil + glass tube, the three
side bulbs, the copper cage barrel with its curled prongs) plus the new LENS ASSEMBLY at the muzzle (emitter rings and
the focusing crystal), drawn from the model renders in art/wunderstrahl/review/.

  python tools/artgen/packs/ws_wunderstrahl_icons.py                 render to art/generated/WS-wunderstrahl/ (+ _review.png)
  python tools/artgen/packs/ws_wunderstrahl_icons.py --install [--out-root DIR]
                                                                     LANDING: copy into <root>/source_data/tod_ui_images/_images
  python tools/artgen/packs/ws_wunderstrahl_icons.py --check [--out-root DIR]
                                                                     fail on stale bytes or missing wiring (GDT block, zone
                                                                     image line, the Lua rows)
"""
import argparse
import io
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import artgen  # noqa: E402
import gun_bay_icons as gb  # noqa: E402
import r4_synthwave_hud as r4  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = artgen.ROOT
PACK = 'WS-wunderstrahl'
OUT = os.path.join(ROOT, 'art', 'generated', PACK)
TRAY = 'i_tod_pu2_wunderstrahl'
GUN = 'i_tod_hud_gun_wunderstrahl'
IMAGES = [TRAY, GUN]
LASER = '#FFD640'           # the beam's core yellow (docs/219; the model's emissive, the effects' core)
NAVY, SHADE, LIGHT = gb.NAVY, gb.SHADE, gb.LIGHT
CY = gb.CY
path, rect, ell, line, fillp, dot, below, Part = gb.path, gb.rect, gb.ell, gb.line, gb.fillp, gb.dot, gb.below, gb.Part


# =========================================================================================== the gun-bay icon
def gun_parts():
    """The Wunderstrahl side-on, muzzle right, light from above (the lower band of every form in SHADE), traced from
    art/wunderstrahl/review/wunderstrahl_profile_left.png mirrored (x_icon = 6 + (1690 - x) * 0.177; the beam axis sits
    above the receiver's middle, at y ~58, as tag_flash does). Read left to right: the composite stock and its lever,
    the receiver with the copper ridge coil behind the glass filament tube on top and the three lit bulbs on its flank,
    the cooling fin blocks under it, the copper bellows coil, the cage of rods with the curled prongs, the three lens
    rings and the faceted crystal. Drawn chunkier than the model so it reads at 144 x 66 beside the class cells."""
    parts = []
    AX = 58.0                                     # the beam axis (tag_flash height on the icon)
    # STOCK + its lever grip
    stock = [(6, 57), (14, 55), (90, 58), (92, 73), (72, 77), (56, 85), (22, 89), (6, 91)]
    parts.append(Part(path(stock), below(CY + 8), line([(11, 56), (11, 90)], 3.0)))
    lever = [(78, 74), (91, 74), (95, 96), (85, 101), (79, 93)]
    parts.append(Part(path(lever), below(90)))
    # COOLING FIN BLOCKS under the receiver (drawn first: the receiver overlaps their tops)
    for x0, x1, y1 in ((104, 131, 99), (143, 180, 92)):
        ribs = ''.join(line([(x, 79), (x, y1 - 3)], 2.6, cap='butt') for x in range(x0 + 5, x1 - 2, 5))
        parts.append(Part(path(rect(x0, 74, x1, y1)), below(y1 - 7), ribs))
    # RECEIVER with the three lit bulbs on its flank
    body = [(88, 51), (176, 51), (181, 56), (181, 77), (88, 77)]
    bulbs = ''.join(dot(x, 65, 4.6, NAVY) + dot(x, 64.4, 2.9, LIGHT) for x in (110, 120, 130))
    parts.append(Part(path(body), below(CY + 6), bulbs))
    # THE TOP: the copper ridge coil behind, the glass tube with the lit filament in front
    coil = [(94, 42), (141, 42), (141, 51), (94, 51)]
    parts.append(Part(path(coil), None, ''.join(line([(x, 43), (x, 50)], 3.2, cap='butt') for x in range(99, 139, 6))))
    tube = [(141, 44), (168, 44), (172, 48), (168, 52), (141, 52)]
    tdet = fillp(path([(145, 46), (167, 46), (169, 48), (167, 50), (145, 50)]), SHADE) + line([(147, 48), (165, 48)], 3.2, LIGHT, cap='butt')
    parts.append(Part(path(tube), None, tdet))
    # THE COPPER BELLOWS COIL on the barrel's root
    bell = [(180, 49), (204, 49), (204, 68), (180, 68)]
    parts.append(Part(path(bell), below(AX + 4), ''.join(line([(x, 50), (x, 67)], 3.0, cap='butt') for x in range(184, 203, 5))))
    # THE CAGE: top and bottom rails and the core rod, out to the lens
    for y0, y1 in ((43, 51), (AX - 4, AX + 4), (65, 73)):      # 8 px each: a thinner rail is all outline at 0.5x
        parts.append(Part(path(rect(202, y0, 258, y1)), below(y1 - 3)))
    for sgn in (-1, 1):                           # the curled prongs: up / down off the cage, hooking back
        y = lambda v: AX + sgn * v                # noqa: E731
        prong = [(221, y(12)), (235, y(20)), (244, y(30)), (238, y(39)), (228, y(37)), (234, y(30)),
                 (229, y(24)), (215, y(18))]
        parts.append(Part(path(prong), None))
    # THE LENS: three emitter rings (big to small) and the faceted crystal
    for rx, ry in ((257, 18.0), (266, 15.0), (274, 12.0)):
        parts.append(Part(path(ell(rx, AX, 5.6, ry, 0, 360, 32)[:-1]), below(AX + 5)))
    crystal = [(275, AX - 9), (282, AX - 6), (286, AX), (282, AX + 6), (275, AX + 9)]
    cdet = fillp(path([(275, AX), (286, AX), (282, AX + 6), (275, AX + 9)]), SHADE)
    parts.append(Part(path(crystal), None, cdet))
    return parts


def gun_icon():
    return gb.render(gb.compose(gun_parts()))


# =========================================================================================== the tray token
def tray_symbol():
    """(white, accent, cut, extra) in r4's 256 token design space: the gun in profile, tilted up, the beam out of
    its lens toward the upper right, a swirl wound round the beam and two orbs riding it."""
    TILT = -9                                       # the gun aims a touch up: it reads as firing, not lying down
    R = lambda pts: r4.rot(pts, TILT, 128, 128)     # noqa: E731
    # the gun, muzzle right, across the token's middle (x 30..150): stock, receiver, the coil + glass top, the grip,
    # the cage barrel with its two tall rings (the DG-2's read), the lens
    stock = R([(30, 120), (36, 116), (66, 122), (74, 124), (74, 138), (64, 140), (52, 146), (36, 150), (30, 152)])
    body = R([(70, 118), (124, 118), (128, 123), (128, 140), (70, 140)])
    top = R([(74, 104), (122, 104), (127, 111), (122, 118), (74, 118)])
    grip = R([(72, 138), (84, 138), (88, 160), (78, 164), (72, 156)])
    cage = R([(126, 124), (150, 124), (150, 134), (126, 134)])
    ring1, ring2 = R([(131, 108), (138, 108), (138, 150), (131, 150)]), R([(142, 111), (148, 111), (148, 147), (142, 147)])
    lens = R([(150, 119), (158, 122), (162, 129), (158, 136), (150, 139)])
    white = ''.join(r4.P(p) for p in (stock, body, top, grip, cage, ring1, ring2, lens))
    cut = r4.ST(r4.poly_d(R([(84, 111), (118, 111)]), close=False), 5, cap='butt')     # the glass window's slot
    # THE BEAM (the accent): straight out of the lens to the right edge of the safe area, a sine swirl wound round it
    # and two orbs riding the swirl (the user's "laser down the middle ... swirls ... little balls on the swirls")
    x0, y0 = R([(165, 129)])[0]
    ang = math.radians(TILT)
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    L, A = 56.0, 12.0
    beam = r4.ST('M%.2f,%.2f L%.2f,%.2f' % (x0, y0, x0 + ux * L, y0 + uy * L), 12, cap='round')
    sw = []
    for i in range(61):
        t = i / 60.0
        off = A * math.sin(t * math.pi * 2.5) * min(1.0, t * 4.0)     # the swirl opens out of the lens
        sw.append((x0 + ux * L * t + nx * off, y0 + uy * L * t + ny * off))
    swirl = r4.ST(r4.poly_d(sw, close=False), 4.2, cap='round')
    orbs = ''
    for t in (0.2, 0.6, 1.0):                       # the orbs sit on the swirl's crests (the beam's end is the last)
        off = A * math.sin(t * math.pi * 2.5) * min(1.0, t * 4.0)
        orbs += r4.CI(x0 + ux * L * t + nx * off, y0 + uy * L * t + ny * off, 8.5)
    # the CORE is white-hot ink (the laser down the middle), the swirl and orbs the ONE accent crossing it. (r4's gap_white
    # seam was tried and rejected: its fixed 6 px halo ate the whole core and left a bare yellow squiggle.)
    return white + beam, swirl + orbs, cut, {}


def tray_icon():
    r4.PU[TRAY] = (256, LASER)
    stock_symbol = r4.powerup_symbol

    def symbol(name):
        if name == TRAY:
            return tray_symbol()
        return stock_symbol(name)

    r4.powerup_symbol = symbol
    try:
        return r4.powerup_icon(TRAY)
    finally:
        r4.powerup_symbol = stock_symbol
        del r4.PU[TRAY]


# =========================================================================================== build / review / install
def png_bytes(im):
    b = io.BytesIO()
    im.save(b, 'PNG', optimize=False)
    return b.getvalue()


def build():
    out = {}
    for name, fn in ((TRAY, tray_icon), (GUN, gun_icon)):
        im = fn()
        if im.size[0] % 4 or im.size[1] % 4:
            raise SystemExit('ws_wunderstrahl_icons: %s is %dx%d, not a multiple of 4' % (name, im.size[0], im.size[1]))
        out[name] = (im, png_bytes(im))
    return out


def review(built):
    """The two icons at their on-screen sizes beside their installed neighbours (the Gift of Death token, the
    Cyber Sword and Peacekeeper bay cells), on the dark HUD plate."""
    img_dir = os.path.join(ROOT, 'source_data', 'tod_ui_images', '_images')
    sheet = Image.new('RGBA', (900, 420), (18, 17, 25, 255))
    def paste(im, x, y, size):
        sheet.alpha_composite(im.resize(size, Image.LANCZOS), (x, y))
    tray = built[TRAY][0]
    paste(tray, 20, 20, (256, 256))
    paste(tray, 300, 20, (73, 73))
    gift = os.path.join(img_dir, 'i_tod_pu2_gift_of_death.png')
    if os.path.isfile(gift):
        paste(Image.open(gift).convert('RGBA'), 390, 20, (73, 73))
    gun = built[GUN][0]
    paste(gun, 300, 120, (288, 132))
    paste(gun, 300, 270, (144, 66))
    for i, n in enumerate(('i_tod_hud_gun_greatsword', 'i_tod_hud_gun_peacekeeper')):
        p = os.path.join(img_dir, n + '.png')
        if os.path.isfile(p):
            paste(Image.open(p).convert('RGBA'), 460 + i * 160, 270, (144, 66))
    os.makedirs(OUT, exist_ok=True)
    sheet.save(os.path.join(OUT, '_review.png'))


def wiring_problems(root):
    bad = []
    gdt = open(os.path.join(root, 'source_data', 'tod_ui_images.gdt'), encoding='utf-8', errors='replace').read()
    zone = open(os.path.join(root, 'zone_source', 'zm_tod2_cybercity.zone'), encoding='utf-8', errors='replace').read()
    zl = set(l.strip() for l in zone.splitlines())
    for n in IMAGES:
        if '"%s" ( "image.gdf" )' % n not in gdt:
            bad.append('%s: no image.gdf block in source_data/tod_ui_images.gdt' % n)
        if 'image,' + n not in zl:
            bad.append('%s: no "image,%s" line in the zone' % (n, n))
    tray = open(os.path.join(root, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'AetheriumPowerupsContainer.lua'),
                encoding='utf-8', errors='replace').read()
    if 'image = "%s"' % TRAY not in tray:
        bad.append('the tray row does not draw %s' % TRAY)
    load = open(os.path.join(root, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'AetheriumLoadout.lua'),
                encoding='utf-8', errors='replace').read()
    if '[ "tod2_wunderstrahl" ]' not in load or '[ "WUNDERSTRAHL" ]' not in load:
        bad.append('AetheriumLoadout.lua has no TOD_GUN_CAT / TOD_NAME_CAT row for the Wunderstrahl')
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--out-root', default=ROOT)
    a = ap.parse_args()
    root = os.path.abspath(a.out_root)
    img_dir = os.path.join(root, 'source_data', 'tod_ui_images', '_images')
    built = build()
    if a.check:
        bad = []
        for name, (_, data) in built.items():
            p = os.path.join(img_dir, name + '.png')
            if not os.path.isfile(p):
                bad.append('MISSING %s' % p)
            elif open(p, 'rb').read() != data:
                bad.append('STALE %s (re-run with --install; never hand-edit it)' % p)
        bad += wiring_problems(root)
        for b in bad:
            print('WS WUNDERSTRAHL ICONS: %s' % b)
        if bad:
            return 1
        print('WS WUNDERSTRAHL ICONS OK %d images + wiring' % len(built))
        return 0
    os.makedirs(OUT, exist_ok=True)
    for name, (_, data) in built.items():
        with open(os.path.join(OUT, name + '.png'), 'wb') as fh:
            fh.write(data)
    review(built)
    print('WS WUNDERSTRAHL ICONS: %s -> %s' % (', '.join(built), OUT))
    if a.install:
        os.makedirs(img_dir, exist_ok=True)
        for name, (_, data) in built.items():
            with open(os.path.join(img_dir, name + '.png'), 'wb') as fh:
                fh.write(data)
        print('  installed -> %s' % img_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
