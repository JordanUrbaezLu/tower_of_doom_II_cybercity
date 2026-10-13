"""THE LIT SIGN CARD (docs/196 s6, 2026-09-30) - GENERATED, never hand-edit the outputs.

  python tools/jump_title/make_sign_card.py           write the card model, its texture, its GDT and the receipt
  python tools/jump_title/make_sign_card.py --check   FAIL if any output differs from a fresh generation

User: "the thing i really want is the sign to not glow and actually be very dull and then after explosion it should
glow very bright". The sky bakes the title gate DULL (build_city.py --sign-state dull); the LIT sign is this CARD: a
two-triangle quad wearing a Blender-derived bake of the approved painting (art/sky3d/sign/v12_native_lit.png).
The original painting and pixel geometry remain pinned by cyber_hero_title.py. The derived image retains the
shared graphite-frame finish and the sky city's foreground visibility, as an HDR emissive, alpha-blended
material. The flyer's client (_tod_jump_title.csc) spawns it hidden on the sign's bearing SIGN_DIST out, facing back
along it, moves it with the camera every frame, and shows it at THE REVEAL with a neon flicker; it stays for the match.

THE GEOMETRY IS THE SKY'S: the sky's card is GATE w_deg wide (65) at D (1000 m) perpendicular to the bearing at
box_el (11), REFERENCE_WIDTH (1536 px) across, the DOOM II centre (TITLE_CENTER_PX) on the bearing. Similar
triangles put the same picture on a card 2 x SIGN_DIST x tan(w_deg / 2) wide at SIGN_DIST on the same bearing, so
it lands exactly over the dull bake at any camera position (both are 'at infinity' from the rider's point of view).
Local frame (the host's: forward +X toward the camera, +Y = the sign's right, +Z = up): the quad lies in X = 0,
Y from -half to +half, Z from +top (the painting's row 0) down to -bottom (its last row), UV (0,0) at the top-left.
Wound clockwise seen from +X (BO3's front face, the fleet exporter's convention), normal +X.

THE MATERIAL: lit_emissive_transparent (the inducer's glass recipe): colorMap = the derived painting (its alpha = the
card's visibility, including foreground/ground holdouts), colorTint black (no lit diffuse: the card is its own light),
colorMap00 (the emissive map) = that same derived image, scaleRGB = SIGN_LIT_SCALE (the HDR level: the sky's own W is ~3.4
units at skyStops 4.35 x sky_intensity_factor 10, so 16 puts the tube cores ~5 W-equivalent - 'very bright' - and
the metal ~0.5 W, lit by its neon; ONE knob if the user wants it hotter or cooler), no specular, no probe.
The image: compressed high color (BC7 + alpha), 1536 x 1024 (multiples of 4), sRGB.
"""
import hashlib, json, math, os, pathlib, re, shutil, struct, sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path(os.environ.get('TOD_REPO') or HERE.parents[1])
sys.path.insert(0, str(HERE))
import gen_fx  # noqa: E402  (SIGN_DIST, gate_geometry, the title contract)

PYCOD = pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'
sys.path.insert(0, str(PYCOD))
from PyCoD import xmodel  # noqa: E402

TITLE_ART = REPO / 'tools/sky3d/cyber_hero_title.py'
SOURCE_PNG = REPO / 'art/sky3d/sign/v12_dealer.png'
NATIVE_PNG = REPO / 'art/sky3d/sign/v12_native_lit.png'
NATIVE_ART_RECEIPT = REPO / 'art/sky3d/dealer_review/native_card_art.json'
EXP = REPO / 'model_export/tod_jump_title'
TEX = EXP / '_images'
GDT = REPO / 'source_data/tod_jump_title.gdt'
RECEIPT = REPO / 'art/jump_title/sign_card.json'
MODEL = 'tod_jt_sign_lit'          # LOCKSTEP: _tod_jump_title.csc TOD_JT_SIGN_MODEL, zone_source xmodel line
MATERIAL = 'mtl_tod_jt_sign_lit'
IMAGE = 'i_tod_jt_sign_lit'
SIGN_LIT_SCALE = 16                # scaleRGB: the lit card's HDR level (the docstring); the one brightness knob


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def title_literals():
    """the card's pixel contract from cyber_hero_title.py (literal assignments only, like gen_fx.title_contract)."""
    import ast
    names = {'REFERENCE_WIDTH', 'IMAGE_SIZE', 'TITLE_CENTER_PX', 'SOURCE_IMAGE', 'SOURCE_SHA256'}
    values = {}
    for node in ast.parse(TITLE_ART.read_text(encoding='utf-8'), filename=str(TITLE_ART)).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    values[target.id] = ast.literal_eval(node.value)
    assert set(values) == names, 'cyber_hero_title.py: missing literal card contract'
    return values


