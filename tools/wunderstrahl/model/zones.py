"""Procedural authoring materials for the emitter zones (Blender/Cycles; needs bpy).

Each zone material computes five channels from object-space position (the parts live in native gun space):
  c  diffuse (linear; baked into an sRGB image)      s  fullspec F0 colour (linear; sRGB image)
  g  gloss 0..1 over glossRange 0..12 (Non-Color)     e  emission colour x strength / EMISSION_SCALE (sRGB image)
  bump height (turning marks, knurled bands, the engraved focus scale, braid) on top of a Bevel-node normal ->
  baked into the DirectX normal map, so machined edges are ROUNDED and catch a highlight.
Wear comes from the same Bevel node (where the rounded normal leaves the true one = an exposed edge), broken up so
it chips rather than outlines; recess dirt from the Ambient Occlusion node; heat staining (straw -> bronze, never
the blue temper band) on the hub face and housing nose next to the crystal. Colours are written in sRGB code
values and converted, so a baked 8-bit map stores exactly the authored sRGB values.
set_channel(mat, 'c'|'s'|'g'|'e'|'n'|'preview') routes one channel to the output (n = a BSDF carrying the bump, so
the NORMAL bake sees the relief).

Review pass 2 (2026-10-06): brass is the body's yellow brass (no olive), the lips glow in the core-yellow family only
(no pale 'hot' cream), the crystal is cut - flat facets alternating in brightness with darker facet edges, a hot
table, no radial rays - and every metal carries turning sheen, smudges and edge wear instead of flat spec/gloss.
Review pass 3: metals add fine scratches, dings and a broad unevenness, with gloss varied at the body's scale; the
spokes carry lengthwise grind marks; each crystal facet swings +-35% from a hash of its own normal, with Bevel-node
cut lines on every facet edge and a small hot point on the star table; the conduit light line is dim with windows.
"""
import bpy, math
from emitter import AXZ
import materials

# The emitter material's scaleRGB (materials.py): baked emission values are relative to it.
EMISSION_SCALE = float(materials.MATERIALS['mtl_tod2_ws_emitter']['scale'])
CORE = (255, 214, 64); HOT = (255, 238, 150); AMBER = (255, 168, 30); GOLD = (232, 170, 30)
HEAT_TINT = (206, 160, 92)        # straw-bronze temper colour on hot steel and brass
BEVEL_R = 0.03                     # inches: the machined edge radius the normal map carries
TURN_FREQ = 12.0                   # turning marks per inch (one period = 9.7 texels at 116.5 px/inch: mip-safe)


def lin(c):
    return tuple(((x / 255.0) / 12.92 if (x / 255.0) <= .04045 else (((x / 255.0) + .055) / 1.055) ** 2.4) for x in c)


class G:
    """Tiny node-graph helper."""
    def __init__(self, mat):
        self.nt = mat.node_tree; self.N = self.nt.nodes; self.L = self.nt.links; self.x = -2200; self.y = 0

    def node(self, kind, **props):
        n = self.N.new(kind); n.location = (self.x, self.y); self.y -= 160
        if self.y < -2600:
            self.y = 0; self.x += 260
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def link(self, a, b):
        self.L.new(a, b)

    def math(self, op, a, b=None, clamp=False):
        n = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                self.link(v, n.inputs[i])
        return n.outputs[0]

    def mix(self, a, b, f, kind='RGBA'):
        n = self.node('ShaderNodeMix', data_type=kind)
        if kind == 'RGBA':
            ia, ib, io = n.inputs[6], n.inputs[7], n.outputs[2]
        else:
            ia, ib, io = n.inputs[2], n.inputs[3], n.outputs[0]
        for sock, v in ((ia, a), (ib, b)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, tuple):
                sock.default_value = (*v, 1.0)
            else:
                self.link(v, sock)
        if isinstance(f, (int, float)):
            n.inputs[0].default_value = f
        else:
            self.link(f, n.inputs[0])
        return io

    def rgb(self, c):
        n = self.node('ShaderNodeRGB'); n.outputs[0].default_value = (*lin(c), 1.0); return n.outputs[0]

    def value(self, v):
        n = self.node('ShaderNodeValue'); n.outputs[0].default_value = v; return n.outputs[0]

    def smooth(self, e0, e1, x):
        n = self.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP', clamp=True)
        self.link(x, n.inputs['Value']); n.inputs['From Min'].default_value = e0; n.inputs['From Max'].default_value = e1
        return n.outputs['Result']

    def band(self, lo, hi, x, soft=.004):
        """1 inside [lo, hi] with soft edges."""
        return self.math('MULTIPLY', self.smooth(lo - soft, lo + soft, x), self.smooth(hi + soft, hi - soft, x))

    def scale_rgb(self, c, f):
        n = self.node('ShaderNodeVectorMath', operation='SCALE')
        self.link(c, n.inputs[0])
        if isinstance(f, (int, float)):
            n.inputs['Scale'].default_value = f
        else:
            self.link(f, n.inputs['Scale'])
        return n.outputs[0]

    def frac_dist(self, t):
        """Distance of t to the nearest integer (0..0.5)."""
        return self.math('ABSOLUTE', self.math('SUBTRACT', t, self.math('FLOOR', self.math('ADD', t, .5))))


