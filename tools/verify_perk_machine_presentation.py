"""Gate machine presentation on complete notes, source assets and banked audio.

2026-10-04 (docs/208): PORTED FROM MAP 1 (tower_of_doom_cybercity v19.32 + v19.45 + v19.48b),
retargeted to zm_tod2_cybercity. Three TOD II differences, all deliberate:
  - THE FOLDERS ARE tod2_perk_machines, NOT map 1's tod_perk_machines. In the private tools root
    C:\\BO3Tools\\TOD2Cybercity, model_export\\tod_perk_machines is a JUNCTION into the shared
    Steam install (map 1's deployed copy, linked at workspace setup), so a sync row there dies on
    tod2_workspace.ps1's "refusing write through source reference" and a GDT path there would make
    this map's conversion read map 1's output. Every clip/model this map converts is its own copy.
  - THE GDT FILE NAME STAYS tod_perk_machines.gdt: the private source_data holds map 1's copy under
    that name (copied at setup, the same four asset names), and the sync overwrites it in place.
    Any other file name would leave two GDTs defining tod_doubletap_* and gdtdb refuses that.
  - NO IMPORTER HERE: map 1's tools/import_perk_machine_presentation.py vendors from donor folders
    under map 1's tmp/; this map carries the frozen outputs, so the shot table is read from the
    manifest ("shots") and cross-checked against the GDT notes and the GSC table below.
Map 1's Widow's Wine 3-layer emissive techsetdef pin (its v19.43, same file) is NOT part of this
port - it is its own fix (techsetdefs + sync rows + a post-link missing_techsetdef gate).

  python tools/verify_perk_machine_presentation.py                 pre-link: assets, notes, audio, zone, tree, GSC
  python tools/verify_perk_machine_presentation.py --ledger CSV    post-link: the linker's asset ledger carries them
"""
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import types
import wave

# ROOT / blocks / the PyCoD loader were imported from two staff tools until their class was
# retired (2026-10-04, archive/mage_retired/tools/); this gate carries its own copies now.
ROOT = Path(__file__).resolve().parents[1]
PYCOD = Path(os.environ.get('TOD_PYCOD', r'C:\Users\jorda\Repositories\test+map\tmp\blender-cod\io_scene_cod'))


def blocks(path):
    return [(m[1],m[2],dict(re.findall(r'"([^"\n]+)"\s*"([^"\n]*)"',m[3])))
            for m in re.finditer(r'"([^"\n]+)"\s*\(\s*"([^"\n]+)"\s*\)\s*\{([^}]+)\}',path.read_text(encoding='latin1'))]


FOLDER = 'tod2_perk_machines'
CLIPS = ['tod_doubletap_intro', 'tod_doubletap_fire', 'tod_doubletap_outro', 'tod_wisp_activate']
KEPT_CLIPS = ['p9_fxanim_zm_gp_speed_cola_initiate', 'p9_fxanim_zm_gp_speed_cola_initiate_off',
              'p9_fxanim_zm_gp_speed_cola_loop', 't10_fxanim_zm_machine_d_mod_idle', 'anim_68e0495f3599ef44']
REPLACED_CLIPS = ['t10_fxanim_zm_machine_d_mod_intro', 't10_fxanim_zm_machine_d_mod_loop',
                  't10_fxanim_zm_machine_d_mod_outro', 'anim_2f28cb2f33eaab2f']
FX = ['tod/perks/doubletap_muzzle', '_wetegg/sat/perks/fx_double_tap_zombie_eye_glow_red',
      '_wetegg/sat/perks/fx_wisp_tea_activate']
GSC = 'scripts/zm/zm_tod2_cybercity/_tod_perk_anims.gsc'


def text(rel):
    return (ROOT/rel).read_bytes().decode('utf-8-sig', errors='replace')