def png_size(path):
    b = pathlib.Path(path).read_bytes()
    assert b[:8] == b'\x89PNG\r\n\x1a\n' and b[12:16] == b'IHDR', 'not a PNG: ' + str(path)
    w, h = struct.unpack('>II', b[16:24])
    assert b[25] == 6, 'the painting must be RGBA (colour type 6), got colour type %d' % b[25]
    return w, h


def geometry():
    """-> the card's numbers at SIGN_DIST (units), from the live sources."""
    t = title_literals()
    assert (REPO / t['SOURCE_IMAGE']).resolve() == SOURCE_PNG.resolve(), 'the title contract names a different painting'
    assert sha(SOURCE_PNG) == t['SOURCE_SHA256'], 'v12_dealer.png changed: remeasure the title contract first'
    w_px, h_px = png_size(SOURCE_PNG)
    assert (w_px, h_px) == tuple(t['IMAGE_SIZE']), 'painting size differs from the contract'
    assert w_px % 4 == 0 and h_px % 4 == 0, 'a compressed image must be a multiple of 4 in both dimensions'
    src = gen_fx.BUILD_CITY.read_text(encoding='utf-8')
    m = re.search(r'(?s)^GATE = dict\((.*?)\n\s*sat=', src, re.M)
    w_deg = float(re.search(r'\bw_deg=([\d.]+)', m.group(1)).group(1))
    d = float(re.search(r'\bD=([\d.]+)', m.group(1)).group(1))
    box_el = float(re.search(r'\bbox_el=([\d.]+)', m.group(1)).group(1))
    ref_w = float(t['REFERENCE_WIDTH'])
    cx, cy = t['TITLE_CENTER_PX']
    width = 2.0 * gen_fx.SIGN_DIST * math.tan(math.radians(w_deg / 2.0))
    s = width / ref_w                                          # units per painting pixel at SIGN_DIST
    return dict(model=MODEL, material=MATERIAL, image=IMAGE, sign_dist=gen_fx.SIGN_DIST, w_deg=w_deg, sky_card_d_m=d,
                box_el=box_el, reference_width_px=ref_w, image_px=[w_px, h_px], title_center_px=[cx, cy],
                units_per_px=s, width=width, height=h_px * s,
                left=-cx * s, right=(w_px - cx) * s, top=cy * s, bottom=-(h_px - cy) * s,
                scale_rgb=SIGN_LIT_SCALE, source_sha256=t['SOURCE_SHA256'])


