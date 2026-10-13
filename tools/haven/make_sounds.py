"""THE HAVEN sounds (docs/202), GENERATED - never hand-edit the .wav files or tod_haven.csv.

  python -B tools/haven/make_sounds.py           write sound_assets/tod/haven/*.wav + sound/aliases/tod_haven.csv
  python -B tools/haven/make_sounds.py --check   FAIL if any written file differs from a fresh render

THE SIXTEEN ALIASES, SEVENTEEN FILES (mono 48 kHz 16-bit; 3D sources must be mono). The SAFE set, then the CORRUPTED set
(docs/202 v3: the haven is evil until its guardians are dead), then v4's (the darkness and the barrier), then v5's (the
purification, the groans, the lift):
  tod_haven_enter    3D  you push INTO the field: a soft low whum, a fizz of field energy, a clean crystal fifth
  tod_haven_exit     3D  you step OUT: the same voice in reverse - fizz first, a rising whup, the fifth falling
  tod_haven_push     3D  a zombie forces its way in: an electric crackle over a buzzing thud (the field fights it)
  tod_haven_absorb   2D  you are hit inside the field: a small glassy tink (the field took a third of it); quiet
  tod_haven_ignite   3D  the haven powers up with the tower: a rising whine, a power thunk, a shimmering tail
  tod_haven_hum      3D  LOOPING, the field's bed: Shadows of Evil's ritual-barrier loop (stock, read from the
                         private tools root), level-matched and kept whole so its seam stays seamless
  tod_haven_hum_dark 3D  LOOPING, the corrupted field's bed: a low detuned drone that throbs, with a rough edge
                         (synthesized on the loop's own period, so it is seamless by construction)
  tod_haven_wake     3D  the guardians rise: a sub boom, a reversed shimmer, a crack, a falling snarl
  tod_haven_guard_down 3D a guardian falls: a glass-and-metal crack with a tonal drop and a splinter
  tod_haven_cleanse  3D  THE BLOOM (v5: the purification's third beat, the instant the field comes back safe; the rise
                         and the collapse are tod_haven_purge's): a bright chord blooming from nothing with a soft white
                         burst as it lands, a sub swell, a shimmering tail and a high sparkle (louder and longer than the
                         ignite: the moment is bigger)
  tod_haven_dark_in  2D  you step into a corrupted field and the darkness takes you: a reversed swell sucked into a
                         low swallow, a falling drone, a breath of whispers (v4, user 2026-10-03: "Going inside will
                         make your screen dark like you are being taken over by the darkness")
  tod_haven_dark_breath 2D the darkness while you stay inside: a slow heartbeat under a breathy whisper bed and a low
                         drone, faded at both ends so the script re-plays it back to back ("slightly annoying")
  tod_haven_deflect  3D  a bullet stops on the corrupted field's barrier: a crackling zap and a short dull thunk
  tod_haven_purge    3D  THE CONVULSION + THE COLLAPSE (v5), from the heart, COMPOSED TO THE MODULE'S CLOCK (the lengths
                         and the strobe schedule are read out of _tod_haven.gsc, as tools/haven/make_fx.py reads them):
                         the strobe's clicks on purge_strobe_steps() (electric snaps, louder and brighter toward the end),
                         the dark hum's drone climbing with the acceleration over a growing rumble, a swell sucked into the
                         collapse; then the collapse - a deep thump, a white burst and the void's vacuum (a thin high ring
                         over near silence) until the bloom (tod_haven_cleanse) takes over
  tod_haven_groan    3D  the breached dome STRAINING (v5; two takes behind one alias, _a bending down and _b bending up,
                         the engine picks one): a low detuned tone with a stick-slip metal creak riding it, from a random
                         point of the dome's rim, now and then while it stands corrupted
  tod_haven_dark_lift 2D the darkness LIFTING (v5): the swallow in reverse - a low drone rising and thinning into an airy
                         whoosh, a soft bright chime as the light comes back (on the way out and at the bloom alike)

Synthesis is seeded numpy (scipy filters), so a fresh render is byte-identical. Every one-shot fades in and out (no
clicks); peaks at -1.5 dBFS (the hum at -9). Alias rows ride BUS_FX with no context columns (the sound-context lint).
"""
import csv, io, json, math, os, pathlib, re, sys, wave

