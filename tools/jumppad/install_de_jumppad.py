#!/usr/bin/env python3
"""install_de_jumppad.py -- THE JUMP PAD wears Der Eisendrache's own jump pad (docs/163 s9).

User 2026-10-03: "The jump pad on this map is a teleporter but I want it to have the jump pad model from der
eisendrache. Can we switch it over with same functionality".

Der Eisendrache's jump pad is the JUMPSPHERE (DE's "flinger", _zm_flingers.gsc): a broken-open half-sphere machine on a
round plinth over a lit deck disc. You walk in through its doorway (its local -x side) and are flung out of its broken
open side (local +x); you land on a matching landing pad. MidgetBlaster's T7 pack (~/Downloads/T7 Assets V2.8.rar)
ships the models, their materials (source_data/_midgetblaster/p7_zm_castle.gdt), most textures and the three fling
sounds; its prefab map_source/_prefabs/_MidgetBlaster/jumppads/castle_flinger_01.map shows how DE assembles them
(launch = jumpsphere_snow + jumpsphere_combined_snow at one origin and yaw; landing = jumpsphere_snow + landing_pad_snow)
and its _zm_flingers.gsc the states (plain = not active, _blue = ready, _red = recharging; the light material is the
only difference on the deck: set_light scaleRGB 0.05 = dark, set_light_blue scaleRGB 5).

This tool copies what the pad needs into repo-owned folders and writes one map-owned GDT, so nothing is read from the
pack at build time:

  model_export/tod_jumppad/<model>/<model>_lodN.xmodel_bin   five models (renamed tod_jumppad_*) x their pack LODs
  model_export/tod_jumppad/_images/i_tod_jp_*.png            every texture the materials need that the tools lack
  source_data/tod_jumppad.gdt                                5 xmodels, the castle materials they name, image blocks
  sound_assets/tod/jumppad/tod_jumppad_{charge,launch,land}.wav   the fling sounds, mastered for this map's mix
  model_export/tod_jumppad/install_manifest.json             hashes + tri counts of every output (--check reads it)

WHAT IS CHANGED FROM THE PACK, AND WHY (everything else is a byte copy / a verbatim block):
  * the models are renamed (MODELS): tod_jumppad_frame (the machine), tod_jumppad_deck_off / _on (the launch deck,
    dark / blue), tod_jumppad_land_off / _on (the landing pad, dark / blue). The RED (recharging) variants are not
    installed: this pad never recharges (walk in and go), so a red deck would only ever lie.
  * every texture the tools do not already have is RENAMED i_tod_jp_<name> (the pack's generic i_t7_* decals are
    referenced - never defined - by several stock GDTs in the tools root; a second session importing them under the
    stock name would make gdtdb refuse the build: memory gdt-duplicate-asset-across-gdts).
  * eight textures the castle materials name exist NOWHERE in the pack (Zurich / Zetsubou / Cairo sets that DE's
    artists borrowed); each is SUBSTITUTED in the material by a same-kind texture (SUBSTITUTES, with the reason).
  * the p7_common / waterpark textures have PNGs but no image block anywhere in the pack; their blocks are AUTHORED
    from a castle block of the same semantic (SIBLINGS: install_keeper's AUTHORED_IMAGES rule). The semantic must be
    the one the material's TECHSET reads in that slot (SLOT_USAGE, checked here and in --check): the first install
    cloned the castle's rare full-colour specularMap block for the micro-tile spec texture, the linker refused it
    ("mismatched usage ( 'specularMap' expected: [specularMask] )", printed in red, the build still OK) and compiled
    the 12 materials that use it EMPTY - the user saw the whole machine flat gray (2026-10-03).
  * textures over MAX_TEX are downscaled to MAX_TEX (a ~210-unit prop seen from a balcony; docs/86 keep it small).
  * the wavs are mastered by their loudest 400 ms (the map's music never ducks and sits at -9..-11 LUFS): the
    launch (DE's flinger_fly, stereo, hot: +0.8 dBTP) downmixed to mono (it plays 3D on the rider's mover) and
    pulled down, the charge and the land (DE's flinger_activate / flinger_land, ~8 dB quieter) brought up.

Usage:
  python tools/jumppad/install_de_jumppad.py              write the outputs into the repo (re-run after any edit here)
  python tools/jumppad/install_de_jumppad.py --stage DIR  write them under DIR (same relative paths) instead
  python tools/jumppad/install_de_jumppad.py --check      the BUILD GATE: every output present with its recorded hash,
                                                          and the GDT self-consistent (every material a model names is
                                                          defined or stock, every texture a material names is defined,
                                                          stock or builtin, every baseImage on disk, every texture's
                                                          semantic the one its slot's techset reads). Never reads the pack.
  python tools/jumppad/install_de_jumppad.py --compiled-ledger <map>_xmodel.csv [--linker-log tmp/native_build/linker_last.log]
                                                          AFTER THE LINK (build_map.ps1): every model + LOD whole, every
                                                          material COMPLETE (an empty one keeps only its name in the
                                                          ledger and draws flat gray), every shipped texture packed, and
                                                          no linker usage / techset complaint naming a pad material or model.
Never hand-edit the outputs.
"""
import hashlib, json, os, pathlib, re, shutil, sqlite3, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
RAR = pathlib.Path.home() / 'Downloads' / 'T7 Assets V2.8.rar'
SEVENZ = r'C:\Program Files\7-Zip\7z.exe'
PACK = 'T7 Assets V2.8'
MB = '_midgetblaster'
CACHE = REPO / 'tmp' / 'jumppad_de' / 'p'          # the pack files this tool reads (gitignored tmp/)
GDTDB = pathlib.Path(r'C:\BO3Tools\TOD2Cybercity\gdtdb\gdt.db')
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))

