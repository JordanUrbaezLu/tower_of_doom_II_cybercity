"""Slot maps + the screen layout for the BLACK MARKET SPIN art request (docs/190).

Every box here is the SAME number TodSpinReel.lua uses (canvas 1280x720), so the
art the generator draws and the wiring cannot drift. Re-run after any layout
change:  python tools/partner_shop/gen_spin_art_refs.py
Writes docs/190_ref/*.png.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'docs', '190_ref')
FONT = os.path.join(ROOT, 'fonts', 'tod_tower1.ttf')
os.makedirs(OUT, exist_ok=True)

BG = (16, 16, 22)
COLS = [(90, 160, 255), (255, 206, 80), (90, 230, 120), (255, 96, 96), (190, 120, 255),
        (255, 140, 80), (80, 220, 240), (255, 150, 200), (200, 200, 200), (160, 255, 160)]
RAR = [(233, 238, 245), (58, 168, 255), (181, 92, 255), (255, 194, 61)]


def font(n):
    return ImageFont.truetype(FONT, n)


# ---- the numbers (LOCKSTEP with TodSpinReel.lua) ------------------------------
PANEL = (100, 112, 1180, 548)          # the frame image's rect on the canvas
REEL = (140, 160, 1140, 272)           # the transparent reel window
HEADER = (100, 112, 1180, 152)           # leaves 8 units above the window for its rim
TITLE = (400, 116, 880, 148)           # baked "BLACK MARKET"
LUCK = (960, 118, 1160, 146)           # empty: the game writes LUCK 80
NEEDLE = (628, 146, 652, 286)          # the needle image
TILE_W, TILE_H, PITCH = 140, 104, 150
BANNER = (440, 286, 840, 338)          # the rarity banner image
NAME = (340, 342, 940, 370)            # game text
EFFECT = (240, 374, 1040, 392)         # game text
STATUS = (340, 396, 940, 414)          # game text
BOX_W, BOX_H, BOX_GAP = 200, 72, 16
BOX_Y = 432
BOX_X0 = 640 - (4 * BOX_W + 3 * BOX_GAP) // 2
HINT = (240, 514, 1040, 534)           # game text (the controls line)
CHIP = 28                              # chips: 3 x 28, gap 4, right edge 1190, bottom 520: on the COMPANION STATUS
CHIP_RIGHT, CHIP_BOTTOM, CHIP_GAP = 1280 - 90, 720 - 200, 4   # PLATE's top edge (PK08, 2026-10-05; was 1238 / 484)
COMP_PLATE = (1002, 524, 1190, 562)    # TodCompanionPlate.lua CP (X0, Y0, X0 + W, Y0 + H): the plate the chips sit on

# tile interior (units inside the 140x104 tile)
T_ICON = (44, 8, 96, 60)
T_NAME = (6, 64, 134, 80)
T_RAR = (10, 84, 130, 100)
# socket interior (units inside the 200x72 socket)
S_LABEL = (64, 6, 194, 20)
S_ICON = (10, 14, 58, 62)
S_NAME = (64, 24, 194, 44)
S_RAR = (64, 48, 194, 64)


def box(d, r, col, w=2, label=None, f=None, s=1.0, ox=0, oy=0):
    x0, y0, x1, y1 = [v * s for v in r]
    x0 += ox; x1 += ox; y0 += oy; y1 += oy
    d.rectangle([x0, y0, x1, y1], outline=col, width=w)
    if label:
        d.text((x1 - 6, y0 + 4), label, fill=col, font=f, anchor='ra')


def legend(img_w, rows, top, fsize=22):
    h = top + 14 + len(rows) * (fsize + 10) + 10
    im = Image.new('RGB', (img_w, h), BG)
    d = ImageDraw.Draw(im)
    f = font(fsize)
    for i, (col, text) in enumerate(rows):
        d.text((14, top + 14 + i * (fsize + 10)), text, fill=col, font=f)
    return im, d


# ---- 1. the frame slot map: 2160x872 (2 px per canvas unit) ------------------
def frame_map():
    s = 2
    W, H = (PANEL[2] - PANEL[0]) * s, (PANEL[3] - PANEL[1]) * s
    rows = []
    items = [
        (HEADER, 'HEADER BAND - YOU DRAW IT'),
        (TITLE, 'TITLE - BAKE  BLACK MARKET  HERE'),
        (LUCK, 'LUCK WINDOW - EMPTY DARK, GAME TEXT'),
        (REEL, 'REEL WINDOW - FULLY TRANSPARENT'),
        ((EFFECT[0], BANNER[1], EFFECT[2], STATUS[3]), 'PRIZE AREA - FLAT DARK, GAME DRAWS'),
        ((BOX_X0, BOX_Y, BOX_X0 + 4 * BOX_W + 3 * BOX_GAP, BOX_Y + BOX_H), 'SLOT ROW - FLAT DARK, GAME DRAWS'),
        (HINT, 'CONTROLS LINE - FLAT DARK, GAME TEXT'),
    ]
    im, d = legend(W, [], 0)
    im = Image.new('RGB', (W, H + 14 + len(items) * 34 + 10), BG)
    d = ImageDraw.Draw(im)
    f = font(22)
    d.rectangle([0, 0, W - 1, H - 1], outline=(120, 120, 140), width=2)
    for i, (r, name) in enumerate(items):
        col = COLS[i]
        rr = (r[0] - PANEL[0], r[1] - PANEL[1], r[2] - PANEL[0], r[3] - PANEL[1])
        box(d, rr, col, 3, str(i + 1), f, s)
        px = [v * s for v in rr]
        d.text((14, H + 14 + i * 34), f'{i + 1} {name}   X {px[0]}..{px[2]}   Y {px[1]}..{px[3]}', fill=col, font=f)
    im.save(os.path.join(OUT, 'frame_slot_map_2160x872.png'))


# ---- 2. the tile slot map: 560x416 (4x) ---------------------------------------
def tile_map():
    s = 4
    W, H = TILE_W * s, TILE_H * s
    items = [(T_ICON, 'ICON WELL (GAME DRAWS)'), (T_NAME, 'ITEM NAME (GAME TEXT)'),
             (T_RAR, 'RARITY WORD (BAKE IT)')]
    im = Image.new('RGB', (W, H + 14 + len(items) * 30 + 10), BG)
    d = ImageDraw.Draw(im)
    f = font(20)
    d.rectangle([0, 0, W - 1, H - 1], outline=(120, 120, 140), width=2)
    for i, (r, name) in enumerate(items):
        col = COLS[i]
        box(d, r, col, 3, str(i + 1), f, s)
        px = [v * s for v in r]
        d.text((10, H + 14 + i * 30), f'{i + 1} {name}  X {px[0]}..{px[2]} Y {px[1]}..{px[3]}', fill=col, font=f)
    im.save(os.path.join(OUT, 'tile_slot_map_560x416.png'))


# ---- 3. the socket slot map: 800x288 (4x) -------------------------------------
def socket_map():
    s = 4
    W, H = BOX_W * s, BOX_H * s
    items = [(S_ICON, 'ICON WELL - GAME DRAWS THE ITEM ICON'), (S_LABEL, 'SLOT LABEL - GAME TEXT'),
             (S_NAME, 'ITEM NAME - GAME TEXT'), (S_RAR, 'RARITY - GAME TEXT')]
    im = Image.new('RGB', (W, H + 14 + len(items) * 30 + 10), BG)
    d = ImageDraw.Draw(im)
    f = font(20)
    d.rectangle([0, 0, W - 1, H - 1], outline=(120, 120, 140), width=2)
    for i, (r, name) in enumerate(items):
        col = COLS[i]
        box(d, r, col, 3, str(i + 1), f, s)
        px = [v * s for v in r]
        d.text((10, H + 14 + i * 30), f'{i + 1} {name}  X {px[0]}..{px[2]} Y {px[1]}..{px[3]}', fill=col, font=f)
    im.save(os.path.join(OUT, 'socket_slot_map_800x288.png'))


# ---- 4. the whole screen, landed on an EPIC (layout only, flat colours) -------
def screen():
    im = Image.new('RGB', (1280, 720), (8, 6, 14))
    d = ImageDraw.Draw(im)
    f = font(16); fb = font(26); fs = font(12)
    # a fake game world behind (dark towers) so the panel reads as an overlay
    for i in range(0, 1280, 90):
        d.rectangle([i + 10, 300 + (i * 37) % 200, i + 60, 720], fill=(14, 10, 26), outline=(60, 30, 90))
    d.rectangle(PANEL, fill=(12, 7, 22), outline=(255, 43, 209), width=2)
    d.rectangle(HEADER, fill=(31, 19, 54))
    d.text(((TITLE[0] + TITLE[2]) / 2, TITLE[1] + 4), 'BLACK MARKET', fill=(255, 43, 209), font=fb, anchor='ma')
    d.rectangle(LUCK, fill=(6, 4, 12), outline=(74, 58, 112))
    d.text((LUCK[2] - 8, LUCK[1] + 6), 'LUCK 80', fill=(31, 229, 255), font=f, anchor='ra')
    d.rectangle(REEL, fill=(4, 3, 8), outline=(31, 229, 255), width=2)
    names = ['OVERCLOCK', 'ARC CHAIN', 'SALVAGE', 'PLATING', 'NANO REPAIR', 'LONG SIGHT', 'LUCKY CHARM']
    rars = [0, 1, 0, 2, 3, 0, 1]
    x0 = 640 - TILE_W // 2 - 3 * PITCH
    for k in range(7):
        tx = x0 + k * PITCH
        if tx + TILE_W < REEL[0] or tx > REEL[2]:
            continue
        c = RAR[rars[k]]
        ty = REEL[1] + 4
        d.rectangle([max(tx, REEL[0]), ty, min(tx + TILE_W, REEL[2]), ty + TILE_H], fill=tuple(v // 6 for v in c), outline=c, width=3)
        cx = tx + TILE_W / 2
        d.rectangle([tx + T_ICON[0], ty + T_ICON[1], tx + T_ICON[2], ty + T_ICON[3]], outline=c, width=1)
        d.text((cx, ty + T_ICON[1] + 18), 'ICON', fill=c, font=fs, anchor='ma')
        d.text((cx, ty + T_NAME[1]), names[k], fill=(240, 240, 250), font=fs, anchor='ma')
        d.text((cx, ty + T_RAR[1]), ['COMMON', 'RARE', 'EPIC', 'LEGENDARY'][rars[k]], fill=c, font=fs, anchor='ma')
    # the needle: two arrow heads in the frame rim (outside the window) and a
    # hairline across the window, so it never hides a tile's icon or words
    d.line([(640, REEL[1]), (640, REEL[3])], fill=(200, 250, 255), width=1)
    d.polygon([(NEEDLE[0], NEEDLE[1]), (NEEDLE[2], NEEDLE[1]), (640, REEL[1])], fill=(31, 229, 255))
    d.polygon([(NEEDLE[0], NEEDLE[3]), (NEEDLE[2], NEEDLE[3]), (640, REEL[3])], fill=(31, 229, 255))
    epic = RAR[2]
    d.rectangle(BANNER, fill=(40, 16, 60), outline=epic, width=3)
    d.text((640, BANNER[1] + 10), 'EPIC', fill=epic, font=fb, anchor='ma')
    d.text((640, NAME[1] + 4), 'PLATING', fill=(255, 255, 255), font=font(22), anchor='ma')
    d.text((640, EFFECT[1]), 'HEALTH X1.8', fill=(210, 220, 255), font=f, anchor='ma')
    d.text((640, STATUS[1]), 'SOCKETED', fill=(31, 229, 255), font=f, anchor='ma')
    labels = ['SLOT 1', 'SLOT 2', 'SLOT 3', '']
    fill_names = [('PLATING', 2), (None, 0), (None, 0)]
    for b in range(4):
        bx = BOX_X0 + b * (BOX_W + BOX_GAP)
        r = (bx, BOX_Y, bx + BOX_W, BOX_Y + BOX_H)
        if b == 3:
            d.rectangle(r, fill=(6, 22, 28), outline=(31, 229, 255), width=2)
            d.text((bx + BOX_W / 2, BOX_Y + 22), 'SCRAP', fill=(255, 255, 255), font=font(20), anchor='ma')
            continue
        nm, rr = fill_names[b]
        c = RAR[rr] if nm else (90, 90, 100)
        d.rectangle(r, fill=(10, 8, 16), outline=c, width=2)
        d.rectangle([bx + S_ICON[0], BOX_Y + S_ICON[1], bx + S_ICON[2], BOX_Y + S_ICON[3]], outline=c, width=1)
        d.text((bx + S_LABEL[0], BOX_Y + S_LABEL[1]), labels[b], fill=(150, 150, 170), font=fs)
        d.text((bx + S_NAME[0], BOX_Y + S_NAME[1]), nm or 'EMPTY', fill=(255, 255, 255) if nm else (120, 120, 130), font=f)
        if nm:
            d.text((bx + S_RAR[0], BOX_Y + S_RAR[1]), 'EPIC', fill=c, font=fs)
    d.text((640, HINT[1]), 'TAC  < MOVE >  LETHAL      HOLD JUMP TO CONFIRM', fill=(184, 174, 216), font=fs, anchor='ma')
    # focus ring on slot 1
    d.rectangle((BOX_X0 - 4, BOX_Y - 4, BOX_X0 + BOX_W + 4, BOX_Y + BOX_H + 4), outline=(31, 229, 255), width=2)
    # chips
    for c in range(3):
        r = CHIP_RIGHT - (2 - c) * (CHIP + CHIP_GAP)
        col = [RAR[2], RAR[0], (80, 80, 90)][c]
        d.rectangle([r - CHIP, CHIP_BOTTOM - CHIP, r, CHIP_BOTTOM], fill=(10, 8, 16), outline=col, width=2)
    d.text((CHIP_RIGHT - 3 * (CHIP + CHIP_GAP), CHIP_BOTTOM - CHIP // 2), 'COMPANION CHIPS', fill=(150, 150, 170), font=fs, anchor='rm')
    d.rectangle(COMP_PLATE, outline=(31, 229, 255), width=1)
    d.text((COMP_PLATE[0] + 4, COMP_PLATE[1] + 4), 'COMPANION STATUS PLATE', fill=(150, 150, 170), font=fs)
    d.text((12, 700), 'LAYOUT ONLY - FLAT PLACEHOLDER COLOURS. THE STYLE IS THE STYLE BOARD.', fill=(255, 255, 255), font=fs)
    im.save(os.path.join(OUT, 'screen_layout_1280x720.png'))


if __name__ == '__main__':
    frame_map(); tile_map(); socket_map(); screen()
    print('wrote', sorted(os.listdir(OUT)))
