"""Read, graft and rewrite BO3 .efx effects (docs/192 s10, THE SKY FLEET v3).

An .efx is text: "iwfx N", an optional effect header (v3: efFlags, efBoundingBoxMin/Max, ...), then one "{ ... }"
block per ELEMENT. Every element field is one line "\tkey value;" except GRAPHS ("\tkey scale\n\t{ {curve a} {curve b} };")
and the visuals block at the end ("\tbillboardSprite\n\t{\n\t\t"material"\n\t};"). v2 elements are v3 elements plus
two optional fields (billboardTopWidth / billboardBottomWidth), which 201 stock v3 files also carry, so a v2 donor
element grafts into a v3 effect unchanged.

  parse(text) -> Effect(version, header_lines, [Element])        Element keeps its fields IN ORDER (round-trips)
  Effect.text()                                                   the file again

The sky's rules (why every grafted element is rewritten, not copied):
  * stock elements only SPAWN within spawnRange of the camera and FADE by fadeInRange - both set for a room, not for
    a ship 12,000 units away: open them (0 .. FAR) and zero the fades;
  * spawnFrustumCull drops a particle whose spawn point is outside the view: harmless, but its radius must not be 0
    with the flag on for big sprites - cleared;
  * useCollision / collision offsets make sky particles hit the tower: removed;
  * SCALE: every length (sizes, velocities, spawn origin/offsets, gravity is units/s^2) is multiplied by one factor, so
    a donor built for a 20-unit drone thruster becomes a 400-unit capital drive with the SAME look and timing;
  * AXES: most thruster donors fire along +X (the tag's forward); a ship's exhaust leaves along -X: mirror X (and Y,
    to keep the handedness - a mirror would flip any spin) = a 180 degree turn about Z.
"""
import re

FAR = 64000


class Graph:
    """A graph field: scale + two curves (a / b), each a list of rows of floats."""
    def __init__(self, key, scale_text, curves):
        self.key, self.scale_text, self.curves = key, scale_text, curves

    @property
    def scale(self):
        return float(self.scale_text)

    @scale.setter
    def scale(self, v):
        self.scale_text = fmt(v)

    def text(self):
        out = ['\t' + self.key + ' ' + self.scale_text, '\t{']
        for c in self.curves:
            out.append('\t\t{')
            for row in c:
                out.append('\t\t\t' + ' '.join(fmt(v) for v in row))
            out.append('\t\t}')
        out.append('\t};')
        return '\n'.join(out)


class Block:
    """A braced list field (the visuals: billboardSprite { "mat" }, elemSpawnSound { }, ...)."""
    def __init__(self, key, body_lines):
        self.key, self.body = key, body_lines

    def text(self):
        return '\n'.join(['\t' + self.key, '\t{'] + self.body + ['\t};'])


def fmt(v):
    if isinstance(v, str):
        return v
    if abs(v - round(v)) < 1e-9 and abs(v) < 1e9:
        return '%d' % round(v)
    s = '%.6f' % v
    return s.rstrip('0').rstrip('.') if '.' in s else s


class Element:
    def __init__(self, items):
        self.items = items          # list of ('line', key, value_text) | Graph | Block

    # ---- access -------------------------------------------------------------------------------------------------------
    def _find(self, key):
        for i, it in enumerate(self.items):
            k = it[1] if isinstance(it, tuple) else it.key
            if k == key:
                return i, it
        return None, None

    def has(self, key):
        return self._find(key)[0] is not None

    def get(self, key):
        i, it = self._find(key)
        if it is None:
            raise KeyError(key)
        return it[2] if isinstance(it, tuple) else it

    def nums(self, key):
        return [float(x) for x in self.get(key).split()]

    def set(self, key, value):
        i, it = self._find(key)
        text = value if isinstance(value, str) else ' '.join(fmt(v) for v in (value if isinstance(value, (list, tuple)) else [value]))
        if it is None:
            raise KeyError('no field ' + key + ' to set')
        self.items[i] = ('line', key, text)

    def graph(self, key):
        g = self.get(key)
        assert isinstance(g, Graph), key
        return g

    @property
    def name(self):
        return self.get('name').strip('"')

    @name.setter
    def name(self, v):
        self.set('name', '"' + v + '"')

    def flags(self, key):
        return self.get(key).split()

    def set_flags(self, key, add=(), remove=()):
        cur = [f for f in self.flags(key) if f not in remove]
        for f in add:
            if f not in cur:
                cur.append(f)
        self.set(key, ' '.join(cur))

    @property
    def visual(self):
        """(type, [materials / effect names]) from the trailing visuals block."""
        for it in reversed(self.items):
            if isinstance(it, Block) and it.key not in ('elemSpawnSound', 'elemFollowSound'):
                return it.key, [b.strip().strip('"') for b in it.body if b.strip()]
        return None, []

    def text(self):
        out = ['{']
        for it in self.items:
            if isinstance(it, tuple):
                out.append('\t' + it[1] + (' ' + it[2] if it[2] != '' else '') + ';')
            else:
                out.append(it.text())
        out.append('}')
        return '\n'.join(out)

    def copy(self):
        return parse_element(self.text())