FOLDER = 'tod_jumppad'
GDT_REL = 'source_data/tod_jumppad.gdt'
MANIFEST_REL = 'model_export/tod_jumppad/install_manifest.json'
SOUND_REL = 'sound_assets/tod/jumppad'
MAX_TEX = 1024

# new name -> (pack model, LOD switch distances for LOD1.., in units). The frame is ~210 wide and 139 tall (the
# teleporter it replaces, ~170 wide, switched at 300/550/850/1250/1800/2600); the deck and the landing pad are flat
# discs (215 / 145 wide) that only ever fill a little of the screen.
MODELS = {
    'tod_jumppad_frame':    ('p7_zm_ctl_jumpsphere_snow',                  (350, 650, 1000, 1500, 2200, 3200)),
    'tod_jumppad_deck_off': ('p7_zm_ctl_jumpsphere_combined_snow',         (400, 800, 1400)),
    'tod_jumppad_deck_on':  ('p7_zm_ctl_jumpsphere_combined_snow_blue',    (400, 800, 1400)),
    'tod_jumppad_land_off': ('p7_zm_ctl_jumpsphere_landing_pad_snow',      (400, 800, 1400)),
    'tod_jumppad_land_on':  ('p7_zm_ctl_jumpsphere_landing_pad_snow_blue', (400, 800, 1400)),
}
LOD_FIELDS = [('filename', None), ('mediumLod', 'mediumLodDist'), ('lowLod', 'lowLodDist'),
              ('lowestLod', 'lowestLodDist'), ('lod4File', 'lod4Dist'), ('lod5File', 'lod5Dist'), ('lod6File', 'lod6Dist')]

