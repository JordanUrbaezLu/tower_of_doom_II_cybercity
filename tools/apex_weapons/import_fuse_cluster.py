"""Fuse's KNUCKLE CLUSTER from the installed Apex, as the Breacher's CLUSTER tactical.

User 2026-09-25: "let's get those cluster grenades ... I have Apex on my computer ... we've taken
stuff from Apex assets before". Recipe = Hellbound's tools/import_apex_thermite.py (read, not
imported: no tool here reads the Hellbound repo), applied to Fuse's canister.

What is Apex and what is not:
  * MODELS + TEXTURES: Apex (RSX 2.3.0 CAST + PNG, extracted by extract_sources.py with
    --filter misc_fuse_tactical_grenade). The held canister rides BO3's shock-charge hand
    motion (no Apex arm retarget), the thrown bomb is the "projectile_large" ball, the
    scripted bomblets are the small "projectile" ball.
  * SOUNDS: Apex (--filter Fuse_Tac_), resampled to 48 kHz mono, peak -1 dBFS.
  * EFFECTS: NOT Apex. Apex particle systems (efct) do not convert to BO3. The trail is BO3's
    incendiary grenade trail; the bomblet pop and sizzle are composed here from the Sparrow
    bow's cluster-arrow emitters (BO3's own cluster bomb), keeping only self-contained blocks.

Inputs are read only: source_library/ (ours), the private tools root's hb_thermite.gdt and
its two thermite XMODEL_BINs (skeleton templates), repo sound/aliases/hb_thermite.csv.

Run:  python tools/apex_weapons/import_fuse_cluster.py          (writes, then a FULL build)
      python tools/apex_weapons/import_fuse_cluster.py --check  (hashes only)
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ADDONS = Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons'
sys.path.extend([str(ADDONS / 'io_scene_cast'), str(ADDONS / 'BetterBetterBlenderCOD')])
import numpy as np  # noqa: E402
import cast  # noqa: E402
from PIL import Image  # noqa: E402
from PyCoD import xmodel  # noqa: E402

sys.path.insert(0, str(REPO / 'tools/bo6_extraction'))
import build_bo6_ice_fx as fxlib  # noqa: E402  (blocks / block_name / child_refs / rescale / v3_header)

TOOLS = Path(json.loads((REPO / '.tod2-workspace.json').read_text())['modToolsRoot']) \
    if (REPO / '.tod2-workspace.json').exists() else Path('C:/BO3Tools/TOD2Cybercity')
LIB = REPO / 'source_library/apex_r99_peacekeeper'
MDL = LIB / 'assets/mdl'
WAV = LIB / 'audio/audio'
OUT = REPO / 'model_export/tod_fuse_cluster'
SOUND = REPO / 'sound_assets/tod/fuse_cluster'
FX_OUT = REPO / 'share/raw/fx/tod/fuse'
GDT = REPO / 'source_data/tod_fuse_cluster.gdt'
ALIASES = REPO / 'sound/aliases/tod_fuse_cluster.csv'
SZC = REPO / 'sound/zoneconfig/zm_tod2_cybercity.szc'
MANIFEST = REPO / 'docs/apex_fuse_cluster/import.json'
TEMPLATE_GDT = TOOLS / 'source_data/hb_thermite.gdt'
TEMPLATE_MODELS = TOOLS / 'model_export/hb/thermite'
DONOR_FX = TOOLS / 'share/raw/fx/weapon'

# usage -> (Apex stem, BO3 template model, uniform scale). The Apex canister is 3.5 units long
# (the thermite is 8.2), so the held one is enlarged about its grip to read in first person.
MODELS = {
    'tod_fuse_cluster_view': ('ptpov_fuse_tactical_grenade_held', 'hb_thermite_view', 2.5),
    'tod_fuse_cluster_world': ('w_fuse_tactical_grenade_projectile_large', 'hb_thermite_world', 1.25),
    'tod_fuse_bomblet': ('w_fuse_tactical_grenade_projectile', 'hb_thermite_world', 2.0),
}
MATERIAL = 'fuse_tactical_grenade'
CHANNELS = [('col', 'colorMap'), ('nml', 'normalMap'), ('gls', 'cosinePowerMap'),
            ('spc', 'specColorMap'), ('ao', 'occMap'), ('ilm', 'colorMap00')]
DEFAULTS = {'col': (255, 255, 255), 'nml': (128, 128, 255), 'gls': (96, 96, 96),
            'spc': (10, 10, 10), 'ao': (255, 255, 255), 'ilm': (0, 0, 0)}

# alias -> (source regex, 2d|3d, volume, looping)
SOUNDS = {
    'tod_fuse_throw': (r'Fuse_Tac_Fire_1p_Merge_2ch_0\d', '2d', 84, False),
    'tod_fuse_throw_3p': (r'Fuse_Tac_Fire_3p_1000_Merge_2ch_0\d', '3d', 86, False),
    'tod_fuse_draw': (r'Fuse_Tac_Deploy_2ch_Shortened_0\d', '2d', 80, False),
    'tod_fuse_impact': (r'Fuse_Tac_Bomb_Impact_Base_3P_Merge_2ch_0\d', '3d', 90, False),
    'tod_fuse_bomb': (r'Fuse_Tac_Bomb_Explode_Merge_2ch_0\d', '3d', 90, False),
    'tod_fuse_sizzle': (r'Fuse_Tac_Bomb_Fuse_SizzleClose_2ch_v01_0\d', '3d', 74, True),
}

# effect -> [(donor file, [block names] | '*', edits)]
EFFECTS = {
    # the bomblet pop: the Sparrow cluster-arrow bomblet explosion without its MP debris
    # models (defs 8..13 carry c_t7_mp_reaper pieces + a child trail emitter)
    'fx_tod_fuse_bomblet_exp': [(DONOR_FX / 'fx_hero_bow_lnchr_exp_bot.efx',
                                 ['wraith_oneshot_def%d' % i for i in (0, 1, 2, 3, 4, 5, 6, 7, 14)], {'scale': 1.15})],
    # the landed bomblet's fuse: the Sparrow stuck-arrow fizz (looping sparks + hot glow),
    # without its two dynamic lights and one-shot rays (eight at once would cost too much)
    'fx_tod_fuse_sizzle': [(DONOR_FX / 'fx_hero_bow_lnchr_impact_sm.efx',
                            ['wraith_looping_def%d' % i for i in (0, 2, 3, 4, 5)], {'scale': 0.7})],
}


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parse(path):
    text = path.read_text(encoding='utf-8-sig')
    return {n: (k, dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*)"', b))) for n, k, b in
            re.findall(r'^[ \t]+"([^"\n]+)"\s*\(\s*"([^"\n]+)"\s*\)\s*\{(.*?)^[ \t]*\}', text, re.M | re.S)}


def block(name, kind, fields):
    return '\t"' + name + '" ( "' + kind + '" )\n\t{\n' + ''.join(
        '\t\t"' + a + '" "' + str(b) + '"\n' for a, b in fields.items()) + '\t}\n'


def pathval(p):
    return str(p).replace('/', '\\').replace('\\', '\\\\')


def mat(pos, quat):
    x, y, z, w = np.array(quat) / np.linalg.norm(quat)
    m = np.eye(4)
    m[:3, :3] = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                 [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                 [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    m[:3, 3] = pos
    return m


def pivot(source):
    """World transform of the grip bone (def_c_base) or identity for a one-bone prop."""
    bones = source.Skeleton().Bones()
    names = [b.Name() for b in bones]
    if 'def_c_base' not in names:
        return np.eye(4)
    world = []
    for b in bones:
        m = mat(b.LocalPosition(), b.LocalRotation())
        world.append(world[b.ParentIndex()] @ m if b.ParentIndex() >= 0 else m)
    return world[names.index('def_c_base')]


def build_material(report):
    tex = MDL / 'w_fuse_tactical_grenade' / 'w_fuse_tactical_grenade'
    tpl = parse(TEMPLATE_GDT)
    fields = dict(tpl['mtl_hb_thermite_thermite_base_main'][1])
    out = []
    for ch, slot in CHANNELS:
        src = tex / f'{MATERIAL}_{ch}.png'
        im = Image.open(src).convert('RGB') if src.exists() else Image.new('RGB', (4, 4), DEFAULTS[ch])
        if ch == 'nml' and src.exists():
            # Apex normals are two-channel: rebuild Z for BO3.
            a = np.array(im)
            xy = a[:, :, :2].astype(np.float32) / 255 * 2 - 1
            a[:, :, 2] = ((np.sqrt(np.maximum(0, 1 - (xy * xy).sum(axis=2))) * .5 + .5) * 255).astype(np.uint8)
            im = Image.fromarray(a)
        dst = OUT / f'{MATERIAL}_{ch}.png'
        im.save(dst)
        name = f'i_tod_fuse_cluster_{ch}'
        fi = dict(tpl[f'i_hb_thermite_thermite_base_main_{ch}'][1])
        fi.update(baseImage=pathval(dst.relative_to(REPO)))
        out.append(block(name, 'image.gdf', fi))
        fields[slot] = name
        report['images'].append(dict(name=name, source=str(src) if src.exists() else 'default', size=im.size))
    out.append(block('mtl_tod_fuse_cluster', 'material.gdf', fields))
    return out


def build_model(name, stem, template, scale, report):
    src = MDL / stem / f'{stem}_LOD0.cast'
    source = cast.Cast.load(str(src)).Roots()[0].ChildrenOfType(cast.Model)[0]
    # Apex's long axis is local Y; BO3 hand/tag frames want Z (Hellbound's measured rotation).
    rotation = np.array([[1., 0, 0], [0, 0, -1], [0, 1, 0]])
    transform = np.eye(4)
    transform[:3, :3] = rotation * scale
    if name.endswith('_view'):
        transform[:3, 3] = [0, 0, -.25]
    transform = transform @ np.linalg.inv(pivot(source))
    model = xmodel.Model()
    model.LoadFile_Bin(str(TEMPLATE_MODELS / f'{template}.XMODEL_BIN'))
    model.meshes, model.materials = [], [xmodel.Material('mtl_tod_fuse_cluster', 'Lambert', {})]
    verts = 0
    for mesh in source.Meshes():
        part = xmodel.Mesh(mesh.Name())
        pos = np.array(mesh.VertexPositionBuffer()).reshape(-1, 3) @ transform[:3, :3].T + transform[:3, 3]
        nrm = np.array(mesh.VertexNormalBuffer()).reshape(-1, 3) @ transform[:3, :3].T
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1)[:, None], 1e-9)
        uv = np.array(mesh.VertexUVLayerBuffer(0)).reshape(-1, 2)
        part.verts = [xmodel.Vertex(tuple(p), [(0, 1.)]) for p in pos]   # rigid on bone 0
        faces = np.array(mesh.FaceBuffer()).reshape(-1, 3)
        dots = np.einsum('ij,ij->i', np.cross(pos[faces[:, 1]] - pos[faces[:, 0]], pos[faces[:, 2]] - pos[faces[:, 0]]),
                         nrm[faces].mean(axis=1))
        order = [0, 2, 1] if np.median(dots[np.abs(dots) > 1e-8]) > 0 else [0, 1, 2]
        for tri in faces:
            f = xmodel.Face(len(model.meshes), 0)
            for j, k in enumerate(order):
                i = int(tri[k])
                f.indices[j] = xmodel.FaceVertex(i, tuple(nrm[i]), (1, 1, 1, 1), tuple(uv[i]))
            part.faces.append(f)
        model.meshes.append(part)
        verts += len(pos)
    path = OUT / f'{name}.XMODEL_EXPORT'
    model.WriteFile_Raw(str(path))
    r = subprocess.run([str(TOOLS / 'bin/export2bin.exe'), path.name], cwd=OUT, capture_output=True, text=True)
    assert r.returncode == 0, (path, r.stdout, r.stderr)
    check = xmodel.Model()
    check.LoadFile_Bin(str(path.with_suffix('.XMODEL_BIN')))
    got = sum(len(m.verts) for m in check.meshes)
    assert got == verts, (name, got, verts)
    lo = np.min([v.offset for m in check.meshes for v in m.verts], axis=0)
    hi = np.max([v.offset for m in check.meshes for v in m.verts], axis=0)
    fields = dict(parse(TEMPLATE_GDT)[template][1])
    fields['filename'] = pathval(f'tod_fuse_cluster/{name}.XMODEL_BIN')
    report['models'].append(dict(name=name, source=str(src), sha256=digest(src), template=template, scale=scale,
                                 vertices=got, bones=[b.name for b in check.bones],
                                 bounds=[np.round(lo, 2).tolist(), np.round(hi, 2).tolist()]))
    return block(name, 'xmodel.gdf', fields)


def build_sounds(report):
    SOUND.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((REPO / 'sound/aliases/hb_thermite.csv').open(encoding='utf-8')))
    tpl2d = next(r for r in rows if r['Name'] == 'hb_thermite_throw')
    tpl3d = next(r for r in rows if r['Name'] == 'hb_thermite_ignite')
    files = sorted(WAV.glob('Fuse_Tac_*.wav'))
    out = []
    for alias, (pattern, pan, vol, loop) in SOUNDS.items():
        picks = [p for p in files if re.fullmatch(pattern, p.stem)]
        assert picks, (alias, pattern)
        for i, src in enumerate(picks):
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(src), '-ar', '48000', '-ac', '1', '-f', 'f32le', '-'],
                                 capture_output=True, check=True).stdout
            s = np.frombuffer(raw, dtype='<f4').copy()
            peak = float(np.max(np.abs(s)))
            assert peak > 0, src
            s *= 10 ** (-1 / 20) / peak
            fade = min(480, len(s) // 2)
            s[:fade] *= np.linspace(0, 1, fade)
            s[-fade:] *= np.linspace(1, 0, fade)
            short = alias.replace('tod_fuse_', '')
            dst = SOUND / f'{short}_{i + 1}.wav'
            with wave.open(str(dst), 'wb') as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(48000)
                w.writeframes(np.round(s * 32767).astype('<i2').tobytes())
            row = dict(tpl3d if pan == '3d' else tpl2d)
            row.update(Name=alias, FileSpec='tod\\fuse_cluster\\' + dst.name, VolMin=str(vol), VolMax=str(vol),
                       ContextType='', ContextValue='', PitchMin='0', PitchMax='0',
                       Looping='looping' if loop else 'nonlooping')
            if pan == '3d':
                row.update(DistMin='150', DistMaxDry='2000', DistMaxWet='2000',
                           LimitCount='4' if alias in ('tod_fuse_bomb', 'tod_fuse_sizzle') else '8', LimitType='oldest',
                           EntityLimitCount='1', EntityLimitType='oldest')
            out.append(row)
            report['audio'].append(dict(alias=alias, source=src.name, sha256=digest(src),
                                        seconds=round(len(s) / 48000, 3), output=str(dst.relative_to(REPO))))
    with ALIASES.open('w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        wr.writeheader()
        wr.writerows(out)
    data = json.loads(SZC.read_text(encoding='utf-8'))
    if not any(s.get('Name') == 'tod_fuse_cluster' for s in data['Sources']):
        data['Sources'].append(dict(Type='ALIAS', Name='tod_fuse_cluster', Filename='tod_fuse_cluster.csv', Specs=[]))
        SZC.write_text(json.dumps(data, indent=4) + '\n', encoding='utf-8')


def build_effects(report):
    FX_OUT.mkdir(parents=True, exist_ok=True)
    for name, recipe in EFFECTS.items():
        parts = []
        for src, want, edits in recipe:
            text = src.read_text(encoding='latin1').replace('\r', '')
            found = {}
            for b in fxlib.blocks(text):
                n = fxlib.block_name(b)
                if want != '*' and n not in want:
                    continue
                assert not fxlib.child_refs(b), (src.name, n, 'child effect')
                assert not re.search(r'"c_t7_mp_', b), (src.name, n, 'MP-only model')
                if edits.get('scale', 1.0) != 1.0:
                    b = fxlib.rescale(b, edits['scale'])
                found[n] = b
            assert want == '*' or set(want) == set(found), (src.name, set(want) - set(found))
            parts += list(found.values())
            report['effects'].setdefault(name, []).append(dict(source=str(src), blocks=sorted(found), edits=edits))
        (FX_OUT / f'{name}.efx').write_text(fxlib.v3_header() + '\n\n'.join(parts) + '\n', encoding='latin1')


def build_weapon():
    f = dict(parse(TEMPLATE_GDT)['hb_thermite'][1])
    f.update(displayName='Knuckle Cluster',
             gunModel='tod_fuse_cluster_view', worldModel='tod_fuse_cluster_world',
             projectileModel='tod_fuse_cluster_world',
             ammoName='tod_cluster', clipName='tod_cluster', sharedAmmoCapName='tod_cluster',
             fireSound='tod_fuse_throw_3p', fireSoundPlayer='tod_fuse_throw',
             raiseSound='tod_fuse_draw', raiseSoundPlayer='tod_fuse_draw',
             projTrailEffect='weapon/fx_incend_grenade_trail',
             # the script bursts it on its FIRST contact ("grenade_bounce"); a sticky
             # grenade never bounces, and the fuse is only the no-contact fallback
             stickiness="Don't stick", fuseTime='3.5')
    return block('tod_cluster', 'grenadeweapon.gdf', f)


def main():
    if '--check' in sys.argv:
        r = json.loads(MANIFEST.read_text())
        for p, h in r['outputs'].items():
            assert (REPO / p).is_file() and digest(REPO / p) == h, ('fuse cluster output changed/missing', p)
        print(f"FUSE CLUSTER OK: {len(r['outputs'])} outputs pinned")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    report = dict(scope='Apex Knuckle Cluster models/textures/sounds; effects composed from BO3 emitters (Apex efct does not convert)',
                  apex_build=(Path('C:/Program Files (x86)/Steam/steamapps/common/Apex Legends/build.txt')).read_text().strip(),
                  models=[], images=[], audio=[], effects={}, native_verified=False)
    gdt = build_material(report)
    for name, (stem, template, scale) in MODELS.items():
        gdt.append(build_model(name, stem, template, scale, report))
    gdt.append(build_weapon())
    GDT.write_text('{\n' + ''.join(gdt) + '}\n', encoding='utf-8')
    build_sounds(report)
    build_effects(report)
    outs = [GDT, ALIASES] + sorted(OUT.glob('*.XMODEL_BIN')) + sorted(OUT.glob('*.png')) + \
        sorted(SOUND.glob('*.wav')) + sorted(FX_OUT.glob('*.efx'))
    report['outputs'] = {str(p.relative_to(REPO)).replace('\\', '/'): digest(p) for p in outs}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(report, indent=2) + '\n')
    for m in report['models']:
        print('MODEL', m['name'], m['vertices'], 'verts', m['bones'], m['bounds'])
    print(f"FUSE CLUSTER: {len(gdt)} GDT blocks, {len(report['audio'])} sound variants, {len(EFFECTS)} effects")


if __name__ == '__main__':
    main()
