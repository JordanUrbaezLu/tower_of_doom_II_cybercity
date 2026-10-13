"""wording_pass.py - ONE WORD PER THING (W3E, 2026-10-05).

User, 2026-10-05: "Choose your class asset should say Weapon not gun. This map is more weapons rather
than guns. Only one class has guns pretty much. Lets find other inconsistent areas."

Only the Breacher carries guns (and the Archer's crossbow is the nearest thing): the Necromancer holds a
skull and two staffs, the Archer bows, the Warrior fists, a gauntlet and a sword. So every PLAYER-FACING
"gun" that means a class's weapon says WEAPON, and the same audit fixed the other places where one thing
had two names or the words had stopped matching the game (the table in tmp/wave3/W3E-wording/LAND.md).

WHAT IT OWNS
  * i_tod_banner_choose_class (900x140, same name, same size): the CHOOSE YOUR CLASS banner's baked
    subline. It is DRAWN by tools/artgen/packs/r3_synthwave_system.py banner('class') - this tool never
    re-implements it, it imports that function, so r3's own --check and this one agree byte for byte.
  * WORDING: the rules below - each names a file, the words that must be gone and the words that must
    be there - plus a scan of every player-facing string literal for the word GUN.

  python tools/wording/wording_pass.py                    # render -> art/generated/W3E-wording/ + _review.png
  python tools/wording/wording_pass.py --stage            # + copy the banner into tmp/wave3/W3E-wording/stage/
  python tools/wording/wording_pass.py --check            # regenerate in memory; fail on bytes, wiring or wording
  python tools/wording/wording_pass.py --check --root D   # ... against an overlay tree D (files D lacks come from the repo)
  python tools/wording/wording_pass.py --text-review OLD NEW   # pause / scoreboard renders (render_menus.py) old vs new

Every --check also runs its NEGATIVE CONTROLS first: the GUN scan must flag a planted player string and
leave comments, identifiers and image names alone, and each rule must fail on its own forbidden text.
"""
import argparse, importlib.util, os, re, sys

sys.dont_write_bytecode = True     # loading r3 from a stage or overlay tree must not drop __pycache__ into it
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'artgen'))
import artgen  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

PACK = 'W3E-wording'
NAME = 'i_tod_banner_choose_class'
IMG_REL = os.path.join('source_data', 'tod_ui_images', '_images', NAME + '.png')
R3_REL = os.path.join('tools', 'artgen', 'packs', 'r3_synthwave_system.py')
STAGE_ROOT = os.path.join(ROOT, 'tmp', 'wave3', PACK, 'stage')
BASE_ROOT = os.path.join(ROOT, 'tmp', 'wave3', PACK, 'base')
NEW_SUB = 'YOUR WEAPON AND UPGRADES - PERMANENT FOR THIS RUN'