# Eight textures the castle materials name that exist nowhere in the pack (DE borrowed them from other maps' sets).
# Each is replaced IN THE MATERIAL by a same-kind texture. A wear mask (alphaRevealMap of a micro-tile blend) becomes
# one of the jumpsphere set's own wear masks; a normal map becomes the flat $normal (the screws are modelled; decal03
# is a normal-only grime decal, so flat = that one decal simply not drawn: no wrong-UV artifact); the snow decal's
# colour becomes the stock snow colour its sibling snow01/snow02 materials already use (its shape is its stock reveal map).
SUBSTITUTES = {
    'i_mtl_p7_zm_zod_gatestone_set_metal02_m':        'i_mtl_p7_zm_ctl_jumpsphere_set_metal05_m',
    'i_mtl_p7_zur_nw_window_industrial_01_metal_m':   'i_mtl_p7_zm_ctl_jumpsphere_set_metal05_m',
    'i_mtl_p7_zur_nw_foundry_set_concrete_m':         'i_mtl_p7_zm_ctl_jumpsphere_set_bracket_m',
    'i_mtl_p7_zur_metro_train_base_03_m':             'i_mtl_p7_zm_ctl_jumpsphere_set_bracket_m',
    'i_mtl_p7_cai_hav_dropship_dmg_set_ext_burned_m': 'i_mtl_p7_zm_ctl_jumpsphere_set_generator_m',
    'i_mtl_p7_zur_train_wreckage_set_dmg_n':          '$normal',
    'i_mtl_p7_zur_nw_foundry_set_screw_n':            '$normal',
    'i_mtl_p7_zur_metro_sign_terminal_set_snow_2_c':  'i_t7_snow_powder_02_c',
}
# A texture with a PNG in the pack but no image block anywhere in it: its block is the castle block below of the
# same semantic (by the material field that uses it), renamed and repointed.
SIBLINGS = {
    'colorMap':       'i_mtl_p7_zm_ctl_jumpsphere_set_bracket_c',     # diffuseMap, compressed high color
    'normalMap':      'i_mtl_p7_zm_ctl_jumpsphere_set_bracket_n',     # normalMap, compressed
    'alphaRevealMap': 'i_mtl_p7_zm_ctl_jumpsphere_set_bracket_m',     # revealMap, compressed
    'cosinePowerMap': 'i_mtl_p7_zm_ctl_box_jewelry_vintage_metal_g',  # glossMap, compressed
    'specColorMap':   'i_mtl_p7_zm_ctl_trunk_wood_vintage_metal_s',   # specularMask, compressed (22 castle _s blocks
}                                                                     # are masks; the 2 specularMap ones are fullspec's)
# The image usage each (techset, slot) READS - the linker's own words for the slots this pad's materials fill
# (tmp/native_build/linker_last.log, 2026-10-03 15:32: "Image ... (specColorMap) has a mismatched usage ( 'specularMap'
# expected: [specularMask] )"; colorMap03 is the micro-tile techset's 'specularMapDetail2'). A texture this tool ships
# into such a slot must carry exactly that semantic, or the linker refuses it and the material compiles EMPTY.
SLOT_USAGE = {
    ('lit_micro_tile_blend_advanced', 'specColorMap'): 'specularMask',
    ('lit_micro_tile_blend_advanced', 'colorMap03'):   'specularMask',
    ('lit_alphatest_advanced',        'specColorMap'): 'specularMask',
    ('lit_transparent_advanced',      'specColorMap'): 'specularMask',
    ('lit_backlit_advanced',          'specColorMap'): 'specularMask',
}
# the pack folders the textures live in (V2.8 layout)
IMAGE_DIRS = [r'model_export\%s\props\p7_zm_castle\_images' % MB, r'model_export\%s\props\p7_common\_images' % MB,
              r'model_export\%s\props\p7_mp_waterpark\_images' % MB, r'model_export\%s\weapons\t7\_images' % MB]
GDTS = ['p7_zm_castle.gdt', 't7_weapons.gdt']        # image + material blocks (the castle one carries the materials)

# name -> (pack wav, mono, gain dB, alias meaning). Measured 2026-10-03 (ffmpeg ebur128, M = the loudest 400 ms):
# the pack's flinger_fly M-max -3.9 LUFS stereo / TP +0.8 dBFS, flinger_activate -13.3 / 0.0, flinger_land -13.7 / -0.9.
# They are transient-heavy, so gain past these mostly feeds the limiter (activate +8 dB reads only 0.4 LU louder than
# +6). Shipped: charge -11.0, launch -8.1, land -11.3 LUFS M-max - every one well over the teleporter boom (tod_warp,
# -17.1) the pad used to play at the same moments, under the never-duck music's -9..-11 LUFS only by a transient's width.
SOUNDS = {
    'tod_jumppad_charge': ('flinger_activate.wav', True, 6.0, 'the pad crackles awake (power on) and fires (every launch)'),
    'tod_jumppad_launch': ('flinger_fly.wav',      True, 1.0, 'the fling: 3D on the rider\'s mover'),
    'tod_jumppad_land':   ('flinger_land.wav',     True, 7.0, 'the touch-down thud on the landing pad'),
}
SOUND_DIR = r'sound_assets\zmb\level\zm_castle\flinger'
LIMIT = 0.84    # alimiter ceiling, linear (-1.5 dBFS sample peak: true peak stays under -0.5 dBTP)

