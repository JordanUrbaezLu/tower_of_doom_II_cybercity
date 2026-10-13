#!/usr/bin/env python3
"""install_keeper.py -- the Battle Arena's level-10 boss, THE KEEPER, from the T7 asset pack.

User 2026-09-28: "lets add him in. As the boss. He is the wave 10 in the battle arena."
The Revelations (Genesis) Keeper ships complete in `~/Downloads/T7 Assets V2.8.rar`:
its full-body model (head included), 16 materials / 17 textures, 82 animation
clips, and its own AI tables (anim mapping, selector, state machine, behavior
tree). This tool copies what the boss needs into repo-owned folders and writes
one map-owned GDT, so nothing is read from the pack at build time:

  model_export/tod_keeper/          the body + the dissolve body (its death), _images/
  xanim_export/tod_keeper/          the 82 Keeper clips (XANIM_BIN, byte copies)
  animtables/tod_keeper.ai_am|ai_ast            (synced to the usermap, like the Mangler's)
  share/raw/animstatemachines/tod_keeper.ai_asm (synced to the tools share tree)
  share/raw/behavior/tod_keeper.ai_bt           (synced to the tools share tree)
  source_data/tod_keeper.gdt        images, materials, 2 xmodels, character, 82 xanims,
                                    and the aitype chain archetype -> variant -> spawner_tod_keeper

WHAT IS CHANGED FROM THE PACK, AND WHY (everything else is a byte copy / verbatim block):
  * the behavior tree loses its PROCEDURAL TRAVERSAL branch: it calls four
    functions registered only by shared/ai/archetype_robot.gsc, which this map
    does not load (it drags in the R.A.P.S. vehicle and robot clientfields). The
    animated-traversal branch stays; the arena is one flat room.
  * the aitype chain is renamed tod_keeper and points at the tables above; its
    second character (the hooded Keeper - the pack has only its preview mesh)
    and its footstep FX bundle are dropped; csvInclude is cleared (the zone
    names what the boss needs instead).
  * the character's fxDef / deathFxDef are cleared: an fxcharacterdef is only
    played when a script calls FxClientUtils::PlayFxBundle, so the glow is
    played by _tod_keeper.csc directly (the pack's own keeper csc does the same).
  * three textures the materials name have PNGs in the pack but no image
    blocks; they are authored here from a same-kind sibling block.
  * every file path is repointed at the repo folders.

Re-run after any edit here; never hand-edit the outputs. `--check` verifies the
written files match what this script would write (a build gate).
"""
import os, re, sys, json, subprocess, hashlib, shutil, tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAR = os.path.join(os.path.expanduser('~'), 'Downloads', 'T7 Assets V2.8.rar')
SEVENZ = r'C:\Program Files\7-Zip\7z.exe'
PACK = 'T7 Assets V2.8'
MB = '_midgetblaster'

OUT_GDT = os.path.join(REPO, 'source_data', 'tod_keeper.gdt')
MODEL_DIR = os.path.join(REPO, 'model_export', 'tod_keeper')
XANIM_DIR = os.path.join(REPO, 'xanim_export', 'tod_keeper')
AM_OUT = os.path.join(REPO, 'animtables', 'tod_keeper.ai_am')
AST_OUT = os.path.join(REPO, 'animtables', 'tod_keeper.ai_ast')
ASM_OUT = os.path.join(REPO, 'share', 'raw', 'animstatemachines', 'tod_keeper.ai_asm')
BT_OUT = os.path.join(REPO, 'share', 'raw', 'behavior', 'tod_keeper.ai_bt')
MANIFEST = os.path.join(MODEL_DIR, 'install_manifest.json')

