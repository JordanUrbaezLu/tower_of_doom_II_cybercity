"""w2g_companion_plate.py - PK08: THE COMPANION STATUS PLATE's art (2026-10-05, wave 2 W2G).

THE GAP (tmp/asset_prod/packs/PK08-companion-status-plate.json). Every player gets a companion from the
Dealer, and its status readout was three server hudelems (_tod_partners.gsc status_hud): a stock-font
label ("TALON - REBUILDING") over two plain white quads, the only stock-font, flat-box piece on a HUD
that is otherwise all synthwave art. It is replaced by a LUI plate (TodCompanionPlate.lua) driven by the
tod_ptn_hud eventstring; this generator draws its two images:

  i_tod_h2_comp_plate   752 x 152 RGBA (188 x 38 canvas at 4 px / unit, canvas x 1002..1190 y 524..562:
                        left edge on the gun plate's, right of it the descent gauge's markers, under it
                        the ability tiles at y 568). The R4 gun-plate chassis language (dark glass at 90 %,
                        steel hairline, chamfered top-left / bottom-right, ONE magenta tube along the top,
                        a cyan tick on the right edge, faint scratches): an octagonal PORTRAIT WELL for the
                        shipped 208 x 208 i_tod_spin_ico_comp_* portraits, the empty name / state strip the
                        glyph typeface draws into, and the recessed BAR CHANNEL the bar sits in.
  i_tod_h2_comp_ring    152 x 152 RGBA (38 x 38 canvas): the portrait well's NEON TUBE alone, near-white so
                        the Lua tints it by STATE (the synthwave rule: one lit tube per container, its colour
                        says the state - cyan online, amber damaged, red destroyed, violet deploying, steel
                        holding), with its soft glow. Drawn over the portrait.

The bar itself is the player's own health bar art (i_tod_h2_hp_fill tinted for the track, the ghost and the
fill; i_tod_h2_hp_frame's 15 cells over it), so the two bars on the HUD read as one family. The portraits are
R1's shipped i_tod_spin_ico_comp_*. No text is baked: the Lua draws the name and the state in our typeface.

GEOMETRY IS SHARED, NOT COPIED BY HAND: GEO below is the plate's layout in canvas units; TodCompanionPlate.lua
carries the same numbers in its CP table and --check fails if any one of them differs (the art's well,
channel and tube would otherwise sit off the Lua's portrait, text and bar).

  python tools/artgen/packs/w2g_companion_plate.py               # -> art/generated/W2G-icons-plate/ + _review_plate.png
  python tools/artgen/packs/w2g_companion_plate.py --install [--out-root DIR]
  python tools/artgen/packs/w2g_companion_plate.py --check [--root DIR]   # BUILD GATE: bytes, GDT, zone (images + the
                                                                          #   widget's rawfile), HudOnly build, Lua lockstep
  python tools/artgen/packs/w2g_companion_plate.py --selftest [--root DIR] # --check's negative controls (7 planted breaks)

Deterministic (seeded grain / scratches, no timestamps). Never hand-edit a generated PNG.
"""
import argparse, importlib.util, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import artgen  # noqa: E402
from synthwave import THEME, Svg, chamfer, poly_d, line_d, scratches  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ROOT = artgen.ROOT
PACK = 'W2G-icons-plate'
U = 4                      # art px per canvas unit (the HUD V2 chrome's 0.25 scale)

# THE LAYOUT, in canvas units (plate-local unless noted). LOCKSTEP TodCompanionPlate.lua CP (checked).
GEO = {
    'X0': 1002, 'Y0': 524, 'W': 188, 'H': 38,       # the plate on the 1280 x 720 canvas
    'WELL': (2, 2, 36, 36), 'WELL_CUT': 6,          # the octagonal portrait well
    'PORT': (6, 6, 32, 32),                         # the portrait inside it (clear of the octagon's cuts)
    'RING': (0, 0, 38, 38),                         # the ring image's rect (the well + its glow)
    'BAR': (42, 23, 180, 35),                       # the bar (track, ghost, fill, hp frame) - hp_frame's aspect
    'NAME': (42, 4, 112, 16),                       # the name's glyph box (left)
    'TAG': (112, 5, 182, 16),                       # the state's glyph box (right aligned)
}
CHANNEL = (40, 21.5, 182, 36.5)                     # the recess under the bar (art only)