HEAD = re.compile(r'^\t"([^"]+)" (?:\( ?"([^"]+)" ?\)|\[ ?"([^"]+)" ?\])\s*$', re.M)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def extract(members):
    """7z x the members into CACHE (once; 7z scans the whole 58 GB archive per call, ~25 s)."""
    need = [m for m in members if not (CACHE / PACK / m.replace('\\', os.sep)).exists()]
    if not need:
        return
    if not RAR.exists():
        raise SystemExit('T7 asset pack not found: %s' % RAR)
    CACHE.mkdir(parents=True, exist_ok=True)
    subprocess.run([SEVENZ, 'x', '-y', '-o' + str(CACHE), str(RAR)] + [PACK + '\\' + m for m in need], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def pack_path(member):
    return CACHE / PACK / member.replace('\\', os.sep)


def index_blocks(text):
    out = {}
    heads = list(HEAD.finditer(text))
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[m.start():end]
        close = body.find('\n\t}')
        out.setdefault(m.group(1), body[:close + 3])
    return out


def field(blk, key):
    m = re.search(r'^\t\t"%s" "([^"]*)"' % re.escape(key), blk, re.M)
    return m.group(1) if m else None


def set_field(blk, key, value):
    pat = re.compile(r'^(\t\t"%s" )"[^"\n]*"' % re.escape(key), re.M)
    if pat.search(blk):
        return pat.sub(lambda m: m.group(1) + '"' + value.replace('\\', '\\\\') + '"', blk, count=1)
    return blk.replace('\n\t}', '\n\t\t"%s" "%s"\n\t}' % (key, value.replace('\\', '\\\\')), 1)


def rename(blk, new):
    first, rest = blk.split('\n', 1)
    return re.sub(r'^\t"[^"]+"', '\t"%s"' % new, first) + '\n' + rest


def normalise(blk):
    """the pack writes its castle blocks with 1-tab fields and ("x.gdf") heads; ours match tod_keeper.gdt."""
    lines = blk.split('\n')
    head = re.sub(r'\(\s*"([^"]+)"\s*\)', r'( "\1" )', lines[0])
    body = []
    for ln in lines[1:]:
        s = ln.strip()
        if not s:
            continue
        body.append('\t' + s if s in ('{', '}') else '\t\t' + s)
    return '\n'.join([head] + body)


def tod_image(name):
    return 'i_tod_jp_' + name[2:]


def slot_problems(gdt_text):
    """every texture defined in this GDT that sits in a SLOT_USAGE slot carries the semantic that slot reads."""
    blocks = index_blocks(gdt_text)
    out = []
    for name, b in sorted(blocks.items()):
        if '( "material.gdf" )' not in b.split('\n')[0]:
            continue
        mtype = field(b, 'materialType')
        for f, v in re.findall(r'^\t\t"(\w+)" "(i_[^"]+)"', b, re.M):
            want = SLOT_USAGE.get((mtype, f))
            if want and v in blocks and field(blocks[v], 'semantic') != want:
                out.append('material %s (%s) %s -> %s is semantic %r; that slot reads a %s (the linker refuses it and '
                           'compiles the material EMPTY = flat gray)' % (name, mtype, f, v, field(blocks[v], 'semantic'), want))
    return out


def stock_sets():
    """the tools root's images and materials, LESS the ones this tool's own GDT put in the database: after a build the
    DB holds tod_jumppad.gdt's 49 materials and 31 textures too, and counting them as stock made a re-install write a
    GDT with no materials at all (caught staging the 2026-10-03 specular fix, before it landed)."""
    db = sqlite3.connect(GDTDB.as_uri() + '?mode=ro', uri=True)
    db.execute('pragma writable_schema=ON')
    own = pathlib.PurePosixPath(GDT_REL).name.lower()
    ours = {n for n, g in db.execute('select e.name, g.name from _entity e join _gdt g on e.FK_gdt = g.PK_id')
            if pathlib.PureWindowsPath(g).name.lower() == own}
    imgs = {r[0] for r in db.execute('select _name from image')} - ours
    mats = {r[0] for r in db.execute('select _name from material')} - ours
    return imgs, mats


def model_info(path):
    """tris, materials, and the triangles with two coincident corners (zero area: the converter drops those silently,
    memory converter-drops-needle-triangles - a compiled count short by exactly these is not a loss)."""
    from PyCoD import xmodel
    m = xmodel.Model()
    m.LoadFile_Bin(str(path), split_meshes=True)
    degen = 0
    for me in m.meshes:
        V = [v.offset for v in me.verts]
        for f in me.faces:
            p = [V[i.vertex] for i in f.indices]
            if any(sum((p[a][k] - p[b][k]) ** 2 for k in range(3)) < 1e-10 for a, b in ((0, 1), (1, 2), (0, 2))):
                degen += 1
    return {'tris': sum(len(me.faces) for me in m.meshes), 'degenerate': degen, 'materials': sorted({x.name for x in m.materials})}


def master(src, dst, mono, gain):
    af = ('aformat=channel_layouts=mono,' if mono else '') + 'volume=%sdB,alimiter=limit=%s:attack=1:release=60:level=false' % (gain, LIMIT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(src), '-af', af, '-ar', '48000',
                    '-c:a', 'pcm_s16le', '-map_metadata', '-1', '-fflags', '+bitexact', '-flags:a', '+bitexact', str(dst)], check=True)


