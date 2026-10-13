"""THE AMBIENCE ANCHORS (PK23, 2026-10-05): scripts/zm/zm_tod2_cybercity/_tod_amb_data.csc, GENERATED from the zone
volumes of the GENERATED map (map_source/zm/zm_tod2_cybercity.map) - never a coordinate typed into script.

  ROOMS    every brush of the Undercity's zones (vault, conduit, the four wings) = kind "undercity": the wind and the
           far-city beds fall silent inside (walls and a ceiling), the room tone plays from its anchors, the drips and
           pipe knocks fall at random points inside. The plaza (base_zone) = kind "plaza": its own street bed. The
           Battle Arena and the Dealer's rooms (arena_zone, house_zone, house_parlour_zone) = kind "quiet": no world
           bed at all (those rooms carry their own scores).
  EMITTERS the room-tone anchors: one per room box centre at standing height, more along a long box (one per
           EMIT_STEP units), so no corner of a room is out of its tone's reach (the loops' DistMaxDry is 1400).

  python tools/sfx/w2c_sounds/gen_amb_data.py [--out-root DIR]   write the file (DIR default: the repo)
  python tools/sfx/w2c_sounds/gen_amb_data.py --check [--root DIR]   regenerate in memory, compare (make_sounds --check runs it)
A geometry change to those zones in tools/gen_tower_map.js changes the .map; re-run this after it (the gate says so).
"""
import argparse, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
MAP_REL = "map_source/zm/zm_tod2_cybercity.map"
OUT_REL = "scripts/zm/zm_tod2_cybercity/_tod_amb_data.csc"
KINDS = {"vault_zone": "undercity", "conduit_zone": "undercity", "wing_n_zone": "undercity", "wing_e_zone": "undercity",
         "wing_s_zone": "undercity", "wing_w_zone": "undercity", "base_zone": "plaza",
         "arena_zone": "quiet", "house_zone": "quiet", "house_parlour_zone": "quiet"}
EMIT_STEP = 1100        # one room-tone anchor per this many units along a long box
EMIT_LIFT = 96          # anchors stand this far above the volume's floor (ear height)
FIX = "run: python tools/sfx/w2c_sounds/gen_amb_data.py"


def volumes(text):
    """{targetname: [(mins, maxs), ...]} for the info_volume entities named in KINDS (axis-aligned box brushes)"""
    out = {}
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip() != '"classname" "info_volume"':
            continue
        # the entity: from the "{" two lines up to the line where the brace depth returns to zero (brushes nest one deep)
        j = i
        while j > 0 and lines[j].strip() != "{":
            j -= 1
        depth, k = 0, j
        while k < len(lines):
            s = lines[k].strip()
            if s == "{":
                depth += 1
            elif s == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        body = "\n".join(lines[j + 1:k])
        tn = re.search(r'^"targetname" "([^"]+)"', body, re.M)
        if not tn or tn.group(1) not in KINDS:
            continue
        boxes = []
        for b in re.finditer(r'\{\s*\n\s*guid "[^"]*"\s*\n(.*?)\n\s*\}', body, re.S):
            lo, hi = [None] * 3, [None] * 3
            for line in b.group(1).splitlines():
                pts = re.findall(r'\(\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\)', line)
                if len(pts) != 3:
                    continue
                p = [[float(v) for v in q] for q in pts]
                for ax in range(3):
                    if p[0][ax] == p[1][ax] == p[2][ax]:
                        v = p[0][ax]
                        lo[ax] = v if lo[ax] is None else min(lo[ax], v)
                        hi[ax] = v if hi[ax] is None else max(hi[ax], v)
            if None in lo or None in hi:
                raise SystemExit("AMB DATA: a %s brush is not an axis-aligned box" % tn.group(1))
            boxes.append((tuple(lo), tuple(hi)))
        out.setdefault(tn.group(1), []).extend(boxes)
    return out


def fmt(v):
    return "( %s )" % ", ".join(("%d" % x) if float(x).is_integer() else ("%.1f" % x) for x in v)


