"""THE RETRIEVER'S FLAME, SCALED (2026-09-26, user on build 14: "too much flames ...
25% less flames on the tomahawk ... it's really hard to see the tomahawk").

Copies the Origins fire staff's bolt trail (weapon/zmb_staff/fx_zmb_staff_fire_trail_bolt,
a real source in the tools root; the hellhound trail is a stub) into the repo as
share/raw/fx/tod/archer/fx_tod_ret_fire.efx with every particle's SIZE, ALPHA and
light-intensity graphs multiplied by SCALE (0.75 = a quarter less flame). Materials,
counts, motion and timing are untouched, so the fire keeps its shape and just
sits lower around the axe. The donor has no child effects.

Re-run after changing SCALE; `--check` fails if the output is stale (a build gate
can call it). Never hand-edit the output.
"""
import argparse, os, re, sys

TOOLS_FX = r"C:\BO3Tools\TOD2Cybercity\share\raw\fx"
DONOR = "weapon/zmb_staff/fx_zmb_staff_fire_trail_bolt"
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "share", "raw", "fx", "tod", "archer", "fx_tod_ret_fire.efx")
OUT_PATH = "tod/archer/fx_tod_ret_fire"     # the zone / precache / TOD_RET_FIRE_FX name
SCALE = 0.75
GRAPHS = ("alphaGraph", "sizeGraph0", "sizeGraph1", "lightIntensityGraph")
FX_PATH_MAX = 63
# THE "LAVA SKIN" (user on build 16: "some kind of like lava skin to the tomahawk ... not just
# a flame ... something kind of blocking it"): the donor wraps its bolt in three MESH elements -
# two shaped fireball spheres and a long tendril sphere - that engulf a thrown axe. They are
# dropped whole; the sprite flames, smoke and sparks stay. The flare the donor attaches to
# def6 (fx_zmb_staff_fire_trail_bolt_c = one superflare sprite, unscaled because it is a child)
# is cleared too: it sits on the axe as a bright bloom.
DROP_ELEMS = ("wraith_looping_def3", "wraith_looping_def4", "wraith_looping_def8")
DROP_MESHES = ("fxuse_sphere_fireball_cold_shaped", "fxuse_sphere_fireball_shaped", "fxuse_sphere_tendril_long")
CLEAR_ATTACH = ("weapon/zmb_staff/fx_zmb_staff_fire_trail_bolt_c",)


def scale_graphs(text, scale):
    out, i = [], 0
    for m in re.finditer(r'\n\t(?:%s)[^\n]*\n\t\{' % "|".join(GRAPHS), text):
        if m.start() < i:
            continue
        j, depth = m.end(), 1
        while depth:
            c = text[j]
            depth += (c == '{') - (c == '}')
            j += 1
        out.append(text[i:m.end()])
        block = re.sub(r'(?m)^(\t+)([\d.]+) ([\d.]+)(\r?)$',
                       lambda r: "%s%s %.6f%s" % (r.group(1), r.group(2), float(r.group(3)) * scale, r.group(4)),
                       text[m.end():j])
        out.append(block)
        i = j
    out.append(text[i:])
    return "".join(out)


def drop_elements(text, names):
    """Remove whole top-level element blocks ('{' + name line ... matching '}')."""
    for name in names:
        key = '\tname "%s";' % name
        k = text.find(key)
        if k < 0:
            sys.exit("element %s not in the donor" % name)
        s = text.rfind('{', 0, k)
        j, depth = s + 1, 1
        while depth:
            c = text[j]
            depth += (c == '{') - (c == '}')
            j += 1
        while j < len(text) and text[j] in '\r\n':
            j += 1
        text = text[:s] + text[j:]
    return text


def render():
    src = os.path.join(TOOLS_FX, DONOR.replace("/", os.sep) + ".efx")
    with open(src, "r", encoding="latin-1", newline="") as f:
        text = f.read()
    if "gfx_debug_missing_fx" in text:
        sys.exit("donor %s is a stub" % DONOR)
    # child refs with a NAME (an empty "" field is the donor saying "none")
    if re.search(r'\n\t(?:fxOnImpact|fxOnDeath|emission)\s+"[^"]+"', text) or re.search(r'\n\trunner\s*\n\t\{\s*\n\t\t"[^"]+"', text):
        sys.exit("donor %s spawns children; scale them too before using it" % DONOR)
    if len(OUT_PATH) > FX_PATH_MAX:
        sys.exit("fx path too long")
    text = drop_elements(text, DROP_ELEMS)
    for m in DROP_MESHES:
        if m in text:
            sys.exit("mesh %s still present" % m)
    for a in CLEAR_ATTACH:
        n = text.count('attachment "%s";' % a)
        if n != 1:
            sys.exit("attachment %s found %d times" % (a, n))
        text = text.replace('attachment "%s";' % a, 'attachment "";')
    return scale_graphs(text, SCALE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = render()
    if a.check:
        cur = open(OUT, "r", encoding="latin-1", newline="").read() if os.path.exists(OUT) else None
        print("make_ret_fire_fx --check:", "OK" if cur == text else "STALE")
        sys.exit(0 if cur == text else 1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="latin-1", newline="") as f:
        f.write(text)
    n = sum(text.count("\n\t" + g) for g in GRAPHS)
    print("wrote %s (%d B, %d graphs x %.2f)" % (OUT_PATH, len(text), n, SCALE))


if __name__ == "__main__":
    main()