def loudness(path):
    p = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True)
    m = [float(x) for x in re.findall(r' M:\s*(-?[\d.]+)', p.stderr)]
    tp = re.findall(r'Peak:\s*(-?[\d.]+) dBFS', p.stderr)
    return {'m_max_lufs': round(max(m), 1) if m else None, 'true_peak_dbfs': float(tp[-1]) if tp else None}


def build(out_root):
    """-> {repo-relative path: bytes}, manifest dict."""
    members = [r'source_data\%s\%s' % (MB, g) for g in GDTS]
    for new, (src, dists) in MODELS.items():
        for lod in range(len(dists) + 1):
            members.append(r'model_export\%s\props\p7_zm_castle\%s\%s_LOD%d.xmodel_bin' % (MB, src, src, lod))
    members += [SOUND_DIR + '\\' + w for w, _, _, _ in SOUNDS.values()]
    extract(members)
    blocks = {}
    for g in GDTS:
        for k, v in index_blocks(pack_path(r'source_data\%s\%s' % (MB, g)).read_text(encoding='utf-8', errors='replace').replace('\r\n', '\n')).items():
            blocks.setdefault(k, v)
    stock_imgs, stock_mats = stock_sets()

    outputs, man = {}, {'pack': RAR.name, 'models': {}, 'materials': [], 'images': {}, 'substitutes': SUBSTITUTES,
                         'stock_images': [], 'stock_materials': [], 'sounds': {}}
    gdt = []

    # MODELS
    used_mats = set()
    for new, (src, dists) in MODELS.items():
        lods = [pack_path(r'model_export\%s\props\p7_zm_castle\%s\%s_LOD%d.xmodel_bin' % (MB, src, src, lod))
                for lod in range(len(dists) + 1)]
        if not all(p.exists() for p in lods):
            raise SystemExit('%s: the pack lacks one of its %d LOD files' % (src, len(lods)))
        info = []
        for i, p in enumerate(lods):
            rel = 'model_export/%s/%s/%s_lod%d.xmodel_bin' % (FOLDER, new, new, i)
            outputs[rel] = p.read_bytes()
            mi = model_info(p)
            used_mats |= set(mi['materials'])
            info.append({'file': rel, 'tris': mi['tris'], 'degenerate': mi['degenerate'], 'materials': mi['materials']})
        man['models'][new] = {'pack': src, 'lods': info}
        blk = ['\t"%s" ( "xmodel.gdf" )' % new, '\t{']
        kv = {'BulletCollisionFile': '', 'BulletCollisionLOD': 'None', 'CollisionMap': '', 'highLodDist': '0',
              'lodPresets': 'custom', 'materials': '', 'physicsPreset': '', 'scale': '1', 'skinOverride': '', 'type': 'rigid'}
        for i, (fk, dk) in enumerate(LOD_FIELDS):
            if i < len(lods):
                kv[fk] = '%s\\%s\\%s_lod%d.xmodel_bin' % (FOLDER, new, new, i)
                if dk:
                    kv[dk] = str(dists[i - 1])
            else:
                kv[fk] = ''
                if dk:
                    kv[dk] = '0'
        for k in sorted(kv, key=str.lower):
            blk.append('\t\t"%s" "%s"' % (k, kv[k].replace('\\', '\\\\')))
        blk.append('\t}')
        gdt.append('\n'.join(blk))

    # MATERIALS (verbatim castle blocks; stock ones are left to the tools)
    need_imgs = {}                      # image -> set of material fields that use it
    mat_blocks = []
    for mt in sorted(used_mats):
        if mt in stock_mats:
            man['stock_materials'].append(mt)
            continue
        if mt not in blocks:
            raise SystemExit('material %s: not stock and not in the pack' % mt)
        b = blocks[mt]
        for f, v in re.findall(r'^\s*"(\w+)" "(i_[^"]+)"', b, re.M):
            v = SUBSTITUTES.get(v, v)
            if v.startswith('$'):
                continue
            need_imgs.setdefault(v, set()).add(f)
        mat_blocks.append((mt, b))
        man['materials'].append(mt)

    if not man['materials']:
        raise SystemExit('install_de_jumppad: the models name %d materials and every one reads as stock - the stock '
                         'lookup is counting tod_jumppad.gdt itself (stock_sets)' % len(used_mats))

    # IMAGES: stock -> untouched; else copied (+ block from the pack or a sibling), renamed i_tod_jp_*
    lst_path = CACHE / 'listing_images.txt'      # one 7z listing of the four texture folders, cached
    if not lst_path.exists():
        lst_path.write_text(subprocess.run([SEVENZ, 'l', '-ba', str(RAR)] + [PACK + '\\' + d + '\\*' for d in IMAGE_DIRS],
                                           capture_output=True, text=True, check=True).stdout)
    listing = {}
    for d in IMAGE_DIRS:                         # first folder wins (the castle's own set before the shared ones)
        for line in lst_path.read_text().splitlines():
            m = re.search(re.escape(d) + r'\\([^\\]+)\.png\s*$', line)
            if m:
                listing.setdefault(m.group(1), d + '\\' + m.group(1) + '.png')
    rename_map = {}
    copy = []
    for img in sorted(need_imgs):
        if img in stock_imgs:
            man['stock_images'].append(img)
            continue
        if img not in listing:
            raise SystemExit('texture %s: not stock, no PNG in the pack and no SUBSTITUTES entry' % img)
        new = tod_image(img)
        if len(new) > 60:
            raise SystemExit('renamed texture %s is %d chars (asset names truncate at 63)' % (new, len(new)))
        rename_map[img] = new
        if img in blocks:
            b, how = blocks[img], 'pack block'
        else:
            # the field that says what the texture IS; a generic colorMapNN layer slot says nothing, so fall back to
            # the texture's own suffix (_c colour, _n normal, _m/_r reveal mask, _g gloss, _s specular)
            prim = sorted(need_imgs[img] - {'colorMap00', 'colorMap01', 'colorMap02', 'colorMap03'})
            by_suffix = {'c': 'colorMap', 'n': 'normalMap', 'm': 'alphaRevealMap', 'r': 'alphaRevealMap',
                         'g': 'cosinePowerMap', 's': 'specColorMap'}.get(img.rsplit('_', 1)[-1])
            sib = next((SIBLINGS[f] for f in prim + ([by_suffix] if by_suffix else []) if f in SIBLINGS), None)
            if not sib or sib not in blocks:
                raise SystemExit('texture %s (fields %s): no image block in the pack and no SIBLINGS rule' % (img, sorted(need_imgs[img])))
            b, how = blocks[sib], 'authored from ' + sib
        b = normalise(rename(b, new))
        b = set_field(b, 'baseImage', 'model_export\\%s\\_images\\%s.png' % (FOLDER, new))
        gdt.append(b)
        copy.append((img, new, listing[img], how))
    extract([src for _, _, src, _ in copy])
    from PIL import Image
    for img, new, src, how in copy:
        p = pack_path(src)
        im = Image.open(p)
        im.load()
        w, h = im.size
        if max(w, h) > MAX_TEX:
            f = MAX_TEX / max(w, h)
            im = im.resize((max(4, int(w * f)), max(4, int(h * f))), Image.LANCZOS)
        import io
        buf = io.BytesIO()
        im.save(buf, format='PNG', optimize=False)
        data = buf.getvalue() if max(w, h) > MAX_TEX else p.read_bytes()
        rel = 'model_export/%s/_images/%s.png' % (FOLDER, new)
        outputs[rel] = data
        man['images'][new] = {'pack_name': img, 'pack': src.replace('\\', '/'), 'size': [w, h], 'shipped': list(im.size) if max(w, h) > MAX_TEX else [w, h],
                              'block': how, 'used_as': sorted(need_imgs[img])}

    for mt, b in mat_blocks:
        for old, new in SUBSTITUTES.items():
            b = b.replace('"%s"' % old, '"%s"' % new)
        for old, new in rename_map.items():
            b = b.replace('"%s"' % old, '"%s"' % new)
        gdt.append(normalise(b))

    text = '{\n' + '\n'.join(gdt) + '\n}\n'
    probs = slot_problems(text)
    if probs:
        raise SystemExit('install_de_jumppad: a texture would sit in a slot that reads another usage:\n  ' + '\n  '.join(probs))
    outputs[GDT_REL] = text.replace('\n', '\r\n').encode('utf-8')

    # SOUNDS
    for new, (wav, mono, gain, what) in SOUNDS.items():
        src = pack_path(SOUND_DIR + '\\' + wav)
        dst = out_root / SOUND_REL / (new + '.wav')
        master(src, dst, mono, gain)
        outputs['%s/%s.wav' % (SOUND_REL, new)] = dst.read_bytes()
        man['sounds'][new] = {'pack': (SOUND_DIR + '\\' + wav).replace('\\', '/'), 'mono': mono, 'gain_db': gain, 'limit': LIMIT,
                              'what': what, **loudness(dst)}
    return outputs, man