def render(root):
    path = os.path.join(root, MAP_REL.replace("/", os.sep))
    if not os.path.exists(path):
        path = os.path.join(REPO, MAP_REL.replace("/", os.sep))
    text = open(path, encoding="utf-8", errors="replace").read()
    vols = volumes(text)
    missing = [k for k in KINDS if k not in vols]
    if missing:
        raise SystemExit("AMB DATA: the map has no zone volume %s" % ", ".join(missing))
    rooms, emit = [], []
    for name in KINDS:
        for lo, hi in vols[name]:
            rooms.append((KINDS[name], name, lo, hi))
            if KINDS[name] == "quiet":
                continue
            sx, sy = hi[0] - lo[0], hi[1] - lo[1]
            nx, ny = max(1, int(round(sx / EMIT_STEP))), max(1, int(round(sy / EMIT_STEP)))
            for i in range(nx):
                for j in range(ny):
                    emit.append((KINDS[name], (lo[0] + sx * (i + 0.5) / nx, lo[1] + sy * (j + 0.5) / ny, lo[2] + EMIT_LIFT)))
    L = ["// GENERATED by tools/sfx/w2c_sounds/gen_amb_data.py from the zone volumes of map_source/zm/zm_tod2_cybercity.map",
         "// - DO NOT HAND-EDIT (re-run the tool after a zone change). THE WORLD AMBIENCE (PK23): read by _tod_amb.csc.",
         "// %d room boxes (%s), %d room-tone anchors." % (len(rooms), ", ".join(sorted(set(k for k, _, _, _ in rooms))), len(emit)),
         "", "#namespace tod_amb_data;", "",
         "// the rooms: kind \"undercity\" (no wind / city bed, the room tone, drips + pipe knocks), \"plaza\" (the street",
         "// bed), \"quiet\" (no world bed: the Battle Arena and the Dealer's rooms)",
         "function room_count() { return %d; }" % len(rooms),
         "function room_kinds()", "{", "\ta = [];"]
    L += ['\ta[ %d ] = "%s";   // %s' % (i, k, n) for i, (k, n, _, _) in enumerate(rooms)]
    L += ["\treturn a;", "}", "function room_mins()", "{", "\ta = [];"]
    L += ["\ta[ %d ] = %s;" % (i, fmt(lo)) for i, (_, _, lo, _) in enumerate(rooms)]
    L += ["\treturn a;", "}", "function room_maxs()", "{", "\ta = [];"]
    L += ["\ta[ %d ] = %s;" % (i, fmt(hi)) for i, (_, _, _, hi) in enumerate(rooms)]
    L += ["\treturn a;", "}", "", "// the room-tone anchors (kind, origin)",
          "function emitter_count() { return %d; }" % len(emit), "function emitter_kinds()", "{", "\ta = [];"]
    L += ['\ta[ %d ] = "%s";' % (i, k) for i, (k, _) in enumerate(emit)]
    L += ["\treturn a;", "}", "function emitter_orgs()", "{", "\ta = [];"]
    L += ["\ta[ %d ] = %s;" % (i, fmt(o)) for i, (_, o) in enumerate(emit)]
    L += ["\treturn a;", "}", ""]
    return "\n".join(L), rooms, emit


def check(root):
    try:
        want, _, _ = render(root)
    except SystemExit as e:
        return [str(e)]
    p = os.path.join(root, OUT_REL.replace("/", os.sep))
    cur = open(p, encoding="utf-8", newline="").read() if os.path.exists(p) else None
    return [] if cur == want else ["%s is stale against the map's zone volumes - %s" % (OUT_REL, FIX)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--out-root", default=REPO)
    a = ap.parse_args()
    if a.check:
        bad = check(os.path.abspath(a.root))
        print("AMB DATA " + ("OK" if not bad else "STALE: " + "; ".join(bad)))
        sys.exit(1 if bad else 0)
    text, rooms, emit = render(os.path.abspath(a.out_root))
    p = os.path.join(os.path.abspath(a.out_root), OUT_REL.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8", newline="").write(text)
    for k, n, lo, hi in rooms:
        print("%-10s %-20s %s .. %s" % (k, n, fmt(lo), fmt(hi)))
    print("wrote", p, "rooms", len(rooms), "emitters", len(emit))


if __name__ == "__main__":
    main()
