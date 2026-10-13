"""THE BATTLE ARENA's cues (docs/185 v2.1), GENERATED - never hand-edit the .wav files or tod_arena.csv.

  python -B tools/battle_arena/make_sounds.py           write sound_assets/tod/arena/*.wav + sound/aliases/tod_arena.csv
                                                        and register tod_arena.csv in sound/zoneconfig/zm_tod2_cybercity.szc
                                                        if it is missing (a copy of the tod_haven entry, placed after it)
  python -B tools/battle_arena/make_sounds.py --check   FAIL (exit 1) if a wav or the csv differs from a fresh render or
                                                        the zone config does not load tod_arena.csv
  python -B tools/battle_arena/make_sounds.py --out DIR a preview: the wavs only, into DIR (nothing in the repo is touched)

THE FOUR CUES (mono 48 kHz 16-bit; a 3D source must be mono). _tod_arena.gsc plays them:
  tod_arena_wave   2D  a wave begins: a low brass swell (detuned saws a fifth apart, opening as they rise) into a deep
                       drum hit - the horn of the pit
  tod_arena_clear  2D  a wave is cleared: two bright bell notes rising (E5 -> B5) over a short shimmer
  tod_arena_level  2D  the level is cleared: a three-note brass fanfare (A3 C#4 E4 -> A4 held) over a sub, with a
                       crystal tail
  tod_arena_gate   3D  a gate opens for an elite: a latch clack and a metal ring, a rising electric whine with a 50 Hz
                       shudder, ending in a heavy clank. Played AT the gate: the room tells you WHERE it comes from.

Synthesis is seeded numpy (scipy filters), so a fresh render is byte-identical. Every cue fades in and out (no clicks);
peaks at -1.5 dBFS. Alias rows ride BUS_FX with no context columns (the sound-context lint). These are synthesised
stand-ins made to the right length, shape and loudness; an authored set replaces them BY NAME (same files, same rows).

THE AUTHORED LANE (W2B / PK16, 2026-10-05): a cue listed in tools/battle_arena/authored_sounds.json (written by
tools/dealer_sfx/make_sounds.py: ElevenLabs takes, measured, composed and levelled) is an AUTHORED replacement BY NAME
(same file, same alias row). For such a cue --check pins the wav to the manifest's sha256 instead of a fresh render
(mono 48 kHz 16-bit, its length within 0.6..1.35x the stand-in's), and the write mode never overwrites it
with the stand-in. A cue NOT in the manifest is still byte-checked against the synthesis (the negative control: delete
its manifest row and the stand-in comes back on the next write). --out DIR always previews the synthesised stand-ins.
"""
import csv, io, json, pathlib, re, sys, wave

import numpy as np
from scipy import signal

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'sound_assets' / 'tod' / 'arena'
CSV_OUT = ROOT / 'sound' / 'aliases' / 'tod_arena.csv'
HEADER_FROM = ROOT / 'sound' / 'aliases' / 'tod_ui.csv'
SZC = ROOT / 'sound' / 'zoneconfig' / 'zm_tod2_cybercity.szc'
SR = 48000
SEED = 20261003
FIX = 'run: python tools/battle_arena/make_sounds.py'

# name -> (kind, volume, (distMin, distMaxDry, distMaxWet))
SOUNDS = {
    'tod_arena_wave':  ('2d', 86, None),
    'tod_arena_clear': ('2d', 82, None),
    'tod_arena_level': ('2d', 90, None),
    'tod_arena_gate':  ('3d', 96, (500, 2200, 2600)),
}


# THE AUTHORED LANE (W2B / PK16): cues replaced BY NAME with authored files, pinned by sha256 in this manifest
AUTHORED = pathlib.Path(__file__).resolve().with_name('authored_sounds.json')
AUTHORED_LEN = (0.6, 1.35)          # an authored file's length, as a fraction of the stand-in it replaces
AUTHORED_EXACT = {}   # cues the script times to the sample: the authored file must keep the length


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


# ---------------------------------------------------------------------------- building blocks (the haven's)
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


def room(y, rng, length=0.35, mix=0.18):
    """a bright decaying tail so a cue rings in the hall"""
    n = int(length * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (0.07 * SR))
    ir = signal.sosfilt(signal.butter(2, 1500, btype='highpass', fs=SR, output='sos'), ir)
    dry = np.concatenate([y, np.zeros(n)])
    wet = signal.fftconvolve(y, ir)[:len(dry)]
    wet = np.concatenate([wet, np.zeros(len(dry) - len(wet))])
    wet = wet / (np.max(np.abs(wet)) + 1e-9) * np.max(np.abs(y))
    return dry * (1 - mix) + wet * mix