def check(root=REPO):
    man_path = root / MANIFEST_REL
    if not man_path.exists():
        raise SystemExit('install_de_jumppad --check: no manifest (%s) - run the installer' % MANIFEST_REL)
    man = json.loads(man_path.read_text())
    bad = []
    for rel, want in man['files'].items():
        p = root / rel
        if not p.exists():
            bad.append('missing ' + rel)
        elif sha(p.read_bytes()) != want:
            bad.append('changed ' + rel)
    gdt = (root / GDT_REL).read_text(encoding='utf-8').replace('\r\n', '\n')
    blocks = index_blocks(gdt)
    stock_m, stock_i = set(man['stock_materials']), set(man['stock_images'])
    for name, mod in man['models'].items():
        if name not in blocks:
            bad.append('the GDT has no xmodel block ' + name)
        for lod in mod['lods']:
            for mt in lod['materials']:
                if mt not in blocks and mt not in stock_m:
                    bad.append('%s names material %s: neither in the GDT nor stock' % (lod['file'], mt))
    for name, b in blocks.items():
        if '( "material.gdf" )' in b.split('\n')[0]:
            for f, v in re.findall(r'^\t\t"(\w+)" "((?:i_|\$)[^"]+)"', b, re.M):
                if v.startswith('$'):
                    continue
                if v not in blocks and v not in stock_i:
                    bad.append('material %s %s -> %s: undefined texture' % (name, f, v))
                if v in man['substitutes']:
                    bad.append('material %s still names the missing %s' % (name, v))
        if '( "image.gdf" )' in b.split('\n')[0]:
            bi = field(b, 'baseImage').replace('\\\\', '\\')
            if not (root / bi.replace('\\', '/')).exists():
                bad.append('image %s: baseImage %s not in the repo' % (name, bi))
    bad.extend(slot_problems(gdt))
    if bad:
        raise SystemExit('install_de_jumppad --check FAILED:\n  ' + '\n  '.join(bad[:40]))
    tris = sum(l['tris'] for m in man['models'].values() for l in m['lods'][:1])
    print('install_de_jumppad --check OK: %d files, %d models (%d LOD0 tris), %d materials, %d textures shipped, %d stock, %d substituted, %d sounds'
          % (len(man['files']), len(man['models']), tris, len(man['materials']), len(man['images']), len(stock_i), len(man['substitutes']), len(man['sounds'])))


