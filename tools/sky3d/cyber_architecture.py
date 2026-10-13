"""Dark, engineered lower-city architecture for the rendered Cybercity sky.

Integration (no scene construction occurs on import)::

    city.cyber = Acc('Cyber block armour')
    city.cyber_roof = Acc('Cyber block decks')
    result = build_cyber_block(city, cx=cx, cy=cy, w=w, d=d, h=h,
        ang=ang, seed=seed, pal=pal, distance=r, far=far, neon=on('neon'))
    city.cyber.build(make_cyber_material('sky3d_cyber_armour'))
    city.cyber_roof.build(make_cyber_material('sky3d_cyber_decks', roof=True))

Use for every ordinary lot selected by cyber_coverage.modernize_lot and for
deck/platform pods. Preferred landmark silhouettes stay intact and reuse the
same surface factory with ``legacy=True`` for their older vertex attributes.
``base_z + h`` is a hard ceiling, including roof machinery. ``w``/``d`` enclose
every piece in the lot's local frame. All random draws are local; callers' layout,
hero placements, and celestial RNG are untouched. No lights are created.

The two new accumulators use the existing Acc poly/prism/loft interface and
the FLOAT_COLOR corner attribute ``bld``. Here bld encodes seed, plate finish,
cool tint, and exposure/wear respectively; do not use the old window shader.
Neon still uses the existing city's neon material and its native intensity.
"""

from __future__ import annotations

import hashlib
import math
import random


CYAN = (0.025, 0.64, 0.86)
MAGENTA = (0.64, 0.025, 0.32)
VIOLET = (0.21, 0.055, 0.64)
BLUE = (0.035, 0.21, 0.74)
ARCHITECTURE_VERSION = 'cyber_architecture_3'
ARCHETYPES = ('tapered_keel', 'split_crown', 'cantilever_relay', 'offset_slot')


class _RaisedAccumulator:
    """Place the same lot-relative architecture on a solid elevated deck.

    Only positions move; UVs and local random choices remain identical. Keeping
    this translation at the boundary prevents roof/panel offsets being omitted.
    """
    def __init__(self, acc, base_z):
        self.acc, self.base_z = acc, base_z

    def poly(self, pts, uvs, col):
        self.acc.poly([(x, y, z + self.base_z) for x, y, z in pts], uvs, col)

    def strip(self, ax, ay, bx, by, z, w, h, col):
        length = math.hypot(bx - ax, by - ay)
        if length < 0.05:
            return
        nx, ny = -(by - ay) / length * w / 2, (bx - ax) / length * w / 2
        fp = [(ax - nx, ay - ny), (bx - nx, by - ny),
              (bx + nx, by + ny), (ax + nx, ay + ny)]
        run = 0.0
        for i, (x0, y0) in enumerate(fp):
            x1, y1 = fp[(i + 1) % 4]
            span = math.hypot(x1 - x0, y1 - y0)
            if span >= 0.02:
                self.poly([(x0,y0,z),(x1,y1,z),(x1,y1,z+h),(x0,y0,z+h)],
                          [(run,z),(run+span,z),(run+span,z+h),(run,z+h)], col)
                run += span
        self.poly([(x,y,z+h) for x,y in fp], fp, col)


def _point(cx, cy, x, y, ang):
    c, s = math.cos(ang), math.sin(ang)
    return cx + x * c - y * s, cy + x * s + y * c


def _footprint(cx, cy, w, d, ang, cut=0.19):
    """Eight-sided plate; every outline has structural chamfers, never a box."""
    x, y, k = w * 0.5, d * 0.5, min(w, d) * cut
    return [_point(cx, cy, px, py, ang) for px, py in (
        (-x + k, -y), (x - k, -y), (x, -y + k), (x, y - k),
        (x - k, y), (-x + k, y), (-x, y - k), (-x, -y + k))]


def _scale(fp, factor, dx=0.0, dy=0.0):
    cx = sum(p[0] for p in fp) / len(fp)
    cy = sum(p[1] for p in fp) / len(fp)
    return [(cx + (x - cx) * factor + dx,
             cy + (y - cy) * factor + dy) for x, y in fp]


