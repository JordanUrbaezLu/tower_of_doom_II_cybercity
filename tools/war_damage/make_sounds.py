"""THE WAR DAMAGE PASS (docs/205): the war's sounds, GENERATED - never hand-edit the wavs or tod_war.csv.

  python tools/war_damage/make_sounds.py           write sound_assets/tod/war/*.wav + sound/aliases/tod_war.csv
  python tools/war_damage/make_sounds.py --check   FAIL if any written file differs from a fresh render
  TOD_WAR_STAGE=<dir> writes everything under <dir> instead (a staged copy)

The alias file is in the exact column layout of a working map alias file (sound/aliases/tod_sky.csv, its first row as
the template). Two rows point at STOCK wavs already in the private tools root (phase 1); the rest are rendered here
(mono 48 kHz 16-bit: 3D sources must be mono; seeded numpy / scipy, so a fresh render is byte-identical):

  tod_war_fire_lp       amb/fire/small/small.wav          fire crackle on the rubble fires (stock)
  tod_war_spark_lp      chr/robot/sparking_lp.wav         a live cable buzzing and spitting (stock)
  tod_war_tube_lp       LOOPING 3D  a broken LED tube's drive buzzing: a 120 Hz hum with a 60 Hz beat, a fizz, ticks
  tod_war_arc_lp        LOOPING 3D  the torn conductors arcing: a harsh buzz, dense crackle, a sizzle
  tod_war_far_boom_a/b/c   3D       a detonation far over the horizon: the user's large explosion (tod_c4_explode.wav)
                                    pitched down, low-passed (air absorbs the top), a long rolling tail; a < b < c
  tod_war_far_guns_a/b     3D       a far heavy gun rattling off a burst: thumps + cracks, muffled, in a room of air
  tod_war_wreck_impact     3D       a stricken ship hitting the city: two explosions a fifth apart, burning debris, a tail
The far rows carry DistMin 3000 / DistMaxDry ~30,000: they play from a point 7,000-11,600 units out and must carry.
"""
import csv, io, os, pathlib, sys, wave

import numpy as np
from scipy import signal

ROOT = pathlib.Path(__file__).resolve().parents[2]
STAGE = pathlib.Path(os.environ['TOD_WAR_STAGE']) if os.environ.get('TOD_WAR_STAGE') else None
OUT = (STAGE / 'sound_assets/tod/war') if STAGE else ROOT / 'sound_assets/tod/war'
CSV_OUT = (STAGE / 'tod_war.csv') if STAGE else ROOT / 'sound/aliases/tod_war.csv'
TEMPLATE_FROM = ROOT / 'sound/aliases/tod_sky.csv'
C4 = ROOT / 'sound_assets/tod/sfx/tod_c4_explode.wav'                           # the user's "explosion large distant"
FIREY = pathlib.Path(r'C:\BO3Tools\TOD2Cybercity\sound_assets\exp\firey\exp_firey_01.wav')   # stock burning debris
STOCK_WAVS = pathlib.Path(r'C:\BO3Tools\TOD2Cybercity\sound_assets')
SR = 48000
SEED = 20261003
BS = chr(92)   # a literal backslash: alias FileSpecs are Windows paths