# ------------------------------------------------------------------------------------------- rules
# (file, must be GONE, must be PRESENT [text, minimum count], why). Paths are repo-relative.
UI = 'ui/uieditor/'
RULES = [
    (R3_REL, ['YOUR GUN AND UPGRADE PATHS'], [("'%s'" % NEW_SUB, 1)],
     'the CHOOSE YOUR CLASS banner says WEAPON (user 2026-10-05)'),
    (UI + 'menus/hud/tod_class_select.lua',
     ['your gun and upgrade paths', 'gravity smash', 'bullet feed + suppression', 'soul beam + summons', 'THRALLS > SOUL HOUNDS'],
     [('SubTitle:setText( "your weapon and upgrades - PERMANENT for this run" )', 2)],
     "the draft's no-art lines match the banner and today's kits"),
    (UI + 'menus/hud/tod_upgrade.lua',
     ['your class gun', 'new gun unpacked', 'MORE MONEY PER KILL', 'more money per kill',
      'DASH WITH YOUR BLADE', 'dash with your blade', 'your blades hit harder', '" blade damage"', 'LONGER SOUL BEAM',
      '[2] = "SOUL HOUNDS"', 'max HP per helper', '"% dmg, +"', '" dmg, "', 'act = "always on"'],
     [('"Pack-a-Punch + floor "', 2),
      ('[1] = { class = "NECROMANCER", [2] = "SOUL STAFF", [3] = "CROWN OF THE DAMNED" }', 1)],
     'cards / pause rows: WEAPON, POINTS, Pack-a-Punch, the Warrior bashes with fists too, the staffs are the tiers '
     '(the class header keeps NEXT: PAP - the long form runs into NECROMANCER / BREACHER beside it)'),
    (UI + 'widgets/HUD/AetheriumWidgets/TodSpinReel.lua', ['"CIVIL PROTECTOR"'],
     [('COMPANIONS = { "PROTECTOR", "TALON", "R.A.P.S.", "CERBERUS" }', 1)],
     'one name per companion: the HUD plate, the gift tile and the pause row all say PROTECTOR'),
    ('scripts/zm/zm_tod2_cybercity/_tod_partners.gsc', ['"CIVIL PROTECTOR"', 'Civil Protector test'],
     [('define( 0, "PROTECTOR",', 1)], 'the server-side name is LOCKSTEP with the reel (partner_shop/test_spin.js)'),
    (UI + 'widgets/HUD/ZM_CursorHint/Prompts/PromptDoors.lua',
     ['CLIMB HIGHER INTO THE TOWER', 'THE FINAL CLIMB BEGINS HERE', 'TELEPORT PADS TO THE LOUNGES', 'PACK-A-PUNCH IS UP HERE'],
     [('"FURTHER DOWN THE TOWER"', 1)], 'the tower is a DESCENT (docs/160): no door says climb'),
    (UI + 'widgets/HUD/ZM_CursorHint/Prompts/PromptPowerRequired.lua', ['THE SWITCH IS AT THE TOWER BASE'],
     [('"THE SWITCH IS IN THE POWER ROOM"', 1)], 'the power lever is in the crown power room (docs/160, 164)'),
    (UI + 'widgets/HUD/ZM_CursorHint/Prompts/PromptPowerSwitch.lua', ['PERKS - PACK-A-PUNCH - PADS'],
     [('"PERKS - PADS - BLACK MARKET"', 1)], 'the crown PaP never waited for the power (user 2026-09-25)'),
    ('scripts/zm/zm_cwpap.gsc', ['class gun can still be packed'], [('class weapon can still be packed', 1)],
     'the ALREADY PACKED status line says WEAPON'),
    ('scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc',
     ['more money per kill', 'your blades hit harder', 'dash with your blade', 'stronger skull staff'], [],
     'the add_domain / tier descriptions say what the Lua cards say'),
    ('scripts/zm/zm_tod2_cybercity/_tod_archer.gsc', ['hold tactical = grapple'], [],
     "the Archer's first bold line is in player voice"),
]

# ------------------------------------------------------------------------------------ the GUN scan
# Strings that are NOT player text even though they hold the word: the retired RUN AND GUN card's id-keyed
# name row (the server can never send id 23 again; tod_upgrade.lua keeps the row nil-safe).
GUN_ALLOW = {'RUN AND GUN'}
GUN_RE = re.compile(r'\bguns?\b', re.I)
LUA_STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
GSC_SITES = re.compile(r'\b(SetHintString|IPrintLnBold|IPrintLn|add_domain)\s*\(|\bo\.desc\s*=')


def strip_lua_comment(line):
    q = None
    i = 0
    while i < len(line):
        c = line[i]
        if q:
            if c == '\\':
                i += 2
                continue
            if c == q:
                q = None
        elif c in '"\'':
            q = c
        elif line.startswith('--', i):
            return line[:i]
        i += 1
    return line


def strip_gsc_comment(line):
    q = False
    i = 0
    while i < len(line):
        c = line[i]
        if c == '"' and (i == 0 or line[i - 1] != '\\'):
            q = not q
        elif not q and line.startswith('//', i):
            return line[:i]
        i += 1
    return line


def gun_hits_lua(rel, text):
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for m in LUA_STR.finditer(strip_lua_comment(line)):
            s = m.group(1)
            if GUN_RE.search(s) and s not in GUN_ALLOW:
                out.append('%s:%d "%s"' % (rel, n, s))
    return out


def gun_hits_gsc(rel, text):
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        code = strip_gsc_comment(line)
        if not GSC_SITES.search(code):
            continue
        for m in LUA_STR.finditer(code):
            s = m.group(1)
            if GUN_RE.search(s) and s not in GUN_ALLOW:
                out.append('%s:%d "%s"' % (rel, n, s))
    return out


def resolve(root, rel):
    p = os.path.join(root, rel)
    return p if os.path.exists(p) else os.path.join(ROOT, rel)


def read(root, rel):
    return open(resolve(root, rel), encoding='utf-8', errors='replace').read()


