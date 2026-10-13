#!/usr/bin/env python3
"""stage_donors.py -- pull the Dealer's donor assets out of the T7 asset pack into art/dealer_boss/donors/.

  the Wunderwaffe DG-2 world model             (his lightning gun)
  the Dingo LMG world model                    (his machine gun)

Writes the XMODEL_BINs, every image their materials name, the GDT blocks they
need (as text, repointed to the staging folder) and donors/manifest.json for the
studio step (11_weapons.py) and the installer. Read-only on
the pack; nothing here touches the tools root.
"""
import os, re, sys, json, hashlib, shutil, tempfile, subprocess
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'keeper'))
import install_keeper as K
OUT = os.path.join(REPO, 'art', 'dealer_boss', 'donors')
os.makedirs(os.path.join(OUT, '_images'), exist_ok=True)

MODELS = {   # our key -> (xmodel block name, gdt, model file inside the pack's model_export)
    'dg2': ('wpn_t7_zmb_dg2_world', 't7_base_dg2.gdt', None),
    # the pack has every Dingo material but no Dingo world xmodel block: the BRM's block is the shape donor
    'dingo': ('wpn_t7_lmg_brm_world', 't7_lmg_cqb.gdt', r'wpn_t7_lmg_dingo_world_LOD0.XMODEL_BIN'),
}
GDTS = ['t7_base_dg2.gdt', 't7_lmg_cqb.gdt', 't7_characters.gdt', 't7_character_assets.gdt', 't7_weapon_assets.gdt', 't7_weapons.gdt']


def list_pack():
    r = subprocess.run([K.SEVENZ, 'l', '-slt', K.RAR], capture_output=True, text=True, check=True)
    return [line[7:].strip() for line in r.stdout.splitlines() if line.startswith('Path = ')]


def main():
    tmp = tempfile.mkdtemp(prefix='tod_dealer_donors_')
    try:
        paths = list_pack()
        by_leaf = {}
        for p in paths:
            by_leaf.setdefault(os.path.basename(p).lower(), []).append(p)
        # every GDT in the pack (260 small text files): the block we need may live in any of them
        gdt_members = [p[len(K.PACK) + 1:] for p in paths if p.lower().endswith('.gdt') and '\\source_data\\' in p]
        K.extract(gdt_members, tmp)
        root = os.path.join(tmp, K.PACK)
        blocks = {}
        for m in gdt_members:
            for k, v in K.index_blocks(K.read(os.path.join(root, m))).items():
                blocks.setdefault(k, v)
        for key, (xm, gdt, forced) in MODELS.items():
            assert xm in blocks, 'no GDT block anywhere in the pack for ' + xm
        manifest = {'pack': os.path.basename(K.RAR), 'models': {}, 'materials': {}, 'images': {}}
        file_members = []
        for key, (xm, gdt, forced) in MODELS.items():
            b = blocks[xm]
            fn = forced or K.field(b, 'filename').replace('\\\\', '\\')
            leaf = os.path.basename(fn)
            cand = [p for p in by_leaf.get(leaf.lower(), []) if '\\model_export\\' in p]
            assert cand, 'model file not in pack: ' + fn
            file_members.append(cand[0][len(K.PACK) + 1:])
            manifest['models'][key] = {'xmodel': xm, 'block_donor': xm, 'file': leaf, 'source': cand[0], 'block': b}
        K.extract(file_members, tmp)
        # materials each model names (read out of the binaries), then every image those materials name
        sys.path.insert(0, os.path.expandvars(r'%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons\BetterBetterBlenderCOD'))
        from PyCoD import xmodel
        need_images = set()
        for key, info in manifest['models'].items():
            src = [os.path.join(root, m.replace('\\', os.sep)) for m in file_members if os.path.basename(m).lower() == info['file'].lower()][0]
            dst = os.path.join(OUT, info['file'])
            shutil.copyfile(src, dst)
            info['sha256'] = hashlib.sha256(open(dst, 'rb').read()).hexdigest()
            m = xmodel.Model(); m.LoadFile_Bin(dst, split_meshes=True)
            info['materials'] = [mm.name for mm in m.materials]
            info['bones'] = len(m.bones); info['triangles'] = sum(len(x.faces) for x in m.meshes)
            for mat in m.materials:
                if mat.name in manifest['materials']:
                    continue
                if mat.name not in blocks:
                    manifest['materials'][mat.name] = {'block': None, 'note': 'not in the pack GDTs (stock?)'}
                    continue
                mb = blocks[mat.name]
                maps = {k: v for k, v in re.findall(r'^\t\t"((?:color|normal|spec|gloss|cosinePower|occ|revealMap|colorMap00|emissive)\w*)" "(i_[a-z0-9_]+)"', mb, re.M)}
                manifest['materials'][mat.name] = {'block': mb, 'maps': maps, 'materialType': K.field(mb, 'materialType'), 'surfaceType': K.field(mb, 'surfaceType')}
                need_images |= set(maps.values())
        img_members = []
        for img in sorted(need_images):
            hits = [p for p in by_leaf.get((img + '.png').lower(), []) if '\\_images\\' in p]
            if not hits:
                manifest['images'][img] = {'png': None, 'note': 'no png in pack'}
                continue
            img_members.append(hits[0][len(K.PACK) + 1:])
            manifest['images'][img] = {'png': img + '.png', 'block': blocks.get(img), 'source': hits[0]}
        K.extract(img_members, tmp)
        for img, info in manifest['images'].items():
            if not info.get('png'):
                continue
            src = [os.path.join(root, m.replace('\\', os.sep)) for m in img_members if os.path.basename(m).lower() == info['png'].lower()][0]
            dst = os.path.join(OUT, '_images', info['png'])
            shutil.copyfile(src, dst)
            info['sha256'] = hashlib.sha256(open(dst, 'rb').read()).hexdigest()
        json.dump(manifest, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1, sort_keys=True)
        print('staged', {k: (v['triangles'], len(v['materials'])) for k, v in manifest['models'].items()},
              'materials', len(manifest['materials']), 'images', sum(1 for i in manifest['images'].values() if i.get('png')),
              'missing pngs', [k for k, i in manifest['images'].items() if not i.get('png')],
              'materials without blocks', [k for k, i in manifest['materials'].items() if not i.get('block')])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