def ledger(path):
    """Post-link: every clip, cue effect, the animtree and the module made it into the fastfile."""
    rows = set()
    with open(path, newline='', encoding='utf-8', errors='replace') as file:
        for row in csv.reader(file):
            if len(row) >= 3:
                rows.add((row[1], row[2]))
    want = [('xanim', n) for n in CLIPS + KEPT_CLIPS] + [('fx', n) for n in FX] + \
           [('rawfile', 'animtrees/tod_perk_machines.atr'), ('scriptparsetree', GSC)]
    missing = [w for w in want if w not in rows]
    stale = [('xanim', n) for n in REPLACED_CLIPS if ('xanim', n) in rows]
    for kind, name in missing:
        print('MISSING from the ledger:', kind, name)
    for kind, name in stale:
        print('STILL LINKED (replaced donor clip):', kind, name)
    if missing or stale:
        print('PERK MACHINE LEDGER FAILED (%d missing, %d stale) - %s' % (len(missing), len(stale), path))
        return 1
    print('PERK MACHINE LEDGER OK: %d clips, %d cue effects, the animtree and the module linked; '
          'the %d replaced donor clips are gone.' % (len(CLIPS + KEPT_CLIPS), len(FX), len(REPLACED_CLIPS)))
    return 0


if len(sys.argv) == 3 and sys.argv[1] == '--ledger':
    sys.exit(ledger(sys.argv[2]))
if len(sys.argv) != 1:
    sys.exit(__doc__)

if 'PyCoD' not in sys.modules:
    sys.path.insert(0, str(PYCOD))
    pkg = types.ModuleType('PyCoD')
    pkg.__path__ = [str(PYCOD/'PyCoD')]
    sys.modules['PyCoD'] = pkg
from PyCoD import xanim as xa

manifest = json.loads(text('docs/perk_machine_presentation_manifest.json'))
for name, expected in manifest['files'].items():
    path = ROOT/name
    assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected, ('asset drift', name)
SHOTS = [(int(frame), hand) for frame, hand in manifest['shots']]
assert len(SHOTS) == 16, 'the fire clip carries sixteen shots'
assets = {name: fields for name, kind, fields in blocks(ROOT/'source_data/tod_perk_machines.gdt')}
assert set(assets) == set(CLIPS)


def notes(fields, prefix):
    result = []
    for key, action in fields.items():
        if re.fullmatch(prefix+r'\d+action', key) and action != 'None':
            base = key.removesuffix('action')
            result.append((int(fields.get(base+'frame', -1)), action,
                           fields.get(base+'actionparam1', ''), fields.get(base+'actionparam2', '')))
    return result


with (ROOT/'sound/aliases/tod_perk_machines.csv').open(newline='', encoding='utf-8-sig') as file:
    rows = list(csv.DictReader(file))
assert len(rows) == 14
aliases = {row['Name'] for row in rows}
assert len(aliases) == 5
assert sum(row['Name'] == 'evt_doubletap_purchase_shots' for row in rows) == 10
for row in rows:
    assert row['Storage'] == 'loaded' and row['PanType'] == '3d'
    with wave.open(str(ROOT/'sound_assets'/row['FileSpec'].replace('\\', '/'))) as wav:
        assert wav.getnframes() > 0 and wav.getsampwidth() == 2