import numpy as np
from scipy import signal

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'sound_assets' / 'tod' / 'haven'
CSV_OUT = ROOT / 'sound' / 'aliases' / 'tod_haven.csv'
HEADER_FROM = ROOT / 'sound' / 'aliases' / 'tod_ui.csv'
HUM_SRC = pathlib.Path(r'C:\BO3Tools\TOD2Cybercity\sound_assets\zmb\level\zm_zod\ritual\barrier\loop\barrier_loop_01.wav')
SR = 48000
SEED = 20261002

# v5 THE PURIFICATION's clock is the module's (LOCKSTEP by construction with tools/haven/make_fx.py and the dome's own
# strobe): its lengths and its strobe schedule are read out of _tod_haven.gsc (the staged copy before the wire step)
GSC = next(p for p in (ROOT / 'scripts/zm/zm_tod2_cybercity/_tod_haven.gsc', ROOT / 'art/haven/staged/_tod_haven.gsc') if p.exists()).read_text(encoding='utf-8')


def gsc_define(name):
    return float(re.search(r'#define\s+%s\s+(-?[\d.]+)' % name, GSC).group(1))


CONVULSE_SECS = gsc_define('TOD_HAVEN_PURGE_CONVULSE_SECS')
VOID_SECS = gsc_define('TOD_HAVEN_PURGE_VOID_SECS')
STROBE_MS = [int(v) for v in re.search(r'function purge_strobe_steps\(\)\s*\{\s*return array\(([^)]*)\);', GSC).group(1).split(',')]

# name -> (kind, volume, (distMin, distMaxDry, distMaxWet))
SOUNDS = {
    'tod_haven_enter':  ('3d', 92, (120, 900, 1100)),
    'tod_haven_exit':   ('3d', 88, (120, 900, 1100)),
    'tod_haven_push':   ('3d', 80, (100, 700, 900)),
    'tod_haven_absorb': ('2d', 66, None),
    'tod_haven_ignite': ('3d', 100, (300, 4200, 5200)),
    'tod_haven_hum':    ('3d_loop', 62, (80, 520, 640)),
    'tod_haven_hum_dark': ('3d_loop', 66, (80, 560, 700)),
    'tod_haven_wake':   ('3d', 100, (300, 3600, 4600)),
    'tod_haven_guard_down': ('3d', 92, (200, 2200, 2800)),
    'tod_haven_cleanse': ('3d', 100, (300, 4200, 5200)),
    'tod_haven_dark_in': ('2d', 74, None),
    'tod_haven_dark_breath': ('2d', 60, None),
    'tod_haven_deflect': ('3d', 78, (80, 900, 1100)),
    'tod_haven_purge':  ('3d', 100, (300, 4200, 5200)),
    'tod_haven_groan':  ('3d', 72, (200, 1600, 2000)),
    'tod_haven_dark_lift': ('2d', 68, None),
}
# one alias, several takes: a row per file under the same Name (the engine picks one at random)
VARIANTS = {'tod_haven_groan': ('tod_haven_groan_a', 'tod_haven_groan_b')}


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


def sweep(t, f0, f1, curve=1.0):
    k = (t / t[-1]) ** curve
    f = f0 + (f1 - f0) * k
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def fades(y, fin=0.004, fout=0.03):
    n_in, n_out = int(fin * SR), int(fout * SR)
    y = y.copy()
    y[:n_in] *= np.linspace(0, 1, n_in)
    y[-n_out:] *= np.linspace(1, 0, n_out)
    return y