class Effect:
    def __init__(self, version, header, elements):
        self.version, self.header, self.elements = version, header, elements

    def text(self):
        parts = ['iwfx ' + str(self.version), '']
        parts += self.header
        body = '\n'.join(parts) + '\n' + '\n'.join(e.text() for e in self.elements) + '\n'
        return body

    def set_bounds(self, lo, hi):
        for i, ln in enumerate(self.header):
            if ln.startswith('\tefBoundingBoxMin '):
                self.header[i] = '\tefBoundingBoxMin %d %d %d;' % tuple(int(round(v)) for v in lo)
            elif ln.startswith('\tefBoundingBoxMax '):
                self.header[i] = '\tefBoundingBoxMax %d %d %d;' % tuple(int(round(v)) for v in hi)


def parse_element(block_text):
    lines = block_text.strip('\n').split('\n')
    assert lines[0] == '{' and lines[-1] == '}', lines[:1] + lines[-1:]
    lines = lines[1:-1]
    items, i = [], 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r'^\t([A-Za-z_][A-Za-z0-9_]*)(.*)$', ln)
        assert m, 'efx: cannot read element line %r' % ln
        key, rest = m.group(1), m.group(2)
        if rest.startswith(' '):
            rest = rest[1:]
        nxt = lines[i + 1] if i + 1 < len(lines) else ''
        if nxt == '\t{' and not rest.endswith(';'):
            # a graph (key scale) or a block (key alone): read to the matching "\t};"
            j = i + 2
            body = []
            while lines[j] != '\t};':
                body.append(lines[j])
                j += 1
            if rest.strip() != '' and body and body[0] == '\t\t{':
                curves, cur = [], None
                for b in body:
                    if b == '\t\t{':
                        cur = []
                    elif b == '\t\t}':
                        curves.append(cur)
                        cur = None
                    else:
                        cur.append([float(x) for x in b.split()])
                items.append(Graph(key, rest.strip(), curves))
            else:
                items.append(Block(key, body))
            i = j + 1
            continue
        assert rest.endswith(';') or ln.endswith(';'), 'efx: unterminated field %r' % ln
        items.append(('line', key, rest[:-1] if rest.endswith(';') else ''))
        i += 1
    return Element(items)


def parse(text):
    text = text.replace('\r\n', '\n')
    first, rest = text.split('\n', 1)
    m = re.match(r'iwfx (\d+)', first.strip())
    assert m, 'not an efx file'
    version = int(m.group(1))
    lines = rest.split('\n')
    header, elements, i = [], [], 0
    while i < len(lines) and lines[i] != '{':
        if lines[i].strip():
            header.append(lines[i])
        i += 1
    while i < len(lines):
        if lines[i] == '{':
            j = i + 1
            while lines[j] != '}':
                j += 1
            elements.append(parse_element('\n'.join(lines[i:j + 1])))
            i = j + 1
        else:
            assert not lines[i].strip(), 'efx: stray line %r' % lines[i]
            i += 1
    return Effect(version, header, elements)


def load(path):
    with open(path, encoding='utf-8', errors='strict') as fh:
        return parse(fh.read())


# ---- the sky rewrites --------------------------------------------------------------------------------------------------
LENGTH_GRAPHS = ('velGraph0X', 'velGraph0Y', 'velGraph0Z', 'velGraph1X', 'velGraph1Y', 'velGraph1Z', 'sizeGraph0', 'sizeGraph1',
                 'lightRadiusGraph')
LENGTH_PAIRS = ('spawnOrgX', 'spawnOrgY', 'spawnOrgZ', 'spawnOffsetRadius', 'spawnOffsetHeight', 'gravity')