# name -> (FileSpec, VolMin, VolMax, DistMin, DistMaxDry, DistMaxWet, PitchMin, PitchMax, Looping)
ALIASES = [
    ('tod_war_fire_lp',      BS.join(['amb', 'fire', 'small', 'small.wav']), 74, 78, 110, 1100, 1250, -60, 60, 'LOOPING'),
    ('tod_war_spark_lp',     BS.join(['chr', 'robot', 'sparking_lp.wav']), 64, 68, 70, 800, 950, -80, 80, 'LOOPING'),
    ('tod_war_tube_lp',      BS.join(['tod', 'war', 'tod_war_tube_lp.wav']), 54, 58, 40, 420, 520, 0, 0, 'LOOPING'),
    ('tod_war_arc_lp',       BS.join(['tod', 'war', 'tod_war_arc_lp.wav']), 62, 66, 50, 540, 660, -40, 40, 'LOOPING'),
    ('tod_war_far_boom_a',   BS.join(['tod', 'war', 'tod_war_far_boom_a.wav']), 84, 88, 3000, 30000, 34000, -40, 40, 'NONLOOPING'),
    ('tod_war_far_boom_b',   BS.join(['tod', 'war', 'tod_war_far_boom_b.wav']), 86, 90, 3000, 30000, 34000, -40, 40, 'NONLOOPING'),
    ('tod_war_far_boom_c',   BS.join(['tod', 'war', 'tod_war_far_boom_c.wav']), 88, 92, 3000, 32000, 36000, -30, 30, 'NONLOOPING'),
    ('tod_war_far_guns_a',   BS.join(['tod', 'war', 'tod_war_far_guns_a.wav']), 76, 80, 3000, 26000, 30000, -40, 40, 'NONLOOPING'),
    ('tod_war_far_guns_b',   BS.join(['tod', 'war', 'tod_war_far_guns_b.wav']), 76, 80, 3000, 26000, 30000, -40, 40, 'NONLOOPING'),
    ('tod_war_wreck_impact', BS.join(['tod', 'war', 'tod_war_wreck_impact.wav']), 92, 95, 3000, 34000, 38000, -20, 20, 'NONLOOPING'),
]


# ---- synthesis helpers ---------------------------------------------------------------------------------------------------
def t_axis(sec):
    return np.arange(int(round(sec * SR))) / SR


def env_exp(t, attack, tau):
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / tau)


def bandnoise(rng, n, lo, hi, order=4):
    x = rng.standard_normal(n)
    y = signal.sosfilt(signal.butter(order, [lo, hi], btype='bandpass', fs=SR, output='sos'), x)
    return y / (np.max(np.abs(y)) + 1e-9)


def lowpass(y, fc, order=4):
    return signal.sosfilt(signal.butter(order, fc, fs=SR, output='sos'), y)


def highpass(y, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, btype='highpass', fs=SR, output='sos'), y)


def norm(y, peak_db):
    return y / (np.max(np.abs(y)) + 1e-12) * (10 ** (peak_db / 20))


def fades(y, fin=0.004, fout=0.03):
    n_in, n_out = int(fin * SR), int(fout * SR)
    y = y.copy()
    y[:n_in] *= np.linspace(0, 1, n_in)
    y[-n_out:] *= np.linspace(1, 0, n_out)
    return y


def seamless(y, xf=0.02):
    """A loop: the tail crossfades into the head so the seam is silent."""
    n = int(xf * SR)
    y = y.copy()
    w = np.linspace(0, 1, n)
    head = y[:n].copy()
    y[:n] = head * w + y[-n:] * (1 - w)
    return y[:-n]


def room(y, rng, length, tau, mix, fc=None):
    """A tail: an exponentially decaying noise impulse response (low-passed for far air), mixed under the dry sound."""
    n = int(length * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (tau * SR))
    if fc:
        ir = lowpass(ir, fc, 2)
    dry = np.concatenate([y, np.zeros(n)])
    wet = signal.fftconvolve(y, ir)[:len(dry)]
    wet = np.concatenate([wet, np.zeros(len(dry) - len(wet))])
    wet = wet / (np.max(np.abs(wet)) + 1e-9) * np.max(np.abs(y))
    return dry * (1 - mix) + wet * mix


def load_mono(p):
    w = wave.open(str(p))
    ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
    assert sw == 2, p
    x = np.frombuffer(w.readframes(n), np.int16).astype(np.float64) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
    return x


def pitch(x, semis):
    """Resample: a pitch change in semitones (down = longer)."""
    f = 2.0 ** (semis / 12.0)
    pos = np.arange(0, len(x) - 1, f)
    return np.interp(pos, np.arange(len(x)), x)


