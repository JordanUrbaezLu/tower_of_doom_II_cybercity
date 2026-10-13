#!/usr/bin/env python3
"""make_punch_aliases.py -- sound/aliases/tod_warrior.csv from the T7 pack's one_inch_punch.csv.

Rows kept verbatim (same mix, no context columns -- the Hellbound water/ringoff
trap does not apply): the whoosh pair wpn_one_inch_punch_plr/npc, the two
first-raise stings. Derived rows: tod_punch_hit_plr/npc (the body hits, a 2D
player copy added), tod_punch_surface_plr/npc (the wall thud). Those are the
names tod_punch_sounds (source_data/tod_warrior_punch.gdt) binds. Re-run after
any edit; never hand-edit the CSV.
"""
import os, subprocess, tempfile, shutil, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAR = os.path.join(os.path.expanduser('~'), 'Downloads', 'T7 Assets V2.8.rar')
SEVENZ = r'C:\Program Files\7-Zip\7z.exe'
MEMBER = r'T7 Assets V2.8\share\raw\sound\aliases\one_inch_punch.csv'
OUT = os.path.join(REPO, 'sound', 'aliases', 'tod_warrior.csv')

KEEP = {'wpn_one_inch_punch_npc', 'wpn_one_inch_punch_plr', 'zmb_oip_first_raise'}   # R5: zmb_oip_ugd_first_raise left with the Map 1 purge

# GRAVITY SMASH (the Warrior's lethal = the stock Gravity Spikes slam): the pack
# ships the slam's own wavs. Stock plays them through DLC1 aliases this map never
# loads, so they are re-authored here on the punch rows' mix. [alias, wav, kind]
GS_WAVS = [('tod_gs_start_plr',   r'wpn\hero\gravity_spikes\plr\swing\wpn_gravity_start_00.wav',       'plr'),
           ('tod_gs_hit_plr',     r'wpn\hero\gravity_spikes\plr\impact\wpn_gravity_hit_00.wav',        'plr'),
           ('tod_gs_hit_lfe_plr', r'wpn\hero\gravity_spikes\plr\impact\lfe\wpn_gravity_hit_lfe_00.wav', 'plr'),
           ('tod_gs_shockwave',   r'wpn\hero\gravity_spikes\shockwave\wpn_gravity_shockwave.wav',       'npc')]
WAV_DIR = os.path.join(REPO, 'sound_assets')


def main():
    tmp = tempfile.mkdtemp(prefix='tod_punch_snd_')
    try:
        members = [MEMBER] + ['T7 Assets V2.8\\sound_assets\\' + w for _, w, _ in GS_WAVS]
        subprocess.run([SEVENZ, 'x', '-y', '-o' + tmp, RAR] + members, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        lines = open(os.path.join(tmp, 'T7 Assets V2.8', 'share', 'raw', 'sound', 'aliases', 'one_inch_punch.csv'),
                     encoding='utf-8', errors='replace').read().replace('\r\n', '\n').split('\n')
        if '--check' not in sys.argv:
            for _, w, _ in GS_WAVS:
                src = os.path.join(tmp, 'T7 Assets V2.8', 'sound_assets', w)
                dst = os.path.join(WAV_DIR, w)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
        else:
            for _, w, _ in GS_WAVS:
                if not os.path.exists(os.path.join(WAV_DIR, w)):
                    print('make_punch_aliases --check: missing wav', w)
                    sys.exit(1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    header = lines[0].split(',')
    col = {n: i for i, n in enumerate(header)}
    out = [lines[0], '#TOD WARRIOR: One Inch Punch (T7 pack one_inch_punch.csv, tools/warrior/make_punch_aliases.py)']
    body_npc, other_npc, plr_row = [], None, None
    for l in lines[1:]:
        if not l or l.startswith('#'):
            continue
        cells = l.split(',')
        name = cells[col['Name']]
        if name in KEEP:
            out.append(l)
            if name == 'wpn_one_inch_punch_plr':
                plr_row = cells
        elif name == 'wpn_one_inch_punch_body':
            body_npc.append(cells)
        elif name == 'wpn_one_inch_punch_other':
            other_npc = cells

    def as_player(cells, new_name):
        # the player's own hit: 2D on the weapon pan, the mix of the whoosh's plr row
        c = list(cells)
        c[col['Name']] = new_name
        for k in ('VolMin', 'VolMax', 'DistMin', 'DistMaxDry', 'DistMaxWet', 'PanType', 'Pan', 'CenterSend',
                  'EnvelopMin', 'EnvelopMax', 'EnvelopPercent', 'LimitCount'):
            c[col[k]] = plr_row[col[k]]
        c[col['VolMin']] = c[col['VolMax']] = '88'
        return ','.join(c)

    def renamed(cells, new_name):
        c = list(cells)
        c[col['Name']] = new_name
        return ','.join(c)

    for cells in body_npc:
        out.append(renamed(cells, 'tod_punch_hit_npc'))
    for cells in body_npc:
        out.append(as_player(cells, 'tod_punch_hit_plr'))
    out.append(renamed(other_npc, 'tod_punch_surface_npc'))
    out.append(as_player(other_npc, 'tod_punch_surface_plr'))
    out.append('#TOD WARRIOR: Gravity Smash (T7 pack Gravity Spikes wavs)')
    for alias, wav, kind in GS_WAVS:
        c = list(other_npc)
        c[col['FileSpec']] = wav
        if kind == 'plr':
            row = as_player(c, alias)
        else:
            c[col['Name']] = alias
            c[col['DistMin']] = '400'
            c[col['DistMaxDry']] = c[col['DistMaxWet']] = '2200'
            c[col['VolMin']] = c[col['VolMax']] = '90'
            row = ','.join(c)
        out.append(row)
    text = '\n'.join(out) + '\n'
    if '--check' in sys.argv:
        ok = os.path.exists(OUT) and open(OUT, encoding='utf-8').read() == text
        print('make_punch_aliases --check', 'OK' if ok else 'STALE')
        sys.exit(0 if ok else 1)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print('wrote', os.path.relpath(OUT, REPO), len(out) - 2, 'rows')


if __name__ == '__main__':
    main()
