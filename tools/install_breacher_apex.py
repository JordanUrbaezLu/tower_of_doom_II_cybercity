"""install_breacher_apex.py - the BREACHER's Apex guns, rendered properly (docs/157).

User 2026-09-23: the Peacekeeper "was in" (map one's ZeRoY port) and its
textures "were kind of weak". Measured, not guessed:

  * The ZeRoY TIFFs ARE Apex's native textures. RSX 2.3.0 re-extracted
    peacekeeper_base_v / mozambique_base_v from the installed game on
    2026-09-23: same resolution (Peacekeeper 2048, Mozambique 1024), mean
    absolute difference 0.2..5.7 / 255. Apex has nothing sharper to give.
  * The weakness is the BO3 SETUP the donor pack shipped:
      - images allow picmip (noPicMip 0, doNotResize 0) and stream
        (streamable 1), so the view model can sit a whole mip down;
      - colour/normal filtering aniso2x, specular/gloss/AO "linear (mip
        nearest)";
      - gloss range 0..17 (tight, plasticky highlights);
      - the Peacekeeper's emission mask is wired at scaleRGB 1;
      - the Mozambique is plain lit_weapon.

So this applies Hellbound's ACCEPTED R-99 ID34 quality recipe
(tower_of_doom_II_hellbound/docs/R99_ID34_MATERIAL_QUALITY.md, user: "Looks
great") to PRIVATE copies: lit_emissive_advanced_fullspec, aniso8x
(mip linear) on colour/normal/specular/emission, gloss 0..13, emission HDR
scale 4, and every image resident at full size (noPicMip 1, doNotResize 1,
streamable 0) with its supported compression unchanged. No upscaling,
sharpening or recolouring - the pixels are Apex's.

NOTHING DONOR-SIDE IS WRITTEN. The ZeRoY GDT and model_export/apex are
read-only inputs (model_export/apex is a junction to the stock install).
The private xmodels point at the donor XMODEL_BINs and swap materials with
`skinOverride` - the lane this repo already ships (Chaos PaP, logical
powerups, the UDM). The Mozambique has no emission mask, so it binds a
private black one (model_export/tod_breacher_apex/black_ilm.png, written
here) - Hellbound found generic `$` images can drop the techset.

The PACKED Peacekeeper is Hellbound's mythic "Breach SWAT" (hb_am_peacekeeper,
already on this recipe) and needs nothing from here.

Run:   python tools/install_breacher_apex.py          (writes the GDT + png)
       python tools/install_breacher_apex.py --check  (verifies, writes nothing)
Then:  node tools/gen_tod_twins.js, and a FULL build (new materials/images).
"""
import hashlib
import json
import re
import struct
import sys
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = Path('C:/BO3Tools/TOD2Cybercity')
DONOR = TOOLS / 'source_data' / 'zeroy' / 'APEX_BO3.gdt'
OUT = REPO / 'source_data' / 'tod_breacher_apex.gdt'
BLACK_DIR = REPO / 'model_export' / 'tod_breacher_apex'
BLACK_PNG = BLACK_DIR / 'black_ilm.png'
BLACK_REF = 'model_export\\\\tod_breacher_apex\\\\black_ilm.png'
MANIFEST = REPO / 'docs' / 'breacher_evidence' / 'install_manifest.json'

# the R-99 ID34 recipe (Hellbound, accepted 2026-09-14)
FILTER = 'aniso8x (mip linear)'
GLOSS_MAX = '13'
EMISSION_SCALE = '4'
RESIDENT = {'noPicMip': '1', 'doNotResize': '1', 'streamable': '0'}

# role -> (donor image suffix, material slot, filter key)
SLOTS = [
    ('col', 'c', 'colorMap',       'filterColor'),
    ('nml', 'n', 'normalMap',      'filterNormal'),
    ('gls', 'g', 'cosinePowerMap', None),
    ('spc', 's', 'specColorMap',   'filterSpecular'),
    ('ao',  'o', 'occMap',         None),
    ('ilm', 'e', 'colorMap00',     'filterColor00'),
]

# private skin -> donor image stem, donor xmodels, and every material name the
# donor XMODEL_BINs carry (read out of the LZ4 payloads 2026-09-23).
SKINS = {
    'pk': {
        'images': 'i_apex_peacekeeper_skin32',
        'emission': True,
        'models': {'view': 'vm_apex_peacekeeper', 'world': 'npc_apex_peacekeeper'},
        'donor_mats': ['mtl_apex_peacekeeper', 'mtl_apex_peacekeeper_skin32',
                       'mtl_apex_peacekeeper_skin32_camo'],
    },
    'moz': {
        'images': 'i_apex_mozambique',
        'emission': False,
        'models': {'view': 'vm_apex_mozambique', 'world': 'npc_apex_mozambique'},
        'donor_mats': ['mtl_apex_mozambique', 'mtl_apex_mozambique_camo'],
    },
    'moz_pap': {   # Mozambique PaP = the white/black/red legendary 02 skin
        'images': 'i_apex_mozambique_legendary_02',
        'emission': False,
        'models': {'view': 'vm_apex_mozambique_legendary_02',
                   'world': 'npc_apex_mozambique_legendary_02'},
        'donor_mats': ['mtl_apex_mozambique_legendary_02',
                       'mtl_apex_mozambique_legendary_02_camo'],
    },
}
MATERIAL_TEMPLATE = 'mtl_apex_peacekeeper'   # the donor's own fullspec block


