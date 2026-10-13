"""THE WUNDERSTRAHL EMITTER ASSEMBLY - parametric geometry (pure Python + mathutils; no bpy needed to build).

Every new part is a revolve (lathe profile around an arbitrary axis) or a sweep along a spline. Each part owns one
rectangular UV island measured in real inches (u = arc length around, v = length along the FULL profile), so one
shelf packing places all islands in the shared emitter atlas, and every LOD rebuilds the same parts - fewer angular
segments, profile points dropped but each kept point keeping its full-profile v - onto the SAME island transforms.
Gun space: native inches, X forward, Y = the gun's left, Z up. The beam axis runs through tag_flash
(41.0, 0, 3.1414) along +X; the whole assembly stays within ~3.1 of it.

Zones (one face material each; the baked atlas carries them all): gunmetal, brass, lip (yellow emissive inner lip),
crystal (the faceted focusing lens), sheath (conduit braid), stripe (conduit light line), dark (bores / recesses).

Review passes 2-3 (2026-10-06): the focusing ring is an OPEN WHEEL - a hoop each claw hook plugs into through a brass
ferrule on the hook's own axis, a hub carrying the lens housing, five spokes BETWEEN the claws (the tie rods' line)
and five windows that show the cage behind it; the old solid disc read as a speaker grille and hid the cage. The
crystal is a staggered cut (triangle facets, a 12-facet star table). The far-LOD spine runs back into the DG-2
receiver, and levels 5-6 carry swept stand-ins for the five claws the DG-2's own far LODs break up or drop, so no
LOD floats the emitter or leaves orphaned claw tips (verify_art measures both). Fasteners buried in a surface have
no buried cap (a cap facing the surface it sits in bent that surface's baked normal inside out).
"""
import math
from mathutils import Vector

AXZ = 3.1414
ZONES = ['gunmetal', 'brass', 'lip', 'crystal', 'sheath', 'stripe', 'dark']
LEVELS = 8   # 0 = first person ... 7 = the farthest world LOD (focusing ring, housing, crystal, spine)

# ---- design constants (inches), measured against the untouched DG-2 (art/wunderstrahl/design.json) -----------
# The DG-2's five copper claws (at 18 + 72k degrees) flare like a tulip: nearest surface radius 1.86 at x 36.4,
# 2.28 at 37.0, 2.84 at 37.5, 4.1 at 38.5, then the hooks curl back in to 3.2 at x 39.2 (tools diag_claws.py).
# So: ring 1 ENCLOSES the copper cage ring the claws grow from (their roots socket into it); ring 2 sits inside the
# tulip; the focusing ring sits just behind the hook tips so the claws visibly clutch its hoop; three tie rods in the
# claw gaps carry the stack; the housing + crystal ride the rod's tip in front of the focusing ring's hub.
RINGS = [  # name, centre x, depth, bore radius, outer radius, brass band height
    ('Emitter ring 1 (claw mount)', 35.85, 0.60, 1.40, 2.12, 0.06),
    ('Emitter ring 2', 37.25, 0.40, 1.30, 2.05, 0.06),
]
# THE FOCUSING RING (an open wheel). The DG-2 hook tips end in points at x 39.073 (claw_tip_probe): radius 2.82-2.94
# (the claw ring sits 0.065 high on the axis) near their claw angles; each plugs into a brass ferrule on the hoop.
FR_X0, FR_X1 = 38.62, 39.02                # hoop + hub depth: front face just behind the hook tips
HOOP_IN, HOOP_OUT, HOOP_BAND = 2.52, 2.95, 0.07
HUB_IN, HUB_OUT = 1.55, 1.98
SPOKE_R0, SPOKE_R1 = 1.92, 2.58            # spoke ends buried in the hub and the hoop
SPOKE_X0, SPOKE_X1, SPOKE_W = 38.68, 38.94, 0.20   # set back from both faces
CLAW_ANGLES = (18.0, 90.0, 162.0, 234.0, 306.0)
# Spokes sit BETWEEN the claws (review pass 2: on the claw axes the claws read as a ship's wheel's handles); three of
# them carry the tie rods, and a hub bolt fastens each one.
SPOKE_ANGLES = (54.0, 126.0, 198.0, 270.0, 342.0)
CLAW_TIP_X = 39.073
CLAW_TIPS = ((2.896, 19.38), (2.940, 90.0), (2.896, 160.62), (2.822, 233.07), (2.822, 306.93))   # (radius, angle)
# Each hook's last segment runs (dx, dr) = (-0.087, -0.367) into its point (claw_tip_probe): a brass ferrule on that
# axis takes the last 0.2 in of the hook, so the claw plugs INTO the focusing ring instead of touching it at a point.
HOOK_DIR = (-0.231, -0.973)
FERRULE_R, FERRULE_IN, FERRULE_OUT = 0.07, 0.06, 0.20
HUB_BOLT_ANGLES = SPOKE_ANGLES
HUB_BOLT_R = 1.80
# The claw ring sits 0.065 ABOVE the beam axis (fits all five measured tip radii 2.822..2.940 at rho 2.875), and this
# is the top claw's centreline about that centre, traced from the DG-2 mesh: root at the cage ring, the tulip flare,
# the hook curling back to the tip. The far-LOD claws (levels 5-6) are swept along it.
CLAW_RING_DZ = 0.065
CLAW_PATH = [(35.90, 1.82), (36.50, 2.08), (37.00, 2.48), (37.50, 3.18), (38.00, 3.80), (38.50, 4.22), (38.95, 4.24),
             (39.25, 4.08), (39.34, 3.80), (39.28, 3.42), (39.17, 3.12), (39.073, 2.875)]