# The usage / techset complaints the linker prints in red WITHOUT failing the link (each one = a material compiled
# EMPTY: no techset, no textures). Any line naming a pad material or model fails the post-link check.
LINKER_COMPLAINTS = ('mismatched usage', "doesn't expose", 'no techset')
# A material whose ledger row is no bigger than this past its name holds nothing but the name: EMPTY. Measured on the
# 15:32 link: the 12 empty pad materials are len(name) + 2 bytes; every complete one is 328..2080 bytes.
EMPTY_MATERIAL_SLACK = 64


def compiled(ledger, linker_log=None):
    """AFTER THE LINK: the linker's xmodel ledger (<map>_xmodel.csv; tris columns run COARSE -> FINE, tris0 = the lowest
    LOD) holds every model with every LOD and its triangles (short only by the zero-area ones the converter drops, which
    the manifest counts), and the asset ledger (<map>.csv) holds the four DE effects, every material COMPLETE (not just
    its name) and every texture this tool ships; the linker's transcript names no pad material or model in a usage /
    techset complaint. A name in the ledger is NOT a working material: the 15:32 link of 2026-10-03 listed all 49 and
    12 of them were empty (the machine drew flat gray)."""
    import csv
    man = json.loads((REPO / MANIFEST_REL).read_text())
    bad, lines = [], []
    with open(ledger, encoding='utf-8-sig', newline='') as f:
        rows = {r['name']: r for r in csv.DictReader(f)}
    for name, mod in man['models'].items():
        row = rows.get(name)
        if row is None:
            bad.append(name + ' missing from the compiled xmodel ledger')
            continue
        n = len(mod['lods'])
        if int(row['lodCount']) != n:
            bad.append('%s compiled with %s LODs, installed %d' % (name, row['lodCount'], n))
            continue
        for lod, info in enumerate(mod['lods']):
            got, want, degen = int(row['tris' + str(n - 1 - lod)]), info['tris'], info.get('degenerate', 0)
            if got == want or got == want - degen:
                lines.append('%s lod%d %d tris%s' % (name, lod, got, '' if got == want else ' (%d zero-area dropped)' % degen))
            else:
                bad.append('%s lod%d compiled %d triangles, installed %d (%d zero-area)' % (name, lod, got, want, degen))
    assets = pathlib.Path(str(ledger).replace('_xmodel.csv', '.csv'))
    with open(assets, encoding='utf-8-sig', newline='') as f:
        arows = list(csv.DictReader(f))
    have = {(r['type'], r['name']) for r in arows}
    resident = {(r['type'], r['name']): int(r['resident'] or 0) for r in arows}
    gsc = (REPO / 'scripts/zm/zm_tod2_cybercity/_tod_jumppad.gsc').read_text(encoding='utf-8')
    for fx in re.findall(r'#precache\( "fx", "([^"]+)" \);', gsc):
        if ('fx', fx) not in have:
            bad.append('effect %s missing from the compiled assets' % fx)
    for mt in man['materials']:
        key = ('material', 'mc/' + mt) if ('material', 'mc/' + mt) in have else ('material', mt)
        if key not in have:
            bad.append('material %s missing from the compiled assets' % mt)
        elif resident[key] <= len(key[1]) + EMPTY_MATERIAL_SLACK:
            bad.append('material %s compiled EMPTY (its ledger row is %d bytes = the name only: no techset, no textures; '
                       'it draws flat gray)' % (mt, resident[key]))
    missing = sorted(n for n in man['images'] if ('image', n) not in have)
    for n in missing:
        bad.append('texture %s (used as %s) missing from the compiled assets' % (n, ', '.join(man['images'][n]['used_as'])))
    imgs = len(man['images']) - len(missing)
    complaints = 0
    if linker_log is not None:
        lp = pathlib.Path(linker_log)
        if not lp.exists():
            bad.append('no linker transcript at %s (the build writes it; without it the usage check cannot run)' % lp)
        else:
            ours = set(man['materials']) | set(man['models'])
            for line in lp.read_text(encoding='utf-8-sig', errors='replace').replace('\0', '').splitlines():
                if not any(c in line for c in LINKER_COMPLAINTS):
                    continue
                named = set(re.findall(r'[\w/]+', line.replace('mc/', '')))
                if named & ours:
                    complaints += 1
                    if complaints <= 12:
                        bad.append('linker: ' + line.replace('^1', '').strip()[:220])
            if complaints > 12:
                bad.append('... %d more linker complaints naming a pad material or model' % (complaints - 12))
    if bad:
        raise SystemExit('install_de_jumppad --compiled-ledger FAILED:\n  ' + '\n  '.join(bad))
    print('install_de_jumppad --compiled-ledger OK: %d models, every LOD compiled whole; %d effects, %d materials (all complete), '
          '%d of %d textures in the assets%s'
          % (len(man['models']), len(re.findall(r'#precache\( "fx"', gsc)), len(man['materials']), imgs, len(man['images']),
             '' if linker_log is None else '; no linker usage / techset complaint names a pad material or model'))
    for l in lines:
        print('  ' + l)