# ---- the sounds -------------------------------------------------------------------------------------------------------------
def tube_lp(rng):
    sec = 2.6                                                   # 312 cycles of 120 Hz, 156 of 60: the tones loop whole
    t = t_axis(sec)
    hum = np.zeros(len(t))
    for k in range(1, 9):
        hum += np.sin(2 * np.pi * 120 * k * t + k * 0.7) / (k ** 1.3)
    hum *= 1 + 0.25 * np.sin(2 * np.pi * 60 * t)
    hum = hum / np.max(np.abs(hum))
    fizz = bandnoise(rng, len(t), 3500, 9500) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t))
    ticks = np.zeros(len(t))
    for _ in range(6):
        k = int(rng.uniform(0, len(t) - SR * 0.01))
        w = int(SR * rng.uniform(0.002, 0.005))
        ticks[k:k + w] += rng.uniform(0.4, 1.0) * np.hanning(w)
    ticks = bandnoise(rng, len(t), 1800, 7000) * ticks
    y = 0.8 * hum + 0.09 * fizz + 0.35 * ticks
    return norm(seamless(y), -12.0)


def arc_lp(rng):
    sec = 1.8                                                   # 180 cycles of 100 Hz
    t = t_axis(sec)
    buzz = signal.sosfilt(signal.butter(2, [250, 3200], btype='bandpass', fs=SR, output='sos'), np.sign(np.sin(2 * np.pi * 100 * t)))
    buzz = buzz / (np.max(np.abs(buzz)) + 1e-9) * (0.7 + 0.3 * np.sin(2 * np.pi * 13 * t))
    clicks = np.zeros(len(t))
    k = 0
    while k < len(t):
        k += int(rng.exponential(SR / 70))
        if k < len(t):
            w = int(SR * rng.uniform(0.0015, 0.006))
            clicks[k:k + w] += rng.uniform(0.3, 1.0) * np.hanning(min(w, len(t) - k))
    crackle = bandnoise(rng, len(t), 1500, 7500) * clicks
    crackle = crackle / (np.max(np.abs(crackle)) + 1e-9)
    sizzle = bandnoise(rng, len(t), 5000, 11000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 25 * t)))
    y = 0.5 * buzz + 0.75 * crackle + 0.18 * sizzle
    return norm(seamless(y), -9.0)


def far_boom(rng, semis, fc, tail, tau, mix):
    x = pitch(load_mono(C4), semis)
    y = lowpass(x, fc, 4)
    y = room(y, rng, tail, tau, mix, fc=min(1200, fc * 1.5))
    return fades(norm(y, -3.0), 0.005, 0.4)


def far_guns(rng, n, rate, fc, tail):
    sec = n / rate + tail + 0.2
    t = t_axis(sec)
    y = np.zeros(len(t))
    at = 0.05
    for i in range(n):
        k = int(at * SR)
        seg = t[:int(0.12 * SR)]
        thump = np.sin(2 * np.pi * (95 - 35 * np.clip(seg / 0.06, 0, 1)) * seg) * env_exp(seg, 0.002, 0.035)
        crack = bandnoise(rng, len(seg), 600, 2600) * env_exp(seg, 0.001, 0.012)
        shot = (0.9 * thump + 0.6 * crack) * rng.uniform(0.75, 1.0)
        y[k:k + len(seg)] += shot[:len(y) - k]
        at += (1.0 / rate) * rng.uniform(0.94, 1.06)
    y = lowpass(y, fc, 3)
    y = room(y, rng, tail, 0.5, 0.35, fc=1800)
    return fades(norm(y, -6.0), 0.003, 0.3)


