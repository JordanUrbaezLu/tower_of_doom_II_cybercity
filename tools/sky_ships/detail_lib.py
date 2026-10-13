"""THE SKY FLEET detail kit (docs/192 s8, v2 "a lot more detail").

Every function writes CLOSED, OUTWARD-FACING solids into a sky_lib.Part (finish it with recalc=False: the winding
here is explicit - each face points away from its solid's centre - so thin plates and touching pieces never get
flipped by a manifold guess). Round parts mark their faces smooth; sky_lib.Part.finish keeps hard edges hard.
Units are BO3 units, ship space (bow +X, port +Y, up +Z).

What reads from 5,000-20,000 units away is SHAPE and LIGHT: silhouette breaks (towers, masts, turrets, fins),
shading breaks (raised plates catching the moon), and many small lights. So the kit is built around those.
"""
import math
from mathutils import Vector


def V(p):
    return Vector(p)


def _face(part, pts, center, smooth=False, uvs=None):
    P = [V(p) for p in pts]
    n = (P[1] - P[0]).cross(P[2] - P[0])
    if n.length < 1e-9 and len(P) > 3:
        n = (P[2] - P[0]).cross(P[3] - P[0])
    c = sum(P, Vector()) / len(P)
    if n.dot(c - V(center)) < 0:
        P.reverse()
        if uvs:
            uvs = list(reversed(uvs))
    f = part.bm.faces.new([part.bm.verts.new(tuple(p)) for p in P])
    f.smooth = smooth
    if uvs:
        for loop, uv in zip(f.loops, uvs):
            loop[part.uv].uv = uv
    return f


def basis(fwd, up=(0, 0, 1)):
    """Right-handed frame from a forward and an up hint: (fwd, left, up)."""
    f = V(fwd).normalized()
    u = V(up)
    l = u.cross(f)
    if l.length < 1e-6:
        l = Vector((0, 0, 1)).cross(f) if abs(f.z) < 0.9 else Vector((0, 1, 0))
    l.normalize()
    u = f.cross(l).normalized()
    return f, l, u


def obox(part, center, axes, half):
    """Oriented box: axes = (a, b, c) unit vectors, half = (ha, hb, hc)."""
    c = V(center)
    a, b, d = [V(x) for x in axes]
    ha, hb, hc = half
    k = lambda sx, sy, sz: c + a * (sx * ha) + b * (sy * hb) + d * (sz * hc)
    for q in (((1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)), ((-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)),
              ((-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)), ((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)),
              ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)), ((-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1))):
        _face(part, [k(*p) for p in q], c)


def abox(part, x0, x1, y0, y1, z0, z1):
    obox(part, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
         (abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2))