def main():
    if '--compiled-ledger' in sys.argv:
        log = sys.argv[sys.argv.index('--linker-log') + 1] if '--linker-log' in sys.argv else None
        return compiled(sys.argv[sys.argv.index('--compiled-ledger') + 1], log)
    out_root = REPO
    if '--stage' in sys.argv:
        out_root = pathlib.Path(sys.argv[sys.argv.index('--stage') + 1]).resolve()
    if '--check' in sys.argv:
        return check(out_root)
    outputs, man = build(out_root)
    man['files'] = {}
    for rel, data in sorted(outputs.items()):
        dst = out_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.read_bytes() != data:
            dst.write_bytes(data)
        man['files'][rel] = sha(data)
    mp = out_root / MANIFEST_REL
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(json.dumps(man, indent=1, sort_keys=True) + '\n')
    lod0 = {k: v['lods'][0]['tris'] for k, v in man['models'].items()}
    print('install_de_jumppad: %d files -> %s' % (len(outputs), out_root))
    print('  models (LOD0 tris): %s' % lod0)
    print('  materials %d (+%d stock), textures shipped %d (+%d stock), substituted %d' % (
        len(man['materials']), len(man['stock_materials']), len(man['images']), len(man['stock_images']), len(SUBSTITUTES)))
    for k, v in man['sounds'].items():
        print('  sound %s: M-max %s LUFS, true peak %s dBFS' % (k, v['m_max_lufs'], v['true_peak_dbfs']))


if __name__ == '__main__':
    main()