def _face_panel(acc, a, b, z0, z1, col, start=0.0, end=1.0, offset=0.0):
    """One outward-facing, inset face patch; also serves as a recessed light."""
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    if length < 0.02 or z1 - z0 < 0.02 or end - start < 0.001:
        return
    nx, ny = (by - ay) / length, -(bx - ax) / length
    p0 = (ax + (bx - ax) * start + nx * offset,
          ay + (by - ay) * start + ny * offset)
    p1 = (ax + (bx - ax) * end + nx * offset,
          ay + (by - ay) * end + ny * offset)
    span = length * (end - start)
    acc.poly([(p0[0], p0[1], z0), (p1[0], p1[1], z0),
              (p1[0], p1[1], z1), (p0[0], p0[1], z1)],
             [(0, z0), (span, z0), (span, z1), (0, z1)], col)


def _armoured_loft(wall, roof, fp0, z0, fp1, z1, col):
    """Small finish shifts between plates make facets legible in low light."""
    run = 0.0
    for i, a in enumerate(fp0):
        b, c, d = fp0[(i + 1) % 8], fp1[(i + 1) % 8], fp1[i]
        length = math.dist(a, b)
        face_col = (col[0], min(1.0, col[1] + (i % 3) * 0.055),
                    col[2], min(1.0, col[3] + (i % 2) * 0.09))
        wall.poly([(a[0], a[1], z0), (b[0], b[1], z0),
                   (c[0], c[1], z1), (d[0], d[1], z1)],
                  [(run, z0), (run + length, z0),
                   (run + length, z1), (run, z1)], face_col)
        run += length
    roof.poly([(x, y, z1) for x, y in fp1], fp1, col)


def _slope_panel(acc, fp0, low, fp1, high, edge, z0, z1, col,
                 start=0.0, end=1.0, offset=0.0):
    """A patch attached to a sloping plate, without hovering or clipping."""
    pts = []
    for along, z in ((start, z0), (end, z0), (end, z1), (start, z1)):
        fraction = (z - low) / (high - low)
        a = tuple(fp0[edge][j] + (fp1[edge][j] - fp0[edge][j]) * fraction for j in (0, 1))
        next_edge = (edge + 1) % len(fp0)
        b = tuple(fp0[next_edge][j] + (fp1[next_edge][j] - fp0[next_edge][j]) * fraction for j in (0, 1))
        length = math.dist(a, b)
        pts.append((a[0] + (b[0] - a[0]) * along + (b[1] - a[1]) / length * offset,
                    a[1] + (b[1] - a[1]) * along - (b[0] - a[0]) / length * offset, z))
    span = length * (end - start)
    acc.poly(pts, [(0, z0), (span, z0), (span, z1), (0, z1)], col)


