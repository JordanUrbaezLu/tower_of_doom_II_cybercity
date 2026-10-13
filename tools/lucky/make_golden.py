"""THE GOLDEN ZOMBIE'S MODELS (2026-09-29, docs/197).

User: "I would like to add a golden zombie that has a 1% chance of spawning and give 3 bars to the killer. But we
need a new model for this."

The golden zombie wears its OWN xmodels - the ordinary horde zombie's mesh and skeleton (the same XMODEL_BIN, so the
same animations, hitboxes and body plan; the charcoal horde, repo source_data/tod_cyber_elites.gdt) with a
skinOverride onto GOLD TWINS of every material. This is exactly how the Necromancer's black helpers are made
(tools/necromancer/make_helper_models.py): the donor material copied field for field, its colour image replaced by a
BAKED copy. The colour lives in the IMAGE because colorTint on these character materials is not honoured in game
(that script's header; builds 12-15). Normal and gloss maps are untouched, so the body keeps every wrinkle and seam.

THE GOLD (per pixel, from the donor colour image's own detail, levels stretched to its 2nd..98th percentiles):
  colorMap    RAMP(t) x ALBEDO   the base: deep bronze in the creases -> gold -> pale gold on the highlights
  specColorMap RAMP(t) x SPEC    coloured (metal) highlights - specMapEnable 1, specColorTint white
  colorMap00  RAMP(t) x GLOW     a faint self-glow (x scaleRGB GLOW_SCALE): the one zombie you can spot in the
                                 dark tower (materialType lit_emissive_advanced_fullspec, the same family as the donor's
                                 lit_advanced_fullspec, which already carries every emissive field)
  eyes        the donor's emissive eye material with a white image and a GOLD tint (an emissive colorTint1 IS
              honoured, unlike the lit colorTint above)

  tod_golden_zombie_body  <- tod_charcoal_c_zom_dlc3_zombie_sentinel_body   (arms / body / legs -> gold)
  tod_golden_zombie_head  <- tod_charcoal_c_zom_dlc4_zombie_charred_head    (body -> gold, eyes -> gold)

It never loses a limb (_tod_golden_zombie sets no_gib): a gib swaps the body for the charcoal gib models, which have no
gold twins. Every donor GDT is only READ. ZONE THE XMODELS ONLY (a bare material, line for a model material failed
build 11). Derived xmodels ship japaneseUnsafe "0".

  python tools/lucky/make_golden.py           write source_data/tod_golden_zombie.gdt + model_export/tod_lucky/golden/*.png
  python tools/lucky/make_golden.py --check   FAIL if any output is stale (a build gate)
"""
import argparse, io, os, re, struct, sys, zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOOLS = r"C:\BO3Tools\TOD2Cybercity"
CHARCOAL_GDT = os.path.join(ROOT, "source_data", "tod_cyber_elites.gdt")
OUT_GDT = os.path.join(ROOT, "source_data", "tod_golden_zombie.gdt")
IMG_DIR = "model_export/tod_lucky/golden"   # repo; sync_to_modtools copies model_export/tod_lucky

GOLD_MAX = 1024       # longest side of a baked image (the body sheet is 2048: gold carries its detail at 1024)
ALBEDO = 0.62         # THE LOOK KNOBS (sRGB 0..1 multipliers on the ramp)
SPEC = 0.92
GLOW = 0.45          # 0.30 until 2026-09-29 21:30 (user: "It should have a golden glow"): a clear gold glow, creases dimmer
GLOW_SCALE = 2.2      # scaleRGB of the self-glow (x2 = one stop brighter). 2.2 until 21:30; 6.0 (21:30 - 2026-09-30 00:10)
                      # was "way too intense" in game (user), so back to 2.2 with GLOW 0.45 = ~0.99, 37% of that
EYE_TINT = "1 0.76 0.18 1"
RAMP = [(0.00, (0.16, 0.085, 0.015)),   # deep bronze in the creases
        (0.45, (0.72, 0.48, 0.10)),     # gold
        (0.80, (0.96, 0.78, 0.32)),
        (1.00, (1.00, 0.93, 0.62))]     # pale gold on the highlights
