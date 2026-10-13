"""THE DEALER'S HOUSE cues (docs/207), GENERATED - never hand-edit the .wav files or tod_house.csv.

  python -B tools/dealer_house/make_sounds.py           write sound_assets/tod/house/*.wav + sound/aliases/tod_house.csv
                                                        and register tod_house.csv in sound/zoneconfig/zm_tod2_cybercity.szc
                                                        if it is missing (a copy of the tod_arena entry, placed after it)
  python -B tools/dealer_house/make_sounds.py --check   FAIL (exit 1) if a wav or the csv differs from a fresh render or
                                                        the zone config does not load tod_house.csv
  python -B tools/dealer_house/make_sounds.py --out DIR a preview: the wavs only, into DIR (nothing in the repo is touched)

THE THREE CUES (mono 48 kHz 16-bit). _tod_house.gsc / _tod_shop.gsc play them, all 2D on the player's own client:
  tod_house_cursed  the last roll lands on CURSED: a reversed sour swell sucked into a dead thud, a glass crack, a low
                    falling tone (the jackpot's bell gone wrong)
  tod_house_drain   the corrupted dome drains the party: a low rising drone with a heartbeat that quickens as the
                    health goes, faded at the end (6.5 s: the drain's length plus a breath)
  tod_house_cut     one step of the drain (a tenth of a player's health): a short dark electrical bite with a falling
                    pitch; played at every step with the HUD flicker

Synthesis is seeded numpy (scipy filters), so a fresh render is byte-identical. Every cue fades in and out (no clicks);
peaks at -1.5 dBFS. Alias rows ride BUS_FX with no context columns (the sound-context lint). These are synthesised cues
made to the right length, shape and loudness; an authored set replaces them BY NAME (same files, same rows).

THE AUTHORED LANE (W2B / PK16, 2026-10-05): a cue listed in tools/dealer_house/authored_sounds.json (written by
tools/dealer_sfx/make_sounds.py: ElevenLabs takes, measured, composed and levelled) is an AUTHORED replacement BY NAME
(same file, same alias row). For such a cue --check pins the wav to the manifest's sha256 instead of a fresh render
(mono 48 kHz 16-bit, its length within 0.6..1.35x the stand-in's; a cue the script times to the sample keeps it exactly), and the write mode never overwrites it
with the stand-in. A cue NOT in the manifest is still byte-checked against the synthesis (the negative control: delete
its manifest row and the stand-in comes back on the next write). --out DIR always previews the synthesised stand-ins.
"""
import csv, io, json, pathlib, re, sys, wave

import numpy as np
from scipy import signal

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'sound_assets' / 'tod' / 'house'
CSV_OUT = ROOT / 'sound' / 'aliases' / 'tod_house.csv'
HEADER_FROM = ROOT / 'sound' / 'aliases' / 'tod_ui.csv'
SZC = ROOT / 'sound' / 'zoneconfig' / 'zm_tod2_cybercity.szc'
SR = 48000
SEED = 20261004
FIX = 'run: python -B tools/dealer_house/make_sounds.py'

# name -> (pan, volume)
SOUNDS = {
    'tod_house_cursed': ('2d', 92),
    'tod_house_drain':  ('2d', 80),
    'tod_house_cut':    ('2d', 86),
}


# THE AUTHORED LANE (W2B / PK16): cues replaced BY NAME with authored files, pinned by sha256 in this manifest
AUTHORED = pathlib.Path(__file__).resolve().with_name('authored_sounds.json')
AUTHORED_LEN = (0.6, 1.35)          # an authored file's length, as a fraction of the stand-in it replaces
AUTHORED_EXACT = {'tod_house_drain': 6.5}   # cues the script times to the sample: the authored file must keep the length


def authored():
    """{wav stem: {sha256, secs}} for every cue an authored file replaces ({} when nothing is authored)"""
    if not AUTHORED.exists():
        return {}
    return json.loads(AUTHORED.read_text(encoding='utf-8')).get('files', {})