GDTS = ['t7_characters.gdt', 't7_character_assets.gdt', 't7_zm_ai.gdt', 't7_aitype.gdt']
BODY_BIN = 'c_zom_dlc4_keeper_fb.XMODEL_BIN'
DISSOLVE_BIN = 'c_zom_dlc4_keeper_body_dissolve_fb_LOD0.XMODEL_BIN'
BODY_SRC = r'model_export\%s\characters\t7\c_zom_dlc4_keeper_body\%s' % (MB, BODY_BIN)
DISSOLVE_SRC = r'model_export\%s\characters\t7\c_zom_dlc4_keeper_body_dissolve\%s' % (MB, DISSOLVE_BIN)
AI_SRC = {
    'am': r'share\raw\animtables\zm_genesis_keeper.ai_am',
    'ast': r'share\raw\animtables\zm_genesis_keeper.ai_ast',
    'asm': r'share\raw\animstatemachines\zm_genesis_keeper.ai_asm',
    'bt': r'share\raw\behavior\zm_genesis_keeper.ai_bt',
}

# the materials the two model binaries name (read out of the decompressed
# XMODEL_BINs; LOD0 of each carries every surface)
MATERIALS = ['arms', 'arms_decal', 'cloth', 'head', 'metal', 'mouth', 'tattered_parts', 'tattered_parts_no_alpha']
MATERIALS = ['mtl_c_zom_dlc4_keeper_' + m for m in MATERIALS] + ['mtl_c_zom_dlc4_keeper_' + m + '_dissolve' for m in MATERIALS]
# stock images already in the private tools root (checked against gdt.db); never re-authored
STOCK_IMAGES = {'i_c_gen_reveal_1k_rec_horiz_r', 'i_c_gen_reveal_1k_sq_r', 'i_generic_lookup'}
# PNG in the pack, no image block anywhere in it: authored from this sibling
AUTHORED_IMAGES = {
    'i_c_zom_zod_keeper_bare_black_metal_n': 'i_c_zom_dlc4_keeper_head_n',
    'i_c_zom_zod_keeper_bare_black_mouth_n': 'i_c_zom_dlc4_keeper_head_n',
    'i_mtl_p7_zm_zod_beast_door_set_text_02b_c': 'i_c_zom_dlc4_keeper_head_c',
}
BODY = 'tod_keeper_body'
DISSOLVE = 'tod_keeper_dissolve'
CHARACTER = 'c_tod_keeper'

HEAD = re.compile(r'^\t"([^"]+)" (?:\( "([^"]+)" \)|\[ "([^"]+)" \])\s*$', re.M)