def block(text, name, gdf):
    decl = f'\t"{name}" ( "{gdf}" )'
    i = text.find(decl)
    if i < 0:
        raise SystemExit(f'donor block missing: {name} ({gdf})')
    j = text.find('\n\t}', i)
    return text[i:j + 3]


def setf(blk, fields):
    for k, v in fields.items():
        pat = re.compile(r'^(\t\t"' + re.escape(k) + r'" )"[^"\r\n]*"', re.M)
        if not pat.search(blk):
            raise SystemExit(f'template has no field {k}')
        blk = pat.sub(lambda m: m.group(1) + '"' + v + '"', blk, count=1)
    return blk


def rename(blk, old, gdf, new):
    return blk.replace(f'\t"{old}" ( "{gdf}" )', f'\t"{new}" ( "{gdf}" )', 1)


def black_png(size=64):
    raw = b''.join(b'\x00' + b'\x00\x00\x00\xff' * size for _ in range(size))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def build():
    donor = DONOR.read_text(encoding='utf-8', errors='replace').replace('\r\n', '\n')
    out, report = [], {}
    for skin, spec in SKINS.items():
        imgs = {}
        for role, suf, slot, _ in SLOTS:
            new = f'i_tod_bra_{skin}_{role}'
            if role == 'ilm' and not spec['emission']:
                tmpl = block(donor, 'i_apex_peacekeeper_skin32_e', 'image.gdf')
                blk = setf(rename(tmpl, 'i_apex_peacekeeper_skin32_e', 'image.gdf', new),
                           dict(RESIDENT, baseImage=BLACK_REF))
            else:
                src = f"{spec['images']}_{suf}"
                blk = setf(rename(block(donor, src, 'image.gdf'), src, 'image.gdf', new), RESIDENT)
            out.append(blk)
            imgs[role] = new
        mat = f'mtl_tod_bra_{skin}'
        fields = {slot: imgs[role] for role, _, slot, _ in SLOTS}
        fields.update({fk: FILTER for _, _, _, fk in SLOTS if fk})
        fields.update({'materialType': 'lit_emissive_advanced_fullspec',
                       'glossRangeMin': '0', 'glossRangeMax': GLOSS_MAX,
                       'scaleRGB': EMISSION_SCALE if spec['emission'] else '1.0',
                       'emissiveIncompetence': '1' if spec['emission'] else '0',
                       'camoMaskMap': ''})
        out.append(setf(rename(block(donor, MATERIAL_TEMPLATE, 'material.gdf'),
                               MATERIAL_TEMPLATE, 'material.gdf', mat), fields))
        override = ''.join(f'{d} {mat}\\r\\n' for d in spec['donor_mats'])
        models = {}
        for use, src in spec['models'].items():
            new = f'tod_bra_{skin}_{use}'
            out.append(setf(rename(block(donor, src, 'xmodel.gdf'), src, 'xmodel.gdf', new),
                            {'skinOverride': override}))
            models[use] = new
        report[skin] = {'material': mat, 'images': imgs, 'models': models,
                        'donor_images': spec['images'], 'donor_models': spec['models'],
                        'skinOverride': spec['donor_mats']}
    text = '{\n' + '\n'.join(out) + '\n}\n'
    if '//' in text.replace('://', ''):
        raise SystemExit('a // line would break gdtdb')
    return text, report


def main():
    text, report = build()
    png = black_png()
    if '--check' in sys.argv:
        ok = OUT.exists() and OUT.read_text(encoding='utf-8') == text and BLACK_PNG.exists() \
            and BLACK_PNG.read_bytes() == png
        print('install_breacher_apex --check', 'OK' if ok else 'STALE (re-run the installer)')
        sys.exit(0 if ok else 1)
    OUT.write_text(text, encoding='utf-8', newline='\n')
    BLACK_DIR.mkdir(parents=True, exist_ok=True)
    BLACK_PNG.write_bytes(png)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({
        'gdt': str(OUT.relative_to(REPO)), 'gdt_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'donor_gdt': str(DONOR), 'recipe': {'filter': FILTER, 'glossRangeMax': GLOSS_MAX,
                                            'emissionScale': EMISSION_SCALE, 'images': RESIDENT},
        'skins': report}, indent=1) + '\n', encoding='utf-8')
    n = text.count('.gdf" )')
    print(f'wrote {OUT.relative_to(REPO)}: {n} assets ({len(SKINS)} skins)')


if __name__ == '__main__':
    main()