def norm(y, peak_db):
    return y / (np.max(np.abs(y)) + 1e-12) * (10 ** (peak_db / 20))


def room(y, rng, length=0.35, mix=0.18):
    """A small, bright tail (an exponentially decaying noise IR) so the field sounds like it rings in the air."""
    n = int(length * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (0.07 * SR))
    ir = signal.sosfilt(signal.butter(2, 1500, btype='highpass', fs=SR, output='sos'), ir)
    dry = np.concatenate([y, np.zeros(n)])
    wet = signal.fftconvolve(y, ir)[:len(dry)]
    wet = np.concatenate([wet, np.zeros(len(dry) - len(wet))])
    wet = wet / (np.max(np.abs(wet)) + 1e-9) * np.max(np.abs(y))
    return dry * (1 - mix) + wet * mix


def crystal(t, f0, f1, tau, detune=0.003):
    a = np.sin(2 * np.pi * f0 * t) + 0.6 * np.sin(2 * np.pi * f0 * (1 + detune) * t)
    b = np.sin(2 * np.pi * f1 * t) + 0.5 * np.sin(2 * np.pi * f1 * (1 - detune) * t)
    return (a + 0.8 * b) * env_exp(t, 0.008, tau)


def enter(rng):
    t = t_axis(0.8)
    whum = sweep(t, 230, 82, 0.6) * env_exp(t, 0.006, 0.17)
    sub = np.sin(2 * np.pi * 52 * t) * env_exp(t, 0.01, 0.12)
    fizz = bandnoise(rng, len(t), 2200, 7600) * env_exp(t, 0.02, 0.28) * (0.65 + 0.35 * np.sin(2 * np.pi * 31 * t))
    ting = crystal(t, 1320, 1980, 0.38)
    y = 0.9 * whum + 0.6 * sub + 0.35 * fizz + 0.22 * ting
    return fades(norm(room(y, rng), -1.5))


def exit_(rng):
    t = t_axis(0.65)
    rev = np.clip(t / 0.18, 0, 1) * np.exp(-np.maximum(t - 0.18, 0) / 0.12)
    fizz = bandnoise(rng, len(t), 2400, 8000) * rev * (0.6 + 0.4 * np.sin(2 * np.pi * 27 * t))
    whup = sweep(t, 95, 210, 1.4) * env_exp(t, 0.09, 0.14)
    fall = crystal(t, 1980, 1320, 0.26)
    y = 0.42 * fizz + 0.8 * whup + 0.2 * fall
    return fades(norm(room(y, rng), -1.5))


def push(rng):
    t = t_axis(0.48)
    clicks = np.zeros(len(t))
    k = 0
    while k < len(t):
        k += int(rng.exponential(SR / 70))
        if k < len(t):
            w = int(SR * rng.uniform(0.002, 0.007))
            clicks[k:k + w] += rng.uniform(0.5, 1.0) * np.hanning(min(w, len(t) - k))
    crack = signal.sosfilt(signal.butter(3, [1500, 6500], btype='bandpass', fs=SR, output='sos'), clicks * rng.standard_normal(len(t)))
    crack = crack / (np.max(np.abs(crack)) + 1e-9) * env_exp(t, 0.004, 0.16)
    buzz = signal.sosfilt(signal.butter(2, 900, fs=SR, output='sos'), np.sign(np.sin(2 * np.pi * 118 * t)))
    buzz = buzz / (np.max(np.abs(buzz)) + 1e-9) * env_exp(t, 0.005, 0.09)
    thud = np.sin(2 * np.pi * 64 * t) * env_exp(t, 0.004, 0.06)
    y = 0.7 * crack + 0.35 * buzz + 0.5 * thud
    return fades(norm(y, -1.5))