FAR_CLAW = {5: (4, 0.085, 0.50), 6: (3, 0.095, 0.80)}   # level: (sides, tube radius - thickened for distance, step)
SPINE_X0, SPINE_X1, SPINE_R = 19.0, 39.35, 0.55      # far LODs: from inside the DG-2's receiver to the housing (its
#                                                       bore is 0.60: the housing sits on it; the DG-2's own far-LOD rod is r ~0.55)
HOUSING_X0, HOUSING_X1 = 38.98, 39.98     # lens housing: rear collar on the ribbed rod -> cup -> brass retaining ring
# The crystal's back cone starts just in front of the ribbed rod's end (x 39.66), never through it.
LENS_BACK, LENS_GIRDLE0, LENS_GIRDLE1, LENS_FRONT = 39.70, 39.86, 40.06, 40.99
LENS_TIP = 40.998                         # the table rises to a shallow 12-facet pyramid (a star), apex just behind 41.0
LENS_R, LENS_TABLE_R = 0.97, 0.52
TIE_ANGLES = (54.0, 126.0, 270.0)          # in the gaps between the five claws (90 + k*72 deg)
TIE_R, TIE_ROD_R = 1.80, 0.072             # tie rods: ring 1 front face -> the focusing ring hub's back face
CONDUIT_R = 0.072
CONDUIT_Y = 0.55
# The conduits ride the collar and the bellows, then arc OVER the copper rail that drops from the top centre
# (z ~5.5 at x 26-27) to the upper left (z ~4.4 at x 27.6-30.3), clamped beside the copper mushroom cap the rail
# rises from (x 26.2-26.5, |y| <= 0.43), then settle onto the rear cage ring and run into ring 1 (diag_overlap.py).
CONDUIT_PATH = [(18.56, 4.20), (19.02, 4.34), (19.45, 4.52), (20.40, 4.53), (21.40, 4.49), (24.60, 4.52),
                (25.60, 4.95), (26.30, 5.55), (27.00, 5.74), (27.60, 5.70), (28.60, 5.45), (29.60, 5.25),
                (30.30, 5.18), (33.00, 5.20), (34.90, 5.16), (35.56, 5.06)]
GLAND = ((18.16, 4.19), (18.62, 4.20))    # brass glands on the glass tube's front cap ridge (top z 4.06)
FERRULE = ((35.30, 5.11), (35.57, 5.06))  # brass ferrules where the conduits enter ring 1's rear face
CLAMPS_X = (20.10, 26.30, 30.65)           # conduit clamp collars (+ standoffs down to what they grip)
STANDOFF_FOOT_Z = {20.10: 4.40, 26.30: 99.0, 30.65: 4.93}   # 99 = no standoff: the collar bears on the cap's side
SEGS = [64, 40, 28, 18, 12, 8, 6, 6]       # angular segments per level (rings, housing)
SMALL = [12, 10, 8, 6, 6, 0, 0, 0]         # small round parts (0 = dropped at that level)
LENS_SEGS = [12, 12, 10, 8, 8, 6, 6, 6]
CONDUIT = [(10, .20), (8, .32), (6, .55), (6, .9), (4, 1.6), (0, 0), (0, 0), (0, 0)]   # (sides, step); 0 = dropped


def axis_point(x, r, angle_deg):
    a = math.radians(angle_deg)
    return Vector((x, r * math.cos(a), AXZ + r * math.sin(a)))


class Part:
    """Polygon soup with per-face zone, per-corner UV in island inches and the key of the island each face lies in
    (big revolves are split into half-circle islands so the packer can use the whole atlas square)."""
    def __init__(self, name, smooth_angle=34.0, flat=False):
        self.name = name; self.verts = []; self.faces = []; self.smooth_angle = smooth_angle; self.flat = flat
        self.islands = {}

    def add_vert(self, co):
        self.verts.append(Vector(co)); return len(self.verts) - 1

    def add_face(self, ids, zone, uvs, island=None):
        self.faces.append((tuple(ids), zone, tuple(tuple(u) for u in uvs), island or self.name))


def with_v(profile):
    """Attach full-profile arc length (island v) to each point: (t, r, zone) -> (t, r, zone, v)."""
    out = [(profile[0][0], profile[0][1], profile[0][2], 0.0)]
    acc = 0.0
    for i in range(1, len(profile)):
        acc += math.hypot(profile[i][0] - profile[i - 1][0], profile[i][1] - profile[i - 1][1])
        out.append((profile[i][0], profile[i][1], profile[i][2], acc))
    return out