def authored_problems(path, pin, standin_secs):
    """-> what is wrong with one authored wav (missing, changed since its manifest, wrong format, wrong length)"""
    import hashlib
    rel = str(path.relative_to(ROOT))
    if not path.exists():
        return [rel + ' (authored) is missing - run: python tools/dealer_sfx/make_sounds.py pick']
    b = path.read_bytes()
    out = []
    if hashlib.sha256(b).hexdigest() != pin.get('sha256'):
        out.append(rel + ' (authored) differs from %s (re-pick it: python tools/dealer_sfx/make_sounds.py pick)' % AUTHORED.name)
    with wave.open(io.BytesIO(b)) as w:
        if (w.getnchannels(), w.getframerate(), w.getsampwidth()) != (1, SR, 2):
            out.append(rel + ' (authored) is not mono 48 kHz 16-bit')
        secs = w.getnframes() / float(SR)
    want = AUTHORED_EXACT.get(path.stem)
    if want is not None and abs(secs - want) > 0.0015:
        out.append('%s (authored) is %.3f s, the script times it to %.3f s' % (rel, secs, want))
    elif not (AUTHORED_LEN[0] * standin_secs <= secs <= AUTHORED_LEN[1] * standin_secs):
        out.append('%s (authored) is %.2f s, outside %.2f..%.2f x the %.2f s stand-in' % (rel, secs, AUTHORED_LEN[0], AUTHORED_LEN[1], standin_secs))
    return out


# ---------------------------------------------------------------------------- building blocks (the arena's)
def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def env_exp(t, attack, tau):
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / tau)


def bandnoise(rng, n, lo, hi, order=4):
    x = rng.standard_normal(n)
    sos = signal.butter(order, [lo, hi], btype='bandpass', fs=SR, output='sos')
    y = signal.sosfilt(sos, x)
    return y / (np.max(np.abs(y)) + 1e-9)


def tone(t, f):
    """a sine at a frequency that may vary per sample (phase integrated, never f * t)"""
    f = np.broadcast_to(f, t.shape)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def fades(y, fin=0.004, fout=0.03):
    n_in, n_out = int(fin * SR), int(fout * SR)
    y = y.copy()
    y[:n_in] *= np.linspace(0, 1, n_in)
    y[-n_out:] *= np.linspace(1, 0, n_out)
    return y


def norm(y, peak_db):
    return y / (np.max(np.abs(y)) + 1e-12) * (10 ** (peak_db / 20))


def lowpass(y, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, fs=SR, output='sos'), y)


def place(n, start, piece):
    out = np.zeros(n)
    i = int(start * SR)
    k = min(len(piece), n - i)
    if k > 0:
        out[i:i + k] = piece[:k]
    return out


def bell(t, f, tau):
    y = tone(t, f) + 0.5 * tone(t, f * 2.76) + 0.28 * tone(t, f * 5.4) + 0.18 * tone(t, f * 1.005)
    return y * env_exp(t, 0.004, tau)


# ---------------------------------------------------------------------------- the cues
def cursed(rng):
    t = t_axis(1.7)
    # the jackpot's bell, reversed and bent flat: a swell that sucks in over 0.55 s
    bt = t_axis(0.55)
    swell = (bell(bt, 587.3 * 0.97, 0.5) + 0.7 * bell(bt, 466.2, 0.5))[::-1] * np.linspace(0.2, 1, len(bt)) ** 1.6
    # the dead thud at 0.55: a sub knock with a quick pitch fall
    kt = t_axis(0.9)
    thud = tone(kt, 48 + 70 * np.exp(-kt / 0.03)) * env_exp(kt, 0.002, 0.18)
    knock = lowpass(bandnoise(rng, len(kt), 60, 900), 700) * env_exp(kt, 0.001, 0.05)
    # the glass crack a hair after, and a low tone falling a fourth under the tail
    ct = t_axis(0.45)
    crack = bandnoise(rng, len(ct), 2500, 9000) * env_exp(ct, 0.001, 0.025) + 0.5 * bandnoise(rng, len(ct), 900, 3000) * env_exp(ct, 0.001, 0.06)
    ft = t_axis(1.1)
    fall = lowpass(signal.sawtooth(2 * np.pi * np.cumsum(140 * (1 - 0.25 * np.clip(ft / 0.9, 0, 1))) / SR), 900) * env_exp(ft, 0.01, 0.45)
    y = place(len(t), 0.0, 0.6 * swell) + place(len(t), 0.55, 1.0 * thud + 0.5 * knock) + place(len(t), 0.58, 0.55 * crack) + place(len(t), 0.6, 0.45 * fall)
    return fades(norm(y, -1.5), 0.005, 0.12)