def absorb(rng):
    t = t_axis(0.16)
    tink = (np.sin(2 * np.pi * 2400 * t) + 0.55 * np.sin(2 * np.pi * 3610 * t)) * env_exp(t, 0.002, 0.045)
    click = bandnoise(rng, len(t), 3000, 9000) * env_exp(t, 0.001, 0.008)
    y = 0.8 * tink + 0.25 * click
    return fades(norm(y, -1.5), 0.002, 0.02)


def ignite(rng):
    t = t_axis(2.4)
    rise_t = 1.35
    k = np.clip(t / rise_t, 0, 1)
    f = 70 + (360 - 70) * k ** 1.6
    saw = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    whine = signal.sosfilt(signal.butter(2, 2400, fs=SR, output='sos'), saw) * (k ** 1.3) * (t < rise_t + 0.02)
    hit_t = t - rise_t
    on = hit_t >= 0
    thunk = np.zeros(len(t)); thunk[on] = (np.sin(2 * np.pi * 48 * hit_t[on]) * env_exp(hit_t[on], 0.004, 0.16))
    burst = np.zeros(len(t)); burst[on] = bandnoise(rng, on.sum(), 400, 5000) * env_exp(hit_t[on], 0.003, 0.08)
    tail = np.zeros(len(t)); tail[on] = bandnoise(rng, on.sum(), 3000, 9000) * env_exp(hit_t[on], 0.05, 0.45) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * hit_t[on]))
    chord = np.zeros(len(t)); chord[on] = crystal(hit_t[on], 990, 1485, 0.6)
    y = 0.45 * whine + 1.0 * thunk + 0.45 * burst + 0.3 * tail + 0.22 * chord
    return fades(norm(room(y, rng, 0.5, 0.15), -1.5), 0.01, 0.08)


def hum(rng):
    w = wave.open(str(HUM_SRC))
    assert w.getnchannels() == 1 and w.getsampwidth() == 2 and w.getframerate() == SR, 'the stock barrier loop changed shape'
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0
    return norm(x, -9.0)   # whole: its own seam is seamless (a stock loop); only the level moves


def hum_dark(rng):
    """A 4 s loop, seamless by construction: every partial completes whole cycles in 4 s, the noise is circular."""
    dur = 4.0
    t = t_axis(dur)
    n = len(t)
    cyc = lambda f: round(f * dur) / dur                   # snap a frequency to the loop's period
    drone = (signal.sawtooth(2 * np.pi * cyc(46) * t) + signal.sawtooth(2 * np.pi * cyc(46.25) * t + 1.1)
             + 0.7 * signal.sawtooth(2 * np.pi * cyc(69.5) * t + 0.4))
    drone = signal.sosfilt(signal.butter(2, 420, fs=SR, output='sos'), np.concatenate([drone, drone]))[n:]   # settle the filter, keep one period
    sub = np.sin(2 * np.pi * cyc(23) * t)
    throb = 0.62 + 0.38 * np.sin(2 * np.pi * cyc(0.5) * t - 1.3)
    rough = bandnoise(rng, n, 140, 620, 3)
    fade = int(0.3 * SR)                                   # circular crossfade: the tail folds under the head
    w = np.linspace(0, 1, fade)
    head = rough[:fade] * w + rough[-fade:] * (1 - w)
    rough = np.concatenate([head, rough[fade:-fade], head[:0]])
    rough = np.concatenate([rough, rough[: n - len(rough)]]) if len(rough) < n else rough[:n]
    rough = signal.sosfilt(signal.butter(2, [140, 620], btype='bandpass', fs=SR, output='sos'), np.concatenate([rough, rough]))[n:]
    rough = rough / (np.max(np.abs(rough)) + 1e-9)
    y = (0.8 * drone + 0.5 * sub) * throb + 0.22 * rough * (0.5 + 0.5 * throb)
    return norm(y, -9.0)