# THE STATE TINTS that are theme chrome (RT 2026-10-05), per synthwave.THEME: the exact Lua literal TodCompanionPlate.lua
# must carry. CYAN (online, the companion's identity), AMBER and RED are content and the same in every theme.
CP_TINTS = {
    'synthwave': {'VIOLET': 'VIOLET = { 0.66, 0.5, 1 }', 'STEEL': 'STEEL = { 0.72, 0.68, 0.85 }',
                  'TEXT': 'TEXT = { 0.96, 0.94, 1 }'},
    'fallen': {'VIOLET': 'VIOLET = { 0.71, 0.36, 1 }', 'STEEL': 'STEEL = { 0.59, 0.64, 0.78 }',
               'TEXT': 'TEXT = { 0.94, 0.95, 0.98 }'},
}

IMAGES = ['i_tod_h2_comp_plate', 'i_tod_h2_comp_ring']
# the shipped images the plate draws besides its own (each must stay zoned)
USES = ['i_tod_h2_hp_fill', 'i_tod_h2_hp_frame', 'i_tod_spin_ico_comp_protector', 'i_tod_spin_ico_comp_talon',
        'i_tod_spin_ico_comp_raps', 'i_tod_spin_ico_comp_cerberus']
LUA_REL = os.path.join('ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodCompanionPlate.lua')


