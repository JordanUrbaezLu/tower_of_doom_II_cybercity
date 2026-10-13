"""companion_maps/render_review.py - OLD vs NEW renders of the four companions under matched lighting (W2A, 2026-10-05).

RUN (background Blender 4.2 + PyCoD; CPU):
  "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe" --background --factory-startup
      --python tools/companion_maps/render_review.py -- --tree OLD=<root> --tree NEW=<root> --out <dir> [--only talon,...]
A <root> holds model_export/tod_partner/ (binaries + _images) and source_data/tod_partners.gdt - the repo, a base
snapshot, or a stage tree. Writes <out>/<label>_<companion>_<view>.png. The same camera, lights, exposure and shading
code render every tree, so the ONLY differences are the trees' maps and materials.

The shading is an explicitly APPROXIMATE reading of the GDT (in the spirit of tools/art_cohesion/native_preview.py):
diffuse albedo + a GGX lobe in the spec colour, gloss -> roughness by the native range, T7 normal maps (green
flipped to Blender's +V), occlusion on both lobes. The T7 micro-tile mixes show the layer TINTS blended by the reveal
mask (their tiling micro textures are left out on both sides). A map the GDT leaves empty renders as the engine's
neutral default (flat normal, white occlusion, full first layer, no emission). Decal overlays draw their colour x tint
blended by colour alpha x tint alpha x reveal (no reveal ramp / soft edge); a decal without a colour map draws nothing,
as on both sides. It is not BO3's BRDF, probes, exposure or tone map: the in-game look is the user's playtest.
"""
import bpy, os, re, sys, math, json, sqlite3, subprocess
from mathutils import Vector

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PRIV = r'C:\BO3Tools\TOD2Cybercity'
sys.path.insert(0, os.path.expanduser('~/AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel  # noqa: E402

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TREES = [a.split('=', 1) for i, a in enumerate(ARGS) if i > 0 and ARGS[i - 1] == '--tree']
OUT = os.path.abspath(ARGS[ARGS.index('--out') + 1])
ONLY = set(ARGS[ARGS.index('--only') + 1].split(',')) if '--only' in ARGS else None
RES = int(ARGS[ARGS.index('--res') + 1]) if '--res' in ARGS else 900
SAMPLES = int(ARGS[ARGS.index('--samples') + 1]) if '--samples' in ARGS else 96
EXPOSURE = float(ARGS[ARGS.index('--exposure') + 1]) if '--exposure' in ARGS else 0.8   # one value for every tree

# companion -> binary, front direction (unit vector the model faces), views
COMPANIONS = {
    'protector': ('tod_partner_protector', (1, 0, 0)),
    'talon': ('tod_partner_talon', (1, 0, 0)),
    'raps': ('tod_partner_raps', (1, 0, 0)),
    'cerberus': ('tod_partner_cerberus', (-1, 0, 0)),
}
BUILTIN = {'$white': 1.0, '$white_diffuse': 1.0, '$white_gloss': 1.0, '$white_specular': 1.0, '$white_ao': 1.0,
           '$occlusion': 1.0, '$white_reveal': 1.0, '$gray': 0.5, '$gray_32_one_channel': 0.5, '$spec_simple': 0.22,
           '$specular_mask': 0.5, '$black_color': 0.0, '$black_specular': 0.0, '$color_black_40': 0.04,
           '$identitynormalmap': None, '$normal': None}
DB = sqlite3.connect('file:' + os.path.join(PRIV, 'gdtdb', 'gdt.db').replace('\\', '/') + '?mode=ro', uri=True)
DB.execute('pragma writable_schema=ON')


def norm(p):
    return re.sub(r'[\\/]+', '/', p)


def gdt_blocks(path):
    t = open(path, encoding='utf-8').read()
    out = {}
    for m in re.finditer(r'\t"([^"]+)" \( "(material|image)\.gdf" \)\n\t\{\n(.*?)\n\t\}', t, re.S):
        out[(m.group(2), m.group(1))] = dict(re.findall(r'\t\t"([^"]*)" "(.*)"', m.group(3)))
    return out


def stock(kind, name):
    cur = DB.execute('select * from ' + kind + ' where _name=?', (name,))
    row = cur.fetchone()
    if not row:
        return None
    return {d[0]: v for d, v in zip(cur.description, row) if isinstance(v, str)}


class Tree:
    def __init__(self, label, root):
        self.label, self.root = label, os.path.abspath(root)
        self.blocks = gdt_blocks(os.path.join(root, 'source_data', 'tod_partners.gdt'))

    def material(self, name):
        return self.blocks.get(('material', name)) or stock('material', name) or {}

    def image(self, name):
        """-> a file path, a float constant, or None (flat / default)."""
        if not name:
            return 'EMPTY'
        if name.startswith('$'):
            return BUILTIN.get(name, 1.0)
        b = self.blocks.get(('image', name))
        if b:
            p = os.path.join(self.root, norm(b['baseImage']))
            return p if os.path.exists(p) else 'EMPTY'
        s = stock('image', name)
        if s and s.get('baseImage'):
            p = os.path.join(PRIV, norm(s['baseImage']))
            return p if os.path.exists(p) else 'EMPTY'
        return 'EMPTY'


def tint(f, key, default=(1, 1, 1)):
    try:
        v = [float(x) for x in f.get(key, '').split()[:3]]
        return tuple(v) if len(v) == 3 else default
    except ValueError:
        return default


def srgb_to_lin(c):
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


class Builder:
    def __init__(self, tree, name, fields):
        self.tree, self.f = tree, fields
        self.mat = bpy.data.materials.new(tree.label + ':' + name)
        self.mat.use_nodes = True
        self.nt = self.mat.node_tree
        self.nt.nodes.clear()
        self.N, self.L = self.nt.nodes, self.nt.links

    def tex(self, key, linear=True, alpha=False):
        src = self.tree.image(self.f.get(key, ''))
        if not isinstance(src, str) or src == 'EMPTY':
            return src
        im = bpy.data.images.load(src, check_existing=True)
        im.colorspace_settings.name = 'Non-Color' if linear else 'sRGB'
        n = self.N.new('ShaderNodeTexImage')
        n.image = im
        n.interpolation = 'Cubic' if not linear else 'Linear'
        return n.outputs['Alpha' if alpha else 'Color']

    def val(self, socket_or_const, default):
        if socket_or_const is None or socket_or_const == 'EMPTY':
            return default
        return socket_or_const

    def scalar(self, s):
        if isinstance(s, (int, float)):
            return s
        n = self.N.new('ShaderNodeRGBToBW')
        self.L.new(s, n.inputs[0])
        return n.outputs[0]

    def math(self, op, a, b=None):
        n = self.N.new('ShaderNodeMath')
        n.operation = op
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                self.L.new(x, n.inputs[i])
        return n.outputs[0]

    def rgb_mul(self, a, b):
        n = self.N.new('ShaderNodeMix')
        n.data_type = 'RGBA'
        n.blend_type = 'MULTIPLY'
        n.inputs['Factor'].default_value = 1.0
        for sock, x in ((n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(x, tuple):
                sock.default_value = (*x, 1.0)
            elif isinstance(x, (int, float)):
                sock.default_value = (x, x, x, 1.0)
            else:
                self.L.new(x, sock)
        return n.outputs[2]

    def rgb_mix(self, fac, a, b):
        n = self.N.new('ShaderNodeMix')
        n.data_type = 'RGBA'
        for sock, x in ((n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(x, tuple):
                sock.default_value = (*x, 1.0)
            else:
                self.L.new(x, sock)
        if isinstance(fac, (int, float)):
            n.inputs['Factor'].default_value = fac
        else:
            self.L.new(fac, n.inputs['Factor'])
        return n.outputs[2]

    def normal(self):
        s = self.tex('normalMap')
        if not hasattr(s, 'node'):
            return None
        sep = self.N.new('ShaderNodeSeparateColor')
        self.L.new(s, sep.inputs[0])
        comb = self.N.new('ShaderNodeCombineColor')
        self.L.new(sep.outputs[0], comb.inputs[0])
        self.L.new(self.math('SUBTRACT', 1.0, sep.outputs[1]), comb.inputs[1])   # T7 green -> Blender +V
        self.L.new(sep.outputs[2], comb.inputs[2])
        nm = self.N.new('ShaderNodeNormalMap')
        self.L.new(comb.outputs[0], nm.inputs['Color'])
        return nm.outputs[0]

    def finish(self, albedo, spec, gloss01, occ, emit=None):
        gmin, gmax = float(self.f.get('glossRangeMin', 0) or 0), float(self.f.get('glossRangeMax', 17) or 17)
        if isinstance(gloss01, (int, float)):
            absolute = gmin + gloss01 * (gmax - gmin)
            rough = (2.0 / (2 ** absolute + 2)) ** 0.25
        else:
            absolute = self.math('ADD', self.math('MULTIPLY', gloss01, gmax - gmin), gmin)
            rough = self.math('POWER', self.math('DIVIDE', 2.0, self.math('ADD', self.math('POWER', 2.0, absolute), 2.0)), 0.25)
        if occ is not None and occ != 1.0:
            albedo = self.rgb_mul(albedo, occ)
            spec = self.rgb_mul(spec, occ)
        nrm = self.normal()
        dif = self.N.new('ShaderNodeBsdfDiffuse')
        glo = self.N.new('ShaderNodeBsdfAnisotropic')
        glo.distribution = 'GGX'
        for node, col in ((dif, albedo), (glo, spec)):
            if isinstance(col, tuple):
                node.inputs['Color'].default_value = (*col, 1)
            elif isinstance(col, (int, float)):
                node.inputs['Color'].default_value = (col, col, col, 1)
            else:
                self.L.new(col, node.inputs['Color'])
            if nrm is not None:
                self.L.new(nrm, node.inputs['Normal'])
        if isinstance(rough, (int, float)):
            glo.inputs['Roughness'].default_value = rough
        else:
            self.L.new(rough, glo.inputs['Roughness'])
        add = self.N.new('ShaderNodeAddShader')
        self.L.new(dif.outputs[0], add.inputs[0])
        self.L.new(glo.outputs[0], add.inputs[1])
        out_sh = add.outputs[0]
        if emit is not None:
            em = self.N.new('ShaderNodeEmission')
            if isinstance(emit, tuple):
                em.inputs['Color'].default_value = (*emit, 1)
            else:
                self.L.new(emit, em.inputs['Color'])
            em.inputs['Strength'].default_value = 3.0
            a2 = self.N.new('ShaderNodeAddShader')
            self.L.new(out_sh, a2.inputs[0])
            self.L.new(em.outputs[0], a2.inputs[1])
            out_sh = a2.outputs[0]
        out = self.N.new('ShaderNodeOutputMaterial')
        self.L.new(out_sh, out.inputs[0])
        return self.mat


def is_decal(original):
    return 'decal' in original


def build_decal(tree, name, original):
    """A decal overlay: its colour x tint, blended by colour alpha x tint alpha x reveal (sampled at revealScale).
    Approximate like everything here (no alphaReveal ramp / soft edge, no layer sort); None = draw nothing."""
    f = tree.material(name)
    b = Builder(tree, name, f)
    col = b.tex('colorMap', linear=False)
    if not hasattr(col, 'node'):
        return None
    alpha = col.node.outputs['Alpha']
    tc = tint(f, 'colorTint')
    try:
        ta = float(f.get('colorTint', '1 1 1 1').split()[3])
    except (IndexError, ValueError):
        ta = 1.0
    fac = b.math('MULTIPLY', alpha, ta)
    rv = b.tex('alphaRevealMap')
    if hasattr(rv, 'node'):
        uvn = b.N.new('ShaderNodeTexCoord')
        mp = b.N.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (float(f.get('revealScaleX', 1) or 1), float(f.get('revealScaleY', 1) or 1), 1)
        b.L.new(uvn.outputs['UV'], mp.inputs['Vector'])
        b.L.new(mp.outputs['Vector'], rv.node.inputs['Vector'])
        fac = b.math('MULTIPLY', fac, b.scalar(rv))
    g = b.tex('cosinePowerMap')
    gloss = g if isinstance(g, float) else (0.4 if g in (None, 'EMPTY') else b.scalar(g))
    b.finish(b.rgb_mul(col, srgb_to_lin(tc)), (0.05, 0.05, 0.05), gloss, 1.0)
    out = [n for n in b.N if n.type == 'OUTPUT_MATERIAL'][0]
    shaded = out.inputs[0].links[0].from_socket
    tr = b.N.new('ShaderNodeBsdfTransparent')
    mix = b.N.new('ShaderNodeMixShader')
    b.L.new(fac, mix.inputs['Fac'])
    b.L.new(tr.outputs[0], mix.inputs[1])
    b.L.new(shaded, mix.inputs[2])
    b.L.new(mix.outputs[0], out.inputs[0])
    return b.mat


def build_material(tree, name, original):
    if is_decal(original):
        return build_decal(tree, name, original)
    f = tree.material(name)
    b = Builder(tree, name, f)
    mt = f.get('materialType', 'lit')
    occ = b.tex('occMap')
    occ = 1.0 if occ in (None, 'EMPTY') else (b.scalar(occ) if not isinstance(occ, float) else occ)
    if 'micro_tile' in mt:
        t0 = srgb_to_lin(tint(f, 'colorTint', (0.3, 0.3, 0.3)))
        t1 = srgb_to_lin(tint(f, 'colorTint1', t0))
        rv = b.tex('alphaRevealMap')
        if rv in (None, 'EMPTY') or isinstance(rv, float):
            albedo = t0
        else:
            albedo = b.rgb_mix(b.scalar(rv), t1, t0)       # white = the first (paint) layer; black = the second
        bare = any(k in original for k in ('bare_metal', 'chrome', 'titanium'))
        spec = (0.5, 0.5, 0.52) if bare else (0.07, 0.07, 0.07)
        if bare:
            albedo = (0.03, 0.03, 0.03)
        gloss = 0.55 if bare else 0.35
        return b.finish(albedo, spec, gloss, occ)
    # lit / lit_plus / lit_advanced(_fullspec) / lit_emissive*
    c = b.tex('colorMap', linear=False)
    if isinstance(c, float):
        albedo = (c, c, c)
    elif c in (None, 'EMPTY'):
        albedo = (0.5, 0.5, 0.5)
    else:
        albedo = c
    albedo = b.rgb_mul(albedo, srgb_to_lin(tint(f, 'colorTint')))
    sp = b.tex('specColorMap', linear=False)
    spec = (sp, sp, sp) if isinstance(sp, float) else ((0.25, 0.25, 0.25) if sp in (None, 'EMPTY') else sp)
    spec = b.rgb_mul(spec, srgb_to_lin(tint(f, 'specColorTint', (0.76, 0.76, 0.76))))
    g = b.tex('cosinePowerMap')
    gloss = g if isinstance(g, float) else (0.5 if g in (None, 'EMPTY') else b.scalar(g))
    emit = None
    if 'emissive' in mt:
        e = b.tex('colorMap00', linear=False)
        if not isinstance(e, float) and e not in (None, 'EMPTY'):
            emit = b.rgb_mul(e, srgb_to_lin(tint(f, 'colorTint')))
    return b.finish(albedo, spec, gloss, occ, emit)


def load(tree, binary):
    path = os.path.join(tree.root, 'model_export', 'tod_partner', binary + '.xmodel_bin')
    mdl = xmodel.Model()
    mdl.LoadFile_Bin(path, split_meshes=False)
    src = mdl.meshes[0]
    man = json.load(open(os.path.join(tree.root, 'model_export', 'tod_partner', 'manifest.json')))
    orig = {}
    for log in man.get('materials', {}).values():
        for e in log:
            if e.get('material'):
                orig[e['material']] = e['original']
    names = [m.name for m in mdl.materials]
    built = {}
    for mid in sorted({f.material_id for f in src.faces}):
        built[mid] = build_material(tree, names[mid], orig.get(names[mid], names[mid]))
    keep = [f for f in src.faces if built[f.material_id] is not None]
    decal = {mid for mid in built if is_decal(orig.get(names[mid], names[mid]))}
    body = make_object(binary, src, [f for f in keep if f.material_id not in decal], built, 0.0)
    if any(f.material_id in decal for f in keep):
        # Decal shells sit ON the hull (the engine draws them with a depth bias). Coplanar in Cycles, a ray that passes
        # a transparent texel skips the hull under it and shows the model's interior: lift the shell a hair instead.
        make_object(binary + '_decals', src, [f for f in keep if f.material_id in decal], built, DECAL_LIFT)
    return body


DECAL_LIFT = 0.02     # model units (the companions are 30-60 units across)


def make_object(label, src, faces, built, lift):
    """One mesh object of these faces. lift > 0: every corner gets its own vertex, moved along its normal."""
    me = bpy.data.meshes.new(label)
    if lift:
        verts = [tuple(src.verts[c.vertex].offset[k] + lift * c.normal[k] for k in range(3))
                 for f in faces for c in (f.indices[0], f.indices[2], f.indices[1])]
        me.from_pydata(verts, [], [[3 * i, 3 * i + 1, 3 * i + 2] for i in range(len(faces))])
    else:
        me.from_pydata([tuple(v.offset) for v in src.verts], [], [[f.indices[i].vertex for i in (0, 2, 1)] for f in faces])
    me.update()
    uv = me.uv_layers.new(name='uv')
    normals = []
    used = sorted({f.material_id for f in faces})
    slot = {m: i for i, m in enumerate(used)}
    for poly, f in zip(me.polygons, faces):
        poly.material_index = slot[f.material_id]
        poly.use_smooth = True
        for li, fi in zip(poly.loop_indices, (0, 2, 1)):
            u, v = f.indices[fi].uv
            uv.data[li].uv = (u, 1 - v)
            normals.append(tuple(f.indices[fi].normal))
    me.normals_split_custom_set(normals)
    for m in used:
        me.materials.append(built[m])
    ob = bpy.data.objects.new(label, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = SAMPLES
    sc.cycles.seed = 3
    sc.cycles.use_denoising = True
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = 6
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = EXPOSURE
    w = bpy.data.worlds.new('w')
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.045, 0.05, 0.06, 1)
    bg.inputs['Strength'].default_value = 1.0
    sc.world = w
    return sc


def lights_and_camera(ob, front):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector([min(v[i] for v in bb) for i in range(3)])
    hi = Vector([max(v[i] for v in bb) for i in range(3)])
    ctr = (lo + hi) / 2
    size = max(hi - lo)
    fr = Vector(front).normalized()
    side = fr.cross(Vector((0, 0, 1))).normalized()
    views = {}
    # three-quarter: 35 degrees off the front, a little above
    d34 = (fr * math.cos(math.radians(35)) + side * math.sin(math.radians(35))).normalized() + Vector((0, 0, 0.42))
    views['34'] = (ctr + d34.normalized() * size * 2.6, ctr, size * 0.62)
    # the close study: the same side, nearer, aimed at the upper third (the shell / hull top where the maps show)
    tgt = ctr + Vector((0, 0, (hi.z - lo.z) * 0.18))
    views['close'] = (tgt + d34.normalized() * size * 1.15, tgt, size * 0.28)

    def light(kind, loc, energy, size_, color=(1, 1, 1)):
        ld = bpy.data.lights.new(kind, 'AREA')
        ld.energy = energy * size * size / 900.0
        ld.size = size_ * size
        ld.color = color
        lo_ = bpy.data.objects.new(kind, ld)
        lo_.location = loc
        lo_.rotation_euler = (ctr - loc).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.scene.collection.objects.link(lo_)
    light('key', ctr + (fr * 1.4 + side * 1.6 + Vector((0, 0, 1.8))) * size, 2600, 0.6, (1.0, 0.97, 0.92))
    light('fill', ctr + (fr * 1.6 - side * 1.8 + Vector((0, 0, 0.5))) * size, 700, 1.0, (0.85, 0.9, 1.0))
    light('rim', ctr + (-fr * 2.0 + side * 0.4 + Vector((0, 0, 1.2))) * size, 1800, 0.5, (0.95, 0.95, 1.0))
    return views


def render(label, comp, views, ob):
    sc = bpy.context.scene
    cam_d = bpy.data.cameras.new('cam')
    cam = bpy.data.objects.new('cam', cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    for v, (loc, tgt, ortho) in views.items():
        cam_d.type = 'PERSP'
        cam_d.lens = 85
        cam.location = loc
        cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
        dist = (tgt - loc).length
        cam_d.lens = 36.0 * dist / (ortho * 2.0)
        sc.render.filepath = os.path.join(OUT, '%s_%s_%s.png' % (label, comp, v))
        bpy.ops.render.render(write_still=True)


def main():
    out = subprocess.run(['tasklist'], capture_output=True, text=True).stdout.lower()
    for n in ('blackops3.exe', 'radiant_modtools.exe', 'cod2map64.exe', 'linker_modtools.exe', 'gdtdb.exe'):
        if n in out:
            raise SystemExit('render_review: %s is running - wait (16 GB machine)' % n)
    os.makedirs(OUT, exist_ok=True)
    for comp, (binary, front) in COMPANIONS.items():
        if ONLY and comp not in ONLY:
            continue
        for label, root in TREES:
            scene()
            ob = load(Tree(label, root), binary)
            views = lights_and_camera(ob, front)
            render(label, comp, views, ob)
            print('render_review:', label, comp)


main()