def wake(rng):
    t = t_axis(2.2)
    boom = np.sin(2 * np.pi * 42 * t) * env_exp(t, 0.006, 0.55) + 0.5 * np.sin(2 * np.pi * 84 * t) * env_exp(t, 0.006, 0.25)
    rev = np.clip(t / 0.3, 0, 1) ** 2 * (t < 0.3)
    shimmer = bandnoise(rng, len(t), 2500, 9000) * rev * (0.6 + 0.4 * np.sin(2 * np.pi * 37 * t))
    crack_t = t - 0.3
    on = crack_t >= 0
    crack = np.zeros(len(t)); crack[on] = bandnoise(rng, on.sum(), 900, 6500) * env_exp(crack_t[on], 0.002, 0.07)
    snarl_f = 190 * np.exp(-np.maximum(crack_t, 0) / 0.9) + 48
    snarl = signal.sawtooth(2 * np.pi * np.cumsum(snarl_f) / SR)
    snarl = signal.sosfilt(signal.butter(2, 900, fs=SR, output='sos'), snarl)
    snarl = snarl / (np.max(np.abs(snarl)) + 1e-9) * np.where(on, env_exp(np.maximum(crack_t, 0), 0.03, 0.7), 0)
    snarl *= 0.7 + 0.3 * np.sign(np.sin(2 * np.pi * 26 * t))   # a growl's rasp
    y = 1.0 * boom + 0.35 * shimmer + 0.55 * crack + 0.55 * snarl
    return fades(norm(room(y, rng, 0.5, 0.14), -1.5), 0.004, 0.1)


def guard_down(rng):
    t = t_axis(1.1)
    crack = bandnoise(rng, len(t), 1500, 7500) * env_exp(t, 0.002, 0.11)
    metal = (np.sin(2 * np.pi * 1180 * t) + 0.6 * np.sin(2 * np.pi * 1770 * t) + 0.4 * np.sin(2 * np.pi * 2630 * t)) * env_exp(t, 0.002, 0.16)
    drop = sweep(t, 230, 66, 0.7) * env_exp(t, 0.01, 0.22)
    splinter = crystal(t, 2200, 900, 0.3)
    thud = np.sin(2 * np.pi * 58 * t) * env_exp(t, 0.004, 0.09)
    y = 0.75 * crack + 0.4 * metal + 0.8 * drop + 0.18 * splinter + 0.5 * thud
    return fades(norm(room(y, rng, 0.4, 0.16), -1.5), 0.002, 0.08)


def cleanse(rng):
    """THE BLOOM (v5): the instant the field comes back safe - a chord blooming from nothing over 0.15 s with a soft white
    burst as it lands, a sub swell under it, a shimmering tail and a high sparkle (the rise and the collapse are purge()'s)"""
    t = t_axis(3.0)
    n = len(t)
    bloom = np.clip(t / 0.15, 0, 1) ** 1.4
    chord = (crystal(t, 880, 1320, 1.3) + 0.7 * crystal(t, 1760, 2640, 1.0) + 0.45 * crystal(t, 660, 990, 1.6)) * bloom
    sub = np.sin(2 * np.pi * 44 * t) * env_exp(t, 0.06, 0.4)
    burst = bandnoise(rng, n, 1000, 8000) * env_exp(t, 0.003, 0.12)
    shimmer = bandnoise(rng, n, 3000, 10000) * env_exp(t, 0.08, 0.9) * (0.6 + 0.4 * np.sin(2 * np.pi * 19 * t))
    sparkle = bandnoise(rng, n, 6000, 14000) * env_exp(t, 0.03, 0.3)
    y = 0.6 * chord + 0.8 * sub + 0.4 * burst + 0.35 * shimmer + 0.2 * sparkle
    return fades(norm(room(y, rng, 0.6, 0.18), -1.5), 0.01, 0.12)