def brass(t, f, amp):
    """three detuned saws, low-passed darker at the start and brighter as `amp` opens (a swelling horn)"""
    raw = signal.sawtooth(2 * np.pi * f * t) + 0.7 * signal.sawtooth(2 * np.pi * f * 1.004 * t) + 0.5 * signal.sawtooth(2 * np.pi * f * 0.996 * t)
    dark, bright = lowpass(raw, 420), lowpass(raw, 1900)
    y = (dark * (1 - 0.65 * amp) + bright * 0.65 * amp) * amp
    return y / (np.max(np.abs(y)) + 1e-9)


def bell(t, f, tau):
    y = tone(t, f) + 0.5 * tone(t, f * 2.76) + 0.28 * tone(t, f * 5.4) + 0.18 * tone(t, f * 1.005)
    return y * env_exp(t, 0.004, tau)


def place(n, start, piece):
    """drop `piece` into a zero buffer of n samples at `start` seconds"""
    out = np.zeros(n)
    i = int(start * SR)
    k = min(len(piece), n - i)
    if k > 0:
        out[i:i + k] = piece[:k]
    return out


# ---------------------------------------------------------------------------- the cues
def wave_horn(rng):
    t = t_axis(1.45)
    swell = np.clip(t / 0.55, 0, 1) ** 1.5 * np.exp(-np.maximum(t - 0.62, 0) / 0.34)
    horn = brass(t, 110, swell) + 0.8 * brass(t, 165, swell)
    hit = t_axis(0.8)
    thump = tone(hit, 50 + 36 * np.exp(-hit / 0.045)) * env_exp(hit, 0.003, 0.22)
    burst = bandnoise(rng, len(hit), 200, 3200) * env_exp(hit, 0.002, 0.07)
    y = 0.7 * horn + place(len(t), 0.58, 1.0 * thump + 0.35 * burst)
    return fades(norm(room(y, rng, 0.45, 0.14), -1.5), 0.01, 0.12)


def wave_clear(rng):
    t = t_axis(0.95)
    first = bell(t, 659.3, 0.30)
    second = place(len(t), 0.17, bell(t_axis(0.78), 987.8, 0.36))
    shimmer = place(len(t), 0.17, bandnoise(rng, int(0.5 * SR), 4000, 9000) * env_exp(t_axis(0.5), 0.01, 0.16))
    y = 0.8 * first + 1.0 * second + 0.18 * shimmer
    return fades(norm(room(y, rng, 0.4, 0.2), -1.5), 0.003, 0.08)


def level_fanfare(rng):
    t = t_axis(2.3)
    notes = [(220.0, 0.00, 0.26), (277.2, 0.22, 0.26), (329.6, 0.44, 0.30), (440.0, 0.70, 1.55)]
    y = np.zeros(len(t))
    for f, at, hold in notes:
        tt = t_axis(hold + 0.35)
        amp = np.clip(tt / 0.035, 0, 1) * np.where(tt < hold, 1.0, np.exp(-(tt - hold) / 0.12))
        y += place(len(t), at, brass(tt, f, amp))
    sub = place(len(t), 0.70, tone(t_axis(1.5), 55.0) * env_exp(t_axis(1.5), 0.02, 0.5))
    tail = place(len(t), 0.72, (bell(t_axis(1.5), 1760.0, 0.6) + 0.6 * bell(t_axis(1.5), 2637.0, 0.5)))
    y = 0.8 * y + 0.5 * sub + 0.16 * tail
    return fades(norm(room(y, rng, 0.55, 0.16), -1.5), 0.005, 0.15)