def native_art(g):
    """Require the reviewed Blender finish/visibility bake for this exact sky.

    This validates provenance, not native appearance. The immutable painting
    still owns all geometry; the derived image supplies only colour/alpha.
    """
    import importlib.util
    config_path = REPO / 'tools/sky_dealer/pass_config.py'
    spec = importlib.util.spec_from_file_location('_tod_native_card_config', config_path)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    r = json.loads(NATIVE_ART_RECEIPT.read_text(encoding='utf-8'))
    assert r.get('schema') == 1, 'unknown native card art receipt schema'
    assert r.get('source_png') == SOURCE_PNG.relative_to(REPO).as_posix(), 'native card uses different source art'
    assert r.get('source_png_sha256') == g['source_sha256'] == sha(SOURCE_PNG), 'native card source painting drift'
    assert r.get('sky_source_hashes') == config.source_hashes(), 'native card sky sources changed; rebake through Blender MCP'
    helpers = {'authoring_script_sha256': 'tools/sky_dealer/bake_native_card.py',
               'renderer_sha256': 'tools/sky_dealer/render_native_card.py'}
    for key, path in helpers.items():
        assert r.get(key) == sha(REPO / path), 'native card helper changed: ' + path
    author = json.loads((config.STAGE / 'author.json').read_text(encoding='utf-8'))
    assert r.get('sky_master_sha256') == author['blend_sha256'], 'native card was authored from a different sky master'
    assert sha(pathlib.Path(author['blend'])) == author['blend_sha256'], 'native card sky master changed'
    assert sha(REPO / r['blend']) == r['blend_sha256'], 'native card bake scene changed'
    assert r.get('generated_asset') == NATIVE_PNG.relative_to(REPO).as_posix(), 'native card permanent asset path differs'
    assert r.get('output') == 'tmp/sky_dealer/native_card_finished.png', 'native card render output path differs'
    image_sha = sha(NATIVE_PNG)
    assert image_sha == r.get('generated_asset_sha256') == r.get('output_sha256'), 'native card permanent/render hashes differ'
    assert sha(REPO / r['output']) == image_sha, 'native card rendered pixels changed'
    assert png_size(NATIVE_PNG) == png_size(REPO / r['output']) == tuple(g['image_px']), 'native card image size changed'
    assert r.get('colour_encoding') == 'Blender Standard / sRGB, RGBA8, straight alpha PNG', 'native card colour/alpha encoding changed'
    assert r.get('occlusion') == 'true scene-depth holdout from the same panorama eye', 'native card lacks scene-depth visibility'
    assert {'ground', 'city_cyber_armour', 'city_cyber_decks', 'city_struct'} <= set(r.get('occluders', [])), 'native card lacks foreground holdouts'
    camera = r['camera']
    assert camera['horizontal_fov'] == g['w_deg'], 'native card horizontal field of view changed'
    shift_y = (g['title_center_px'][1] - g['image_px'][1] / 2) / g['reference_width_px']
    assert math.isfinite(camera['shift_y']) and abs(camera['shift_y'] - shift_y) < 1e-7, 'native card optical-center shift changed'
    w, h = g['image_px']
    anchors = [[0, 0], [w, 0], [w, h], [0, h], g['title_center_px']]
    proofs = camera.get('pixel_contract', [])
    assert len(proofs) == len(anchors), 'native card needs all four corners and the title-anchor proof'
    for proof, expected in zip(proofs, anchors):
        assert proof['source'] == expected, 'native card pixel-contract anchor differs'
        observed = proof['projected']
        assert len(observed) == 2 and all(math.isfinite(v) for v in observed), 'invalid native card projection'
        assert max(abs(a - b) for a, b in zip(observed, expected)) < 0.002, 'native card no longer aligns with the sky'
    return dict(derived_art_receipt=NATIVE_ART_RECEIPT.relative_to(REPO).as_posix(),
                derived_art_receipt_sha256=sha(NATIVE_ART_RECEIPT),
                native_image_source=NATIVE_PNG.relative_to(REPO).as_posix(), native_image_sha256=image_sha)


def build_model(g):
    """the quad as a PyCoD model: one bone, one material, two triangles wound for BO3's front face (+X)."""
    mod = xmodel.Model(MODEL)
    bone = xmodel.Bone('tag_origin')
    bone.offset = (0, 0, 0)
    bone.matrix = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    mod.bones = [bone]
    mod.materials.append(xmodel.Material(MATERIAL, 'Phong', {}))
    mesh = xmodel.Mesh('sign_card')
    # corners: top-left, top-right, bottom-right, bottom-left (in the camera's view; +Y = its right, +Z = up)
    corners = [(0.0, g['left'], g['top']), (0.0, g['right'], g['top']), (0.0, g['right'], g['bottom']), (0.0, g['left'], g['bottom'])]
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    mesh.verts = [xmodel.Vertex(c, [(0, 1.0)]) for c in corners]
    # Seen from +X (the camera), with +Y to the right and +Z up, top-left -> top-right -> bottom-right runs CLOCKWISE:
    # that is BO3's front face (tools/sky_ships/06_export.py emits Blender's CCW loops as (0, 2, 1) = CW).
    for tri in ((0, 1, 2), (0, 2, 3)):
        f = xmodel.Face(0, 0)
        f.indices = [xmodel.FaceVertex(i, (1.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0), uvs[i]) for i in tri]
        mesh.faces.append(f)
    mod.meshes.append(mesh)
    return mod, corners


