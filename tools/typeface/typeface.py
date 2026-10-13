"""typeface.py - the map typeface's ONE check + specimen tool (2026-09-29 legibility revision).

THE TYPEFACE (docs/172 option A + the legibility revision noted at its top, 2026-09-29, user: "our typography is a little bit
hard to read ... the letters and symbols are a little bit too thick ... make it a little bit easier to
read ... maybe more round"). Its masters are the two sheets:
    source_data/tod_ui_images/_sheets/i_tod_hud_letters.png   A-Z - ' (points coin) .
    source_data/tod_ui_images/_sheets/i_tod_hud_digits.png    0-9 / + -
Everything else is BUILT from them:
    source_data/tod_ui_images/_images/i_tod_hud_l* / i_tod_hud_d*   node tools/slice_hud_sheets.js --src <_sheets>
    ui/.../TodGlyphMetrics.lua + tools/tod_hud_glyphs.generated.json  (same run)
    fonts/tod_tower1.ttf (the menus' font)                         python tools/build_tod_ttf.py
    art/typeface/specimen.png (+ every art pack's typography/)     python tools/typeface/typeface.py --specimen

THE OLD FACE IS RETIRED, NOT PARKED: its sheets, font and specimen live in archive/typeface_retired/,
which nothing in the build, the HUD, the menus or the art packs reads. art/typeface/typeface.json pins
the live masters by sha256, and --check (a build gate) fails when a master changes without that file
being re-written on purpose - so the old face can never come back by accident.

  python tools/typeface/typeface.py --check        gate: masters = the pinned hashes, nothing live
                                                   references the retired folder, derived files fresh
  python tools/typeface/typeface.py --specimen     re-draw art/typeface/specimen.png from the masters
  python tools/typeface/typeface.py --pin          re-pin after a DELIBERATE redraw of the masters
"""
import argparse, hashlib, json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHEETS = os.path.join(REPO, 'source_data', 'tod_ui_images', '_sheets')
MASTERS = ['i_tod_hud_letters.png', 'i_tod_hud_digits.png']
PIN = os.path.join(REPO, 'art', 'typeface', 'typeface.json')
SPECIMEN = os.path.join(REPO, 'art', 'typeface', 'specimen.png')
TTF_PROOF = os.path.join(REPO, 'art', 'typeface', 'ttf_proof.png')   # the menus' font set as lines (not pinned)
TTF = os.path.join(REPO, 'fonts', 'tod_tower1.ttf')
METRICS = os.path.join(REPO, 'ui', 'uieditor', 'widgets', 'HUD', 'AetheriumWidgets', 'TodGlyphMetrics.lua')
RETIRED = 'archive/typeface_retired'
# the live trees a reference to the retired face must never appear in
LIVE = ['tools', 'ui', 'scripts', 'zone_source', 'source_data', 'fonts']
LET = dict(file='i_tod_hud_letters.png', cw=80, ch=112, cols=15, chars=list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') + ['-', "'", '$', '.'], base=103, cap=89)
DIG = dict(file='i_tod_hud_digits.png', cw=128, ch=160, cols=13, chars=list('0123456789') + ['/', '+', '-'], base=151, cap=137)
SPECIMEN_LINES = [(46, "0123456789"), (46, "32 / 240"), (46, "- / -   +3"), (30, "TOWER OF DOOM II"), (30, "FALLEN CYBERCITY"),
                  (30, "BLACK MARKET"), (30, "LEGENDARY +4   EPIC +3"), (30, "R-99 SPAS-12 M1927"), (30, "RASPUTIN'S RETRIBUTION"),
                  (20, "YOUR BLASTS HEAL YOU"), (20, "SPIN / SOCKET / SCRAP"), (14, "HALF SIZE: SUMMONER MASTER 5S 8B 0O 1I")]


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def ttf_digest(p):
    """the font's DRAWING (outlines, advances, character map), not its bytes: fontTools stamps a
    creation time into the file, so a rebuild from the same masters must still match."""
    from fontTools.ttLib import TTFont
    f = TTFont(p)
    h = hashlib.sha256()
    for tag in ('glyf', 'loca', 'hmtx', 'cmap', 'maxp'):
        h.update(tag.encode())
        h.update(f.getTableData(tag))
    return h.hexdigest()


def glyphs():
    out = {}
    for S in (LET, DIG):
        im = np.array(Image.open(os.path.join(SHEETS, S['file'])).convert('RGBA'))
        for i, ch in enumerate(S['chars']):
            c, r = i % S['cols'], i // S['cols']
            cell = im[r * S['ch']:(r + 1) * S['ch'], c * S['cw']:(c + 1) * S['cw']]
            a = cell[..., 3] > 24
            if a.any():
                xs = np.nonzero(a.any(axis=0))[0]
                out[(S is DIG, ch)] = (cell[:, xs.min():xs.max() + 1], S)
    return out


def compose(G, text, cap):
    """a line set like TodGlyphRow: letters at `cap`, numerals scaled to the letters' cap, one baseline."""
    pieces, x = [], 0.0
    for ch in text:
        if ch == ' ':
            x += 0.45 * cap
            continue
        if ch == ':':
            ch = '-'
        num = ch in '0123456789+/'
        key = (num, ch) if (num, ch) in G else (not num, ch)
        if key not in G:
            continue
        cell, S = G[key]
        k = cap / S['cap']   # each set at the same cap height, like a mixed line in TodGlyphRow
        im = Image.fromarray(cell, 'RGBA').resize((max(1, round(cell.shape[1] * k)), max(1, round(cell.shape[0] * k))), Image.LANCZOS)
        pieces.append((im, x, cap * 1.35 - S['base'] * k))
        x += im.width + 0.1 * cap
    canvas = Image.new('RGBA', (int(x + 4), int(cap * 1.8)), (0, 0, 0, 0))
    for im, px, py in pieces:
        canvas.alpha_composite(im, (int(round(px)), int(round(py))))
    return canvas


def specimen():
    G = glyphs()
    rows = [compose(G, t, c) for c, t in SPECIMEN_LINES]
    W = max(r.width for r in rows) + 48
    H = sum(r.height for r in rows) + 60
    sheet = Image.new('RGBA', (W, H), (12, 16, 32, 255))
    d = ImageDraw.Draw(sheet)
    d.text((24, 14), 'TOWER OF DOOM II typeface - legibility revision 2026-09-29', fill=(120, 130, 160))
    y = 40
    for r in rows:
        sheet.alpha_composite(r, (24, y))
        y += r.height
    sheet.convert('RGB').save(SPECIMEN)
    print('SPECIMEN', os.path.relpath(SPECIMEN, REPO), sheet.size)
    # the menus' TTF, built from the same masters (tools/build_tod_ttf.py)
    from PIL import ImageFont
    lines = ['ACTIVE - HEALTH 85%', 'DESTROYED - BACK IN 23 sec', 'HOLLOW, QUICK REBOOT, LUCKY CHARM',
             'SOUL SUCK  +90% DAMAGE, 5 SOULS, 6 PACKED', 'build one at a partner bench, then equip it', '5S 8B 0O 1I  0123456789',
             'burns 10%/s, slows 37.5% (4.0 sec)  100%', 'symbols  % : ; , . ! ? ( ) + - / = < > * # $ & _ |']
    rows = [(ImageFont.truetype(TTF, size), size, t) for size in (28, 16) for t in lines]
    W = 40 + max(int(f.getlength(t)) for f, _, t in rows)
    H = 50 + sum(int(sz * 1.5) for _, sz, _ in rows)
    im = Image.new('RGB', (W, H), (12, 16, 32))
    d = ImageDraw.Draw(im)
    d.text((20, 12), 'fonts/tod_tower1.ttf (the menus) - legibility revision 2026-09-29', fill=(120, 130, 160))
    y = 40
    for f, sz, t in rows:
        d.text((20, y), t, font=f, fill=(233, 238, 246))
        y += int(sz * 1.5)
    im.save(TTF_PROOF)
    print('TTF PROOF', os.path.relpath(TTF_PROOF, REPO), im.size)


def pin():
    data = {'revision': 'legibility 2026-09-29 (docs/172, top note)',
            'masters': {m: sha(os.path.join(SHEETS, m)) for m in MASTERS},
            'ttf': ttf_digest(TTF), 'specimen': sha(SPECIMEN), 'metrics': sha(METRICS),
            'retired': RETIRED}
    json.dump(data, open(PIN, 'w'), indent=2)
    print('PINNED', os.path.relpath(PIN, REPO))


def check():
    bad = []
    pinned = json.load(open(PIN))
    for m in MASTERS:
        if sha(os.path.join(SHEETS, m)) != pinned['masters'][m]:
            bad.append('master changed without a re-pin: ' + m + ' (the retired face? run --pin only for a deliberate redraw)')
    for k, p, dig in (('ttf', TTF, ttf_digest), ('specimen', SPECIMEN, sha), ('metrics', METRICS, sha)):
        if dig(p) != pinned[k]:
            bad.append('%s is not the one built from the pinned masters: %s (rebuild it, then --pin)' % (k, os.path.relpath(p, REPO)))
    pat = re.compile(r'typeface_retired|tower1_original|option_a_refined')
    for top in LIVE:
        for root, _, files in os.walk(os.path.join(REPO, top)):
            if '__pycache__' in root or os.sep + 'typeface' + os.sep + '__' in root:
                continue
            for f in files:
                p = os.path.join(root, f)
                if os.path.abspath(p) == os.path.abspath(__file__) or not f.endswith(('.py', '.js', '.ps1', '.lua', '.gsc', '.csc', '.zone', '.zpkg', '.gdt', '.json', '.csv')):
                    continue
                try:
                    if pat.search(open(p, encoding='utf-8', errors='ignore').read()):
                        bad.append('a live file references the retired typeface: ' + os.path.relpath(p, REPO))
                except OSError:
                    pass
    if bad:
        print('TYPEFACE FAIL:\n  ' + '\n  '.join(bad))
        sys.exit(1)
    print('TYPEFACE OK: masters pinned (%s), font + specimen + metrics built from them, nothing live reads the retired face' % pinned['revision'])


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--specimen', action='store_true')
    ap.add_argument('--pin', action='store_true')
    a = ap.parse_args()
    if a.specimen:
        specimen()
    if a.pin:
        pin()
    if a.check or not (a.specimen or a.pin):
        check()
