"""Install the converted BO6 Rampage Inducer as a BO3 static prop, idempotently.

Pairs with stage_rampage_inducer.py, which writes the joined single-bone mesh.
This step takes the BO6 texture dump and produces:
  model_export/tod_bo6_inducer/tod_inducer.xmodel_bin      (copied from staging)
  model_export/tod_bo6_inducer/_images/*.png               (capped colour/normal/emission)
  source_data/tod_bo6_inducer.gdt                          (images+materials+2 xmodels)

TEXTURE SEMANTICS ARE HASHED IN A BO6 DUMP - the `_mat_info` files name every
slot `unk_semantic_NN` and the numbering is per-techset, so the slot number
cannot be trusted across materials. Colour and normal are identified by
MEASUREMENT: a packed normal map has a mean colour near (x, 128, 255) -
blue-dominant with a mid green - which nothing else in these sheets looks like;
the colour map is then the largest remaining sheet. That rule picks correctly
for all seven materials here, and it FAILS LOUDLY rather than guessing.

THE GLOW IS THE MODEL'S OWN (v18.99j; user: "make the model actually orange and
the orange glows ... not like the perk glow ... I want just a model with a glow
on it"). The first port kept only colour + normal and threw away the sheets BO6
uses to make the prop glow, so it rendered as a black-and-grey drum. Now:
  - THE FLUID (the two `material_36ade/503f` slots, a dark smoke sheet) carries
    BO6's own 512x512 yellow-orange emission sheet, hue-nudged to orange, on
    `lit_emissive_plus` - the material type the BO6 ice staff already proved.
  - THE CRYSTALS ship purple in BO6 (an aether crystal). The albedo is HUE-
    ROTATED to orange and BO6's crack mask (`image_6a8f686fd9bc7929`, shared by
    both crystal materials) is tinted orange and used as the emission sheet.
  - THE GLASS is `lit_emissive_transparent` (the stock Annihilator glass
    recipe: colour alpha = opacity, `$white_diffuse` emission under an orange
    `colorTint1`) - BO6's glass colour sheet is 98% transparent, so the crystals
    show THROUGH it with a soft orange haze on the rim.
  - THE STEEL stays `lit_plus`. A AAA prop keeps its contrast; the orange is the
    energy, not the whole can.
TWO STATES, ONE MESH: every glowing material has an `_on` twin (hotter, deeper
orange, higher scaleRGB) and `tod_inducer_on` is the same xmodel_bin with a
`skinOverride` mapping each glowing material to its twin - the stock way to make
a lit twin without a second mesh (44+ stock GDT blocks do exactly this). Script
swaps the model on the toggle; a dynamic-light FX does the pulse on the floor.

SIZE: every sheet is capped at 1024 (the BO6 originals are 4K and up to 27 MB
each). Re-run with --cap N to change it.

Run: python tools/bo6_extraction/install_inducer_bo3.py
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[2]
EXPORT = Path.home()/'Downloads/BO6_Pilot_Export/bo6/models'
STAGING = REPO/'local_sync_cache/bo6_inducer/staging'
MODEL_DIR = REPO/'model_export/tod_bo6_inducer'
IMAGE_DIR = MODEL_DIR/'_images'
GDT = REPO/'source_data/tod_bo6_inducer.gdt'
FFMPEG = Path(os.environ.get('TOD_FFMPEG', r'C:\Users\jorda\AppData\Local\Microsoft\WinGet'
              r'\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe'
              r'\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'))

XMODEL = 'tod_inducer'
XMODEL_ON = 'tod_inducer_on'
PARTS = ['t10_zm_essence_container_orange',
         't10_zm_essence_container_crystal_01',
         't10_zm_essence_container_crystal_02',
         't10_zm_essence_container_crystal_03',
         't10_zm_essence_container_crystal_04']

# ---------------------------------------------------------------- the look
# Which BO6 sheet is the emission, per material ROLE. Pinned by hash name on
# purpose: the fluid's orange sheet is the only orange thing in its folder and
# the crack mask is byte-identical in both crystal folders, so a name is more
# honest than a colour rule here. Missing = loud failure, not a guess.
FLUID_EMISSION = 'image_76bcc7fc69c91d60.png'      # 512x512 yellow-orange, BO6's own
CRYSTAL_EMISSION = 'image_6a8f686fd9bc7929.png'    # 2048 gray crack mask

# ffmpeg filter chains. Hue is degrees; BO6's crystal albedo sits at ~275
# (violet) and the fluid emission at ~47 (amber); orange is ~25.
CRYSTAL_COLOR_FILTER = 'hue=h=110:s=1.35'
FLUID_EMISSION_FILTER = 'hue=h=-18:s=1.25'
# gray mask -> orange emission (channel scale on an equal-channel image).
CRYSTAL_EMISSION_FILTER = 'format=gray,format=rgb24,colorchannelmixer=rr=1:gg=0.42:bb=0.08'

ORANGE_IDLE = '1 0.40 0.08 1'      # a warm lamp
ORANGE_ON = '1 0.24 0.03 1'        # deeper, hotter
# scaleRGB = emission multiplier. The ice staff's tip crystals ship at 14 and
# were judged right; the idle state sits well under that so ON reads as a jump.
# v18.99k (user, after playing v18.99j: "the indication that it's on is not that
# good compared to when it's off ... the off state a little bit less colourful"):
# idle dropped to a third, ON raised ~60% - the CONTRAST is the indicator.
GLOW = {
    #  role     : (idle scaleRGB, on scaleRGB)
    'fluid':   ('1.2', '16'),
    'crystal': ('1.5', '22'),
    'glass':   ('0.4', '6'),
}
FLUID_BASE_TINT = {'idle': '1 0.80 0.65 1',    # barely warm: the lava reads dark when off
                   'on': '1 0.55 0.25 1'}      # warm under the hot emission


# BO3 TRUNCATES AN ASSET NAME AT 63 CHARACTERS AND THEN CANNOT FIND IT IN THE
# gdtDB - it reports "Material <truncated> was not found" and silently
# default-substitutes, which on a glass cylinder is a white face. The first cut
# built the name straight from BO6's, giving
# mtl_tod_inducer_m_mtl_t10_zm_essence_container_large_orange_glass (65) and
# exactly that failure. This is the ONE naming rule, duplicated verbatim in
# stage_rampage_inducer.py and install_inducer_bo3.py; they MUST agree, because
# stage writes the name into the mesh and install writes the GDT block it binds
# to. Longest name it can now produce is 32 characters (+3 for an `_on` twin).
def short_key(name):
    key = name
    for prefix in ('material_', 'm_', 'mtl_t10_zm_', 't10_zm_'):
        key = key.removeprefix(prefix)
    key = key.replace('essence_container_large_orange_', '').replace('essence_container_', '')
    key = key.replace('crystal_medium_', 'crystal')
    return key[:24]


def role_of(folder):
    if 'glass' in folder:
        return 'glass'
    if 'crystal' in folder:
        return 'crystal'
    if folder in ('material_36ade0417853ec32', 'material_503f0f822297b23b'):
        return 'fluid'
    return 'steel'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mean_rgb(path):
    run = subprocess.run([str(FFMPEG), '-v', 'error', '-i', str(path), '-vf', 'scale=1:1',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True)
    data = run.stdout[:3]
    return tuple(data) if len(data) == 3 else None


def looks_like_normal(mean):
    # packed tangent-space normal: blue channel pinned high, green mid-range.
    return mean is not None and mean[2] > 200 and 90 <= mean[1] <= 170


def collect():
    """folder -> {'material','role','color','normal','emission'}"""
    found = {}
    for part in PARTS:
        roots = [EXPORT/part/'_images', EXPORT/part/'_images'/'m']
        for root in roots:
            if not root.is_dir():
                continue
            for folder in sorted(root.iterdir()):
                if not folder.is_dir() or folder.name in found or folder.name == 'm':
                    continue
                prefix = 'm_' if root.name == 'm' else ''
                material = 'mtl_tod_inducer_' + short_key(prefix + folder.name)
                images = []
                for img in sorted(folder.glob('*.png')):
                    if img.name.startswith('$') or 'flicker' in img.name:
                        continue
                    images.append((img, img.stat().st_size, mean_rgb(img)))
                normals = [i for i in images if looks_like_normal(i[2])]
                rest = [i for i in images if not looks_like_normal(i[2]) and i[1] > 50_000]
                assert normals, f'no normal-looking sheet in {folder}'
                assert rest, f'no colour-looking sheet in {folder}'
                normal = max(normals, key=lambda i: i[1])[0]
                color = max(rest, key=lambda i: i[1])[0]
                role = role_of(folder.name)
                emission = None
                if role == 'fluid':
                    emission = folder/FLUID_EMISSION
                elif role == 'crystal':
                    emission = folder/CRYSTAL_EMISSION
                if emission is not None:
                    assert emission.is_file(), f'{role} emission sheet missing: {emission}'
                found[folder.name] = dict(material=material, role=role, color=color,
                                          normal=normal, emission=emission)
    return found


def convert(src, dst, cap, filters=''):
    dst.parent.mkdir(parents=True, exist_ok=True)
    chain = (filters + ',' if filters else '') + f"scale='min({cap},iw)':-1"
    run = subprocess.run([str(FFMPEG), '-v', 'error', '-y', '-i', str(src), '-vf', chain, str(dst)],
                         capture_output=True, text=True)
    assert run.returncode == 0, (src, run.stderr)
    return dst


IMAGE_BLOCK = """\t"{name}" ( "image.gdf" )
\t{{
\t\t"baseImage" "model_export\\\\tod_bo6_inducer\\\\_images\\\\{name}.png"
\t\t"imageType" "Texture"
\t\t"type" "image"
\t\t"compressionMethod" "{compression}"
\t\t"semantic" "{semantic}"
{extra}\t\t"streamable" "1"
\t}}"""


def material_block(name, fields):
    body = '\n'.join(f'\t\t"{k}" "{v}"' for k, v in fields.items())
    return f'\t"{name}" ( "material.gdf" )\n\t{{\n{body}\n\t}}'


def lit_fields(surface, color, normal):
    return {'surfaceType': surface, 'template': 'material.template',
            'materialCategory': 'Geometry Plus', 'materialType': 'lit_plus',
            'colorMap': color, 'normalMap': normal, 'colorTint': '1 1 1 1',
            'textureAtlasRowCount': '1', 'textureAtlasColumnCount': '1',
            'usage': '<not in editor>', 'heatmap': '$gray_32_one_channel',
            'normalHeightScale': '1', 'glossRangeMin': '0', 'glossRangeMax': '13'}


def emissive_fields(surface, color, normal, emission, tint, scale, base_tint='1 1 1 1'):
    # The BO6 ice staff's recipe (install_ice_staff_bo3.py), proven in this map.
    f = lit_fields(surface, color, normal)
    f.update({'materialType': 'lit_emissive_plus', 'colorTint': base_tint,
              'colorMap00': emission, 'colorTint1': tint, 'scaleRGB': scale,
              'emissiveIncompetence': '1', 'emissiveFalloff': '0'})
    return f


def glass_fields(color, normal, tint, scale):
    # Stock `alistairs_annihilator_glass` (hb_alistairs.gdt): colour alpha is
    # the opacity, the emission is a flat white sheet under a colour tint.
    return {'surfaceType': 'glass', 'template': 'material.template',
            'materialCategory': 'Geometry', 'materialType': 'lit_emissive_transparent',
            'colorMap': color, 'normalMap': normal, 'colorTint': '1 1 1 1',
            'colorMap00': '$white_diffuse', 'colorTint1': tint, 'scaleRGB': scale,
            'emissiveIncompetence': '1', 'emissiveFalloff': '1.0',
            'glossSurfaceType': 'glass', 'glossRangeMin': '6', 'glossRangeMax': '17',
            'specAmount': '1', 'reflectionProbeAmount': '1',
            'textureAtlasRowCount': '1', 'textureAtlasColumnCount': '1',
            'usage': '<not in editor>', 'normalHeightScale': '1'}


XMODEL_BLOCK = """\t"{name}" ( "xmodel.gdf" )
\t{{
\t\t"filename" "tod_bo6_inducer\\\\tod_inducer.xmodel_bin"
\t\t"type" "rigid"
\t\t"skinOverride" "{skin}"
\t\t"BulletCollisionLOD" "High"
\t\t"physicsPreset" ""
\t\t"scale" "1"
\t\t"highLodDist" "0"
\t\t"lodNormalPriority" "1"
\t\t"lodPositionPriority" "1"
\t}}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cap', type=int, default=1024)
    args = ap.parse_args()

    src_bin = next(p for p in STAGING.iterdir() if p.name.lower() == 'tod_inducer.xmodel_bin')
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_bin, MODEL_DIR/'tod_inducer.xmodel_bin')

    found = collect()
    assert len(found) == 7, sorted(found)

    images, materials, report, overrides = [], [], {}, []
    for folder, info in sorted(found.items()):
        key = info['material'].removeprefix('mtl_tod_inducer_')
        role = info['role']
        cname, nname, ename = (f'i_tod_inducer_{key}_c', f'i_tod_inducer_{key}_n',
                               f'i_tod_inducer_{key}_e')
        convert(info['color'], IMAGE_DIR/f'{cname}.png', args.cap,
                CRYSTAL_COLOR_FILTER if role == 'crystal' else '')
        convert(info['normal'], IMAGE_DIR/f'{nname}.png', args.cap)
        images.append(IMAGE_BLOCK.format(name=cname, compression='compressed high color',
                                         semantic='diffuseMap',
                                         extra='\t\t"coreSemantic" "sRGB3chAlpha"\n'))
        images.append(IMAGE_BLOCK.format(name=nname, compression='compressed',
                                         semantic='normalMap', extra=''))
        rec = dict(material=info['material'], role=role, color=str(info['color']),
                   normal=str(info['normal']),
                   color_sha256=None, normal_sha256=digest(IMAGE_DIR/f'{nname}.png'))

        if role == 'steel':
            materials.append(material_block(info['material'], lit_fields('metal', cname, nname)))
        else:
            if role == 'glass':
                idle = glass_fields(cname, nname, ORANGE_IDLE, GLOW[role][0])
                on = glass_fields(cname, nname, ORANGE_ON, GLOW[role][1])
            else:
                convert(info['emission'], IMAGE_DIR/f'{ename}.png', args.cap,
                        FLUID_EMISSION_FILTER if role == 'fluid' else CRYSTAL_EMISSION_FILTER)
                images.append(IMAGE_BLOCK.format(name=ename, compression='compressed high color',
                                                 semantic='diffuseMap',
                                                 extra='\t\t"coreSemantic" "sRGB3chAlpha"\n'))
                surface = 'glass' if role == 'crystal' else 'metal'
                base_idle = FLUID_BASE_TINT['idle'] if role == 'fluid' else '1 1 1 1'
                base_on = FLUID_BASE_TINT['on'] if role == 'fluid' else '1 1 1 1'
                idle = emissive_fields(surface, cname, nname, ename, ORANGE_IDLE, GLOW[role][0], base_idle)
                on = emissive_fields(surface, cname, nname, ename, ORANGE_ON, GLOW[role][1], base_on)
                rec.update(emission=str(info['emission']),
                           emission_sha256=digest(IMAGE_DIR/f'{ename}.png'))
            materials.append(material_block(info['material'], idle))
            materials.append(material_block(info['material'] + '_on', on))
            overrides.append(f"{info['material']} {info['material']}_on")
            rec.update(glow=dict(idle=GLOW[role][0], on=GLOW[role][1]))
        rec['color_sha256'] = digest(IMAGE_DIR/f'{cname}.png')
        report[folder] = rec

    # skinOverride is "orig repl\r\n" pairs, the \r\n LITERAL in the GDT text.
    skin = ''.join(pair + '\\r\\n' for pair in overrides)
    xmodels = [XMODEL_BLOCK.format(name=XMODEL, skin=''),
               XMODEL_BLOCK.format(name=XMODEL_ON, skin=skin)]
    body = '{\n' + '\n'.join(images + materials + xmodels) + '\n}\n'
    GDT.write_text(body, encoding='utf-8')

    longest = max(len(m.split('"')[1]) for m in materials)
    assert longest <= 63, longest

    (STAGING/'install.json').write_text(json.dumps(dict(
        gdt=str(GDT), xmodel=XMODEL, xmodel_on=XMODEL_ON, cap=args.cap, materials=report,
        skin_override=overrides,
        xmodel_bin_sha256=digest(MODEL_DIR/'tod_inducer.xmodel_bin')), indent=2) + '\n')
    total = sum(p.stat().st_size for p in IMAGE_DIR.glob('*.png'))
    print(f'INSTALL_OK materials={len(materials)} images={len(images)} overrides={len(overrides)} '
          f'longest_name={longest} texture_bytes={total} ({total/1048576:.1f} MB) cap={args.cap}')


main()