def _r4():
    """R4's chassis helpers (layered / bevel / octagon), imported from the shipped generator, never copied."""
    spec = importlib.util.spec_from_file_location('r4_synthwave_hud', os.path.join(HERE, 'r4_synthwave_hud.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


R4 = _r4()


def a(v):
    """canvas units -> art px"""
    return v * U


def well_pts(inset=0.0):
    x0, y0, x1, y1 = GEO['WELL']
    return R4.octagon(a(x0) + inset, a(y0) + inset, a(x1) - inset, a(y1) - inset, a(GEO['WELL_CUT']) - inset * 0.41)


def comp_plate():
    W, H = a(GEO['W']), a(GEO['H'])
    out = chamfer(4, 4, W - 4, H - 4, tl=20, br=20)
    ch = chamfer(a(CHANNEL[0]), a(CHANNEL[1]), a(CHANNEL[2]), a(CHANNEL[3]), tl=8, br=12)
    well = well_pts()

    def base(s):
        s.plate(out, 'plate', top='plate_top')
        s.steel(out, 2.0)
        R4.bevel(s, out, 3.0)
        # the portrait well: a deep recess (the gun bay's gradient), its unlit keyline (the ring lights it)
        s.path(poly_d(well), fill='url(#%s)' % s.rad([(0, 'port_well', 1), (1, 'deep', 1)], 0.5, 0.42, 0.72))
        s.steel(well, 1.6, opacity=0.9)
        s.path(line_d((well[1][0], well[1][1] + 1.5), (well[2][0], well[2][1] + 1.5)), stroke='#000000', sw=2.0,
               opacity=0.5)
        # the bar channel: the luck plate's recess, the bar's own frame sits inside it
        s.path(poly_d(ch), fill='url(#%s)' % s.lin([(0, 'deep', 1), (1, 'channel_lo', 1)]))
        s.steel(ch, 1.4, opacity=0.85)
        s.path(line_d((ch[1][0], ch[1][1] + 1.2), (ch[2][0] - 1, ch[2][1] + 1.2)), stroke='#000000', sw=1.6,
               opacity=0.55)
        # a hairline under the name strip, from the well to the right edge (where the strip ends)
        s.path(line_d((a(40), a(19.6)), (a(183), a(19.6))), stroke='steel', sw=1.0, opacity=0.35)
        scratches(s, (a(40), 10, W - 30, a(19)), 5, 402, opacity=0.035, length=(24, 90))
        scratches(s, (a(8), a(36), W - 40, H - 8), 2, 403, opacity=0.03, length=(20, 60))

    def top(s):
        # ONE frame-light tube (the theme's: Fallen red / synthwave magenta): down the left edge, round the chamfer,
        # along the top (the gun plate's run, 58 %)
        s.tube(line_d((4, 70), (4, 24), (24, 4), (440, 4)), 'magenta', 3.0, glow=0.9, spread=0.6)
        # the right edge's tick (the gun plate's, synthwave.PAL 'tick'), level with the name strip. (The bar's own
        # frame, i_tod_h2_hp_frame, carries the tick at the bar's start: a second one here doubled it.)
        s.tube(line_d((W - 4, 30), (W - 4, 84)), 'tick', 2.6, glow=0.6, spread=0.5)

    return R4.layered(W, H, base, top, seed=330, base_alpha=0.90, hud=True)


def comp_ring():
    """The well's neon tube, NEAR-WHITE (the Lua tints it by state), with its halo, on transparency."""
    x0, y0, x1, y1 = GEO['RING']
    W, H = a(x1 - x0), a(y1 - y0)
    s = Svg(W, H)
    d = poly_d(well_pts(1.0))
    # glow wide + tight, the glass, the white-hot core: R3's tube recipe in white
    s.path(d, stroke='#FFFFFF', sw=13.0, opacity=0.20, filt=s.blur(6.0), join='round')
    s.path(d, stroke='#FFFFFF', sw=6.5, opacity=0.50, filt=s.blur(2.2), join='round')
    s.path(d, stroke='#DCE4EE', sw=3.6, join='miter')
    s.path(d, stroke='#FFFFFF', sw=1.5, opacity=0.95, join='miter')
    # corner glints: the octagon's four chamfer facets catch more light (the toast well's lit corners)
    pts = well_pts(1.0)
    for i in range(0, 8, 2):
        p, q = pts[i], pts[(i + 1) % 8]
        s.path(line_d(p, q), stroke='#FFFFFF', sw=2.4, opacity=0.9, join='round', cap='round')
    return s.render(ss=4)


BUILDERS = {'i_tod_h2_comp_plate': comp_plate, 'i_tod_h2_comp_ring': comp_ring}


def build():
    return {n: BUILDERS[n]() for n in IMAGES}

# ------------------------------------------------------------------------------------------ review

def onscreen(images, comp='i_tod_spin_ico_comp_talon', tint=(0.12, 0.9, 1.0), fill=0.7):
    """The plate at 1080p (1.5 px per canvas unit) with a portrait, a tinted ring and the bar - a static
    preview of the art only (the live widget, text and states are tools/ui_mockup/render_companion_plate.py)."""
    k = 1.5
    W, H = int(GEO['W'] * k), int(GEO['H'] * k)
    bg = Image.new('RGBA', (W + 40, H + 40), (24, 18, 34, 255))
    ox, oy = 20, 20

    def put(im, box, rgb=(1, 1, 1), alpha=1.0):
        x0, y0, x1, y1 = box
        w, h = int(round((x1 - x0) * k)), int(round((y1 - y0) * k))
        if w <= 0 or h <= 0:
            return
        t = im.resize((w, h), Image.BILINEAR)
        r, g, b, al = t.split()
        f = lambda band, m: band.point(lambda v: int(v * m))   # noqa: E731
        t = Image.merge('RGBA', (f(r, rgb[0]), f(g, rgb[1]), f(b, rgb[2]), f(al, alpha)))
        bg.alpha_composite(t, (ox + int(round(x0 * k)), oy + int(round(y0 * k))))

    put(images['i_tod_h2_comp_plate'], (0, 0, GEO['W'], GEO['H']))
    put(Image.open(artgen.shipped(comp)).convert('RGBA'), GEO['PORT'])
    put(images['i_tod_h2_comp_ring'], GEO['RING'], tint)
    bx0, by0, bx1, by1 = GEO['BAR']
    hp = Image.open(artgen.shipped('i_tod_h2_hp_fill')).convert('RGBA')
    put(hp, GEO['BAR'], (0.05, 0.07, 0.11))
    put(hp, (bx0, by0, bx0 + (bx1 - bx0) * fill, by1), tint)
    put(Image.open(artgen.shipped('i_tod_h2_hp_frame')).convert('RGBA'), GEO['BAR'])
    return bg


def review(images, out_dir):
    font = artgen.ttf(16)
    gun = Image.open(artgen.shipped('i_tod_h2_gun_plate')).convert('RGBA')
    toast = Image.open(artgen.shipped('i_tod_h2_toast')).convert('RGBA')
    rows = [
        ('i_tod_h2_comp_plate 752 x 152 (1:1)  |  the gun plate it sits over (R4, 1056 x 288)', [images['i_tod_h2_comp_plate'], gun]),
        ('i_tod_h2_comp_ring 152 x 152 (white; tinted by state in code)  |  the toast well it echoes', [images['i_tod_h2_comp_ring'], toast]),
    ]
    p1 = artgen.contact_sheet(rows, os.path.join(out_dir, '_review_plate_p1.png'), height=152)
    s1 = Image.open(p1).convert('RGBA')
    os.remove(p1)
    states = [((0.12, 0.9, 1.0), 0.85, 'i_tod_spin_ico_comp_protector'), ((1.0, 0.69, 0.13), 0.3, 'i_tod_spin_ico_comp_talon'),
              ((1.0, 0.18, 0.22), 0.0, 'i_tod_spin_ico_comp_raps'), ((0.48, 0.27, 1.0), 1.0, 'i_tod_spin_ico_comp_cerberus')]
    tiles = [onscreen(images, c, t, f) for t, f, c in states]
    w = sum(t.width for t in tiles) + 12 * (len(tiles) + 1)
    s2 = Image.new('RGBA', (max(w, s1.width), tiles[0].height + 44), (28, 30, 38, 255))
    ImageDraw.Draw(s2).text((12, 6), 'AT 1080P (1.5 px / unit), ring + bar tinted: online / damaged / destroyed / deploying '
                                     '(art preview; the live widget is render_companion_plate.py)', fill=(220, 225, 235, 255), font=font)
    x = 12
    for t in tiles:
        s2.alpha_composite(t, (x, 34))
        x += t.width + 12
    full = Image.new('RGBA', (max(s1.width, s2.width), s1.height + s2.height), (28, 30, 38, 255))
    full.alpha_composite(s1, (0, 0))
    full.alpha_composite(s2, (0, s1.height))
    out = os.path.join(out_dir, '_review_plate.png')
    full.save(out)
    return out

# ------------------------------------------------------------------------------------------- check

def _read(p):
    with open(p, 'rb') as f:
        return f.read()


def lua_geo(lua_text):
    """The CP numbers TodCompanionPlate.lua draws with: { name: value | tuple }."""
    code = re.sub(r'--[^\n]*', '', lua_text)
    m = re.search(r'local CP = \{(.*?)\n\}', code, re.S)
    if not m:
        return None
    body = m.group(1)
    got = {}
    for k in ('X0', 'Y0', 'W', 'H', 'WELL_CUT'):
        mm = re.search(r'\b%s\s*=\s*(-?[\d.]+)' % k, body)
        if mm:
            got[k] = float(mm.group(1))
    for k in ('WELL', 'PORT', 'RING', 'BAR', 'NAME', 'TAG'):
        mm = re.search(r'\b%s\s*=\s*\{([^}]*)\}' % k, body)
        if mm:
            got[k] = tuple(float(v) for v in mm.group(1).split(','))
    return got


def check(root):
    fails = []
    images = build()
    for name, im in images.items():
        p = os.path.join(root, 'source_data', 'tod_ui_images', '_images', name + '.png')
        if not os.path.exists(p):
            fails.append('%s: not installed (%s)' % (name, p))
        elif _read(p) != artgen.png_bytes(im):
            fails.append('%s: installed PNG differs from the generator (re-run --install; never hand-edit)' % name)
        if im.width % 4 or im.height % 4:
            fails.append('%s: %dx%d is not a multiple of 4' % (name, im.width, im.height))
    gdt = _read(os.path.join(root, 'source_data', 'tod_ui_images.gdt')).decode('utf-8', 'replace')
    zone = _read(os.path.join(root, 'zone_source', 'zm_tod2_cybercity.zone')).decode('utf-8', 'replace')
    zlines = set(l.strip() for l in zone.splitlines())
    for name in IMAGES:
        blk = re.search(r'"%s" \( "image\.gdf" \)\s*\{(.*?)\n\s*\}' % re.escape(name), gdt, re.S)
        if not blk:
            fails.append('%s: no image.gdf block in source_data/tod_ui_images.gdt' % name)
        else:
            b = blk.group(1)
            for want in ('"baseImage" "source_data/tod_ui_images/_images/%s.png"' % name,
                         '"compressionMethod" "compressed high color"', '"noMipMaps" "1"', '"noPicMip" "1"',
                         '"semantic" "diffuseMap"'):
                if want not in b:
                    fails.append('%s: GDT block lacks %s (NPOT HUD art: the gun plate\'s block)' % (name, want))
    for name in IMAGES + USES:
        if 'image,' + name not in zlines:
            fails.append('%s: no "image,%s" line in zone_source/zm_tod2_cybercity.zone - the plate would draw a '
                         'WHITE SQUARE' % (name, name))
    # the widget itself rides in the zone as a rawfile: an unzoned require fails SILENTLY (tod_upgrade.lua
    # pcall-requires it), and with the server hudelems gone the companion would have no readout at all
    if 'rawfile,' + LUA_REL.replace(os.sep, '/') not in zlines:
        fails.append('no "rawfile,%s" line in zone_source/zm_tod2_cybercity.zone - the pcall require would fail '
                     'silently and the companion would have NO status readout' % LUA_REL.replace(os.sep, '/'))
    up = os.path.join(root, 'ui', 'uieditor', 'menus', 'hud', 'tod_upgrade.lua')
    upc = re.sub(r'--[^\n]*', '', _read(up).decode('utf-8', 'replace')) if os.path.exists(up) else ''
    if ('"ui.uieditor.widgets.HUD.AetheriumWidgets.TodCompanionPlate"' not in upc
            or not re.search(r'HudOnly:addElement\(\s*CompanionPlate\s*\)', upc)):
        fails.append('tod_upgrade.lua does not require TodCompanionPlate and add it to HudOnly (the veiled layer): '
                     'the plate would never be built, or would show through the HUD veil')
    lp = os.path.join(root, LUA_REL)
    if not os.path.exists(lp):
        fails.append('%s: missing (the widget that draws these images)' % LUA_REL)
    else:
        lua = _read(lp).decode('utf-8', 'replace')
        code = re.sub(r'--[^\n]*', '', lua)
        for name in IMAGES + USES:
            if '"%s"' % name not in code:
                fails.append('TodCompanionPlate.lua does not name "%s" as a literal (lint_tod_assets reads literals)' % name)
        got = lua_geo(lua)
        if got is None:
            fails.append('TodCompanionPlate.lua has no "local CP = {" layout table')
        else:
            for k, v in GEO.items():
                want = tuple(float(x) for x in v) if isinstance(v, tuple) else float(v)
                if got.get(k) != want:
                    fails.append('LOCKSTEP: TodCompanionPlate.lua CP.%s = %s, the art is drawn for %s' % (k, got.get(k), want))
        for k, lit in CP_TINTS[THEME].items():
            if lit not in code:
                fails.append('THEME: TodCompanionPlate.lua CP.%s is not the %s theme\'s "%s" (tools/artgen/synthwave.py '
                             'THEME; the state tints follow it)' % (k, THEME, lit))
        for other, tints in CP_TINTS.items():
            for k, lit in tints.items():
                if other != THEME and lit != CP_TINTS[THEME][k] and lit in code:
                    fails.append('THEME: TodCompanionPlate.lua still carries the %s theme\'s "%s"' % (other, lit))
    if fails:
        print('COMPANION PLATE ART FAILED (%d):' % len(fails))
        for f in fails:
            print('  * ' + f)
        return 1
    print('COMPANION PLATE ART OK %d (bytes = generator; GDT + zone wired; widget zoned + built in HudOnly; Lua names '
          'every image; layout in step)' % len(images))
    return 0


def selftest(root):
    """NEGATIVE CONTROLS for check(): copy the files it reads into a scratch tree, require a clean pass there,
    then break the wiring seven ways and require a FAIL for each (a gate nobody has watched fire is not a gate)."""
    import contextlib, io, shutil, tempfile
    zone_rel = os.path.join('zone_source', 'zm_tod2_cybercity.zone')
    up_rel = os.path.join('ui', 'uieditor', 'menus', 'hud', 'tod_upgrade.lua')
    gdt_rel = os.path.join('source_data', 'tod_ui_images.gdt')
    png_rel = lambda n: os.path.join('source_data', 'tod_ui_images', '_images', n + '.png')   # noqa: E731
    rels = [LUA_REL, up_rel, gdt_rel, zone_rel] + [png_rel(n) for n in IMAGES]

    def fresh():
        tmp = tempfile.mkdtemp(prefix='w2g_plate_selftest_')
        for rel in rels:
            if not os.path.exists(os.path.join(root, rel)):
                continue   # the clean check below then fails and says what is missing
            os.makedirs(os.path.dirname(os.path.join(tmp, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(root, rel), os.path.join(tmp, rel))
        return tmp

    def swap(rel, old, new):
        def f(tmp):
            p = os.path.join(tmp, rel)
            b = _read(p)
            assert b.count(old) >= 1, 'selftest anchor missing in %s: %r' % (rel, old)
            with open(p, 'wb') as fh:
                fh.write(b.replace(old, new, 1))
        return f

    def append_byte(rel):
        def f(tmp):
            with open(os.path.join(tmp, rel), 'ab') as fh:
                fh.write(b'\0')
        return f

    def gdt_ring_uncompressed(tmp):
        p = os.path.join(tmp, gdt_rel)
        t = _read(p)
        i = t.index(b'"i_tod_h2_comp_ring" ( "image.gdf" )')
        j = t.index(b'"compressionMethod" "compressed high color"', i)
        with open(p, 'wb') as fh:
            fh.write(t[:j] + b'"compressionMethod" "uncompressed"' + t[j + len(b'"compressionMethod" "compressed high color"'):])

    cases = [
        ('a hand-edited plate PNG', append_byte(png_rel('i_tod_h2_comp_plate'))),
        ('the ring image unzoned', swap(zone_rel, b'image,i_tod_h2_comp_ring', b'// image,i_tod_h2_comp_ring')),
        ('the widget rawfile unzoned', swap(zone_rel, b'rawfile,ui/uieditor/widgets/HUD/AetheriumWidgets/TodCompanionPlate.lua',
                                           b'// rawfile,ui/uieditor/widgets/HUD/AetheriumWidgets/TodCompanionPlate.lua')),
        ('the widget built outside the veil', swap(up_rel, b'HudOnly:addElement( CompanionPlate )', b'Hud:addElement( CompanionPlate )')),
        ('the Lua bar drifted off the art', swap(LUA_REL, b'BAR = { 42, 23, 180, 35 }', b'BAR = { 42, 23, 178, 35 }')),
        ('the ring GDT block uncompressed', gdt_ring_uncompressed),
        ('the idle steel is the other theme\'s', swap(LUA_REL, CP_TINTS[THEME]['STEEL'].encode(),
                                                  [v for t, v in CP_TINTS.items() if t != THEME][0]['STEEL'].encode())),
    ]
    out = io.StringIO()
    tmp = fresh()
    try:
        with contextlib.redirect_stdout(out):
            ok = check(tmp) == 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if not ok:
        print('COMPANION PLATE SELFTEST: the unmodified tree does not pass check() - fix that first\n' + out.getvalue())
        return 1
    blind = []
    for label, mutate in cases:
        tmp = fresh()
        try:
            mutate(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                caught = check(tmp) != 0
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        if not caught:
            blind.append(label)
    if blind:
        print('COMPANION PLATE SELFTEST FAILED: --check is BLIND to: ' + '; '.join(blind))
        return 1
    print('COMPANION PLATE SELFTEST OK: the clean tree passes, %d planted breaks each fail' % len(cases))
    return 0


def main():
    ap = argparse.ArgumentParser(description='PK08 companion status plate art (plate + state ring)')
    ap.add_argument('--install', action='store_true', help='write the PNGs into <out-root>/source_data/tod_ui_images/_images/')
    ap.add_argument('--out-root', default=ROOT, help='install root (default: the repo)')
    ap.add_argument('--check', action='store_true', help='build gate: bytes + GDT + zone + Lua lockstep')
    ap.add_argument('--selftest', action='store_true', help='negative controls: --check must fail seven planted breaks')
    ap.add_argument('--root', default=ROOT, help='tree --check reads (default: the repo)')
    ap.add_argument('--out', default=None, help='render folder (default art/generated/%s)' % PACK)
    o = ap.parse_args()
    if o.check:
        sys.exit(check(o.root))
    if o.selftest:
        sys.exit(selftest(o.root))
    images = build()
    if o.install:
        dst = os.path.join(o.out_root, 'source_data', 'tod_ui_images', '_images')
        for name, im in images.items():
            print('installed %s.png  md5 %s' % (name, artgen.save_png(im, os.path.join(dst, name + '.png'))))
        return
    out_dir = o.out or artgen.stage_dir(PACK)
    os.makedirs(out_dir, exist_ok=True)
    for name, im in images.items():
        md5 = artgen.save_png(im, os.path.join(out_dir, name + '.png'))
        print('%s.png  %dx%d  md5 %s' % (name, im.width, im.height, md5))
    print('review ->', review(images, out_dir))


if __name__ == '__main__':
    main()