def extract(members, dest):
    subprocess.run([SEVENZ, 'x', '-y', '-o' + dest, RAR] + [PACK + '\\' + m for m in members], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read(path):
    return open(path, encoding='utf-8', errors='replace').read().replace('\r\n', '\n')


def index_blocks(text):
    out = {}
    heads = list(HEAD.finditer(text))
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[m.start():end]
        close = body.find('\n\t}')
        out.setdefault(m.group(1), body[:close + 3])
    return out


def set_field(blk, key, value):
    pat = re.compile(r'^(\t\t"%s" )"[^"\n]*"' % re.escape(key), re.M)
    if pat.search(blk):
        return pat.sub(lambda m: m.group(1) + '"' + value.replace('\\', '\\\\') + '"', blk, count=1)
    return blk.replace('\n\t}', '\n\t\t"%s" "%s"\n\t}' % (key, value), 1)


def rename(blk, new, parent=None):
    first, rest = blk.split('\n', 1)
    if parent:
        first = '\t"%s" [ "%s" ]' % (new, parent)
    else:
        first = re.sub(r'^\t"[^"]+"', '\t"%s"' % new, first)
    return first + '\n' + rest


def field(blk, key):
    m = re.search(r'^\t\t"%s" "([^"]*)"' % re.escape(key), blk, re.M)
    return m.group(1) if m else None


def strip_procedural_traversal(bt_text):
    """Drop the child of the BT's traversalbehavior selector whose id is
    proceduraltraversebehavior (JSON-parsed, never regex-cut)."""
    tree = json.loads(bt_text)
    hits = []

    def walk(node):
        kids = node.get('children')
        if not kids:
            return
        keep = []
        for k in kids:
            if k.get('id') == 'proceduraltraversebehavior':
                hits.append(k)
                continue
            walk(k)
            keep.append(k)
        node['children'] = keep
    walk(tree)
    if len(hits) != 1:
        raise SystemExit('expected exactly one proceduraltraversebehavior node, found %d' % len(hits))
    text = json.dumps(tree, indent=4)
    for f in ('robotcalcproceduraltraversal', 'robotproceduraltraversal', 'robotprocedurallanding', 'robottraverseend'):
        if f in text:
            raise SystemExit('behavior tree still names ' + f)
    return text + '\n'


def build(tmp):
    members = [r'source_data\%s\%s' % (MB, g) for g in GDTS] + list(AI_SRC.values()) + [BODY_SRC, DISSOLVE_SRC]
    extract(members, tmp)
    root = os.path.join(tmp, PACK)
    blocks = {}
    for g in GDTS:
        for k, v in index_blocks(read(os.path.join(root, 'source_data', MB, g))).items():
            blocks.setdefault(k, v)

    am = read(os.path.join(root, AI_SRC['am']))
    ast = read(os.path.join(root, AI_SRC['ast']))
    asm = read(os.path.join(root, AI_SRC['asm']))
    bt = strip_procedural_traversal(read(os.path.join(root, AI_SRC['bt'])))
    clips = sorted({c.strip() for line in am.split('\n')[1:] for c in line.split(',')[1:] if c.strip()})
    keeper_clips = [c for c in clips if c in blocks]   # the rest (ai_zombie_base_*, void) are stock, in gdt.db

    # images: every map name the 16 materials use
    need_images = set()
    for m in MATERIALS:
        if m not in blocks:
            raise SystemExit('material %s not in the pack' % m)
        need_images |= set(re.findall(r'"(i_[a-z0-9_]+)"', blocks[m]))
    need_images -= STOCK_IMAGES

    out = []          # GDT blocks, in order
    files = {}        # dest -> (kind, source-in-tmp or text)
    png_members = []
    for img in sorted(need_images):
        if img in blocks:
            b = blocks[img]
        elif img in AUTHORED_IMAGES:
            b = rename(blocks[AUTHORED_IMAGES[img]], img)
        else:
            raise SystemExit('image %s has no block and no authored sibling' % img)
        png = img + '.png'
        png_members.append(r'model_export\%s\characters\t7\_images\%s' % (MB, png))
        b = set_field(b, 'baseImage', r'model_export\tod_keeper\_images\%s' % png)
        out.append(b)
        files[os.path.join(MODEL_DIR, '_images', png)] = ('copy', os.path.join(root, 'model_export', MB, 'characters', 't7', '_images', png))
    for m in MATERIALS:
        out.append(blocks[m])

    # models (the character body is the full-body model, head included)
    b = rename(blocks['c_zom_dlc4_keeper_fb'], BODY)
    b = set_field(b, 'filename', r'tod_keeper\%s' % BODY_BIN)
    out.append(b)
    b = rename(blocks['c_zom_dlc4_keeper_dissolve'], DISSOLVE)
    b = set_field(b, 'filename', r'tod_keeper\%s' % DISSOLVE_BIN)
    out.append(b)
    files[os.path.join(MODEL_DIR, BODY_BIN)] = ('copy', os.path.join(root, BODY_SRC))
    files[os.path.join(MODEL_DIR, DISSOLVE_BIN)] = ('copy', os.path.join(root, DISSOLVE_SRC))

    b = rename(blocks['c_zom_dlc4_keeper'], CHARACTER)
    b = set_field(b, 'body', BODY)
    b = set_field(b, 'previewxmodel', BODY)
    b = set_field(b, 'fxDef', '')
    b = set_field(b, 'deathFxDef', '')
    out.append(b)

    xanim_members = []
    for c in keeper_clips:
        b = blocks[c]
        src = field(b, 'filename')
        base = src.replace('\\\\', '\\').split('\\')[-1]
        xanim_members.append('xanim_export\\' + src.replace('\\\\', '\\'))
        b = set_field(b, 'filename', r'tod_keeper\%s' % base)
        if field(b, 'model'):
            b = set_field(b, 'model', r'tod_keeper\%s' % BODY_BIN)
        if field(b, 'previewModel'):
            b = set_field(b, 'previewModel', BODY)
        out.append(b)
        files[os.path.join(XANIM_DIR, base)] = ('copy', os.path.join(root, 'xanim_export', src.replace('\\\\', os.sep).replace('\\', os.sep)))

    # the aitype chain (Hellbound's shape: archetype aitype.gdf -> variant -> spawner)
    over = {'animMappingTableName': 'tod_keeper.ai_am', 'animSelectorTableName': 'tod_keeper.ai_ast',
            'animStateMachineName': 'tod_keeper.ai_asm', 'behaviorTreeName': 'tod_keeper.ai_bt',
            'character1': CHARACTER, 'character2': '', 'csvInclude': '', 'aiFxBundle': '',
            'radiantModel': BODY}
    chain = [('archetype_zm_genesis_keeper', 'archetype_tod_keeper', None),
             ('variant_zm_genesis_keeper', 'variant_tod_keeper', 'archetype_tod_keeper'),
             ('spawner_zm_genesis_keeper', 'spawner_tod_keeper', 'variant_tod_keeper')]
    for src, new, parent in chain:
        b = rename(blocks[src], new, parent)
        for k, v in over.items():
            if field(b, k) is not None or parent is None:
                b = set_field(b, k, v)
        out.append(b)

    extract(png_members + xanim_members, tmp)
    gdt = '{\n' + '\n'.join(out) + '\n}\n'
    texts = {OUT_GDT: gdt, AM_OUT: am, AST_OUT: ast, ASM_OUT: asm, BT_OUT: bt}
    return files, texts, keeper_clips


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def main():
    check = '--check' in sys.argv
    if not os.path.exists(RAR):
        raise SystemExit('T7 asset pack not found: ' + RAR)
    tmp = tempfile.mkdtemp(prefix='tod_keeper_')
    try:
        files, texts, clips = build(tmp)
        bad = []
        manifest = {'pack': os.path.basename(RAR), 'clips': len(clips), 'files': {}, 'texts': {}}
        for dst, (kind, src) in sorted(files.items()):
            if not os.path.exists(src):
                raise SystemExit('pack file missing: ' + src)
            want = sha(src)
            manifest['files'][os.path.relpath(dst, REPO).replace('\\', '/')] = want
            if check:
                if not os.path.exists(dst) or sha(dst) != want:
                    bad.append(os.path.relpath(dst, REPO))
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
        for dst, text in sorted(texts.items()):
            # CRLF everywhere: the pack and stock ship their AI tables CRLF, and the
            # first build (LF tables) asserted in q_string.cpp while loading
            # tod_keeper.ai_ast (tmp/keeper/full1.log, 2026-09-28).
            data = text.replace('\n', '\r\n').encode('utf-8')
            manifest['texts'][os.path.relpath(dst, REPO).replace('\\', '/')] = hashlib.sha256(data).hexdigest()
            if check:
                if not os.path.exists(dst) or open(dst, 'rb').read() != data:
                    bad.append(os.path.relpath(dst, REPO))
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, 'wb').write(data)
        if check:
            if bad:
                raise SystemExit('install_keeper --check: STALE/MISSING:\n  ' + '\n  '.join(bad))
            print('install_keeper --check OK: %d files + %d generated texts, %d clips' % (len(files), len(texts), len(clips)))
        else:
            open(MANIFEST, 'w').write(json.dumps(manifest, indent=1, sort_keys=True) + '\n')
            print('install_keeper: wrote %d files + %d generated texts (%d clips) -> %s' % (len(files), len(texts), len(clips), REPO))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