NAME_MAX = 63

CH = "tod_charcoal_mtl_c_zom_dlc3_rus_sentinel_zombie_"
GOLD = {CH + "arms": "tod_golden_mtl_arms", CH + "body": "tod_golden_mtl_body", CH + "legs": "tod_golden_mtl_legs"}
CHARCOAL_EYES = "tod_charcoal_mtl_char_rus_zombie_eyes"
EYES = "tod_golden_mtl_eyes"
EYE_IMG = "i_tod_golden_eyes"
MODELS = {   # out xmodel -> (donor xmodel, {bin material: our material})  LOCKSTEP: _tod_golden_zombie.gsc TOD_GOLDEN_MODEL_*
    "tod_golden_zombie_body": ("tod_charcoal_c_zom_dlc3_zombie_sentinel_body", dict(GOLD)),
    "tod_golden_zombie_head": ("tod_charcoal_c_zom_dlc4_zombie_charred_head", dict(GOLD, **{CHARCOAL_EYES: EYES})),
}


def read(path):
    return open(path, "rb").read().decode("latin-1")


def block(text, name):
    i = text.index('\t"%s" (' % name)
    j = text.index("\n\t}", i) + len("\n\t}")
    return text[i:j]


def rename(b, old, new):
    return b.replace('\t"%s" (' % old, '\t"%s" (' % new, 1)


def field(b, key, value):
    pat = re.compile(r'(\t\t"%s" ")([^"]*)("\r\n)' % re.escape(key))
    if pat.search(b):
        return pat.sub(lambda m: m.group(1) + value + m.group(3), b, count=1)
    i = b.index("\r\n\t{\r\n") + len("\r\n\t{\r\n")
    return b[:i] + '\t\t"%s" "%s"\r\n' % (key, value) + b[i:]


def get(b, key):
    m = re.search(r'\t\t"%s" "([^"]*)"\r\n' % re.escape(key), b)
    return m.group(1) if m else ""


def src_file(base):
    rel = base.replace("\\\\", "/").replace("\\", "/")
    for r in (ROOT, TOOLS):
        p = os.path.join(r, rel)
        if os.path.exists(p):
            return p
    sys.exit("donor image not found: " + base)


def ramp(t):
    for (t0, c0), (t1, c1) in zip(RAMP, RAMP[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            return tuple(a + (b - a) * u for a, b in zip(c0, c1))
    return RAMP[-1][1]


def baked(path):
    # -> {'c': png bytes, 's': png bytes, 'e': png bytes}: the donor's detail mapped onto the gold ramp
    from PIL import Image
    im = Image.open(path); im.load()
    if max(im.size) > GOLD_MAX:
        k = GOLD_MAX / max(im.size)
        im = im.resize((max(4, int(im.size[0] * k) // 4 * 4), max(4, int(im.size[1] * k) // 4 * 4)), Image.LANCZOS)
    alpha = im.getchannel("A") if "A" in im.getbands() else None
    grey = im.convert("RGB").convert("L")
    hist = grey.histogram(); n = sum(hist); acc = 0; lo = 0; hi = 255
    for v, c in enumerate(hist):
        acc += c
        if acc <= n * 0.02: lo = v
        if acc <= n * 0.98: hi = v
    hi = max(hi, lo + 8)
    luts = {}
    for key, gain in (("c", ALBEDO), ("s", SPEC), ("e", GLOW)):
        lut = [[], [], []]
        for v in range(256):
            t = min(1.0, max(0.0, (v - lo) / float(hi - lo)))
            col = ramp(t)
            for ch in range(3):
                lut[ch].append(int(max(0, min(255, round(col[ch] * gain * 255)))))
        luts[key] = lut
    out = {}
    for key, lut in luts.items():
        chans = [grey.point(lut[ch]) for ch in range(3)]
        img = Image.merge("RGBA", chans + [alpha]) if alpha else Image.merge("RGB", chans)
        buf = io.BytesIO(); img.save(buf, "PNG", compress_level=6); out[key] = buf.getvalue()
    return out


def white_png(size=32):
    raw = b"".join(b"\x00" + b"\xff\xff\xff\xff" * size for _ in range(size))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def image_block(template_block, name, rel, semantic, srgb):
    b = rename(template_block, re.match(r'\t"([^"]+)" \(', template_block).group(1), name)
    b = field(b, "baseImage", rel)
    b = field(b, "semantic", semantic)
    b = field(b, "compressionMethod", "compressed high color" if srgb else "compressed")
    b = field(b, "coreSemantic", "sRGB3chAlpha" if srgb else "None")
    return b


def build(images):
    text = read(CHARCOAL_GDT)
    out = []
    for donor, name in GOLD.items():
        m = rename(block(text, donor), donor, name)
        src = get(m, "colorMap")
        ib = block(text, src)
        maps = baked(src_file(get(ib, "baseImage")))
        names = {}
        for key, sem, srgb in (("c", "diffuseMap", True), ("s", "specularMap", True), ("e", "diffuseMap", True)):
            img = "i_" + name + "_" + key
            rel = IMG_DIR + "/" + img + ".png"
            images[os.path.join(ROOT, *rel.split("/"))] = maps[key]
            out.append(image_block(ib, img, rel, sem, srgb))
            names[key] = img
        m = field(m, "materialType", "lit_emissive_advanced_fullspec")
        m = field(m, "colorMap", names["c"])
        m = field(m, "colorTint", "1 1 1 1")
        m = field(m, "specColorMap", names["s"])
        m = field(m, "specMapEnable", "1")
        m = field(m, "specColorTint", "1 1 1 1")
        m = field(m, "colorMap00", names["e"])
        m = field(m, "colorTint1", "1 1 1 1")
        m = field(m, "scaleRGB", str(GLOW_SCALE))
        m = field(m, "emissiveIncompetence", "1")
        out.append(m)

    # the gold eyes: the donor's emissive eye material, a white image, a gold tint
    eimg = rename(block(text, "i_" + CHARCOAL_EYES), "i_" + CHARCOAL_EYES, EYE_IMG)
    rel = IMG_DIR + "/" + EYE_IMG + ".png"
    images[os.path.join(ROOT, *rel.split("/"))] = white_png()
    out.append(field(eimg, "baseImage", rel))
    eyes = rename(block(text, CHARCOAL_EYES), CHARCOAL_EYES, EYES)
    for k in ("colorMap", "colorMap00"):
        eyes = field(eyes, k, EYE_IMG)
    for k in ("colorTint", "colorTint1"):
        eyes = field(eyes, k, EYE_TINT)
    out.append(eyes)

    for name, (donor, skins) in MODELS.items():
        b = rename(block(text, donor), donor, name)
        lines = [l for l in get(b, "skinOverride").split("\\r\\n") if l.strip()]
        lines = [l for l in lines if l.split()[0] not in skins]
        lines = ["%s %s" % (s, d) for s, d in skins.items()] + lines
        b = field(b, "skinOverride", "".join(l + "\\r\\n" for l in lines))
        b = field(b, "japaneseUnsafe", "0")
        out.append(b)

    for b in out:
        n = re.match(r'\t"([^"]+)" \(', b).group(1)
        if len(n) > NAME_MAX:
            sys.exit("%s is over %d chars" % (n, NAME_MAX))
    return "{\r\n" + "\r\n".join(out) + "\r\n}\r\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    images = {}
    gdt = build(images).encode("latin-1")
    files = [(OUT_GDT, gdt)] + sorted(images.items())
    if a.check:
        bad = [p for p, want in files if not os.path.exists(p) or open(p, "rb").read() != want]
        for p in bad:
            print("STALE", os.path.relpath(p, ROOT))
        print("GOLDEN ZOMBIE MODELS", "OK: %d files" % len(files) if not bad else "STALE - run python tools/lucky/make_golden.py")
        sys.exit(1 if bad else 0)
    for p, data in files:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").write(data)
    print("wrote", os.path.relpath(OUT_GDT, ROOT), "(%d blocks) and" % gdt.count(b'" ( "'), len(images), "images in", IMG_DIR)


if __name__ == "__main__":
    main()