def revolve(name, profile, segs, circ, length, origin=(0, 0, AXZ), axis=(1, 0, 0), ref=None, start=0.0, flat=False,
            smooth=34.0, borrow=None):
    """profile: [(t, r, zone, v)] - t along the axis from origin, r from it, v = island coordinate. The zone of a
    segment is its start point's zone. r == 0 points become poles (triangle fans). circ/length = island size; a
    revolve wider than 6 inches around is split into two half-circle islands (every level's segs is even).
    borrow=(island key, (w, h)): a far-LOD-only part maps itself, scaled to fit, onto an existing level-0 island."""
    part = Part(name, smooth, flat)
    sectors = 1 if borrow else (2 if circ > 6.0 else 1)
    if borrow is None:
        for s in range(sectors):
            part.islands[name if sectors == 1 else '%s #%d' % (name, s)] = (circ / sectors, length)
    su = sv = 1.0
    if borrow is not None:
        su = borrow[1][0] / circ; sv = borrow[1][1] / max(length, 1e-6)
    axis = Vector(axis).normalized()
    if ref is None:
        ref = Vector((0, 0, 1)) if abs(axis.z) < .9 else Vector((0, 1, 0))
    b1 = (Vector(ref) - axis * Vector(ref).dot(axis)).normalized(); b2 = axis.cross(b1).normalized()
    o = Vector(origin)
    rings = []
    for (t, r, z, v) in profile:
        if r <= 1e-6:
            rings.append([part.add_vert(o + axis * t)]); continue
        rings.append([part.add_vert(o + axis * t + (b1 * math.cos(start + 2 * math.pi * k / segs) +
                                                    b2 * math.sin(start + 2 * math.pi * k / segs)) * r)
                      for k in range(segs)])
    for i in range(len(profile) - 1):
        zone = profile[i][2]; v0 = profile[i][3]; v1 = profile[i + 1][3]
        A, B = rings[i], rings[i + 1]
        for k in range(segs):
            s = k * sectors // segs
            key = borrow[0] if borrow else (name if sectors == 1 else '%s #%d' % (name, s))
            off = circ * s / sectors
            u0 = (circ * k / segs - off) * su; u1 = (circ * (k + 1) / segs - off) * su; k2 = (k + 1) % segs
            um = (u0 + u1) * .5; w0 = v0 * sv; w1 = v1 * sv
            if len(A) == 1 and len(B) == 1:
                continue
            if len(A) == 1:
                part.add_face((A[0], B[k2], B[k]), zone, ((um, w0), (u1, w1), (u0, w1)), key)
            elif len(B) == 1:
                part.add_face((A[k], A[k2], B[0]), zone, ((u0, w0), (u1, w0), (um, w1)), key)
            else:
                part.add_face((A[k], A[k2], B[k2], B[k]), zone, ((u0, w0), (u1, w0), (u1, w1), (u0, w1)), key)
    return part


def lathe(name, full, keep, segs, **kw):
    """Revolve a subset (indices `keep`, or all) of a full profile, keeping full-profile v and island size."""
    pv = with_v(full)
    pts = pv if keep is None else [pv[i] for i in keep]
    circ = 2 * math.pi * max(p[1] for p in full)
    return revolve(name, pts, segs, circ, pv[-1][3], **kw)


def cylinder_profile(L, r, zone, caps=True, chamfer=0.0, chamfer_points=None):
    """caps: True / False / (cap at p0, cap at p1). An uncapped end is left open (it is buried in what it meets) -
    a buried cap would face the surface it sits in, and the bake's Bevel node would bend that surface's normal
    through it (review pass 2: inverted normal-map patches round every nut). chamfer_points, if a list, receives the
    indices of the chamfer points a 'simple' LOD drops."""
    cap0, cap1 = (caps, caps) if isinstance(caps, bool) else caps
    c = min(chamfer, r * .4, L * .3)
    prof = []
    if cap0:
        prof.append((0.0, 0.0, zone))
        if c > 0:
            if chamfer_points is not None:
                chamfer_points.append(len(prof))
            prof += [(0.0, r - c, zone), (c, r, zone)]
        else:
            prof.append((0.0, r, zone))
    else:
        prof.append((0.0, r, zone))
    if cap1:
        if c > 0:
            prof.append((L - c, r, zone))
            if chamfer_points is not None:
                chamfer_points.append(len(prof))
            prof.append((L, r - c, zone))
        else:
            prof.append((L, r, zone))
        prof.append((L, 0.0, zone))
    else:
        prof.append((L, r, zone))
    return prof


def cylinder(name, p0, p1, r, segs, zone='gunmetal', caps=True, chamfer=0.0, simple=False):
    p0 = Vector(p0); p1 = Vector(p1)
    cham = []
    full = cylinder_profile((p1 - p0).length, r, zone, caps, chamfer, cham)
    keep = None
    if simple and cham:   # drop the chamfer points, keep their v
        keep = [i for i in range(len(full)) if i not in cham]
    return lathe(name, full, keep, segs, origin=p0, axis=p1 - p0)