def drain(rng):
    t = t_axis(6.5)
    k = np.clip(t / 6.0, 0, 1)
    # the drone: two detuned low saws rising a fifth over the drain, darker at the start
    f = 55 * (1 + 0.5 * k ** 1.3)
    saw = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) + 0.8 * signal.sawtooth(2 * np.pi * np.cumsum(f * 1.007) / SR)
    # the filter opens as the drain goes: a dark copy and a bright copy blended by k (the arena's brass trick)
    dark, bright = lowpass(saw, 320), lowpass(saw, 1300)
    drone = (dark * (1 - k) + bright * k) * (0.35 + 0.65 * k)
    drone = drone / (np.max(np.abs(drone)) + 1e-9)
    # the heartbeat: a double knock whose period shortens from 1.0 s to 0.45 s
    beats = np.zeros(len(t))
    at = 0.2
    while at < 6.0:
        period = 1.0 - 0.55 * np.clip(at / 6.0, 0, 1)
        for off, amp in ((0.0, 1.0), (0.14, 0.7)):
            bt = t_axis(0.3)
            kick = tone(bt, 42 + 40 * np.exp(-bt / 0.04)) * env_exp(bt, 0.002, 0.09) * amp
            beats += place(len(t), at + off, kick)
        at += period
    # a whispering band of noise that swells with the drone
    hiss = bandnoise(rng, len(t), 1800, 5200) * (0.05 + 0.25 * k ** 2)
    y = 0.75 * drone + 0.9 * beats + 0.35 * hiss
    y *= np.where(t < 6.0, 1.0, np.exp(-(t - 6.0) / 0.18))
    return fades(norm(y, -1.5), 0.08, 0.25)


def cut(rng):
    t = t_axis(0.38)
    f = 420 * (1 - 0.55 * np.clip(t / 0.3, 0, 1))
    buzz = lowpass(signal.square(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 95 * t)), 2600) * env_exp(t, 0.002, 0.11)
    zap = bandnoise(rng, len(t), 1200, 7000) * env_exp(t, 0.001, 0.03)
    sub = tone(t, 70) * env_exp(t, 0.003, 0.08)
    y = 0.8 * buzz / (np.max(np.abs(buzz)) + 1e-9) + 0.5 * zap + 0.6 * sub
    return fades(norm(y, -1.5), 0.002, 0.06)


RENDER = {'tod_house_cursed': cursed, 'tod_house_drain': drain, 'tod_house_cut': cut}


# ---------------------------------------------------------------------------- files
def wav_bytes(y):
    pcm = np.clip(np.round(y * 32767), -32768, 32767).astype('<i2')
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return buf.getvalue()


def alias_csv():
    header_line = HEADER_FROM.read_text(encoding='utf-8-sig').splitlines()[0]
    header = next(csv.reader([header_line]))
    col = {h: i for i, h in enumerate(header)}
    lines = [header_line]
    for name, (kind, vol) in SOUNDS.items():
        r = [''] * len(header)
        r[col['Name']] = name
        r[col['FileSpec']] = 'tod\\house\\' + name + '.wav'
        r[col['Template']] = 'UIN_MOD'
        r[col['VolMin']] = r[col['VolMax']] = str(vol)
        r[col['Bus']] = 'BUS_FX'
        r[col['PanType']] = kind
        r[col['Looping']] = 'NONLOOPING'
        assert not any(c in v for v in r for c in ',"\r\n'), name + ': a field would need csv quoting'
        lines.append(','.join(r))
    return ('\r\n'.join(lines) + '\r\n').encode('utf-8')