def wreck_impact(rng):
    a = pitch(load_mono(C4), -5)
    b = pitch(load_mono(C4), -11) * 0.8
    f = pitch(load_mono(FIREY), -4) * 0.55 if FIREY.exists() else np.zeros(1)
    n = max(len(a), len(b) + int(0.07 * SR), len(f) + int(0.12 * SR))
    y = np.zeros(n)
    y[:len(a)] += a
    y[int(0.07 * SR):int(0.07 * SR) + len(b)] += b
    y[int(0.12 * SR):int(0.12 * SR) + len(f)] += f
    y = lowpass(y, 1200, 3)
    y = room(y, rng, 4.0, 1.2, 0.5, fc=900)
    return fades(norm(y, -2.0), 0.004, 0.5)


RENDER = {
    'tod_war_tube_lp': tube_lp,
    'tod_war_arc_lp': arc_lp,
    'tod_war_far_boom_a': lambda rng: far_boom(rng, -3, 800, 3.0, 0.9, 0.42),
    'tod_war_far_boom_b': lambda rng: far_boom(rng, -6, 550, 3.6, 1.1, 0.48),
    'tod_war_far_boom_c': lambda rng: far_boom(rng, -9, 380, 4.5, 1.4, 0.55),
    'tod_war_far_guns_a': lambda rng: far_guns(rng, 11, 11.5, 1400, 1.0),
    'tod_war_far_guns_b': lambda rng: far_guns(rng, 15, 13.5, 1200, 1.2),
    'tod_war_wreck_impact': wreck_impact,
}


def wav_bytes(y):
    pcm = np.clip(np.round(y * 32767), -32768, 32767).astype('<i2')
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return buf.getvalue()


def alias_csv():
    rows = list(csv.reader(io.StringIO(TEMPLATE_FROM.read_text(encoding='utf-8-sig'))))
    head, template = rows[0], dict(zip(rows[0], rows[1]))
    assert template['PanType'] == '3d' and template['Looping'] == 'LOOPING', 'the template row must be a looping 3D alias'
    out = [head]
    for name, spec, vmin, vmax, dmin, dmaxd, dmaxw, pmin, pmax, loop in ALIASES:
        r = dict(template)
        for k, v in dict(Name=name, FileSpec=spec, VolMin=vmin, VolMax=vmax, DistMin=dmin, DistMaxDry=dmaxd, DistMaxWet=dmaxw,
                         PitchMin=pmin, PitchMax=pmax, Looping=loop).items():
            assert k in head, k
            r[k] = str(v)
        out.append([r[h] for h in head])
    buf = io.StringIO()
    csv.writer(buf, lineterminator='\r\n').writerows(out)
    return buf.getvalue().encode('utf-8')


def render():
    files = {}
    for i, (name, fn) in enumerate(RENDER.items()):
        rng = np.random.default_rng(SEED + i)
        files[OUT / (name + '.wav')] = wav_bytes(fn(rng))
    files[CSV_OUT] = alias_csv()
    return files


def main():
    files = render()
    if '--check' in sys.argv:
        bad = [p for p, b in files.items() if not p.exists() or p.read_bytes() != b]   # bytes: read_text would fold the CRLFs
        for p in bad:
            print('STALE', p)
        print('WAR SOUNDS OK (fresh)' if not bad else 'WAR SOUNDS STALE: run python tools/war_damage/make_sounds.py')
        sys.exit(1 if bad else 0)
    for p, b in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
        dur = (len(b) - 44) / 2 / SR if p.suffix == '.wav' else 0
        print('wrote %s  %d B%s' % (p, len(b), ('  %.2f s' % dur) if dur else ''))
    for name, spec, *_ in ALIASES:
        w = (STOCK_WAVS / spec.replace(BS, '/')) if not spec.startswith('tod' + BS + 'war') else OUT / spec.split(BS)[-1]
        print(f"{name:22s} {spec:38s} wav {'present' if w.exists() else 'MISSING'}")
    print('WAR SOUNDS written:', CSV_OUT)


if __name__ == '__main__':
    main()