def ring_profile(depth, r_in, r_out, band, x0, lip=0.07, ch=0.045):
    """A machined emitter ring: gunmetal body, raised knurled brass band, yellow emissive lips on the front AND rear
    bore edges (the rear ones are what the player sees down the barrel), a dark bore between them."""
    d = depth / 2.0
    return [
        (x0 - d, r_in + lip + .03, 'gunmetal'),  # 0  back face (outside the rear lip)
        (x0 - d, r_out - ch, 'gunmetal'),        # 1
        (x0 - d + ch, r_out, 'gunmetal'),        # 2
        (x0 - .42 * d, r_out, 'brass'),          # 3
        (x0 - .36 * d, r_out + band, 'brass'),   # 4
        (x0 + .36 * d, r_out + band, 'brass'),   # 5
        (x0 + .42 * d, r_out, 'gunmetal'),       # 6
        (x0 + d - ch, r_out, 'gunmetal'),        # 7
        (x0 + d, r_out - ch, 'gunmetal'),        # 8  front face
        (x0 + d, r_in + lip + .03, 'lip'),       # 9  front lip
        (x0 + d - .025, r_in + lip, 'lip'),      # 10
        (x0 + d - .06, r_in + .01, 'lip'),       # 11
        (x0 + d - .10, r_in, 'dark'),            # 12 bore
        (x0 - d + .10, r_in, 'lip'),             # 13 rear lip
        (x0 - d + .06, r_in + .01, 'lip'),       # 14
        (x0 - d + .025, r_in + lip, 'lip'),      # 15
        (x0 - d, r_in + lip + .03, 'gunmetal'),  # 16 (= 0, closes the section)
    ]


RING_KEEP = {3: [0, 1, 3, 5, 6, 8, 9, 11, 12, 13, 15, 16], 4: [0, 1, 3, 6, 8, 9, 12, 13, 16],
             5: [0, 1, 6, 8, 9, 12, 13, 16], 6: [0, 1, 8, 9, 12, 13, 16], 7: [0, 1, 8, 9, 12, 13, 16]}


def hoop_profile():
    """The focusing ring's outer hoop: gunmetal, a raised knurled brass band round its outside, a turned groove on
    its face (the engraved focus scale sits outside it), chamfered edges. Same traversal as every profile here:
    back face outward, the outside forward, the front face inward, the inside back."""
    x0, x1, ri, ro, band = FR_X0, FR_X1, HOOP_IN, HOOP_OUT, HOOP_BAND
    xm = (x0 + x1) / 2
    return [
        (x0, ri + .04, 'gunmetal'),       # 0  back face
        (x0, ro - .045, 'gunmetal'),      # 1
        (x0 + .045, ro, 'gunmetal'),      # 2
        (xm - .13, ro, 'brass'),          # 3  knurled brass band
        (xm - .11, ro + band, 'brass'),   # 4
        (xm + .11, ro + band, 'brass'),   # 5
        (xm + .13, ro, 'gunmetal'),       # 6
        (x1 - .045, ro, 'gunmetal'),      # 7
        (x1, ro - .045, 'gunmetal'),      # 8  front face (focus scale band)
        (x1, 2.80, 'dark'),               # 9  turned groove
        (x1 - .03, 2.77, 'dark'),         # 10
        (x1, 2.74, 'gunmetal'),           # 11
        (x1, ri + .04, 'gunmetal'),       # 12
        (x1 - .04, ri, 'gunmetal'),       # 13 inner edge
        (x0 + .04, ri, 'gunmetal'),       # 14
        (x0, ri + .04, 'gunmetal'),       # 15 (= 0)
    ]


HOOP_KEEP = {3: [0, 1, 3, 5, 6, 8, 9, 11, 12, 14, 15], 4: [0, 1, 3, 6, 8, 12, 14, 15], 5: [0, 1, 3, 6, 8, 12, 15],
             6: [0, 1, 3, 6, 8, 12, 15], 7: [0, 1, 8, 12, 15]}


def hub_profile(lip=0.07):
    """The focusing ring's hub: gunmetal, a brass bolt-circle ring on its face, yellow emissive lips on the front and
    rear bore edges (the front one rings the lens housing), a dark bore."""
    x0, x1, ri, ro = FR_X0, FR_X1, HUB_IN, HUB_OUT
    return [
        (x0, ri + lip + .03, 'gunmetal'),   # 0  back face (outside the rear lip)
        (x0, ro - .04, 'gunmetal'),         # 1
        (x0 + .04, ro, 'gunmetal'),         # 2
        (x1 - .04, ro, 'gunmetal'),         # 3
        (x1, ro - .04, 'gunmetal'),         # 4  front face
        (x1, 1.87, 'brass'),                # 5  brass bolt-circle ring
        (x1, 1.73, 'gunmetal'),             # 6
        (x1, ri + lip + .03, 'lip'),        # 7  front lip
        (x1 - .025, ri + lip, 'lip'),       # 8
        (x1 - .06, ri + .01, 'lip'),        # 9
        (x1 - .10, ri, 'dark'),             # 10 bore
        (x0 + .10, ri, 'lip'),              # 11 rear lip
        (x0 + .06, ri + .01, 'lip'),        # 12
        (x0 + .025, ri + lip, 'lip'),       # 13
        (x0, ri + lip + .03, 'gunmetal'),   # 14 (= 0)
    ]