def frustum_box(part, center, axes, half_lo, half_hi):
    """A box whose top (+c) face is smaller: half_lo = (ha, hb) at -hc, half_hi = (ha, hb) at +hc, hc = half_lo[2]."""
    c = V(center)
    a, b, d = [V(x) for x in axes]
    hc = half_lo[2]
    lo = [c + a * (sx * half_lo[0]) + b * (sy * half_lo[1]) - d * hc for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    hi = [c + a * (sx * half_hi[0]) + b * (sy * half_hi[1]) + d * hc for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for i in range(4):
        j = (i + 1) % 4
        _face(part, [lo[i], lo[j], hi[j], hi[i]], c)
    _face(part, lo, c)
    _face(part, hi, c)


def cyl(part, a, b, ra, rb, sides=12, caps=(True, True), smooth=True, phase=0.0):
    """Cylinder / frustum along a -> b."""
    A, B = V(a), V(b)
    ax = B - A
    if ax.length < 1e-6:
        return
    ax.normalize()
    t = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
    u = ax.cross(t).normalized()
    w = ax.cross(u).normalized()
    ring = lambda C, r: [C + (u * math.cos(phase + 2 * math.pi * i / sides) + w * math.sin(phase + 2 * math.pi * i / sides)) * r
                         for i in range(sides)]
    RA, RB = ring(A, ra), ring(B, rb)
    mid = (A + B) / 2
    for i in range(sides):
        j = (i + 1) % sides
        P = [RA[i], RA[j], RB[j], RB[i]]
        # outward from the AXIS (not the centre): frustum sides stay right however long the cylinder is
        n = (P[1] - P[0]).cross(P[3] - P[0])
        c = sum(P, Vector()) / 4
        foot = A + ax * (c - A).dot(ax)
        if n.dot(c - foot) < 0:
            P.reverse()
        f = part.bm.faces.new([part.bm.verts.new(tuple(p)) for p in P])
        f.smooth = smooth
    if caps[0] and ra > 0:
        _face(part, RA, B)                                       # faces away from the far end
    if caps[1] and rb > 0:
        _face(part, RB, A)


def dome(part, center, up, r, sides=12, rings=4):
    """A half sphere (sensor blister) on `center`, bulging along `up`."""
    C = V(center)
    f, l, u = basis(Vector((1, 0, 0)) if abs(V(up).normalized().x) < 0.9 else Vector((0, 1, 0)), up)
    # basis() returns (fwd, left, up) with up = the given up (orthogonalised)
    pts = []
    for k in range(rings + 1):
        a = (math.pi / 2) * k / rings
        rr, hh = r * math.cos(a), r * math.sin(a)
        pts.append([C + (f * math.cos(2 * math.pi * i / sides) + l * math.sin(2 * math.pi * i / sides)) * rr + u * hh for i in range(sides)])
    apex = C + u * r
    for k in range(rings):
        for i in range(sides):
            j = (i + 1) % sides
            if k == rings - 1:
                P = [pts[k][i], pts[k][j], apex]                 # the top ring closes on the apex
            else:
                P = [pts[k][i], pts[k][j], pts[k + 1][j], pts[k + 1][i]]
            _face(part, P, C, smooth=True)
    _face(part, pts[0], apex)


def dish(part, center, normal, r, depth, sides=14):
    """A radar dish: a shallow cone opening along `normal`, a back cap and a feed spike."""
    C = V(center)
    n = V(normal).normalized()
    f, l, u = basis(n)
    rim = [C + (l * math.cos(2 * math.pi * i / sides) + u * math.sin(2 * math.pi * i / sides)) * r for i in range(sides)]
    back = C - n * depth
    for i in range(sides):
        j = (i + 1) % sides
        _face(part, [rim[i], rim[j], back], back - n * 10, smooth=True)       # the bowl faces outward (front)
        _face(part, [rim[j], rim[i], back], C + n * r * 3, smooth=True)       # its back
    cyl(part, back, C + n * (r * 0.9), r * 0.05, r * 0.03, sides=6)
    cyl(part, back, back - n * (depth * 1.2), r * 0.18, r * 0.12, sides=8)


def turret(part, pos, s, yaw_deg=0.0, up=(0, 0, 1), barrels=2, barrel_len=2.2, barrel_r=0.085):
    """A gun turret: round base, armoured housing, barrels along its facing. s = base radius."""
    P = V(pos)
    U = V(up).normalized()
    fwd0 = Vector((math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg)), 0))
    f, l, u = basis(fwd0, U)
    cyl(part, P - u * (s * 0.1), P + u * (s * 0.35), s, s * 0.92, sides=14)
    hc = P + u * (s * 0.35 + s * 0.28)
    frustum_box(part, hc, (f, l, u), (s * 0.85, s * 0.7, s * 0.28), (s * 0.6, s * 0.55))
    obox(part, hc + u * (s * 0.36) - f * (s * 0.25), (f, l, u), (s * 0.22, s * 0.18, s * 0.1))     # rangefinder
    for i in range(barrels):
        off = (i - (barrels - 1) / 2) * s * 0.34
        a = hc + f * (s * 0.55) + l * off
        cyl(part, a, a + f * (s * barrel_len), s * barrel_r, s * barrel_r * 0.82, sides=6)
        cyl(part, a + f * (s * barrel_len * 0.92), a + f * (s * barrel_len), s * barrel_r * 1.3, s * barrel_r * 1.3, sides=6)   # muzzle ring