def whisper(rng, n, t, rate):
    """a breathy whisper bed: noise through two slowly sweeping formant bands, gated by a syllable rhythm"""
    x = rng.standard_normal(n)
    out = np.zeros(n)
    for f0, f1, q in ((700, 1300, 3), (2100, 3200, 4)):
        f = f0 + (f1 - f0) * (0.5 + 0.5 * np.sin(2 * np.pi * rate * t + rng.uniform(0, 6.28)))
        seg = 2400
        for s in range(0, n, seg):
            fc = float(np.mean(f[s:s + seg]))
            sos = signal.butter(2, [fc / (1 + 0.5 / q), fc * (1 + 0.5 / q)], btype='bandpass', fs=SR, output='sos')
            out[s:s + seg] += signal.sosfilt(sos, x[s:s + seg])
    gate = np.clip(0.5 + 0.5 * np.sin(2 * np.pi * rate * 3.1 * t) + 0.3 * np.sin(2 * np.pi * rate * 7.3 * t + 1.1), 0, 1) ** 1.5
    out = out * gate
    return out / (np.max(np.abs(out)) + 1e-9)


def dark_in(rng):
    t = t_axis(1.7)
    n = len(t)
    rev = (np.clip(t / 0.9, 0, 1) ** 2.4) * (t < 0.92)                         # a swell sucked in ...
    suck = bandnoise(rng, n, 300, 4200) * rev
    hit_t = t - 0.92
    on = hit_t >= 0
    swallow = np.zeros(n)
    swallow[on] = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-hit_t[on] / 0.35) + 32) / SR) * env_exp(hit_t[on], 0.01, 0.32)
    drone = sweep(t, 140, 55, 0.8) * np.clip(t / 0.4, 0, 1) * np.exp(-np.maximum(t - 0.9, 0) / 0.5)
    drone = signal.sosfilt(signal.butter(2, 600, fs=SR, output='sos'), drone)
    hush = whisper(rng, n, t, 0.9) * np.clip((t - 0.5) / 0.4, 0, 1) * np.exp(-np.maximum(t - 1.1, 0) / 0.35)
    y = 0.55 * suck + 1.0 * swallow + 0.45 * drone + 0.30 * hush
    return fades(norm(room(y, rng, 0.5, 0.2), -1.5), 0.02, 0.15)


def dark_breath(rng):
    """5.5 s, faded at both ends: the script re-plays it back to back while you stay inside a corrupted field"""
    dur = 5.5
    t = t_axis(dur)
    n = len(t)
    beat = np.zeros(n)
    for k in range(5):                                                          # a slow lub-dub, ~54 bpm
        for off, amp in ((0.0, 1.0), (0.24, 0.7)):
            s = 0.35 + k * 1.11 + off
            bt = t - s
            m = bt >= 0
            beat[m] += amp * np.sin(2 * np.pi * 48 * bt[m]) * env_exp(bt[m], 0.006, 0.08)
    drone = signal.sosfilt(signal.butter(2, 260, fs=SR, output='sos'),
                           signal.sawtooth(2 * np.pi * 41 * t) + signal.sawtooth(2 * np.pi * 41.3 * t + 0.7))
    drone = drone / (np.max(np.abs(drone)) + 1e-9) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.18 * t))
    hush = whisper(rng, n, t, 0.55)
    y = 1.0 * beat + 0.22 * drone + 0.26 * hush
    y = norm(y, -3.0)
    edge = int(0.25 * SR)
    y[:edge] *= np.linspace(0, 1, edge)
    y[-edge:] *= np.linspace(1, 0, edge)
    return y


def deflect(rng):
    t = t_axis(0.38)
    n = len(t)
    clicks = np.zeros(n)
    k = 0
    while k < n * 0.5:
        k += int(rng.exponential(SR / 140))
        if k < n:
            w = int(SR * rng.uniform(0.001, 0.004))
            clicks[k:k + w] += rng.uniform(0.6, 1.0) * np.hanning(min(w, n - k))
    zap = signal.sosfilt(signal.butter(3, [1800, 7800], btype='bandpass', fs=SR, output='sos'), clicks * rng.standard_normal(n))
    zap = zap / (np.max(np.abs(zap)) + 1e-9) * env_exp(t, 0.002, 0.07)
    thunk = sweep(t, 160, 58, 0.6) * env_exp(t, 0.003, 0.06)
    y = 0.75 * zap + 0.65 * thunk
    return fades(norm(y, -1.5), 0.002, 0.04)