def gdt_text(g):
    def block(name, kind, fields):
        return '\t"' + name + '" ( "' + kind + '.gdf" )\n\t{\n' + ''.join('\t\t"' + k + '" "' + str(v) + '"\n' for k, v in fields.items()) + '\t}\n'
    # The camera-following card has a fixed angular size. Its measured 1536x1024
    # source is intentionally NPOT; BO3 rejects automatic mipmaps for this size.
    image = dict(baseImage='model_export/tod_jump_title/_images/' + IMAGE + '.png', imageType='Texture', type='image',
                 semantic='diffuseMap', coreSemantic='sRGB3chAlpha', streamable=1, compressionMethod='compressed high color',
                 noMipMaps=1, noPicMip=1)
    material = dict(surfaceType='metal', template='material.template', materialCategory='Geometry',
                    materialType='lit_emissive_transparent', colorMap=IMAGE, colorTint='0 0 0 1', normalMap='$identitynormalmap',
                    colorMap00=IMAGE, colorTint1='1 1 1 1', scaleRGB=SIGN_LIT_SCALE, emissiveIncompetence=1, emissiveFalloff=0,
                    glossRangeMin=0, glossRangeMax=8, specAmount=0, reflectionProbeAmount=0,
                    textureAtlasRowCount=1, textureAtlasColumnCount=1, usage='<not in editor>')
    model = dict(filename='tod_jump_title/' + MODEL + '.xmodel_bin', type='rigid', scale=1, CollisionMap='',
                 BulletCollisionLOD='None', physicsPreset='', cullOutDiameter=0, noCastShadow=1, materials='')
    # BO3 gdtdb rejects leading // comments as an unnamed entity. Keep generator
    # metadata in this source and the JSON receipt; the GDT starts with its brace.
    return '{\n' + block(IMAGE, 'image', image) + block(MATERIAL, 'material', material) + block(MODEL, 'xmodel', model) + '}\n'


def generate(out_exp, out_gdt):
    g = geometry()
    art = native_art(g)
    mod, corners = build_model(g)
    (out_exp / '_images').mkdir(parents=True, exist_ok=True)
    png = out_exp / '_images' / (IMAGE + '.png')
    shutil.copyfile(NATIVE_PNG, png)
    path = out_exp / (MODEL + '.xmodel_bin')
    mod.WriteFile_Bin(str(path), version=7)
    out_gdt.parent.mkdir(parents=True, exist_ok=True)
    out_gdt.write_text(gdt_text(g), encoding='utf-8', newline='\n')
    receipt = dict(g, **art, corners_local=[list(c) for c in corners], files={
        'model': path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else str(path),
        'image': png.relative_to(REPO).as_posix() if png.is_relative_to(REPO) else str(png),
        'gdt': out_gdt.relative_to(REPO).as_posix() if out_gdt.is_relative_to(REPO) else str(out_gdt)},
        sha256=dict(model=sha(path), image=sha(png), gdt=sha(out_gdt)),
        zone_line='xmodel,' + MODEL, native_verified=False,
        notes='Dealer crest painting with unchanged GATE geometry; Blender-derived graphite finish and foreground visibility alpha; native appearance awaits the user.')
    return receipt


def main():
    if '--check' in sys.argv:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            fresh = generate(td / 'exp', td / 'card.gdt')
        bad = []
        for key, rel in (('model', EXP / (MODEL + '.xmodel_bin')), ('image', TEX / (IMAGE + '.png')), ('gdt', GDT)):
            if not rel.exists():
                bad.append(key + ' missing: ' + str(rel))
            elif sha(rel) != fresh['sha256'][key]:
                bad.append(key + ' stale: ' + str(rel))
        if not RECEIPT.exists():
            bad.append('receipt missing: ' + str(RECEIPT))
        else:
            r = json.loads(RECEIPT.read_text(encoding='utf-8'))
            for k in ('sign_dist', 'width', 'height', 'left', 'right', 'top', 'bottom', 'scale_rgb', 'source_sha256', 'sha256',
                      'derived_art_receipt', 'derived_art_receipt_sha256', 'native_image_source', 'native_image_sha256'):
                if r.get(k) != fresh.get(k):
                    bad.append('receipt field %s differs (%r vs fresh %r)' % (k, r.get(k), fresh.get(k)))
        if bad:
            print('SIGN CARD STALE:\n  ' + '\n  '.join(bad) + '\n  run: python tools/jump_title/make_sign_card.py')
            sys.exit(1)
        print('SIGN CARD OK %s at %d u: %.0f x %.0f u, scaleRGB %s' % (MODEL, fresh['sign_dist'], fresh['width'], fresh['height'], fresh['scale_rgb']))
        return
    receipt = generate(EXP, GDT)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('SIGN CARD WRITTEN', json.dumps({k: receipt[k] for k in ('model', 'sign_dist', 'width', 'height', 'top', 'bottom', 'scale_rgb')}))


if __name__ == '__main__':
    main()