def open_for_sky(e, far=FAR):
    """Spawn at any distance, never fade by distance, never collide."""
    e.set('spawnRange', [0, far])
    e.set('fadeInRange', [0, 0])
    e.set('fadeOutRange', [0, 0])
    e.set_flags('flags', remove=('useCollision', 'spawnFrustumCull'))
    if e.has('collRadius'):
        e.set('collRadius', 0)
    if e.has('collOffset'):
        e.set('collOffset', [0, 0, 0])
    if e.has('fxOnImpact'):
        e.set('fxOnImpact', '""')


def scale_space(e, k):
    """Every length in the element x k (sizes, velocities, spawn origin + offsets, gravity, light radius, trail
    segment lengths). Timing untouched: the donor's look at k times the size."""
    for key in LENGTH_GRAPHS:
        if e.has(key):
            g = e.graph(key)
            g.scale = g.scale * k
    for key in LENGTH_PAIRS:
        if e.has(key):
            e.set(key, [v * k for v in e.nums(key)])
    for key in ('trailSplitDist', 'trailRepeatDist'):
        if e.has(key):
            e.set(key, max(1, int(round(float(e.get(key)) * k))))
    for key in ('trailFadeInDist', 'trailFadeOutDist', 'emitSizeForDensity', 'attachmentSizeForDensity', 'spotLightStartRadius',
                'spotLightEndRadius', 'zFeather'):
        if e.has(key):
            e.set(key, float(e.get(key)) * k)
    if e.has('emitDist'):
        e.set('emitDist', [v * k for v in e.nums('emitDist')])
    if e.has('billboardTopWidth'):
        e.set('billboardTopWidth', float(e.get('billboardTopWidth')) * k)
    if e.has('billboardBottomWidth'):
        e.set('billboardBottomWidth', float(e.get('billboardBottomWidth')) * k)


def turn_about_z(e):
    """Mirror X and Y (a 180 degree turn about Z): a donor firing along +X now fires along -X."""
    for axis in ('X', 'Y'):
        for key in ('velGraph0' + axis, 'velGraph1' + axis):
            if e.has(key):
                g = e.graph(key)
                g.scale = -g.scale
        k = 'spawnOrg' + axis
        if e.has(k):
            base, rng = e.nums(k)
            e.set(k, [-base, -rng])


def shift(e, dx, dy, dz):
    """Move the element's spawn origin (in effect space)."""
    for key, d in (('spawnOrgX', dx), ('spawnOrgY', dy), ('spawnOrgZ', dz)):
        base, rng = e.nums(key)
        e.set(key, [base + d, rng])


def tint(e, rgb, mix=1.0):
    """Blend every colour key toward rgb (mix 1 = replace hue, keep each key's brightness)."""
    g = e.graph('colorGraph')
    for c in g.curves:
        for row in c:
            lum = max(row[1], row[2], row[3])
            for j in range(3):
                row[1 + j] = row[1 + j] * (1 - mix) + rgb[j] * lum * mix


def mul_alpha(e, k):
    g = e.graph('alphaGraph')
    for c in g.curves:
        for row in c:
            row[1] = min(1.0, row[1] * k)


def life_scale(e, k):
    base, rng = e.nums('lifeSpanMsec')
    e.set('lifeSpanMsec', [int(round(base * k)), int(round(rng * k))])


def uses(e):
    """The materials / child effects this element names (the visuals block, plus runner / impact / death children)."""
    t, mats = e.visual
    extra = []
    for key in ('fxOnImpact', 'fxOnDeath', 'emission', 'attachment'):
        if e.has(key):
            v = e.get(key).strip().strip('"')
            if v:
                extra.append(v)
    return t, mats, extra


def summary(e):
    t, mats, extra = uses(e)
    life = e.nums('lifeSpanMsec')
    loop = e.nums('spawnLooping')
    size = e.graph('sizeGraph0').scale if e.has('sizeGraph0') else 0
    vel = [e.graph(k).scale for k in ('velGraph0X', 'velGraph0Y', 'velGraph0Z') if e.has(k)]
    return '%-18s %-14s life %5d+%-4d loop %4d/%-3d size %7.1f vel %s flags [%s] %s %s' % (
        e.name[:18], t, life[0], life[1], loop[0], loop[1], size, [round(v, 1) for v in vel],
        ' '.join(f for f in e.flags('flags') if f in ('runRelToEffect', 'runRelToSpawn', 'runRelToWorld', 'spawnRelative')),
        mats, extra)