def build_cyber_block(city, *, cx, cy, w, d, h, ang, seed, pal,
                      distance, far=False, neon=True, base_z=0.0, source_spire=False):
    """Append a distinct industrial silhouette within the original lot/height.

    Tapered keels, split crowns, supported cantilevers and offset slot towers
    share a material language rather than the same stepped shape.
    Readable armor seams and localized inlays survive panorama sampling.
    """
    if not all(math.isfinite(v) for v in (cx, cy, w, d, h, ang, seed, pal, distance, base_z)):
        raise ValueError('Cyber building parameters must be finite')
    if min(w, d, h) <= 0:
        raise ValueError('Cyber building dimensions must be positive')
    if distance < 0:
        raise ValueError('Cyber building distance must be nonnegative')
    if not hasattr(city, 'cyber') or not hasattr(city, 'cyber_roof'):
        raise ValueError('Create city.cyber and city.cyber_roof accumulators first')
    key = '|'.join(format(v, '.9g') for v in (cx, cy, w, d, h, ang, seed, pal))
    rng = random.Random(int.from_bytes(hashlib.blake2s(key.encode(), digest_size=8).digest(), 'big'))
    wall, roof, glow = (_RaisedAccumulator(acc, base_z)
                        for acc in (city.cyber, city.cyber_roof, city.neon))
    archetype = rng.randrange(4)
    detail = not far and distance < 10000
    texel = max(0.35, distance * 2.0 * math.pi / 8192)
    line = min(max(0.55, texel * 1.05), h * 0.028, min(w, d) * 0.018)
    offset = min(0.28, min(w, d) * 0.001)
    tint = rng.random()
    col = (seed, rng.uniform(0.06, 0.18), tint, rng.uniform(0.25, 0.55))
    plate = (seed, rng.uniform(0.75, 0.95), tint, rng.uniform(0.42, 0.76))
    dark = (seed, 0.0, tint, 0.06)
    accent = (CYAN, MAGENTA, CYAN, VIOLET, BLUE)[int(pal * 997) % 5]
    secondary = MAGENTA if accent in (CYAN, BLUE) else CYAN
    strength = rng.uniform(0.38, 0.55) * (0.80 if far else 1.0)
    tiers, crowns = [], []
    upper_scale = 0.72 if source_spire else 0.88

    # Low, structural foundation. A repeated bell-shaped plinth used to make
    # every variant look like a bunker; the shallow deck now yields to each
    # building's asymmetric working masses and their negative space.
    base = _footprint(cx, cy, w * 0.94, d * 0.90, ang, 0.075)
    base_top = _scale(base, 0.975)
    deck_z = h * 0.065
    _armoured_loft(wall, roof, base, 0.0, base_top, deck_z, plate)
    tiers.append((base, 0.0, deck_z))

    def mass(ox, oy, fw, fd, top, *, bottom=0.065, lean=0.0, lit=False,
             finish=None, bevel=0.075, taper=0.93, cap_scale=0.84):
        ox, oy, fw, fd, lean = (v * upper_scale for v in (ox, oy, fw, fd, lean))
        qx, qy = _point(cx, cy, ox * w, oy * d, ang)
        fp = _footprint(qx, qy, fw * w, fd * d, ang, rng.uniform(0.07, 0.13))
        dx, dy = _point(0, 0, lean * w, 0, ang)
        z0, z1 = h * bottom, h * top
        zm = z1 - min((z1 - z0) * 0.16, h * bevel)
        shoulder = _scale(fp, taper * rng.uniform(0.985, 1.015), dx, dy)
        cap = _scale(shoulder, cap_scale)
        body_col = finish or col
        _armoured_loft(wall, roof, fp, z0, shoulder, zm, body_col)
        _armoured_loft(wall, roof, shoulder, zm, cap, z1, plate)
        if bottom > 0.065:
            underside = list(reversed(fp))
            roof.poly([(x, y, z0) for x, y in underside], underside, dark)
        tiers.append((fp, z0, zm))
        crowns.append((z1, cap, fw * w, fd * d, zm))

        edges = (0, 2, 4, 6)
        def facing(edge):
            a, b = fp[edge], fp[(edge + 1) % 8]
            length = math.dist(a, b)
            return -((a[0] + b[0]) * (b[1] - a[1]) -
                     (a[1] + b[1]) * (b[0] - a[0])) / length
        visible = max(edges, key=facing)
        height = zm - z0
        if detail:
            # Two large armor sections at unequal heights, separated by dark
            # service recesses. This is a hull plate rhythm, not a floor grid.
            for edge in (visible, (visible + 2) % 8):
                _slope_panel(wall, fp, z0, shoulder, zm, edge,
                             z0 + height * 0.07, z0 + height * 0.86,
                             plate, 0.07, 0.36, offset)
                _slope_panel(wall, fp, z0, shoulder, zm, edge,
                             z0 + height * 0.24, z0 + height * 0.96,
                             (seed, 0.40, tint, 0.45), 0.42, 0.91, offset)
                _slope_panel(wall, fp, z0, shoulder, zm, edge,
                             z0 + height * 0.43, z0 + height * 0.49,
                             dark, 0.43, 0.92, offset * 1.8)
                # Contact dirt is confined to panel feet and intake recesses;
                # the broad faces remain quieter than their exposed shoulders.
                _slope_panel(wall, fp, z0, shoulder, zm, edge,
                             z0 + height * 0.035, z0 + height * 0.075,
                             dark, 0.06, 0.93, offset * 1.9)
                for lo in (0.70, 0.765):
                    _slope_panel(wall, fp, z0, shoulder, zm, edge,
                                 z0 + height * lo, z0 + height * (lo + 0.035),
                                 dark, 0.67, 0.89, offset * 1.9)

        if neon and lit:
            # A few inset power channels; their widths hold a final panorama
            # texel. Short dark breaks make them engineered rather than wire.
            edge_len = math.dist(fp[visible], fp[(visible + 1) % 8])
            width = min(0.09, max(0.035, line * 1.35 / edge_len))
            a0 = 0.39 - width * 0.5
            for lo, hi in ((0.12, 0.43), (0.51, 0.88)):
                _slope_panel(wall, fp, z0, shoulder, zm, visible,
                             z0 + height * (lo - 0.035), z0 + height * (hi + 0.035),
                             dark, a0 - width * 0.6, a0 + width * 1.6, offset * 2.0)
                _slope_panel(glow, fp, z0, shoulder, zm, visible,
                             z0 + height * lo, z0 + height * hi,
                             (*accent, strength), a0, a0 + width, offset * 2.8)
            # One horizontal service slit, offset from the long channel.
            _slope_panel(glow, fp, z0, shoulder, zm, visible,
                         z0 + height * 0.16, z0 + height * 0.16 + min(line, height * 0.065),
                         (*accent, strength * 0.63), 0.64, 0.89, offset * 2.8)

        # Unequal recessed roof access panels remain visible from the crown.
        if detail and min(fw * w, fd * d) > 12:
            for position, length in ((-0.22, 0.32), (0.18, 0.19)):
                top_scale = taper * 0.985 * cap_scale
                tx, ty = _point(qx + dx, qy + dy, fw * w * position * top_scale, 0, ang)
                access = _footprint(tx, ty, fw * w * 0.13 * top_scale, fd * d * length * top_scale, ang, 0.12)
                roof.poly([(x, y, z1 + min(h * 0.0005, 0.04)) for x, y in access], access, dark)
        return fp, cap, z1

    if archetype == 0:
        # TAPERED KEEL: a long armored blade with a sharply pinched crown;
        # unequal side shoulders leave its silhouette tall and directional.
        mass(-0.055, 0.035, 0.36, 0.66, 0.99, lean=0.045,
             taper=0.73, cap_scale=0.62, bevel=0.14, lit=True)
        mass(-0.305, -0.07, 0.22, 0.42, rng.uniform(0.38, 0.48),
             taper=0.86, lit=False, finish=plate)
        mass(0.255, 0.07, 0.30, 0.49, rng.uniform(0.55, 0.65),
             lean=-0.025, taper=0.82, lit=True)
    elif archetype == 1:
        # SPLIT CROWN: unequal, inward-leaning fins frame an open air slot.
        # The low connecting service bridge is supported by both fins.
        mass(-0.235, 0.01, 0.28, 0.67, 0.99, lean=0.025,
             taper=0.84, cap_scale=0.69, bevel=0.11, lit=True)
        mass(0.225, -0.055, 0.28, 0.57, rng.uniform(0.79, 0.90),
             lean=-0.025, taper=0.80, cap_scale=0.73, lit=True)
        mass(0.0, 0.15, 0.63, 0.17, 0.40, bottom=0.29,
             taper=0.98, lit=False, finish=plate, bevel=0.025)
    elif archetype == 2:
        # CANTILEVER RELAY: one grounded mast and a shorter support carry an
        # offset command deck; the notch beneath it remains visibly open.
        mass(0.22, 0.08, 0.30, 0.49, 0.99, lean=-0.015,
             taper=0.84, cap_scale=0.65, bevel=0.13, lit=True)
        mass(-0.245, 0.13, 0.20, 0.38, 0.64,
             taper=0.90, lit=False)
        mass(-0.06, 0.055, 0.72, 0.45, 0.78, bottom=0.57,
             lean=-0.01, taper=0.90, cap_scale=0.86, lit=True,
             finish=plate, bevel=0.045)
        mass(-0.09, -0.285, 0.55, 0.15, 0.24, lit=False)
    else:
        # OFFSET SLOT: two tall blades and a low rear knuckle. Unlike a
        # Manhattan setback block it has no concentric tiers or roof needle.
        mass(-0.195, 0.065, 0.32, 0.58, 0.99, lean=0.02,
             taper=0.79, cap_scale=0.67, bevel=0.12, lit=True)
        mass(0.235, 0.11, 0.28, 0.35, rng.uniform(0.76, 0.89),
             lean=-0.025, taper=0.86, lit=True)
        mass(0.01, 0.305, 0.66, 0.17, 0.46,
             taper=0.92, lit=False, finish=plate)

    if detail:
        # An asymmetric protected utility spine along the front deck. Open
        # gaps and dark housings give a believable attachment to the city.
        mass(-0.08, -0.355, 0.57, 0.075, 0.18, lit=False, finish=plate, bevel=0.025)
        if neon:
            for x0, x1 in ((-0.28, -0.08), (0.015, 0.14)):
                a = _point(cx, cy, w * x0 * upper_scale, d * -0.352 * upper_scale, ang)
                b = _point(cx, cy, w * x1 * upper_scale, d * -0.352 * upper_scale, ang)
                glow.strip(a[0], a[1], b[0], b[1], h * 0.18,
                           min(line, d * 0.015), min(line * 0.3, h * 0.006),
                           (*secondary, strength * 0.48))

    # Top surfaces include a tiny panel offset. The highest bulk stops at
    # .99 h so every detail still respects the caller's exact title-lane cap.
    ztop, top_fp, top_w, top_d, ztop0 = max(crowns, key=lambda x: x[0])
    return dict(tiers=[(fp, z0 + base_z, z1 + base_z) for fp, z0, z1 in tiers],
                top_fp=top_fp, ztop0=ztop0 + base_z, ztop=ztop + base_z,
                w=top_w, d=top_d, style=4.0, archetype=archetype,
                archetype_name=ARCHETYPES[archetype], version=ARCHITECTURE_VERSION,
                skip_legacy_details=True)