szc = json.loads(text('sound/zoneconfig/zm_tod2_cybercity.szc'))
assert sum(s.get('Filename') == 'tod_perk_machines.csv' for s in szc['Sources']) == 1
for name, fields in assets.items():
    assert fields['looping'] == '0'
    for key in ('filename', 'model'):
        assert fields[key].replace('\\', '/').split('/')[0] == FOLDER, \
            (name, key, fields[key], 'a TOD II clip/model lives in ' + FOLDER + ' (the private tod_perk_machines model folder is a junction into map 1)')
    clip = xa.Anim()
    clip.LoadFile_Bin(str(ROOT/'xanim_export'/fields['filename'].replace('\\', '/')))
    assert clip.framerate == 30
    assert (ROOT/'model_export'/fields['model'].replace('\\', '/')).is_file()
    for prefix, limit in [('customnote', 50), ('fx_customnote', 20), ('sound_customnote', 20),
                          ('fx_shutdownnote', 10), ('sound_shutdownnote', 10)]:
        entries = notes(fields, prefix)
        assert len(entries) <= limit
        for frame, action, param, bone in entries:
            assert frame == -1 or 0 <= frame < len(clip.frames), (name, frame, len(clip.frames))
            assert 'FxOnObject@' not in param, ('inert BO6 FX string', name, param)
            if action in ('Sound', 'Stop Sound'):
                assert param in aliases, ('unbanked sound', name, param)
            if action in ('Play Fx', 'Kill Fx', 'Stop Fx'):
                assert (ROOT/'share/raw/fx'/param.replace('\\', '/')).is_file(), ('missing FX', param)
    print(name, len(clip.frames), 'frames at', clip.framerate, 'fps')
fire = assets['tod_doubletap_fire']
assert notes(fire, 'customnote') == [(frame, 'Self Notify', 'tod_doubletap_shot', 'j_pistol_'+hand+'_muzzle') for frame, hand in SHOTS]
shots = [entry for entry in notes(fire, 'sound_customnote') if entry[2] == 'evt_doubletap_purchase_shots']
flashes = [entry for entry in notes(fire, 'fx_customnote') if 'doubletap_muzzle' in entry[2]]
assert [entry[0] for entry in shots] == [frame for frame, hand in SHOTS]
assert [(entry[0], entry[3]) for entry in flashes] == [(frame, 'j_pistol_'+hand) for frame, hand in SHOTS]
assert sum(entry[2] == 'evt_doubletap_purchase_loop' for entry in notes(fire, 'sound_customnote')) == 1
# map 1, 2026-09-23 (v19.44): the volley is SCHEDULED in script from the clip's start on these
# same frames (the clip's script notes wake the AnimScripted done-notify instead of reaching a
# listener), so the GSC frame table is pinned to the shot table.
gsc = text(GSC)
table = re.search(r'function volley_frames\(\)\s*\{\s*return array\(([^)]*)\);', gsc)
assert table, 'volley_frames() table missing from _tod_perk_anims.gsc'
assert [int(v) for v in table.group(1).split(',')] == [frame for frame, hand in SHOTS], 'GSC shot frames drifted from the manifest shots'
assert [hand for frame, hand in SHOTS] == ['le' if i % 2 == 0 else 'ri' for i in range(len(SHOTS))], \
    'shots no longer alternate left/right from the left pistol; volley_muzzle() assumes that'
assert 'waittill( done, note )' in gsc and 'if ( note == "end" ) break;' in gsc, 'a clip must finish only on the "end" note'
assert notes(assets['tod_wisp_activate'], 'sound_customnote')[0][2] == 'ff13a722f5a3c511'
zone = text('zone_source/zm_tod2_cybercity.zone')
tree = text('animtrees/tod_perk_machines.atr')
for name in assets:
    assert 'xanim,'+name in zone and name in tree
for name in REPLACED_CLIPS:
    assert 'xanim,'+name not in zone and name not in tree, ('replaced donor clip still zoned / in the tree', name)
for name in FX:
    assert 'fx,'+name in zone, ('clip cue effect not zoned', name)
assert 't10_zm_machine_d_mod_bullet' not in zone, 'No new weapon registration is needed'
sync = text('tools/sync_to_modtools.ps1')
for tree_name in ('model_export', 'xanim_export'):
    assert sync.count('"' + tree_name + '\\' + FOLDER + '"') == 2, ('sync row missing', tree_name + '\\' + FOLDER)
print('Perk machine assets pass: 16 paired shots/FX/sounds, interruption cleanup, finite clips, 14 WAVs, '
      'loaded alias source, map-owned ' + FOLDER + ' clips + models synced, replaced donor clips unzoned.')