def geometry_signals(g):
    tc = g.node('ShaderNodeTexCoord')
    sep = g.node('ShaderNodeSeparateXYZ'); g.link(tc.outputs['Object'], sep.inputs[0])
    x, y, z = sep.outputs[0], sep.outputs[1], sep.outputs[2]
    dz = g.math('SUBTRACT', z, AXZ)
    r = g.math('SQRT', g.math('ADD', g.math('MULTIPLY', y, y), g.math('MULTIPLY', dz, dz)))
    theta = g.math('ARCTAN2', dz, y)
    geo = g.node('ShaderNodeNewGeometry')
    nsep = g.node('ShaderNodeSeparateXYZ'); g.link(geo.outputs['Normal'], nsep.inputs[0])
    facing_x = g.math('ABSOLUTE', nsep.outputs[0])
    # outward-radial-ness of the surface (1 on the outside of a ring, 0 on its faces)
    radial = g.math('DIVIDE', g.math('ADD', g.math('MULTIPLY', nsep.outputs[1], y), g.math('MULTIPLY', nsep.outputs[2], dz)),
                    g.math('MAXIMUM', r, .001))
    bev = g.node('ShaderNodeBevel', samples=8); bev.inputs['Radius'].default_value = BEVEL_R
    dot = g.node('ShaderNodeVectorMath', operation='DOT_PRODUCT')
    g.link(bev.outputs['Normal'], dot.inputs[0]); g.link(geo.outputs['Normal'], dot.inputs[1])
    bevel_dev = g.math('SUBTRACT', 1.0, dot.outputs['Value'])
    edge = g.smooth(.006, .055, bevel_dev)
    ao = g.node('ShaderNodeAmbientOcclusion', samples=12)
    ao.inputs['Distance'].default_value = .30
    dirt = g.smooth(.93, .55, ao.outputs['AO'])
    # The Bevel node rounds concave junctions too (a spoke meeting the hoop, a seat on its face): a short-range AO
    # tells the two apart - an exposed convex edge sees open sky, a concave corner does not. Corners take grime.
    ao_short = g.node('ShaderNodeAmbientOcclusion', samples=8)
    ao_short.inputs['Distance'].default_value = .06
    concave = g.smooth(.95, .78, ao_short.outputs['AO'])
    edge = g.math('MULTIPLY', edge, g.math('SUBTRACT', 1.0, concave))
    dirt = g.math('MAXIMUM', dirt, g.math('MULTIPLY', concave, .65))
    return dict(tc=tc, pos=tc.outputs['Object'], x=x, y=y, z=z, r=r, theta=theta, facing_x=facing_x, radial=radial,
                bevel=bev.outputs['Normal'], bevel_dev=bevel_dev, edge=edge, dirt=dirt,
                true_normal=geo.outputs['True Normal'])