HUB_KEEP = {3: [0, 1, 3, 4, 5, 6, 7, 9, 10, 11, 13, 14], 4: [0, 1, 4, 5, 6, 7, 10, 11, 14], 5: [0, 1, 4, 7, 10, 11, 14],
            6: [0, 1, 4, 7, 10, 11, 14], 7: [0, 1, 4, 7, 10, 11, 14]}


def spoke_section(c=0.03):
    """The spoke's cross-section (a = tangential, b = along the beam axis): a chamfered rectangle, counter-clockwise."""
    hw = SPOKE_W / 2; hd = (SPOKE_X1 - SPOKE_X0) / 2
    return [(hw, hd - c), (hw - c, hd), (-hw + c, hd), (-hw, hd - c), (-hw, -hd + c), (-hw + c, -hd), (hw - c, -hd),
            (hw, -hd + c)]


def prism(name, p0, p1, section, b_dir, zone='gunmetal', simple=False):
    """A straight extrusion of a closed counter-clockwise section from p0 to p1, ends open (buried in what it joins).
    `b_dir` orients the section's b axis. One island: u = the FULL section's perimeter (a `simple` level drops the
    chamfers to the bounding rectangle and keeps the full u range), v = length."""
    p0 = Vector(p0); p1 = Vector(p1); d = p1 - p0; L = d.length; d = d.normalized()
    b = (Vector(b_dir) - d * Vector(b_dir).dot(d)).normalized(); a = b.cross(d).normalized()

    def perimeter(sec):
        acc = [0.0]
        for i in range(len(sec)):
            acc.append(acc[-1] + math.dist(sec[i], sec[(i + 1) % len(sec)]))
        return acc
    full_p = perimeter(section)[-1]
    sec = section
    if simple:
        ha = max(s[0] for s in section); hb = max(s[1] for s in section)
        sec = [(ha, hb), (-ha, hb), (-ha, -hb), (ha, -hb)]
    us = perimeter(sec); k = full_p / us[-1]
    part = Part(name, smooth_angle=34.0)
    part.islands[name] = (full_p, L)
    r0 = [part.add_vert(p0 + a * s[0] + b * s[1]) for s in sec]
    r1 = [part.add_vert(p1 + a * s[0] + b * s[1]) for s in sec]
    for i in range(len(sec)):
        j = (i + 1) % len(sec)
        u0 = us[i] * k; u1 = us[i + 1] * k
        part.add_face((r0[i], r0[j], r1[j], r1[i]), zone, ((u0, 0.0), (u1, 0.0), (u1, L), (u0, L)))
    return part


def housing_profile():
    x0, x1 = HOUSING_X0, HOUSING_X1
    return [
        (x0, 0.60, 'dark'),            # 0
        (x0, 0.66, 'gunmetal'),        # 1
        (x0 + .04, 0.70, 'gunmetal'),  # 2
        (x0 + .26, 1.05, 'gunmetal'),  # 3
        (x0 + .32, 1.22, 'gunmetal'),  # 4
        (x1 - .20, 1.22, 'gunmetal'),  # 5
        (x1 - .17, 1.16, 'brass'),     # 6
        (x1 - .02, 1.16, 'brass'),     # 7
        (x1, 1.12, 'brass'),           # 8
        (x1, 1.00, 'dark'),            # 9
        (x1 - .10, 0.99, 'dark'),      # 10
        (x0 + .30, 0.60, 'dark'),      # 11
        (x0, 0.60, 'dark'),            # 12
    ]


HOUSING_KEEP = {3: [0, 1, 3, 4, 5, 6, 8, 9, 11, 12], 4: [0, 1, 4, 5, 6, 8, 9, 11, 12], 5: [0, 1, 4, 6, 8, 9, 12],
                6: [0, 1, 4, 8, 9, 12], 7: [0, 1, 4, 8, 9, 12]}


def lens_profile():
    return [
        (LENS_BACK, 0.0, 'crystal'),
        (LENS_GIRDLE0 - .07, 0.62, 'crystal'),
        (LENS_GIRDLE0, LENS_R, 'crystal'),
        (LENS_GIRDLE1, LENS_R, 'crystal'),
        (LENS_GIRDLE1 + .34, 0.82, 'crystal'),
        (LENS_FRONT - .16, 0.62, 'crystal'),
        (LENS_FRONT, LENS_TABLE_R, 'crystal'),
        (LENS_TIP, 0.0, 'crystal'),
    ]


LENS_KEEP = {5: [0, 2, 3, 5, 6, 7], 6: [0, 2, 3, 6, 7], 7: [0, 2, 3, 6, 7]}


def catmull(points, step):
    pts = [Vector(p) for p in points]
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        n = max(1, int(math.ceil((p2 - p1).length / step)))
        for j in range(n):
            t = j / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-1])
    return out