def code_only(rel, text):
    """The rules judge CODE, not history: a comment may quote the old words (that is how this repo records
    why a line changed), so comments are stripped per language before a rule reads the file."""
    if rel.endswith('.lua'):
        return '\n'.join(strip_lua_comment(l) for l in text.splitlines())
    if rel.endswith(('.gsc', '.csc', '.gsh')):
        text = re.sub(r'/\*[\s\S]*?\*/', '', text)
        return '\n'.join(strip_gsc_comment(l) for l in text.splitlines())
    if rel.endswith('.py'):
        return '\n'.join(l for l in text.splitlines() if not l.lstrip().startswith('#'))
    return text


def rule_problems(root, rules=RULES, reader=None):
    reader = reader or (lambda rel: read(root, rel))
    out = []
    for rel, gone, present, why in rules:
        src = code_only(rel, reader(rel))
        for g in gone:
            if g in src:
                out.append('%s still says %r (%s)' % (rel, g, why))
        for p, n in present:
            if src.count(p) < n:
                out.append('%s lacks %r x%d (%s)' % (rel, p, n, why))
    return out


def gun_problems(root):
    out = []
    ui_root = os.path.join(root, 'ui') if os.path.isdir(os.path.join(root, 'ui')) else os.path.join(ROOT, 'ui')
    for d, _, fs in os.walk(ui_root):
        for f in fs:
            if f.endswith('.lua'):
                p = os.path.join(d, f)
                out += gun_hits_lua(os.path.relpath(p, os.path.dirname(ui_root)), open(p, encoding='utf-8', errors='replace').read())
    sc_root = os.path.join(root, 'scripts') if os.path.isdir(os.path.join(root, 'scripts')) else os.path.join(ROOT, 'scripts')
    for d, _, fs in os.walk(os.path.join(sc_root, 'zm', 'zm_tod2_cybercity')):
        for f in fs:
            if f.endswith(('.gsc', '.csc')):
                p = os.path.join(d, f)
                out += gun_hits_gsc(os.path.relpath(p, os.path.dirname(sc_root)), open(p, encoding='utf-8', errors='replace').read())
    p = os.path.join(sc_root, 'zm', 'zm_cwpap.gsc')
    if os.path.exists(p):
        out += gun_hits_gsc('scripts/zm/zm_cwpap.gsc', open(p, encoding='utf-8', errors='replace').read())
    return out


def selftest():
    """Negative controls: the scan and the rules must each catch what they exist to catch."""
    bad = []
    lua = ('local a = "your class gun is tier 2"   -- a comment about a gun\n'
           'card.Gun:setText( c.gun )\nlocal img = "i_tod_hud_gun_mozambique"\nlocal r = "RUN AND GUN"\n'
           "local q = 'the gunship'\n")
    hits = gun_hits_lua('x.lua', lua)
    if len(hits) != 1 or 'your class gun' not in hits[0]:
        bad.append('GUN scan (Lua) should flag exactly the planted player string, got %r' % hits)
    gsc = ('\tself IPrintLnBold( "PACK YOUR GUN" );   // gun\n'
           '\tlog( "next gun not linked" );\n\tself SetHintString( "Hold for a WEAPON" );\n')
    hits = gun_hits_gsc('x.gsc', gsc)
    if len(hits) != 1 or 'PACK YOUR GUN' not in hits[0]:
        bad.append('GUN scan (GSC) should flag the bold print and nothing else, got %r' % hits)
    hist = rule_problems(None, [('x.lua', ['your class gun'], [], 'h'), ('x.gsc', ['more money per kill'], [], 'h')],
                         reader=lambda r: ('local a = 1   -- was "your class gun"\n' if r.endswith('.lua')
                                           else 'a = 1;   // was: more money per kill\n'))
    if hist:
        bad.append('a rule fired on a COMMENT that records the old words: %r' % hist)
    for rel, gone, present, why in RULES:
        if gone:
            planted = rule_problems(None, [(rel, gone, [], why)], reader=lambda _r, g=gone[0]: 'x ' + g + ' x')
            if not planted:
                bad.append('rule for %s did not catch its own forbidden text %r' % (rel, gone[0]))
        if present:
            missing = rule_problems(None, [(rel, [], present, why)], reader=lambda _r: '')
            if not missing:
                bad.append('rule for %s did not catch a missing %r' % (rel, present[0][0]))
    return bad

# ------------------------------------------------------------------------------------------ the art