def mast(part, base, height, w, bars=3, bar_len=None, up=(0, 0, 1), fwd=(1, 0, 0)):
    """An antenna mast: a tapering square spar with cross-arms. Returns the tip point (for a beacon)."""
    B = V(base)
    f, l, u = basis(V(fwd), V(up))
    frustum_box(part, B + u * (height / 2), (f, l, u), (w, w, height / 2), (w * 0.35, w * 0.35))
    bar_len = bar_len or w * 8
    for k in range(bars):
        h = height * (0.45 + 0.45 * k / max(1, bars - 1)) if bars > 1 else height * 0.7
        L = bar_len * (1 - 0.35 * k / max(1, bars))
        obox(part, B + u * h, (l, f, u), (L / 2, w * 0.35, w * 0.35))
    return B + u * (height + w * 0.5)


def vent_bank(part, origin, along, out, n, pitch, w, h, d):
    """n louvre slats along `along`, standing out of a surface (normal `out`)."""
    O = V(origin)
    a = V(along).normalized()
    o = V(out).normalized()
    b = o.cross(a).normalized()
    for i in range(n):
        c = O + a * (i * pitch) + o * (d / 2)
        obox(part, c, (a, b, o), (w / 2, h / 2, d / 2))


def fin_bank(part, center, axis, out, n, pitch, length, height, t):
    """Radiator fins: n thin plates spaced along `axis`, each `length` along `out`-perpendicular, `height` out."""
    C = V(center)
    ax = V(axis).normalized()
    o = V(out).normalized()
    s = o.cross(ax).normalized()
    for i in range(n):
        c = C + ax * ((i - (n - 1) / 2) * pitch) + o * (height / 2)
        obox(part, c, (ax, s, o), (t / 2, length / 2, height / 2))


def truss(part, a, b, w, seg, t=None):
    """A square lattice beam a -> b: four longerons, a frame at every segment, one diagonal per face."""
    A, B = V(a), V(b)
    L = (B - A).length
    f, l, u = basis(B - A)
    t = t or w * 0.09
    corners = [l * (w / 2) + u * (w / 2), -l * (w / 2) + u * (w / 2), -l * (w / 2) - u * (w / 2), l * (w / 2) - u * (w / 2)]
    for c in corners:
        obox(part, (A + B) / 2 + c, (f, l, u), (L / 2, t / 2, t / 2))
    n = max(1, int(round(L / seg)))
    for k in range(n + 1):
        P = A + f * (L * k / n)
        for i in range(4):
            p0, p1 = P + corners[i], P + corners[(i + 1) % 4]
            _bar(part, p0, p1, t * 0.8)
        if k < n:
            Q = A + f * (L * (k + 1) / n)
            for i in range(4):
                j = (i + 1) % 4
                if k % 2 == 0:                                   # the diagonals zig-zag bay to bay
                    _bar(part, P + corners[i], Q + corners[j], t * 0.7)
                else:
                    _bar(part, P + corners[j], Q + corners[i], t * 0.7)


def _bar(part, p0, p1, t):
    P0, P1 = V(p0), V(p1)
    d = P1 - P0
    if d.length < 1e-3:
        return
    f, l, u = basis(d)
    obox(part, (P0 + P1) / 2, (f, l, u), (d.length / 2, t / 2, t / 2))