def render():
    files = {}
    for i, (name, fn) in enumerate(RENDER.items()):
        rng = np.random.default_rng(SEED + i)
        files[OUT / (name + '.wav')] = wav_bytes(fn(rng))
    files[CSV_OUT] = alias_csv()
    return files


def szc_loads(text):
    try:
        data = json.loads(text)
    except ValueError:
        return False
    return any(isinstance(s, dict) and s.get('Type') == 'ALIAS' and str(s.get('Filename', '')).lower() == 'tod_house.csv'
               for s in data.get('Sources', []))


def szc_register():
    """add the tod_house ALIAS source if it is missing: a text copy of the tod_arena entry, placed right after it"""
    raw = SZC.read_bytes()
    bom = b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
    text = raw[len(bom):].decode('utf-8')
    if szc_loads(text):
        return False
    tpl = re.search(r'([ \t]*)(\{[^{}]*"Filename"\s*:\s*"tod_arena\.csv"[^{}]*\})', text)
    if not tpl:
        raise SystemExit('HOUSE SOUNDS: no tod_arena entry in %s to copy - add the tod_house ALIAS source by hand' % SZC)
    nl = '\r\n' if '\r\n' in text else '\n'
    clone = tpl.group(2).replace('"tod_arena.csv"', '"tod_house.csv"').replace('"tod_arena"', '"tod_house"')
    new = text[:tpl.end()] + ',' + nl + tpl.group(1) + clone + text[tpl.end():]
    if not szc_loads(new):
        raise SystemExit('HOUSE SOUNDS: %s would not parse with tod_house added - left untouched' % SZC)
    SZC.write_bytes(bom + new.encode('utf-8'))
    return True


def main():
    files = render()
    if '--out' in sys.argv:
        out_dir = pathlib.Path(sys.argv[sys.argv.index('--out') + 1])
        out_dir.mkdir(parents=True, exist_ok=True)
        for p, b in files.items():
            if p.suffix == '.wav':
                (out_dir / p.name).write_bytes(b)
                print('HOUSE SOUND PREVIEW', out_dir / p.name, '%.2f s' % ((len(b) - 44) / 2 / SR))
        return
    if '--check' in sys.argv:
        auth = authored()
        bad = []
        for p, b in files.items():
            if p.suffix == '.wav' and p.stem in auth:
                bad += authored_problems(p, auth[p.stem], (len(b) - 44) / 2 / SR)
            elif not p.exists() or p.read_bytes() != b:
                bad.append(str(p.relative_to(ROOT)))
        if not SZC.exists() or not szc_loads(SZC.read_bytes().decode('utf-8-sig')):
            bad.append('sound/zoneconfig/zm_tod2_cybercity.szc does not load tod_house.csv')
        if bad:
            print('HOUSE SOUNDS STALE: ' + '; '.join(bad) + ' - ' + FIX)
            sys.exit(1)
        print('HOUSE SOUNDS OK: %d cues (%d authored, sha-pinned) + tod_house.csv match the generator; the zone config loads them' % (len(SOUNDS), len(auth)))
        return
    OUT.mkdir(parents=True, exist_ok=True)
    auth = authored()
    for p, b in files.items():
        if p.suffix == '.wav' and p.stem in auth:
            print('authored', p.relative_to(ROOT), '(kept: %s)' % (' '.join(authored_problems(p, auth[p.stem], (len(b) - 44) / 2 / SR)) or 'sha matches'))
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
        print('wrote', p.relative_to(ROOT), '' if p.suffix != '.wav' else '%.2f s' % ((len(b) - 44) / 2 / SR))
    if szc_register():
        print('HOUSE SOUNDS: registered tod_house.csv in sound/zoneconfig/zm_tod2_cybercity.szc')


if __name__ == '__main__':
    main()