def load_r3(root):
    path = resolve(root, R3_REL)
    spec = importlib.util.spec_from_file_location('r3_for_wording_%d' % abs(hash(path)), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render(root):
    im = load_r3(root).banner('class').convert('RGBA')
    ref = Image.open(resolve(root, IMG_REL))
    if im.size != ref.size or im.size != (900, 140):
        raise SystemExit('wording: %s renders %s, ships %s - a drop-in keeps 900x140' % (NAME, im.size, ref.size))
    return im


def wiring_problems(root):
    import glob
    out = []
    gdt = read(root, os.path.join('source_data', 'tod_ui_images.gdt'))
    if not re.search(r'"%s"\s*\(\s*"image\.gdf"' % NAME, gdt):
        out.append('%s: no GDT block in source_data/tod_ui_images.gdt' % NAME)
    zdir = os.path.join(root, 'zone_source') if os.path.isdir(os.path.join(root, 'zone_source')) else os.path.join(ROOT, 'zone_source')
    zone = ''.join(open(z, encoding='utf-8', errors='replace').read() for z in glob.glob(os.path.join(zdir, '*.zone')))
    if not re.search(r'^\s*image,%s\s*$' % NAME, zone, re.M):
        out.append('%s: no zone image line' % NAME)
    lua = read(root, UI + 'menus/hud/tod_class_select.lua')
    if 'RegisterImage( "%s" )' % NAME not in lua:
        out.append('tod_class_select.lua no longer registers %s' % NAME)
    return out

# ----------------------------------------------------------------------------------------- review

def _font(px):
    return ImageFont.truetype(artgen.TTF, px)


def review_sheet(old, new, r3, out_path):
    """OLD vs NEW at the size the draft draws it at 1080p (600x93 canvas units x 1.5 = 900x140), on a
    world-grey patch, a 2x zoom of the changed subline, and both banners in the class-draft composite."""
    W = 1920
    pad = 24
    zoom_old = old.crop((60, 92, 840, 124)).resize((1560, 64), Image.LANCZOS)
    zoom_new = new.crop((60, 92, 840, 124)).resize((1560, 64), Image.LANCZOS)
    tmp_dir = os.path.join(ROOT, 'tmp', 'wave3', PACK, '_draft')    # scratch frames; only the sheet is kept
    os.makedirs(tmp_dir, exist_ok=True)
    get_old = lambda n: old if n == NAME else Image.open(artgen.shipped(n)).convert('RGBA')
    get_new = lambda n: new if n == NAME else Image.open(artgen.shipped(n)).convert('RGBA')
    d_old = Image.open(r3.class_select_mock(get_old, os.path.join(tmp_dir, 'draft_old.png'))).convert('RGB')
    d_new = Image.open(r3.class_select_mock(get_new, os.path.join(tmp_dir, 'draft_new.png'))).convert('RGB')
    band = (0, int(96 * 1.5), 1920, int(330 * 1.5))     # the banner + the top of the cards, 1:1 at 1080p
    d_old, d_new = d_old.crop(band), d_new.crop(band)
    H = pad + 40 + 140 + pad + 40 + 64 * 2 + 30 + pad + 40 + d_old.height * 2 + 60 + pad
    sheet = Image.new('RGB', (W, H), (16, 12, 26))
    d = ImageDraw.Draw(sheet)
    f = _font(26)
    y = pad
    d.text((pad, y), 'i_tod_banner_choose_class at its 1080p size (900 x 140)   OLD (left)  ->  NEW (right)', fill=(225, 220, 240), font=f)
    y += 40
    for i, im in enumerate((old, new)):
        x = pad + i * (900 + 60)
        sheet.paste((44, 52, 64), (x, y, x + 900, y + 140))
        sheet.paste(im, (x, y), im)
    y += 140 + pad
    d.text((pad, y), 'ZOOM x2 on the subline: OLD (top) / NEW (bottom). The new line keeps the full 15 cap (the old one was squeezed to fit).', fill=(225, 220, 240), font=f)
    y += 40
    for im in (zoom_old, zoom_new):
        bg = Image.new('RGBA', im.size, (30, 22, 52, 255))
        bg.alpha_composite(im)
        sheet.paste(bg.convert('RGB'), (pad, y))
        y += 64 + 15
    y += pad
    d.text((pad, y), 'IN CONTEXT: the class draft at 1080p, 1:1 (the shipped cards, plates and timers around it). OLD above, NEW below.', fill=(225, 220, 240), font=f)
    y += 40
    sheet.paste(d_old, (0, y))
    y += d_old.height + 30
    sheet.paste(d_new, (0, y))
    sheet.save(out_path, optimize=True)
    return out_path


def text_review(old_dir, new_dir, out_path):
    """The real pause menu / scoreboard (render_menus.py under the real Lua) before and after, cropped to
    the lines this pass changed, resized to 1080p (render_menus draws 2560x1440)."""
    crops = [
        ('pause_warrior_full.png', (150, 430, 1590, 1240),
         'Warrior: BASH says BASH DAMAGE (the fists and gauntlet bash too), DEMON SLAYER says DAMAGE not DMG, VITALITY drops ALWAYS ON'),
        ('pause_necromancer_full.png', (150, 430, 1590, 1240),
         'Necromancer: the companion is PROTECTOR everywhere, SUMMONER MASTER says MAX HEALTH not MAX HP'),
        ('pause_breacher_full.png', (150, 430, 1590, 1240), 'Breacher: CLUSTER says DAMAGE not DMG; every other row unchanged (the control)'),
        ('scoreboard_necromancer.png', (180, 342, 1000, 440), 'Scoreboard companion row: PROTECTOR'),
        ('pause_necromancer_full.png', (1060, 100, 1600, 240), 'Class header: NEXT: PAP stays short (the long form ran into NECROMANCER)'),
    ]
    tiles = []
    for fname, box, label in crops:
        a, b = os.path.join(old_dir, fname), os.path.join(new_dir, fname)
        if not (os.path.exists(a) and os.path.exists(b)):
            continue
        ca = Image.open(a).convert('RGB').crop(box)
        cb = Image.open(b).convert('RGB').crop(box)
        s = 0.75   # 2560 -> 1920: the 1080p size
        ca = ca.resize((int(ca.width * s), int(ca.height * s)), Image.LANCZOS)
        cb = cb.resize((int(cb.width * s), int(cb.height * s)), Image.LANCZOS)
        tiles.append((label, ca, cb))
    if not tiles:
        raise SystemExit('text review: no render pairs found in %s / %s' % (old_dir, new_dir))
    W = max(t[1].width * 2 + 90 for t in tiles)
    H = sum(t[1].height + 60 for t in tiles) + 20
    sheet = Image.new('RGB', (W, H), (16, 12, 26))
    d = ImageDraw.Draw(sheet)
    f = _font(24)
    y = 10
    for label, ca, cb in tiles:
        d.text((20, y), label + '   OLD (left) -> NEW (right), 1080p', fill=(225, 220, 240), font=f)
        y += 40
        sheet.paste(ca, (20, y))
        sheet.paste(cb, (40 + ca.width + 30, y))
        y += ca.height + 20
    sheet.save(out_path, optimize=True)
    return out_path

# ------------------------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--stage', action='store_true', help='copy the banner into tmp/wave3/%s/stage/' % PACK)
    ap.add_argument('--root', default=None, help='an overlay tree to read (default: the repo; --stage renders from the stage)')
    ap.add_argument('--text-review', nargs=2, metavar=('OLD_DIR', 'NEW_DIR'))
    ap.add_argument('--no-review', action='store_true')
    a = ap.parse_args()

    if a.text_review:
        out = text_review(a.text_review[0], a.text_review[1], os.path.join(artgen.stage_dir(PACK), '_review_text.png'))
        print('text review ->', out)
        return

    if a.check:
        root = os.path.abspath(a.root) if a.root else ROOT
        bad = ['NEGATIVE CONTROL: ' + b for b in selftest()]
        im = render(root)
        if open(resolve(root, IMG_REL), 'rb').read() != artgen.png_bytes(im):
            bad.append('%s: the installed bytes are not what r3 banner(\'class\') draws - run the generator' % NAME)
        bad += wiring_problems(root)
        bad += rule_problems(root)
        bad += ['player-facing GUN: ' + h for h in gun_problems(root)]
        if bad:
            print('WORDING CHECK FAILED (%d):' % len(bad))
            for b in bad:
                print('   ', b)
            sys.exit(1)
        print('WORDING OK: banner bytes + wiring, %d rules, the GUN scan, negative controls (%s)' % (len(RULES), root))
        return

    root = os.path.abspath(a.root) if a.root else (STAGE_ROOT if os.path.exists(os.path.join(STAGE_ROOT, R3_REL)) else ROOT)
    im = render(root)
    out = artgen.stage_dir(PACK)
    artgen.save_png(im, os.path.join(out, NAME + '.png'))
    print('rendered %s from %s' % (NAME, resolve(root, R3_REL)))
    if a.stage:
        dest = os.path.join(STAGE_ROOT, IMG_REL)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        artgen.save_png(im, dest)
        print('staged ->', dest)
    if not a.no_review:
        old_p = os.path.join(BASE_ROOT, IMG_REL)
        old = Image.open(old_p if os.path.exists(old_p) else artgen.shipped(NAME)).convert('RGBA')
        print('review ->', review_sheet(old, im, load_r3(root), os.path.join(out, '_review.png')))


if __name__ == '__main__':
    main()