def make_cyber_material(name='sky3d_cyber_armour', *, roof=False, legacy=False):
    """Build a dark alloy material with broad plate wear and fine roughness.

    The ambient floor is deliberately close to build_city.BODY_FLOOR. The
    shader adds no illuminated windows/circuit grids and changes no world
    settings. Sparse native-neon geometry carries the architectural light.
    Blender is imported lazily so geometry can be checked without Blender.

    ``legacy=True`` adapts the landmark schema (seed, style, palette, lit
    fraction) to this kit's coating and exposure roles. In particular, a
    spire's style of 2..3 is not a metal/finish value. The approved ordinary
    kit keeps its exact original graph and values when this flag is false.
    """
    import bpy

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()

    def node(kind, name):
        n = nodes.new(kind)
        n.label = n.name = name
        return n

    def math_node(operation, a, b=0.0, label=''):
        n = node('ShaderNodeMath', label or operation)
        n.operation = operation
        for index, value in enumerate((a, b)):
            if isinstance(value, (int, float)):
                n.inputs[index].default_value = value
            else:
                links.new(value, n.inputs[index])
        return n.outputs[0]

    def ramp(source, stops, label):
        n = node('ShaderNodeValToRGB', label)
        cr = n.color_ramp
        for i, (position, color) in enumerate(stops):
            entry = cr.elements[i] if i < 2 else cr.elements.new(position)
            entry.position, entry.color = position, (*color, 1.0)
        links.new(source, n.inputs['Fac'])
        return n.outputs['Color']

    attr = node('ShaderNodeAttribute', 'Per-plate finish / exposure')
    attr.attribute_name = 'bld'
    split = node('ShaderNodeSeparateColor', 'Seed / finish / cool tint')
    links.new(attr.outputs['Color'], split.inputs['Color'])
    geom = node('ShaderNodeNewGeometry', 'True city-space wear scale')
    finish_input, wear_input = split.outputs['Green'], attr.outputs['Alpha']
    if legacy:
        # The former palette channel is already normalized, so keep its blue
        # channel meaning as cool-tint metadata. Neither material turns whole
        # panels into the landmark's neon hue; the inset light carries that.
        # Existing seed/style draws supply restrained coating variation while
        # upward-facing shoulders receive the same exposed-alloy role as the
        # modeled shoulder plates of the ordinary kit.
        variant = math_node('FRACT', split.outputs['Green'], label='Legacy style variant only')
        seed = math_node('FRACT', split.outputs['Red'], label='Stable landmark coating seed')
        normal = node('ShaderNodeSeparateXYZ', 'Landmark structural face direction')
        links.new(geom.outputs['Normal'], normal.inputs[0])
        exposure = node('ShaderNodeMapRange', 'Exposed landmark shoulders')
        exposure.clamp = True
        exposure.inputs['From Min'].default_value = 0.08
        exposure.inputs['From Max'].default_value = 0.65
        links.new(normal.outputs['Z'], exposure.inputs['Value'])
        # The landmark roof accumulator also contains reversed underside caps
        # (for example the saucer). Only upward-facing surfaces are exposed;
        # an underside must not inherit the roof's worn-alloy ambient floor.
        shoulder = exposure.outputs['Result']
        coating = math_node('ADD', 0.10, math_node('MULTIPLY', variant, 0.10),
                            'Landmark blue-black coating')
        alloy = math_node('ADD', 0.76, math_node('MULTIPLY', seed, 0.12),
                          'Landmark worn shoulder alloy')
        finish_input = math_node('ADD',
            math_node('MULTIPLY', coating, math_node('SUBTRACT', 1.0, shoulder)),
            math_node('MULTIPLY', alloy, shoulder), 'Landmark finish in kit range')
        activity = node('ShaderNodeMapRange', 'Legacy activity to bounded weather exposure')
        activity.clamp = True
        activity.inputs['From Min'].default_value = 0.0
        activity.inputs['From Max'].default_value = 0.36
        activity.inputs['To Min'].default_value = 0.28
        activity.inputs['To Max'].default_value = 0.53
        links.new(attr.outputs['Alpha'], activity.inputs['Value'])
        wear_input = math_node('ADD', activity.outputs['Result'],
                              math_node('MULTIPLY', shoulder, 0.18),
                              'Landmark exposure in kit range')
    coarse = node('ShaderNodeTexNoise', 'Uneven mineral deposits and rain staining')
    coarse.inputs['Scale'].default_value = 0.035 if roof else 0.022
    coarse.inputs['Detail'].default_value = 2.0
    coarse.inputs['Roughness'].default_value = 0.64
    runoff = node('ShaderNodeVectorMath', 'Long restrained rain runoff')
    runoff.operation = 'MULTIPLY'
    runoff.inputs[1].default_value = (1.0, 1.0, 0.25 if not roof else 1.0)
    links.new(geom.outputs['Position'], runoff.inputs[0])
    links.new(runoff.outputs['Vector'], coarse.inputs['Vector'])
    fine = node('ShaderNodeTexNoise', 'Subtle alloy finish')
    fine.inputs['Scale'].default_value = 0.8
    fine.inputs['Detail'].default_value = 2.0
    links.new(geom.outputs['Position'], fine.inputs['Vector'])
    deposits = node('ShaderNodeMapRange', 'Readable coating deposits at panorama scale')
    deposits.clamp = True
    deposits.inputs['From Min'].default_value = 0.30
    deposits.inputs['From Max'].default_value = 0.68
    links.new(coarse.outputs['Fac'], deposits.inputs['Value'])
    finish = math_node('ADD', math_node('MULTIPLY', finish_input, 0.63),
                       math_node('ADD', math_node('MULTIPLY', deposits.outputs['Result'], 0.31),
                                 math_node('MULTIPLY', wear_input, 0.06)),
                       'Plate finish plus deposits')
    coord = node('ShaderNodeTexCoord', 'Metre-scaled architectural panel UVs')
    plates = node('ShaderNodeTexBrick', 'Inset armor joints, never luminous windows')
    plates.inputs['Scale'].default_value = 1.0
    plates.inputs['Brick Width'].default_value = 19.0
    plates.inputs['Row Height'].default_value = 32.0
    plates.inputs['Mortar Size'].default_value = 0.38
    plates.inputs['Mortar Smooth'].default_value = 0.08
    plates.offset = 0.21
    links.new(coord.outputs['UV'], plates.inputs['Vector'])
    joint = math_node('SUBTRACT', 1.0, math_node('MULTIPLY', plates.outputs['Fac'], 0.68), 'Dirt in panel joints')
    finish = math_node('MULTIPLY', finish, joint, 'Surface wear with recessed seams')
    base = ramp(finish, [(0.0, (0.002, 0.003, 0.005)),
                         (0.45, (0.010, 0.014, 0.022)),
                         (1.0, (0.052, 0.057, 0.068))], 'Blue-black coating / worn graphite shoulders')
    ambient = ramp(finish, [(0.0, (0.0004, 0.00055, 0.0009)),
                            (0.45, (0.0012, 0.0016, 0.0028)),
                            (0.75, (0.0034, 0.0040, 0.0062)),
                            (1.0, (0.0080, 0.0085, 0.0110))], 'Dark panels and worn exposed shoulders')
    roughness = math_node('ADD', 0.52 if roof else 0.43,
                         math_node('MULTIPLY', coarse.outputs['Fac'], 0.25), 'Uneven worn roughness')
    metal = math_node('ADD', 0.25, math_node('MULTIPLY', finish_input, 0.34), 'Paint / exposed alloy')
    bsdf = node('ShaderNodeBsdfPrincipled', 'Dark weathered architectural alloy')
    links.new(base, bsdf.inputs['Base Color'])
    links.new(roughness, bsdf.inputs['Roughness'])
    links.new(metal, bsdf.inputs['Metallic'])
    links.new(ambient, bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 1.0
    bump = node('ShaderNodeBump', 'Tiny surface pitting; silhouette stays clean')
    bump.inputs['Strength'].default_value = 0.12
    bump.inputs['Distance'].default_value = 0.07
    relief = math_node('SUBTRACT', math_node('MULTIPLY', fine.outputs['Fac'], 0.28),
                       math_node('MULTIPLY', plates.outputs['Fac'], 0.55), 'Pitting and shallow panel recesses')
    links.new(relief, bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    output = node('ShaderNodeOutputMaterial', 'Cyber architecture output')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat
