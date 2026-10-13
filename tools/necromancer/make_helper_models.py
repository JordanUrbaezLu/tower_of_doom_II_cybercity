"""THE NECROMANCER'S HELPER MODELS (2026-09-26).

User, first: "the necromanced allies ... all need to have white eyes". Then, the same
day: "they look too close to the actual enemies. So they need to be a complete black
model with white eyes and that white smoke ... the mangler uses the regular mangler
model, but it has like an orange glow, so that white smoke starts to look orange ...
still have the depth and the textures, but it should be black ... these should be
different models from the enemy models."

So every helper wears its OWN xmodel - the enemy's mesh and skeleton (same bin, same
animations, same hitboxes) with a skinOverride onto BLACK TWINS of every material:
the donor material copied field for field, its colorMap swapped for a DARKENED COPY
of the donor's colour image (grey detail kept, squeezed into BLK_FLOOR..BLK_FLOOR +
255 x BLK_GAIN, alpha kept for the hound's fur cards). The normal, gloss, occlusion
and specular maps are untouched, so the shape still reads (the depth and the
textures) - the albedo just goes black. No Blender: the geometry does not change,
only what it is painted with.

THE TINT DID NOT WORK (user, after builds 12-15: "I don't think we ever made the
models ... black"): the first cut only set colorTint 0.06 on the twins and the
helpers still wore their enemy colours. colorTint on these lit / lit_plus model
materials is not honoured (Hellbound's own black Mangler did the same and its notes
call it an "UNPROVEN override"). The darkness now lives in the IMAGE, which every
shader reads; colorTint is back to white so it cannot double-darken if it ever is
honoured.

  tod_necro_thrall_body  the charcoal horde body   (repo source_data/tod_cyber_elites.gdt)
  tod_necro_thrall_head  the charcoal horde head   (same; eyes -> white)
  tod_necro_hound        the stock hellhound       (tools root model_export/t7_characters_zombie.gdt, read only)
  tod_necro_mangler      Hellbound's BO6 Mangler   (repo donor_gdt/hellbound/hb_mangler.gdt, the donor snapshot)

Eyes: the thrall's are baked into its head material (tod_necro_eyes_white, white tint +
a white image); the hound's are an emissive_add material (tod_necro_hound_eyes: its
eye-glow copied with the white image); the Mangler has no eye material - its white
glow is the client effect on tag_eye (_tod_necro_skull.csc helper_eyes).

Everything goes into ONE GDT, source_data/tod_necro_helpers.gdt, plus the 32x32 white
image. Every donor GDT is only READ. ZONE THE XMODELS ONLY - the materials follow the
models as mc/<name> (a bare material, line for a model's material failed build 11).
Derived xmodels ship japaneseUnsafe "0" (the linker drops a flagged model the zone
names; our derived models ship unflagged - the user's call on the cyber roster).

Run it after any change to a donor GDT; --check fails if the outputs are stale.
"""
import argparse
import os
import re
import struct
import sys
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOOLS = r"C:\BO3Tools\TOD2Cybercity"
CHARCOAL_GDT = os.path.join(ROOT, "source_data", "tod_cyber_elites.gdt")
HOUND_GDT = os.path.join(TOOLS, "model_export", "t7_characters_zombie.gdt")
MANGLER_GDT = os.path.join(ROOT, "donor_gdt", "hellbound", "hb_mangler.gdt")
OUT_GDT = os.path.join(ROOT, "source_data", "tod_necro_helpers.gdt")
OUT_PNG = os.path.join(ROOT, "model_export", "tod_necro", "i_tod_necro_eyes_white.png")
BLK_DIR = "model_export/tod_necro/blk"   # the darkened colour images (repo; sync mirrors model_export/tod_necro)

BLK_FLOOR = 6       # THE LOOK KNOBS: the darkened albedo = BLK_FLOOR + grey x BLK_GAIN (sRGB, 0..255),
BLK_GAIN = 0.20     # so 6..57 - near black with the texture's own detail. Lower = blacker; the normal/gloss maps keep the shape either way
BLK_MAX = 1024      # longest side of a darkened image: a near-black albedo carries little detail, and four 4096 Mangler sheets would add ~64 MB of resident memory
BLACK_TINT = "1 1 1 1"   # colorTint stays white: the darkness is in the image (the tint was not honoured, see the header)
WHITE_TINT = "1 1 1 1"
NAME_MAX = 63

IMG = "i_tod_necro_eyes_white"
IMG_PATH = "model_export/tod_necro/i_tod_necro_eyes_white.png"
EYES = "tod_necro_eyes_white"            # the thrall's eye material (white)
HOUND_EYES = "tod_necro_hound_eyes"      # the hound's eye glow (white)

CH = "tod_charcoal_mtl_c_zom_dlc3_rus_sentinel_zombie_"
CHARCOAL_BLACK = {CH + "arms": "tod_necro_blk_charcoal_arms",
                  CH + "body": "tod_necro_blk_charcoal_body",
                  CH + "legs": "tod_necro_blk_charcoal_legs"}
CHARCOAL_EYES = "tod_charcoal_mtl_char_rus_zombie_eyes"
HOUND_BLACK = {"mtl_c_zom_der_zombie_hound_" + k: "tod_necro_blk_hound_" + k
               for k in ("body", "head", "teeth", "fur_tail", "fur_body", "fur_leg", "fur_bloody")}
HOUND_EYE_SRC = "mtl_c_zom_der_zombie_hound_eye"        # the name in the bin ...
HOUND_EYE_DONOR = "mtl_c_zom_der_zombie_hound_eye_glow"  # ... the stock model skins it with this
MANGLER_HASHES = ("1ff89f3de9582270", "22c3f289c026aa5a", "22c3f389c026ac0d", "242ae040306a6fbb",
                  "407bc047c19822a5", "44205245fb58620", "5e59a8339d298a4e", "72d123676ff9da3",
                  "7b8bd6301c002224", "7b8bd9301c00273d", "e763d0928c1de71")
MANGLER_BLACK = {"mtl_hb_mangler_" + h: "tod_necro_blk_mangler_" + h for h in MANGLER_HASHES}

# out xmodel -> (donor gdt, donor xmodel, {bin material: our material})
MODELS = {
    "tod_necro_thrall_body": (CHARCOAL_GDT, "tod_charcoal_c_zom_dlc3_zombie_sentinel_body", dict(CHARCOAL_BLACK)),
    "tod_necro_thrall_head": (CHARCOAL_GDT, "tod_charcoal_c_zom_dlc4_zombie_charred_head",
                              dict(CHARCOAL_BLACK, **{CHARCOAL_EYES: EYES})),
    "tod_necro_hound":       (HOUND_GDT, "c_zom_der_hellhound_fb", dict(HOUND_BLACK, **{HOUND_EYE_SRC: HOUND_EYES})),
    "tod_necro_mangler":     (MANGLER_GDT, "hb_bo6_mangler", dict(MANGLER_BLACK)),
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
    # set a field in a CRLF block, adding it when the donor left it out
    pat = re.compile(r'(\t\t"%s" ")([^"]*)("\r\n)' % re.escape(key))
    if pat.search(b):
        return pat.sub(lambda m: m.group(1) + value + m.group(3), b, count=1)
    i = b.index("\r\n\t{\r\n") + len("\r\n\t{\r\n")
    return b[:i] + '\t\t"%s" "%s"\r\n' % (key, value) + b[i:]


def get(b, key):
    m = re.search(r'\t\t"%s" "([^"]*)"\r\n' % re.escape(key), b)
    return m.group(1) if m else ""


def white_png(size=32):
    # RGBA (PNG colour type 6), the donor eye image's shape (Archer/lead 2026-09-26, build 11)
    raw = b"".join(b"\x00" + b"\xff\xff\xff\xff" * size for _ in range(size))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def src_file(base):
    # a GDT baseImage (escaped backslashes or forward slashes) -> the file, repo first then the tools root
    rel = base.replace("\\\\", "/").replace("\\", "/")
    for r in (ROOT, TOOLS):
        p = os.path.join(r, rel)
        if os.path.exists(p):
            return p
    sys.exit("donor image not found: " + base)


def open_image(path):
    # Pillow reads a TIFF's 4th channel only when ExtraSamples says alpha; the stock hound's
    # fur TIFs mark it 0 "unspecified" and would come in as RGB with the fur cards' alpha
    # (85% cut-out) gone. Patch that one tag to 2 in memory; the file is never written.
    from PIL import Image
    d = bytearray(open(path, "rb").read())
    if d[:2] in (b"II", b"MM"):
        e = "<" if d[:2] == b"II" else ">"
        off = struct.unpack(e + "I", d[4:8])[0]
        for i in range(struct.unpack(e + "H", d[off:off + 2])[0]):
            q = off + 2 + 12 * i
            tag, typ, cnt = struct.unpack(e + "HHI", d[q:q + 8])
            if tag == 338 and typ == 3 and cnt == 1 and struct.unpack(e + "H", d[q + 8:q + 10])[0] == 0:
                d[q + 8:q + 10] = struct.pack(e + "H", 2)
    import io
    im = Image.open(io.BytesIO(bytes(d)))
    im.load()
    return im


def dark_png(path):
    # the donor colour image, greyscaled and squeezed dark; alpha kept (fur cards are alpha-tested)
    from PIL import Image
    im = open_image(path)
    if max(im.size) > BLK_MAX:
        k = BLK_MAX / max(im.size)
        im = im.resize((max(4, int(im.size[0] * k)), max(4, int(im.size[1] * k))), Image.LANCZOS)
    alpha = im.getchannel("A") if "A" in im.getbands() else None
    grey = im.convert("RGB").convert("L").point(lambda v: int(BLK_FLOOR + v * BLK_GAIN + 0.5))
    out = Image.merge("RGBA", (grey, grey, grey, alpha)) if alpha else Image.merge("RGB", (grey, grey, grey))
    import io
    buf = io.BytesIO()
    out.save(buf, "PNG", compress_level=6)
    return buf.getvalue()


def black(text, donor, name, images):
    # the black twin + its darkened colour image (images: {out png path: bytes}, filled here)
    b = rename(block(text, donor), donor, name)
    src = get(b, "colorMap")
    img = "i_" + name
    ib = rename(block(text, src), src, img)
    rel = BLK_DIR + "/" + img + ".png"
    images[os.path.join(ROOT, *rel.split("/"))] = dark_png(src_file(get(ib, "baseImage")))
    return [field(ib, "baseImage", rel), field(field(b, "colorMap", img), "colorTint", BLACK_TINT)]


def build(images):
    gdts = {p: read(p) for p in {m[0] for m in MODELS.values()}}
    charcoal, hound, mangler = gdts[CHARCOAL_GDT], gdts[HOUND_GDT], gdts[MANGLER_GDT]
    out = []

    # the white image + the two white eye materials
    img = rename(block(charcoal, "i_" + CHARCOAL_EYES), "i_" + CHARCOAL_EYES, IMG)
    out.append(field(img, "baseImage", IMG_PATH))
    eyes = rename(block(charcoal, CHARCOAL_EYES), CHARCOAL_EYES, EYES)
    for k in ("colorTint", "colorTint1"):
        eyes = field(eyes, k, WHITE_TINT)
    for k in ("colorMap", "colorMap00"):
        eyes = field(eyes, k, IMG)
    out.append(eyes)
    heyes = rename(block(hound, HOUND_EYE_DONOR), HOUND_EYE_DONOR, HOUND_EYES)
    out.append(field(field(heyes, "colorMap", IMG), "colorTint", WHITE_TINT))

    # the black twins
    for table, text in ((CHARCOAL_BLACK, charcoal), (HOUND_BLACK, hound), (MANGLER_BLACK, mangler)):
        for donor, name in table.items():
            out.extend(black(text, donor, name, images))

    # the models: donor block, renamed, skinned onto our materials
    for name, (gdt, donor, skins) in MODELS.items():
        b = rename(block(gdts[gdt], donor), donor, name)
        lines = [l for l in get(b, "skinOverride").split("\\r\\n") if l.strip()]
        lines = [l for l in lines if l.split()[0] not in skins]   # our mapping replaces the donor's for the same source
        lines = ["%s %s" % (src, dst) for src, dst in skins.items()] + lines
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
    gdt, png = build(images).encode("latin-1"), white_png()
    files = [(OUT_GDT, gdt), (OUT_PNG, png)] + sorted(images.items())
    if a.check:
        bad = 0
        for p, want in files:
            if not os.path.exists(p) or open(p, "rb").read() != want:
                print("STALE", p)
                bad += 1
        print("make_helper_models --check:", "OK" if not bad else "STALE")
        sys.exit(1 if bad else 0)
    for p, data in files:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").write(data)
    print("wrote", os.path.relpath(OUT_GDT, ROOT), "(%d blocks)," % gdt.count(b'" ( "'), os.path.relpath(OUT_PNG, ROOT),
          "and", len(images), "darkened colour images in", BLK_DIR)


if __name__ == "__main__":
    main()
