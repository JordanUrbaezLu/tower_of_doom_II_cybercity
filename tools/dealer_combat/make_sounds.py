"""Dedicated Dealer weapon cues. Two authored takes per cue; measured, selected, pinned.

Generate only into the scratch stage. --check never calls an API. No voice changes.
"""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools/black_market_vo'))
spec = importlib.util.spec_from_file_location('dc_sound_dsp', REPO / 'tools/dealer_sfx/make_sounds.py')
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)
WORK = REPO / 'tmp/dealer_combat_audio'
OUT = pathlib.Path('sound_assets/tod/dealer_combat')
CUES = {
    'warning': (1.8, -20, '2d', 'A menacing electrical weapon charging: a thin rising capacitor whine with rapid red-hot sparking ticks, crescendo then abrupt stop. Dark science fiction, one continuous build, no initial impact, no voice, no music.'),
    'burst_tell': (1.3, -19, '2d', 'A heavy machine gun bolt racks with a cold sharp metallic clack, followed by an ominous short rising servo whine. One ready-to-fire warning, close and dry, no shots, no music, no voice.'),
    'shock': (.65, -16, '3d', 'A violent high-voltage lightning discharge: one sharp electrical crack, thick crackling arc and short bass thud, with a very brief sizzling tail. Close and punchy science fiction weapon, no voice, no music.'),
    'shot': (.28, -18, '3d', 'One single heavy belt-fed machine gun shot, a deep dry concussive report with a short metallic bolt clatter. Absolutely one shot only, no burst, no voice, no music.'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def csv_bytes():
    header = (REPO / 'sound/aliases/tod_ui.csv').read_text(encoding='utf-8-sig').splitlines()[0]
    fields = next(csv.reader([header]))
    out = io.StringIO(newline='')
    w = csv.DictWriter(out, fieldnames=fields, lineterminator='\r\n')
    w.writeheader()
    for key, (_, _, pan, _) in CUES.items():
        w.writerow(dict(Name='tod_dc_'+key, Storage='loaded', FileSpec='tod\\dealer_combat\\tod_dc_'+key+'.wav',
                        Template='UIN_MOD', Bus='BUS_FX', VolMin='88', VolMax='88', PanType=pan,
                        DistMin='200', DistMaxDry='2800', DistMaxWet='3200', Looping='NONLOOPING',
                        LimitCount='6', LimitType='oldest', EntityLimitCount='1', EntityLimitType='oldest',
                        Pauseable='yes', StopOnEntDeath='yes'))
    return out.getvalue().encode('utf-8')


def generate(root):
    import eleven
    WORK.mkdir(parents=True, exist_ok=True)
    dest = root / OUT
    dest.mkdir(parents=True, exist_ok=True)
    man = {}
    for key, (seconds, loudness, pan, prompt) in CUES.items():
        options = []
        for i in range(2):
            path = WORK / ('%s_take%d.pcm' % (key, i+1))
            if not path.exists():
                raw = eleven.call('POST', '/v1/sound-generation', body=dict(text=prompt,
                    duration_seconds=max(.5, seconds), prompt_influence=.65, model_id='eleven_text_to_sound_v2'),
                    query={'output_format': 'pcm_48000'})
                path.write_bytes(raw)
            x = np.frombuffer(path.read_bytes(), dtype='<i2').astype(np.float64) / 32768
            # pcm_48000 from this endpoint is interleaved stereo (the established Dealer SFX lane).
            x = (x[0::2] + x[1::2]) * .5
            n = int(seconds * D.SR)
            x = x[:n]
            if len(x) < n:
                x = np.pad(x, (0, n-len(x)))
            x -= np.mean(x)
            if key == 'warning':
                # Ascending tension even if the provider puts its loudest transient first.
                x *= np.linspace(.16, 1, len(x))
            x = D.fades(x, .008, .025 if key != 'warning' else .009)
            x = D.level_to(x, loudness)
            env = D.envelope(x)
            score = float(np.max(env)) / (float(np.mean(env)) + 1e-8)
            if key == 'warning':
                score = float(np.mean(env[-max(1, len(env)//4):])) / (float(np.mean(env[:max(1, len(env)//4)])) + 1e-8)
            options.append((score, x, path.name))
        _, x, take = max(options, key=lambda item: item[0])
        raw = D.encode(x)
        name = 'tod_dc_' + key + '.wav'
        (dest / name).write_bytes(raw)
        man[key] = dict(file=name, sha256=sha(raw), take=take, seconds=len(x)/D.SR,
                        lufs=D.lufs(x), peak_db=float(20*np.log10(np.max(np.abs(x))+1e-12)), prompt=prompt)
    (dest / 'manifest.json').write_text(json.dumps(man, indent=2))
    (root / 'sound/aliases').mkdir(parents=True, exist_ok=True)
    (root / 'sound/aliases/tod_dealer_combat.csv').write_bytes(csv_bytes())
    print('DEALER WEAPON SOUNDS: four cues authored and measured; no voice changed')


def check(root):
    import wave
    man = json.loads((root / OUT / 'manifest.json').read_text())
    assert set(man) == set(CUES)
    for key, entry in man.items():
        path = root / OUT / entry['file']
        assert sha(path.read_bytes()) == entry['sha256'], key + ' hash'
        with wave.open(str(path)) as w:
            assert (w.getnchannels(), w.getframerate(), w.getsampwidth()) == (1, 48000, 2)
            assert abs(w.getnframes()/48000-CUES[key][0]) < .01
            samples = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2')
            assert np.max(np.abs(samples.astype(np.int32))) <= 27600
    assert (root / 'sound/aliases/tod_dealer_combat.csv').read_bytes() == csv_bytes()
    print('DEALER WEAPON SOUNDS OK: 4 pinned mono cues; length, peaks and aliases pass')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=pathlib.Path, default=REPO)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    check(args.root) if args.check else generate(args.root)