def nozzle(bell_part, glow_part, pos, r, length, axis=(-1, 0, 0), sides=20):
    """A detailed engine: flanged bell opening along `axis`, inner glowing throat, collar ring.
    Returns the exhaust plane centre (where the engine FX anchor goes)."""
    P = V(pos)
    ax = V(axis).normalized()
    exit_c = P + ax * length
    cyl(bell_part, P, exit_c, r * 0.78, r, sides=sides, caps=(False, False))                  # the bell
    cyl(bell_part, P + ax * (length * 0.18), P + ax * (length * 0.28), r * 0.95, r * 0.98, sides=sides, caps=(True, True))   # collar
    cyl(bell_part, exit_c - ax * (length * 0.06), exit_c + ax * (length * 0.02), r * 1.06, r * 1.08, sides=sides, caps=(True, True))  # lip
    cyl(bell_part, P - ax * (length * 0.25), P, r * 0.6, r * 0.78, sides=sides, caps=(True, False))   # throat housing
    # inner glow: a recessed disc + a cone pointing back into the bell (reads hot from behind and the side)
    cyl(glow_part, exit_c - ax * (length * 0.55), exit_c - ax * (length * 0.05), r * 0.2, r * 0.9, sides=sides, caps=(False, True))
    return exit_c


def plates_on_loft(part, rings, rng, nu, nv, hmin, hmax, inset, skip=0.06, merge=0.45, keep=None, sunk=3.0, axis=(0, 0),
                   alt=None):
    """Raised armour plates over a lofted hull (rings of points around an x-parallel axis through (y, z) = axis,
    same count per ring). Each station gap splits into `nu` cells, each ring edge into `nv`; cells merge up to
    2x2; each plate is inset by `inset`, lifted `h` along its outward normal and closed with side walls.
    keep(center) -> bool filters cells (e.g. leave room for a superstructure). Returns the plate count."""
    S, R = len(rings), len(rings[0])
    Rv = [[V(p) for p in ring] for ring in rings]
    NU, NV = (S - 1) * nu, R * nv

    def G(ui, vi):
        s = min(ui // nu, S - 2)
        fu = (ui - s * nu) / nu
        r = (vi // nv) % R
        fv = (vi % nv) / nv
        r2 = (r + 1) % R
        a = Rv[s][r].lerp(Rv[s][r2], fv)
        b = Rv[s + 1][r].lerp(Rv[s + 1][r2], fv)
        return a.lerp(b, fu)

    used = set()
    count = 0
    for ui in range(NU):
        for vi in range(NV):
            if (ui, vi) in used:
                continue
            opts = [(1, 1)]
            if rng.random() < merge:
                opts = [(2, 2), (2, 1), (1, 2), (1, 1)]
            du, dv = 1, 1
            for (a, b) in opts:
                cells = [(ui + i, (vi + j) % NV) for i in range(a) for j in range(b)]
                if ui + a <= NU and all(c not in used for c in cells):
                    du, dv = a, b
                    break
            for i in range(du):
                for j in range(dv):
                    used.add((ui + i, (vi + j) % NV))
            if rng.random() < skip:
                continue
            c00, c10, c11, c01 = G(ui, vi), G(ui + du, vi), G(ui + du, vi + dv), G(ui, vi + dv)
            ctr = (c00 + c10 + c11 + c01) / 4
            radial = Vector((0, ctr.y - axis[0], ctr.z - axis[1]))
            if radial.length < 30:
                continue
            if keep is not None and not keep(ctr):
                continue
            n = (c10 - c00).cross(c01 - c00) + (c11 - c10).cross(c11 - c01)
            if n.length < 1e-6:
                continue
            n.normalize()
            if n.dot(radial) < 0:
                n = -n
            ins = []
            for p in (c00, c10, c11, c01):
                d = ctr - p
                k = min(inset, d.length * 0.4)
                ins.append(p + d.normalized() * k if d.length > 1e-6 else p)
            if min((ins[1] - ins[0]).length, (ins[3] - ins[0]).length) < inset * 1.5:
                continue
            h = rng.uniform(hmin, hmax) * (1 + 0.25 * (du * dv - 1))
            base = [p - n * sunk for p in ins]
            top = [p + n * h for p in ins]
            mid = ctr + n * (h / 2 - sunk / 2)
            tgt = alt[0] if (alt is not None and rng.random() < alt[1]) else part     # two-tone armour
            _face(tgt, top, mid)
            for i in range(4):
                j = (i + 1) % 4
                _face(tgt, [base[i], base[j], top[j], top[i]], mid)
            count += 1
    return count


def block_field(part, rng, n, sample, size_range, h_range, yaw_snap=True):
    """n greeble blocks: sample() -> (point on the surface, outward normal) or None."""
    placed = 0
    tries = 0
    while placed < n and tries < n * 6:
        tries += 1
        s = sample()
        if s is None:
            continue
        p, up = V(s[0]), V(s[1]).normalized()
        fwd = Vector((1, 0, 0)) if yaw_snap else Vector((math.cos(rng.uniform(0, 6.283)), math.sin(rng.uniform(0, 6.283)), 0))
        f, l, u = basis(fwd - up * fwd.dot(up) if abs(fwd.dot(up)) < 0.95 else Vector((0, 1, 0)), up)
        a = rng.uniform(*size_range)
        b = rng.uniform(*size_range) * rng.uniform(0.4, 1.0)
        h = rng.uniform(*h_range)
        obox(part, p + u * (h / 2 - 2), (f, l, u), (a / 2, b / 2, h / 2))
        if rng.random() < 0.3:                                   # a smaller block on top (stepped greeble)
            obox(part, p + u * (h + h * 0.3 - 2), (f, l, u), (a * 0.3, b * 0.3, h * 0.3))
        placed += 1
    return placed


def light_row(part, pts, s):
    for p in pts:
        c = V(p)
        abox(part, c.x - s / 2, c.x + s / 2, c.y - s / 2, c.y + s / 2, c.z - s / 2, c.z + s / 2)


def deco_quad(part, center, right, up, w, h, cell, atlas=(1024, 512)):
    """A marking: a quad (w x h) facing right x up, UV-mapped onto a DECO_CELLS box (pixels, make_textures.py)."""
    C, Rt, Up = V(center), V(right).normalized(), V(up).normalized()
    x0, y0, x1, y1 = cell
    W, H = atlas
    u0, u1 = x0 / W, x1 / W
    v0, v1 = 1 - y1 / H, 1 - y0 / H
    pts = [C - Rt * (w / 2) - Up * (h / 2), C + Rt * (w / 2) - Up * (h / 2), C + Rt * (w / 2) + Up * (h / 2), C - Rt * (w / 2) + Up * (h / 2)]
    normal = Rt.cross(Up)
    f = part.bm.faces.new([part.bm.verts.new(tuple(p)) for p in pts])
    uvs = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    for loop, uv in zip(f.loops, uvs):
        loop[part.uv].uv = uv
    f.normal_update()
    if f.normal.dot(normal) < 0:
        f.normal_flip()
    return f


def ad_panel(part, center, right, up, w, h, cell_index, cols=4, rows=2):
    """One billboard screen showing ad cell `cell_index` of the i_tod_sky_ads_c atlas (4 x 2 cells)."""
    C, Rt, Up = V(center), V(right).normalized(), V(up).normalized()
    cx, cy = cell_index % cols, cell_index // cols
    u0, u1 = cx / cols, (cx + 1) / cols
    v1, v0 = 1 - cy / rows, 1 - (cy + 1) / rows
    pts = [C - Rt * (w / 2) - Up * (h / 2), C + Rt * (w / 2) - Up * (h / 2), C + Rt * (w / 2) + Up * (h / 2), C - Rt * (w / 2) + Up * (h / 2)]
    f = part.bm.faces.new([part.bm.verts.new(tuple(p)) for p in pts])
    for loop, uv in zip(f.loops, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]):
        loop[part.uv].uv = uv
    f.normal_update()
    if f.normal.dot(Rt.cross(Up)) < 0:
        f.normal_flip()
    return f