def path_length(path):
    pts = catmull(path, .02)
    return sum((pts[i] - pts[i - 1]).length for i in range(1, len(pts)))


def sweep(name, path, r, sides, step, stripe_half_angle=50.0, zone=None):
    """A conduit: circular section swept along a Catmull-Rom path (v = true arc length, consistent across levels);
    faces whose centre looks up (world +Z, within stripe_half_angle) are the glowing 'stripe', the rest 'sheath'
    (or every face `zone`, when given)."""
    part = Part(name, smooth_angle=55.0)
    fine = catmull(path, .02)
    cum = [0.0]
    for i in range(1, len(fine)):
        cum.append(cum[-1] + (fine[i] - fine[i - 1]).length)
    total = cum[-1]
    n_rings = max(2, int(math.ceil(total / step)) + 1)
    pts = []; vs = []
    j = 0
    for i in range(n_rings):
        target = total * i / (n_rings - 1)
        while j < len(cum) - 2 and cum[j + 1] < target:
            j += 1
        span = max(cum[j + 1] - cum[j], 1e-9); t = (target - cum[j]) / span
        pts.append(fine[j].lerp(fine[j + 1], min(max(t, 0), 1))); vs.append(target)
    circ = 2 * math.pi * r
    part.islands[name] = (circ, total)
    n = Vector((0, 0, 1))
    rings = []; frames = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        n = (n - t * n.dot(t)).normalized()
        b = t.cross(n).normalized()
        rings.append([part.add_vert(p + (n * math.cos(2 * math.pi * k / sides) + b * math.sin(2 * math.pi * k / sides)) * r)
                      for k in range(sides)])
        frames.append((n, b))
    for i in range(len(pts) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides; amid = 2 * math.pi * (k + .5) / sides
            nn, bb = frames[i]
            fz = zone or ('stripe' if (nn * math.cos(amid) + bb * math.sin(amid)).z > math.cos(math.radians(stripe_half_angle))
                          else 'sheath')
            u0 = circ * k / sides; u1 = circ * (k + 1) / sides
            part.add_face((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]), fz,
                          ((u0, vs[i]), (u1, vs[i]), (u1, vs[i + 1]), (u0, vs[i + 1])))
    return part


def gem(name, full, keep, segs, stagger, segs0=12):
    """The cut crystal: a flat-shaded lathe whose alternate facet rings are turned half a facet, so the stone is cut
    into triangles (kites, a star table) instead of a quad grid. One island at every level: the full turn plus half a
    level-0 facet of room for the turned rings' wrap; every level keeps the full-profile v (like lathe())."""
    pv = with_v(full)
    pts = pv if keep is None else [pv[i] for i in keep]
    circ = 2 * math.pi * max(p[1] for p in full)
    part = Part(name, flat=True)
    part.islands[name] = (circ * (1.0 + 0.5 / segs0), pv[-1][3])
    start = math.pi / segs
    b1 = Vector((0, 0, 1)); b2 = Vector((1, 0, 0)).cross(b1)
    rings, offs, n_ring = [], [], 0
    for (t, r, z, v) in pts:
        c = Vector((t, 0.0, AXZ))
        if r <= 1e-6:
            rings.append([part.add_vert(c)]); offs.append(0.0); continue
        off = 0.5 if (stagger and n_ring % 2 == 1) else 0.0
        n_ring += 1
        rings.append([part.add_vert(c + (b1 * math.cos(start + 2 * math.pi * (k + off) / segs) +
                                         b2 * math.sin(start + 2 * math.pi * (k + off) / segs)) * r) for k in range(segs)])
        offs.append(off)

    def U(k, off):
        return circ * (k + off) / segs
    for i in range(len(pts) - 1):
        zone = pts[i][2]; v0 = pts[i][3]; v1 = pts[i + 1][3]
        A, B = rings[i], rings[i + 1]; oa, ob = offs[i], offs[i + 1]
        for k in range(segs):
            k2 = (k + 1) % segs
            if len(A) == 1 and len(B) == 1:
                continue
            if len(A) == 1:
                part.add_face((A[0], B[k2], B[k]), zone, ((U(k + .5, ob), v0), (U(k + 1, ob), v1), (U(k, ob), v1)))
            elif len(B) == 1:
                part.add_face((A[k], A[k2], B[0]), zone, ((U(k, oa), v0), (U(k + 1, oa), v0), (U(k + .5, oa), v1)))
            elif oa == ob:
                part.add_face((A[k], A[k2], B[k2], B[k]), zone,
                              ((U(k, oa), v0), (U(k + 1, oa), v0), (U(k + 1, ob), v1), (U(k, ob), v1)))
            elif ob > oa:   # B turned half a facet: B[k] sits between A[k] and A[k + 1]
                part.add_face((A[k], A[k2], B[k]), zone, ((U(k, oa), v0), (U(k + 1, oa), v0), (U(k, ob), v1)))
                part.add_face((A[k2], B[k2], B[k]), zone, ((U(k + 1, oa), v0), (U(k + 1, ob), v1), (U(k, ob), v1)))
            else:           # A turned half a facet: B[k + 1] sits between A[k] and A[k + 1]
                part.add_face((A[k], A[k2], B[k2]), zone, ((U(k, oa), v0), (U(k + 1, oa), v0), (U(k + 1, ob), v1)))
                part.add_face((A[k], B[k2], B[k]), zone, ((U(k, oa), v0), (U(k + 1, ob), v1), (U(k, ob), v1)))
    return part