def purge(rng):
    """THE CONVULSION + THE COLLAPSE from the heart, composed to the module's clock (CONVULSE_SECS, VOID_SECS and
    STROBE_MS read out of _tod_haven.gsc): the strobe's CLICKS on the schedule (electric snaps, louder and brighter toward
    the end), the dark hum's drone climbing with the acceleration over a growing rumble, a swell sucked into the collapse;
    then the collapse - a deep thump, a white burst, and the void's vacuum (a thin high ring over near silence)."""
    conv, void = CONVULSE_SECS, VOID_SECS
    t = t_axis(conv + void + 0.05)
    n = len(t)
    k = np.clip(t / conv, 0, 1)
    live = t < conv
    f = 46 + (190 - 46) * k ** 2.2
    drone = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) + signal.sawtooth(2 * np.pi * np.cumsum(f * 1.006) / SR + 1.1)
    drone = signal.sosfilt(signal.butter(2, 900, fs=SR, output='sos'), drone)
    drone = drone / (np.max(np.abs(drone)) + 1e-9) * (0.3 + 0.7 * k ** 1.5) * live
    rumble = bandnoise(rng, n, 25, 120, 3) * (k ** 1.3) * live
    clicks = np.zeros(n)
    for i, ms in enumerate(STROBE_MS):
        s = int(ms / 1000 * SR)
        w = min(int(0.07 * SR), n - s)
        tt = np.arange(w) / SR
        g = i / max(1, len(STROBE_MS) - 1)
        snap = bandnoise(rng, w, 1400 + 500 * g, 6500 + 2500 * g) * env_exp(tt, 0.0012, 0.012 + 0.006 * g)
        tick = np.sin(2 * np.pi * (2300 + 900 * g) * tt) * env_exp(tt, 0.001, 0.02)
        clicks[s:s + w] += (0.55 + 0.45 * g) * (snap + 0.5 * tick)
    suck = bandnoise(rng, n, 300, 5000) * (np.clip((t - (conv - 0.6)) / 0.6, 0, 1) ** 2.2) * live
    ct = t - conv
    on = ct >= 0
    thump = np.zeros(n); thump[on] = np.sin(2 * np.pi * np.cumsum(62 * np.exp(-ct[on] / 0.25) + 30) / SR) * env_exp(ct[on], 0.003, 0.22)
    burst = np.zeros(n); burst[on] = bandnoise(rng, int(on.sum()), 800, 9000) * env_exp(ct[on], 0.002, 0.07)
    ring = np.zeros(n); ring[on] = (np.sin(2 * np.pi * 3100 * ct[on]) + 0.6 * np.sin(2 * np.pi * 4650 * ct[on])) * env_exp(ct[on], 0.01, 0.3)
    y = 0.5 * drone + 0.55 * rumble + 0.9 * clicks + 0.5 * suck + 1.0 * thump + 0.6 * burst + 0.16 * ring
    return fades(norm(room(y, rng, 0.5, 0.14), -1.5), 0.01, 0.1)


def groan(rng, dur, f0, bend):
    """the breached dome straining: a low detuned tone bending (down for bend < 1, up for > 1) with a stick-slip metal
    creak riding it, swelling and dying"""
    t = t_axis(dur)
    n = len(t)
    f = f0 * bend ** (t / dur)
    tone = (signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) + signal.sawtooth(2 * np.pi * np.cumsum(f * 1.5 * 1.004) / SR + 0.8)
            + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 0.5) / SR))
    tone = signal.sosfilt(signal.butter(2, 700, fs=SR, output='sos'), tone)
    tone = tone / (np.max(np.abs(tone)) + 1e-9)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
    slip = 0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(14 + 9 * np.sin(2 * np.pi * 0.6 * t)) / SR)
    slip = np.clip((slip - 0.55) / 0.45, 0, 1) ** 2
    creak = bandnoise(rng, n, 500, 2800) * slip
    y = 0.85 * tone * env + 0.4 * creak * env
    return fades(norm(room(y, rng, 0.45, 0.2), -2.5), 0.02, 0.15)