def gate_open(rng):
    t = t_axis(1.35)
    clack = bandnoise(rng, int(0.12 * SR), 1200, 6500) * env_exp(t_axis(0.12), 0.001, 0.014)
    ring = (tone(t_axis(0.5), 1820.0) + 0.5 * tone(t_axis(0.5), 2710.0)) * env_exp(t_axis(0.5), 0.002, 0.11)
    wt = t_axis(0.98)
    k = np.clip(wt / 0.9, 0, 1)
    f = 120 + (480 - 120) * k ** 1.4
    whine = lowpass(signal.sawtooth(2 * np.pi * np.cumsum(f) / SR), 2000) * (0.15 + 0.85 * k) * (0.7 + 0.3 * np.sin(2 * np.pi * 50 * wt))
    whine = whine / (np.max(np.abs(whine)) + 1e-9)
    clank = bandnoise(rng, int(0.35 * SR), 300, 5000) * env_exp(t_axis(0.35), 0.003, 0.06)
    clank_ring = (tone(t_axis(0.35), 240.0) + 0.6 * tone(t_axis(0.35), 640.0)) * env_exp(t_axis(0.35), 0.003, 0.16)
    y = place(len(t), 0.0, 0.7 * clack) + place(len(t), 0.0, 0.45 * ring) + place(len(t), 0.06, 0.65 * whine) \
        + place(len(t), 1.0, 1.0 * clank + 0.8 * clank_ring)
    return fades(norm(room(y, rng, 0.4, 0.15), -1.5), 0.002, 0.1)


RENDER = {'tod_arena_wave': wave_horn, 'tod_arena_clear': wave_clear, 'tod_arena_level': level_fanfare,
          'tod_arena_gate': gate_open}


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
    for name, (kind, vol, dist) in SOUNDS.items():
        r = [''] * len(header)
        r[col['Name']] = name
        r[col['FileSpec']] = 'tod\\arena\\' + name + '.wav'
        r[col['Template']] = 'UIN_MOD'
        r[col['VolMin']] = r[col['VolMax']] = str(vol)
        r[col['Bus']] = 'BUS_FX'
        if kind == '2d':
            r[col['PanType']] = '2d'
        else:
            r[col['DistMin']], r[col['DistMaxDry']], r[col['DistMaxWet']] = (str(d) for d in dist)
            r[col['PitchMin']] = r[col['PitchMax']] = '0'
            r[col['PanType']] = '3d'
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
    return any(isinstance(s, dict) and s.get('Type') == 'ALIAS' and str(s.get('Filename', '')).lower() == 'tod_arena.csv'
               for s in data.get('Sources', []))


def szc_register():
    """add the tod_arena ALIAS source if it is missing: a text copy of the tod_haven entry, placed right after it"""
    raw = SZC.read_bytes()
    bom = b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
    text = raw[len(bom):].decode('utf-8')
    if szc_loads(text):
        return False
    tpl = re.search(r'([ \t]*)(\{[^{}]*"Filename"\s*:\s*"tod_haven\.csv"[^{}]*\})', text)
    if not tpl:
        raise SystemExit('ARENA SOUNDS: no tod_haven entry in %s to copy - add the tod_arena ALIAS source by hand' % SZC)
    nl = '\r\n' if '\r\n' in text else '\n'
    clone = tpl.group(2).replace('"tod_haven.csv"', '"tod_arena.csv"').replace('"tod_haven"', '"tod_arena"')
    new = text[:tpl.end()] + ',' + nl + tpl.group(1) + clone + text[tpl.end():]
    if not szc_loads(new):
        raise SystemExit('ARENA SOUNDS: %s would not parse with tod_arena added - left untouched' % SZC)
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
                print('ARENA SOUND PREVIEW', out_dir / p.name, '%.2f s' % ((len(b) - 44) / 2 / SR))
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
            bad.append('sound/zoneconfig/zm_tod2_cybercity.szc does not load tod_arena.csv')
        if bad:
            print('ARENA SOUNDS STALE: ' + '; '.join(bad) + ' - ' + FIX)
            sys.exit(1)
        print('ARENA SOUNDS OK: %d cues (%d authored, sha-pinned; %d synthesised, byte-checked)' % (len(RENDER), len(auth), len(RENDER) - len(auth)))
        return
    auth = authored()
    for p, b in files.items():
        if p.suffix == '.wav' and p.stem in auth:
            print('authored  %s  (kept: %s)' % (p.relative_to(ROOT), ' '.join(authored_problems(p, auth[p.stem], (len(b) - 44) / 2 / SR)) or 'sha matches'))
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        same = p.exists() and p.read_bytes() == b
        if not same:
            p.write_bytes(b)
        dur = (len(b) - 44) / 2 / SR if p.suffix == '.wav' else 0
        print('%s %s  %d B%s' % ('unchanged' if same else 'wrote', p.relative_to(ROOT), len(b), ('  %.2f s' % dur) if dur else ''))
    if szc_register():
        print('ARENA SOUNDS: registered tod_arena.csv in sound/zoneconfig/zm_tod2_cybercity.szc')


if __name__ == '__main__':
    main()