def far_claws(level):
    """Levels 5-6 only: swept stand-ins for the DG-2's five copper claws (its own LOD3-4 break them into orphaned hook
    tips and thin slivers, LOD5+ drops them). Geometry only - the export maps them onto a copper patch of the coil
    material (they are not part of the emitter atlas)."""
    if level not in FAR_CLAW:
        return []
    sides, rad, step = FAR_CLAW[level]
    parts = []
    for k, ang in enumerate(CLAW_ANGLES):
        a = math.radians(ang)
        path = [(x, rho * math.cos(a), AXZ + CLAW_RING_DZ + rho * math.sin(a)) for x, rho in CLAW_PATH]
        parts.append(sweep('Far claw %d' % k, path, rad, sides, step, zone='copper'))
    return parts


def build(level=0):
    """All parts at a detail level (0..7). Part names are stable across levels (they key the UV islands)."""
    seg = SEGS[level]; small = SMALL[level]
    parts = []
    if level < 7:
        for name, x, depth, r_in, r_out, band in RINGS:
            parts.append(lathe(name, ring_profile(depth, r_in, r_out, band, x), RING_KEEP.get(level), seg))
    # The focusing ring keeps its open wheel at EVERY level, so no LOD swap closes its windows (no pop).
    parts.append(lathe('Focusing ring hoop', hoop_profile(), HOOP_KEEP.get(level), seg))
    parts.append(lathe('Focusing ring hub', hub_profile(), HUB_KEEP.get(level), seg))
    xm = (SPOKE_X0 + SPOKE_X1) / 2
    for k, ang in enumerate(SPOKE_ANGLES):
        parts.append(prism('Focusing ring spoke %d' % k, axis_point(xm, SPOKE_R0, ang), axis_point(xm, SPOKE_R1, ang),
                           spoke_section(), (1.0, 0.0, 0.0), 'gunmetal', simple=level >= 3))
    if small and level <= 4:
        for k, (rr, ang) in enumerate(CLAW_TIPS):
            # a brass ferrule on the hook's last segment, its axis through the measured tip: the hook plugs into it
            a = math.radians(ang)
            tip = axis_point(CLAW_TIP_X, rr, ang)
            d = Vector((HOOK_DIR[0], HOOK_DIR[1] * math.cos(a), HOOK_DIR[1] * math.sin(a)))
            parts.append(cylinder('Claw ferrule %d' % k, tip + d * FERRULE_IN, tip - d * FERRULE_OUT, FERRULE_R, small,
                                  'brass', chamfer=.015, simple=level >= 2))
    if level <= 1:
        for k, ang in enumerate(HUB_BOLT_ANGLES):
            parts.append(cylinder('Hub bolt %d' % k, axis_point(FR_X1 - .01, HUB_BOLT_R, ang),
                                  axis_point(FR_X1 + .06, HUB_BOLT_R, ang), .085, 6, 'brass', caps=(False, True),
                                  chamfer=.015))
    parts.append(lathe('Lens housing', housing_profile(), HOUSING_KEEP.get(level), seg))
    ls = LENS_SEGS[level]
    parts.append(gem('Focusing crystal', lens_profile(), LENS_KEEP.get(level), ls, stagger=(ls == LENS_SEGS[0])))
    r1, r2 = RINGS
    x_from = r1[1] + r1[2] / 2; x_to = FR_X0                      # ring 1 front face -> the hub's back face
    if level >= 5:
        # The DG-2's own far LODs drop everything between the receiver and the claws (LOD6 even opens a hole between
        # the receiver and its front collar at x 20.8-21.3): a plain spine from inside the receiver box to the lens
        # housing keeps the emitter from floating free of the gun (verify_art measures the side silhouette).
        tie_island = ('Tie rod 0', (2 * math.pi * TIE_ROD_R, (x_to + .02) - (x_from - .02)))
        p0 = Vector((SPINE_X0, 0.0, AXZ)); p1 = Vector((SPINE_X1, 0.0, AXZ))
        full = cylinder_profile((p1 - p0).length, SPINE_R, 'gunmetal', caps=False)
        pv = with_v(full)
        parts.append(revolve('Spine rod (far LODs)', pv, 6, 2 * math.pi * SPINE_R, pv[-1][3], origin=p0, axis=p1 - p0,
                             borrow=tie_island))
        # ...and a thin web across the hub's bore: at far LODs nothing else ties the focusing ring to the spine
        # (verify_art fails any group of parts hanging in mid-air)
        web = [(0.0, SPINE_R - .02, 'dark'), (0.0, HUB_IN + .005, 'dark'), (.02, HUB_IN + .005, 'dark'),
               (.02, SPINE_R - .02, 'dark'), (0.0, SPINE_R - .02, 'dark')]
        wv = with_v(web)
        parts.append(revolve('Hub web (far LODs)', wv, seg, 2 * math.pi * HUB_IN, wv[-1][3],
                             origin=(FR_X0 + .10, 0.0, AXZ), borrow=tie_island))
    if level <= 6:
        # the tie rods stay through level 6: at levels 5-6 they are what holds rings 1-2 to the focusing ring
        for i, ang in enumerate(TIE_ANGLES):
            parts.append(cylinder('Tie rod %d' % i, axis_point(x_from - .02, TIE_R, ang), axis_point(x_to + .02, TIE_R, ang),
                                  TIE_ROD_R, max(4, small or 4), 'gunmetal', caps=False))
            if small and level <= 2:
                # brass nuts where the rod meets each ring face
                faces = [(x_from, 1), (r2[1] - r2[2] / 2, -1), (r2[1] + r2[2] / 2, 1), (x_to, -1)]
                for j, (fx, sgn) in enumerate(faces):
                    parts.append(cylinder('Tie nut %d-%d' % (i, j), axis_point(fx, TIE_R, ang),
                                          axis_point(fx + sgn * .09, TIE_R, ang), TIE_ROD_R + .055, 6,
                                          'brass', caps=(False, True), chamfer=.012, simple=level >= 2))
    if level <= 1:
        for k in range(6):
            ang = 30 + k * 60
            parts.append(cylinder('Housing screw %d' % k, axis_point(HOUSING_X1 - .45, 1.20, ang),
                                  axis_point(HOUSING_X1 - .45, 1.30, ang), .07, 8, 'brass', caps=(False, True),
                                  chamfer=.015))
    sides, step = CONDUIT[level]
    for side, label in ((1, 'left'), (-1, 'right')):
        path = [(x, side * CONDUIT_Y, z) for x, z in CONDUIT_PATH]
        if sides:
            parts.append(sweep('Conduit %s' % label, path, CONDUIT_R, sides, step))
        if level <= 3 and small:
            g0 = Vector((GLAND[0][0], side * CONDUIT_Y, GLAND[0][1])); g1 = Vector((GLAND[1][0], side * CONDUIT_Y, GLAND[1][1]))
            parts.append(cylinder('Conduit gland %s' % label, g0, g1, .135, small, 'brass', chamfer=.03, simple=level >= 2))
            f0 = Vector((FERRULE[0][0], side * CONDUIT_Y, FERRULE[0][1])); f1 = Vector((FERRULE[1][0], side * CONDUIT_Y, FERRULE[1][1]))
            parts.append(cylinder('Conduit ferrule %s' % label, f0, f1, .108, small, 'brass', chamfer=.025, simple=level >= 2))
        if level <= 2 and small:
            pts = catmull(path, .05)
            for cx in CLAMPS_X:
                q = min(pts, key=lambda p: abs(p.x - cx)); i = pts.index(q)
                tdir = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
                parts.append(cylinder('Conduit clamp %s %.2f' % (label, cx), q - tdir * .08, q + tdir * .08,
                                      CONDUIT_R + .04, small, 'gunmetal', chamfer=.02, simple=level >= 2))
                foot = Vector((q.x, q.y, STANDOFF_FOOT_Z[cx]))
                if q.z - CONDUIT_R - .02 - foot.z > .05:
                    parts.append(cylinder('Conduit standoff %s %.2f' % (label, cx), foot,
                                          Vector((q.x, q.y, q.z - CONDUIT_R + .01)), .045, max(5, small // 2), 'gunmetal'))
    return parts


def shelf_pack(islands, margin_px=8, size=2048):
    """islands: {name: (w_in, h_in)} -> ({name: (u0, v0, scale, rotated)}, inches->uv scale). Every island is laid
    out in real inches at ONE scale, so texel density is uniform across the atlas."""
    items = []
    for name, (w, h) in islands.items():
        rot = h > w
        items.append((name, max(w, h), min(w, h), rot))
    items.sort(key=lambda it: (-it[2], -it[1], it[0]))
    m = margin_px / size

    def attempt(s):
        x = y = 0.0; row_h = 0.0; out = {}
        for name, w, h, rot in items:
            W = w * s + m; H = h * s + m
            if W > 1.0:
                return None
            if x + W > 1.0:
                x = 0.0; y += row_h; row_h = 0.0
            if y + H > 1.0:
                return None
            out[name] = (x + m / 2, y + m / 2, s, rot)
            x += W; row_h = max(row_h, H)
        return out
    lo, hi, best = 1e-4, 1.0, None
    for _ in range(48):
        mid = (lo + hi) / 2
        r = attempt(mid)
        if r is None:
            hi = mid
        else:
            lo = mid; best = r
    return best, lo


def island_uv(transform, u, v):
    """Island inches -> atlas uv (Blender convention, v up)."""
    u0, v0, s, rot = transform
    if rot:
        u, v = v, u
    return (u0 + u * s, v0 + v * s)