def noise(g, vec, scale, detail=3.0, rough=.55):
    n = g.node('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough
    g.link(vec, n.inputs['Vector'])
    return n.outputs['Fac']


def turning(g, s):
    """-1..1 machining pattern: concentric turning on lathe faces, lengthwise on cylinders, slightly irregular (a real
    lathe); the five flat spokes (the only surfaces in the window band) carry lengthwise GRIND marks instead - lathe
    rings across a flat bar read as corrugation (review pass 3)."""
    wob = g.math('MULTIPLY', noise(g, s['pos'], 2.5, 2.0), 2.2)
    face = g.math('SINE', g.math('ADD', g.math('MULTIPLY', s['r'], 2 * math.pi * TURN_FREQ), wob))
    cyl = g.math('SINE', g.math('ADD', g.math('MULTIPLY', s['x'], 2 * math.pi * TURN_FREQ), wob))
    turn = g.mix(cyl, face, s['facing_x'], 'FLOAT')
    # across a spoke's front / back face: the arc distance from the NEAREST spoke's centre line (spokes at 54 + 72k
    # degrees), so the grind runs along each spoke rather than diagonally across it
    a54, a72 = math.radians(54.0), math.radians(72.0)
    kk = g.math('FLOOR', g.math('ADD', g.math('DIVIDE', g.math('SUBTRACT', s['theta'], a54), a72), .5))
    dth = g.math('SUBTRACT', s['theta'], g.math('ADD', a54, g.math('MULTIPLY', kk, a72)))
    arc = g.math('MULTIPLY', dth, s['r'])
    grind_face = g.math('SINE', g.math('ADD', g.math('MULTIPLY', arc, 2 * math.pi * 14.0), wob))
    grind_side = g.math('SINE', g.math('ADD', g.math('MULTIPLY', s['x'], 2 * math.pi * 14.0), wob))
    grind = g.mix(grind_side, grind_face, s['facing_x'], 'FLOAT')
    spoke = g.math('MULTIPLY', g.band(1.995, 2.515, s['r'], .004), g.band(38.665, 38.955, s['x'], .004))
    return g.mix(turn, grind, spoke, 'FLOAT')


def scratches(g, s):
    """0..1 fine straight scratches in three families of directions, broken into short runs and gathered in patches
    (handling, holstering, cleaning) - the scratch density of the DG-2's own body maps."""
    out = g.value(0.0)
    for k, (euler, seed) in enumerate((((0.3, 1.1, 0.2), 11.0), ((1.2, -0.4, 0.9), 23.0), ((-0.8, 0.6, -1.3), 37.0))):
        rot = g.node('ShaderNodeVectorRotate', rotation_type='EULER_XYZ')
        rot.inputs['Rotation'].default_value = euler
        g.link(s['pos'], rot.inputs['Vector'])
        mp = g.node('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1.4, 1.4, 7.0)
        mp.inputs['Location'].default_value = (seed, seed * .37, seed * .61)
        g.link(rot.outputs['Vector'], mp.inputs['Vector'])
        n = noise(g, mp.outputs['Vector'], 1.0, 0.0, .5)
        ridge = g.math('SUBTRACT', 1.0, g.math('ABSOLUTE', g.math('SUBTRACT', g.math('MULTIPLY', n, 2.0), 1.0)))
        line = g.smooth(.955, .99, ridge)
        mp2 = g.node('ShaderNodeMapping'); mp2.inputs['Location'].default_value = (seed * 1.7, seed * .2, seed)
        g.link(rot.outputs['Vector'], mp2.inputs['Vector'])
        runs = g.smooth(.55, .63, noise(g, mp2.outputs['Vector'], 3.2, 1.0))
        out = g.math('MAXIMUM', out, g.math('MULTIPLY', line, runs))
    patch = g.smooth(.40, .66, noise(g, s['pos'], 1.6, 2.0))
    return g.math('MULTIPLY', out, patch)


def relief(g, s, zone, turn):
    """Height field (inches) for the NORMAL bake + the engraving mask (grime fills engraved lines). Every period
    spans >= 9 texels of the 116.5 px/inch atlas, so the relief survives mips without shimmer or moire. Metals also
    get small dings and a broad unevenness (hand-finished, knocked about - not CAD-perfect)."""
    h = g.math('MULTIPLY', turn, g.mix(.0012, .0018, s['facing_x'], 'FLOAT'))
    if zone in METALS:
        dings = g.smooth(.70, .77, noise(g, s['pos'], 14.0, 1.0))
        h = g.math('ADD', h, g.math('MULTIPLY', dings, -.0022))
        h = g.math('ADD', h, g.math('MULTIPLY', g.math('SUBTRACT', noise(g, s['pos'], 4.0, 2.0), .5), .0016))
        # fine surface grain (period ~2.6 texels): the pixel-scale tooth of the DG-2's own metal maps
        h = g.math('ADD', h, g.math('MULTIPLY', g.math('SUBTRACT', noise(g, s['pos'], 45.0, 2.0), .5), .0005))
    groove = g.value(0.0)
    if zone == 'brass':
        # diamond knurl on the outside of the ring bands and the hoop band (an integer count of teeth per turn keeps
        # the pattern seamless; pitch 1/12 inch at every radius), not on the claw seats in front of the hoop
        teeth = g.math('FLOOR', g.math('ADD', g.math('MULTIPLY', s['r'], 2 * math.pi * TURN_FREQ), .5))
        a = g.math('MULTIPLY', s['theta'], teeth)
        b = g.math('MULTIPLY', s['x'], 2 * math.pi * TURN_FREQ)
        k = g.math('MULTIPLY', g.math('SINE', g.math('ADD', a, b)), g.math('SINE', g.math('SUBTRACT', a, b)))
        mask = g.math('MULTIPLY', g.smooth(.80, .95, s['radial']), g.smooth(1.92, 2.0, s['r']))
        mask = g.math('MULTIPLY', mask, g.smooth(38.985, 38.965, s['x']))
        h = g.mix(h, g.math('MULTIPLY', k, .003), mask, 'FLOAT')
    if zone == 'gunmetal':
        # THE FOCUS SCALE engraved on the hoop face outside its turned groove: a tick every 10 degrees, a longer one
        # every 30 - the focusing ring of a lens, not a speaker grille (the old 24 full-length radial lines)
        on_face = g.math('MULTIPLY', g.smooth(.88, .97, s['facing_x']), g.smooth(39.0, 39.015, s['x']))
        t10 = g.math('DIVIDE', s['theta'], math.pi / 18.0)
        t30 = g.math('DIVIDE', s['theta'], math.pi / 6.0)
        d10 = g.math('MULTIPLY', g.frac_dist(t10), g.math('MULTIPLY', s['r'], math.pi / 18.0))
        d30 = g.math('MULTIPLY', g.frac_dist(t30), g.math('MULTIPLY', s['r'], math.pi / 6.0))
        minor = g.math('MULTIPLY', g.smooth(.013, .006, d10), g.band(2.825, 2.875, s['r'], .004))
        major = g.math('MULTIPLY', g.smooth(.016, .008, d30), g.band(2.812, 2.893, s['r'], .004))
        groove = g.math('MULTIPLY', g.math('MAXIMUM', minor, major), on_face)
        h = g.math('ADD', h, g.math('MULTIPLY', groove, -.0016))
    if zone == 'sheath':
        # braided sleeve: crossing helices along the conduit
        a = g.math('MULTIPLY', s['x'], 2 * math.pi * 16.0)
        c1 = g.math('SINE', g.math('ADD', a, g.math('MULTIPLY', s['z'], 44.0)))
        c2 = g.math('SINE', g.math('SUBTRACT', a, g.math('MULTIPLY', s['z'], 44.0)))
        h = g.math('MULTIPLY', g.math('MAXIMUM', c1, c2), .0035)
    if zone == 'crystal':
        h = g.value(0.0)    # polished facets: the flat faces themselves are the cut
    return h, groove


ZONE_DEF = {   # sRGB code values; gloss 0..1 over glossRange 0..12; e* = worn edge, d* = recess dirt
    'gunmetal': dict(d=(20, 20, 22), s=(118, 118, 122), g=.54, es=(198, 198, 200), eg=.76, dd=(14, 13, 12), dg=.30),
    'brass': dict(d=(30, 22, 8), s=(214, 170, 80), g=.68, es=(246, 218, 150), eg=.85, dd=(22, 18, 10), dg=.36),
    'lip': dict(d=(58, 42, 8), s=(176, 144, 62), g=.80, es=(176, 144, 62), eg=.80, dd=(40, 30, 10), dg=.5),
    'crystal': dict(d=(70, 46, 6), s=(122, 114, 92), g=.97, es=(122, 114, 92), eg=.97, dd=(70, 46, 6), dg=.97),
    'sheath': dict(d=(34, 32, 30), s=(52, 52, 52), g=.34, es=(58, 56, 54), eg=.42, dd=(22, 21, 20), dg=.24),
    'stripe': dict(d=(150, 112, 26), s=(60, 60, 60), g=.70, es=(60, 60, 60), eg=.70, dd=(120, 88, 22), dg=.6),
    'dark': dict(d=(14, 14, 15), s=(70, 70, 72), g=.36, es=(120, 120, 122), eg=.55, dd=(10, 10, 10), dg=.22),
}
METALS = ('gunmetal', 'brass')


def facet_hash(g, s):
    """0..1, constant over each flat facet and different between facets: a hash of the facet's TRUE normal (the
    staggered cut gives every triangle its own normal), so each cut catches its own amount of light."""
    k = g.node('ShaderNodeCombineXYZ')
    k.inputs[0].default_value, k.inputs[1].default_value, k.inputs[2].default_value = 12.9898, 78.233, 37.719
    dot = g.node('ShaderNodeVectorMath', operation='DOT_PRODUCT')
    g.link(s['true_normal'], dot.inputs[0]); g.link(k.outputs[0], dot.inputs[1])
    return g.math('FRACT', g.math('MULTIPLY', g.math('SINE', dot.outputs['Value']), 43758.5453))


def crystal_emission(g, s):
    """The cut crystal: each facet ring has its own level (the girdle darkest, rising to the table), each triangle facet
    swings +-35% on its own (facet_hash), the cut lines between facets are dark (the Bevel node finds every facet edge
    exactly), and the table's star is the beam exit - a small hot point, not a frosted dome. Core-yellow family only."""
    ring_x = s['x']
    crown = g.smooth(40.06, 40.10, ring_x)
    upper = g.smooth(40.40, 40.44, ring_x)
    bevel = g.smooth(40.83, 40.87, ring_x)
    level = g.mix(.30, .40, crown, 'FLOAT')
    level = g.mix(level, .46, upper, 'FLOAT')
    level = g.mix(level, .54, bevel, 'FLOAT')
    girdle = g.band(39.86, 40.06, ring_x, .01)
    level = g.mix(level, .24, girdle, 'FLOAT')
    level = g.math('MULTIPLY', level, g.math('ADD', .65, g.math('MULTIPLY', facet_hash(g, s), .70)))
    e = g.scale_rgb(g.mix(g.rgb(GOLD), g.rgb(CORE), g.smooth(39.9, 40.4, ring_x)), level)
    # the table star (x 40.99 .. apex 40.998): its facets keep their swing; only the very middle runs hot
    table = g.math('MULTIPLY', g.smooth(40.982, 40.989, ring_x), g.smooth(.53, .49, s['r']))
    hot = g.smooth(.22, .03, s['r'])
    e = g.mix(e, g.scale_rgb(g.rgb(HOT), .82), g.math('MULTIPLY', table, hot))
    seam = g.smooth(.004, .03, s['bevel_dev'])
    return g.scale_rgb(e, g.math('SUBTRACT', 1.0, g.math('MULTIPLY', seam, .55)))


def build(zone):
    name = 'WS zone | ' + zone
    old = bpy.data.materials.get(name)
    if old:
        bpy.data.materials.remove(old)
    mat = bpy.data.materials.new(name); mat.use_nodes = True; mat.use_fake_user = True
    mat['ws_zone'] = zone
    mat['preview_limit'] = 'Authoring/bake source; the shipped look is the baked emitter atlas (approximate preview).'
    g = G(mat); g.N.clear()
    s = geometry_signals(g)
    zd = ZONE_DEF[zone]
    var = noise(g, s['pos'], 7.0)
    breakup = noise(g, s['pos'], 18.0, 3.0)
    smudge = g.smooth(.56, .74, noise(g, s['pos'], 2.2, 3.0))
    turn = turning(g, s)
    h, groove = relief(g, s, zone, turn)
    if zone == 'crystal':
        wear = g.value(0.0); dirt = g.value(0.0); heat = g.value(0.0)
    else:
        wear = g.math('MULTIPLY', s['edge'], g.smooth(.36, .62, breakup))
        dirt = g.math('MULTIPLY', s['dirt'], g.math('ADD', .55, g.math('MULTIPLY', var, .45)))
        dirt = g.math('MAXIMUM', dirt, g.math('MULTIPLY', groove, .9))
        # heat staining where the beam is made: the hub face around the bore and the housing nose by the crystal
        hub = g.math('MULTIPLY', g.math('MULTIPLY', g.smooth(2.15, 1.60, s['r']), g.smooth(38.98, 39.02, s['x'])),
                     s['facing_x'])
        nose = g.math('MULTIPLY', g.smooth(39.70, 39.98, s['x']), g.smooth(1.30, 1.0, s['r']))
        heat = g.math('MULTIPLY', g.math('MAXIMUM', hub, nose), g.math('ADD', .75, g.math('MULTIPLY', var, .5)))
        if zone not in METALS:
            heat = g.value(0.0)
    # fine scratches on the metals (not down in the grime), the scratch density of the body next to them
    scr = scratches(g, s) if zone in METALS else g.value(0.0)
    scr = g.math('MULTIPLY', scr, g.math('SUBTRACT', 1.0, dirt))
    mid = noise(g, s['pos'], 26.0, 2.0)
    grain = g.math('SUBTRACT', noise(g, s['pos'], 45.0, 2.0), .5)       # pixel-scale tooth (metals)
    # diffuse
    d = g.mix(g.rgb(zd['d']), g.rgb(zd['dd']), g.math('MULTIPLY', dirt, .85))
    # specular F0: base * broad variation -> heat temper -> worn edge -> scratches -> recess loss
    sp = g.scale_rgb(g.rgb(zd['s']), g.math('ADD', .86, g.math('MULTIPLY', var, .28)))
    if zone in METALS:
        sp = g.scale_rgb(sp, g.math('ADD', 1.0, g.math('MULTIPLY', grain, .20)))
    sp = g.mix(sp, g.rgb(HEAT_TINT), g.math('MULTIPLY', heat, .45))
    sp = g.mix(sp, g.rgb(zd['es']), wear)
    sp = g.mix(sp, g.rgb(zd['es']), g.math('MULTIPLY', scr, .55))
    sp = g.scale_rgb(sp, g.math('SUBTRACT', 1.0, g.math('MULTIPLY', dirt, .45)))
    # gloss: base + broad and mid variation + machining sheen - handling smudges - scratches -> polished worn edge
    # -> dull recess (review pass 3: the emitter's gloss was a third as varied as the body's)
    gl = g.math('ADD', zd['g'], g.math('MULTIPLY', g.math('SUBTRACT', var, .5), .22 if zone in METALS else .14))
    if zone in METALS:
        gl = g.math('ADD', gl, g.math('MULTIPLY', g.math('SUBTRACT', mid, .5), .16))
        gl = g.math('ADD', gl, g.math('MULTIPLY', grain, .30))
        gl = g.math('ADD', gl, g.math('MULTIPLY', turn, .06))
        gl = g.math('SUBTRACT', gl, g.math('MULTIPLY', smudge, .13))
        gl = g.math('SUBTRACT', gl, g.math('MULTIPLY', heat, .06))
        gl = g.math('SUBTRACT', gl, g.math('MULTIPLY', scr, .16))
    gl = g.mix(gl, zd['eg'], wear, 'FLOAT')
    gl = g.mix(gl, zd['dg'], dirt, 'FLOAT')
    # emission (relative to EMISSION_SCALE), all in the core-yellow family
    if zone == 'lip':
        flow = g.math('ADD', .94, g.math('MULTIPLY', g.math('SINE', g.math('MULTIPLY', s['theta'], 2.0)), .06))
        e = g.scale_rgb(g.rgb(CORE), g.math('MULTIPLY', g.math('ADD', .34, g.math('MULTIPLY', s['edge'], .08)), flow))
        e = g.scale_rgb(e, g.math('ADD', .95, g.math('MULTIPLY', breakup, .10)))
    elif zone == 'crystal':
        e = crystal_emission(g, s)
    elif zone == 'stripe':
        # a dim running line with brighter windows every 0.9 in (review pass 3: a continuous line at full emitter
        # strength was the brightest mark in the ADS sight picture)
        window = g.smooth(.60, .82, g.math('ADD', .5, g.math('MULTIPLY', g.math('SINE', g.math('ADD', g.math(
            'MULTIPLY', s['x'], 2 * math.pi / .9), 1.3)), .5)))
        e = g.scale_rgb(g.rgb(CORE), g.math('ADD', .10, g.math('MULTIPLY', window, .14)))
    else:
        e = g.rgb((0, 0, 0))
    # bump on top of the bevelled normal: rounded machined edges + the relief
    bump = g.node('ShaderNodeBump'); bump.inputs['Strength'].default_value = 1.0; bump.inputs['Distance'].default_value = 1.0
    g.link(h, bump.inputs['Height'])
    if zone != 'crystal':
        g.link(s['bevel'], bump.inputs['Normal'])
    # outputs: one emission per bake channel + a BSDF for the normal bake + an approximate preview
    out = g.node('ShaderNodeOutputMaterial'); out.location = (1600, 0)
    ch = {}
    for key, sock in (('c', d), ('s', sp), ('g', gl), ('e', e)):
        em = g.node('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0; em.label = 'bake ' + key
        if key == 'g':
            comb = g.node('ShaderNodeCombineXYZ')
            clampg = g.math('MINIMUM', g.math('MAXIMUM', gl, 0.0), 1.0)
            for i in range(3):
                g.link(clampg, comb.inputs[i])
            g.link(comb.outputs[0], em.inputs['Color'])
        else:
            g.link(sock, em.inputs['Color'])
        ch[key] = em.outputs[0]
    nb = g.node('ShaderNodeBsdfDiffuse'); nb.label = 'bake n'
    g.link(bump.outputs['Normal'], nb.inputs['Normal']); ch['n'] = nb.outputs[0]
    # preview: diffuse + Fresnel-coloured GGX from the same channels, emission at the material's scaleRGB
    lw = g.node('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = .5; g.link(bump.outputs['Normal'], lw.inputs['Normal'])
    f5 = g.math('POWER', lw.outputs['Facing'], 5.0)
    fres = g.mix(sp, (1.0, 1.0, 1.0), f5)
    gstops = g.math('MULTIPLY', gl, 12.0)
    rough = g.math('POWER', g.math('DIVIDE', 2.0, g.math('ADD', g.math('POWER', 2.0, gstops), 2.0)), .25)
    dif = g.node('ShaderNodeBsdfDiffuse'); g.link(d, dif.inputs['Color']); g.link(bump.outputs['Normal'], dif.inputs['Normal'])
    glo = g.node('ShaderNodeBsdfAnisotropic'); g.link(fres, glo.inputs['Color']); g.link(rough, glo.inputs['Roughness'])
    g.link(bump.outputs['Normal'], glo.inputs['Normal'])
    em = g.node('ShaderNodeEmission'); g.link(e, em.inputs['Color']); em.inputs['Strength'].default_value = EMISSION_SCALE * materials.PREVIEW_EMIT
    a1 = g.node('ShaderNodeAddShader'); g.link(dif.outputs[0], a1.inputs[0]); g.link(glo.outputs[0], a1.inputs[1])
    a2 = g.node('ShaderNodeAddShader'); a2.label = 'preview'
    g.link(a1.outputs[0], a2.inputs[0]); g.link(em.outputs[0], a2.inputs[1])
    mat['ws_channels'] = 'c,s,g,e,n,preview'
    set_channel(mat, 'preview')
    return mat


def set_channel(mat, key):
    """Route one channel to the material output. Sockets are found by node label every time (safe after reloads)."""
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    for l in list(out.inputs['Surface'].links):
        nt.links.remove(l)
    want = 'preview' if key == 'preview' else 'bake ' + key
    node = next(n for n in nt.nodes if n.label == want)
    nt.links.new(node.outputs[0], out.inputs['Surface'])