def groan_a(rng):
    return groan(rng, 1.9, 58, 0.72)


def groan_b(rng):
    return groan(rng, 2.3, 49, 1.35)


def dark_lift(rng):
    """the darkness lifting (2D): the swallow in reverse - a low drone rising and thinning into an airy whoosh, a soft
    bright chime as the light comes back"""
    t = t_axis(1.25)
    n = len(t)
    drone = signal.sosfilt(signal.butter(2, 700, fs=SR, output='sos'), sweep(t, 55, 170, 1.2)) * env_exp(t, 0.02, 0.3)
    whoosh = bandnoise(rng, n, 500, 6000) * (np.clip(t / 0.5, 0, 1) ** 1.5) * np.exp(-np.maximum(t - 0.5, 0) / 0.22)
    ct = t - 0.35
    on = ct >= 0
    chime = np.zeros(n); chime[on] = crystal(ct[on], 1320, 1980, 0.5)
    y = 0.6 * drone + 0.5 * whoosh + 0.3 * chime
    return fades(norm(room(y, rng, 0.4, 0.18), -2.0), 0.01, 0.12)


RENDER = {'tod_haven_enter': enter, 'tod_haven_exit': exit_, 'tod_haven_push': push, 'tod_haven_absorb': absorb,
          'tod_haven_ignite': ignite, 'tod_haven_hum': hum, 'tod_haven_hum_dark': hum_dark, 'tod_haven_wake': wake,
          'tod_haven_guard_down': guard_down, 'tod_haven_cleanse': cleanse,
          'tod_haven_dark_in': dark_in, 'tod_haven_dark_breath': dark_breath, 'tod_haven_deflect': deflect,
          'tod_haven_purge': purge, 'tod_haven_groan_a': groan_a, 'tod_haven_groan_b': groan_b, 'tod_haven_dark_lift': dark_lift}


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
        for stem in VARIANTS.get(name, (name,)):
            assert stem in RENDER, stem + ': no renderer'
            r = [''] * len(header)
            r[col['Name']] = name
            r[col['FileSpec']] = 'tod\\haven\\' + stem + '.wav'
            r[col['Template']] = 'UIN_MOD'
            r[col['VolMin']] = r[col['VolMax']] = str(vol)
            r[col['Bus']] = 'BUS_FX'
            if kind == '2d':
                r[col['PanType']] = '2d'
            else:
                r[col['DistMin']], r[col['DistMaxDry']], r[col['DistMaxWet']] = (str(d) for d in dist)
                r[col['PitchMin']] = r[col['PitchMax']] = '0'
                r[col['PanType']] = '3d'
            r[col['Looping']] = 'LOOPING' if kind == '3d_loop' else 'NONLOOPING'
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


def main():
    files = render()
    if '--check' in sys.argv:
        bad = [p for p, b in files.items() if not p.exists() or p.read_bytes() != b]
        for p in bad:
            print('STALE', p.relative_to(ROOT))
        print('HAVEN SOUNDS --check:', 'OK' if not bad else '%d stale' % len(bad))
        sys.exit(1 if bad else 0)
    for p, b in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
        dur = (len(b) - 44) / 2 / SR if p.suffix == '.wav' else 0
        print('wrote %s  %d B%s' % (p.relative_to(ROOT), len(b), ('  %.2f s' % dur) if dur else ''))


if __name__ == '__main__':
    main()
