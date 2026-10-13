"""THE LUCKY SOURCES - their nine sounds (docs/197): synthesised, deterministic, GENERATED - never hand-edit the wavs
or the aliases; change this script and re-run it.

  python tools/lucky/make_sounds.py            write sound_assets/tod/luck/tod_luck_*.wav and sound/aliases/tod_luck.csv
                                               (a file whose bytes did not change is left alone), and register
                                               tod_luck.csv in sound/zoneconfig/zm_tod2_cybercity.szc if it is missing
                                               (a copy of the tod_sky entry, placed after tod_jump; a no-op once there)
  python tools/lucky/make_sounds.py --check    synthesise everything again IN MEMORY and FAIL (exit 1,
                                               "LUCKY SOUNDS STALE: <what> - run python tools/lucky/make_sounds.py")
                                               if a wav is missing or not byte-identical, the csv is missing or differs
                                               (line endings aside: git's eol=lf rewrites them on checkout), or the
                                               zone config does not load tod_luck.csv; else "LUCKY SOUNDS OK: 9 sounds"
  python tools/lucky/make_sounds.py --out DIR  a preview: the wavs only, into DIR (nothing in the repo is touched)

THE LUCKY METEOR (sky scenery that pays out when shot) and its clover:
  tod_luck_meteor_announce  2D, 1.8 s         "look up, something lucky is in the sky": an airy whoosh sweeping up
                                              400 Hz -> 4 kHz over 1.2 s and fading, and from 0.45 s a bright two-note
                                              bell chime (E6 then B6) ringing out for about a second
  tod_luck_meteor_loop      3D loop, 2.000 s  the burning rock far away: a low turbulent fiery roar (50-400 Hz) with a
                                              flame texture over it, a soft crackle and a faint high shimmer
  tod_luck_meteor_burst     3D, 2.6 s         the rock shot apart: a deep boom falling 80 -> 35 Hz with a noise blast,
                                              a crystalline shatter (46 glassy pings 2-9 kHz over 0.6 s), a sparkling
                                              tail and a long low rumble with two late echoes (it carries across the tower)
  tod_luck_clover_fall      3D loop, 1.000 s  the glowing charm streaking down: an airy 2-5 kHz whistle-shimmer under a
                                              gentle 6 Hz tremolo, with a faint glitter over it
  tod_luck_clover_land      3D, 1.2 s         the touch-down: a soft 90 Hz thump and a rising C-E-G bell arpeggio
                                              (70 ms apart) into a sparkle tail
THE GOLDEN ZOMBIE (all four in G major, so they belong together):
  tod_luck_golden_spawn     2D, 1.6 s         "a golden zombie appeared somewhere": a soft bell glissando up the G major
                                              pentatonic over a warm swelling chord, then a gentle metallic "cha-ching"
  tod_luck_golden_loop      3D loop, 2.000 s  the sparkle around it: sparse soft bell twinkles (2.5-6 kHz) over a faint
                                              airy hum (G3 + D4 + G4 with one slow beat per loop)
  tod_luck_golden_death     3D, 1.8 s         it bursts: a soft pop, one bright G6 chime and a cascade of 34 metallic
                                              coin clinks (denser at first, some bouncing)
  tod_luck_golden_jackpot   2D, 1.5 s         the killer's reward: a G-B-D-G bell arpeggio (90 ms apart) into a sparkle tail

Every file is mono 48 kHz 16-bit with its peak at -1.5 dBFS. One-shots are DC-blocked (a zero-phase high-pass at 16 Hz)
and faded in (3 ms) and out, so they start and end on silence and never click. Loops are EXACTLY their length and
SEAMLESS by construction: every noise is shaped in the frequency domain over exactly the loop's length (the FFT is
circular), every tone and modulation completes whole cycles in it (loop_sine asserts it), and every event near the
end folds round to the start; they are not faded (a fade would put a dip at the seam), only their mean is removed.

The aliases take tod_ui.csv's header row verbatim. No row has a ContextType/ContextValue (a context makes a sound
silent in this map: tools/lint_tod_sound_context.js) and none randomises pitch. 3D rows are shaped like tod_sky.csv's
(Template UIN_MOD, no Bus, PitchMin/Max 0), 2D rows like tod_jump.csv's tod_jt_boom (UIN_MOD, BUS_FX, no distances).
Every generator is seeded, so --check can be byte-exact on the wavs (a numpy upgrade could in principle move a sample
by one step; if --check ever fails right after one, re-run the script).
"""
import csv, io, json, pathlib, re, sys, wave
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
SR = 48000
PEAK_DB = -1.5
WAV_DIR = ROOT / 'sound_assets/tod/luck'
CSV_PATH = ROOT / 'sound/aliases/tod_luck.csv'
HEADER_FROM = ROOT / 'sound/aliases/tod_ui.csv'
SZC = ROOT / 'sound/zoneconfig/zm_tod2_cybercity.szc'
FIX = 'run python tools/lucky/make_sounds.py'


# ---------------------------------------------------------------------------------------------- building blocks
def timeline(secs):
    n = int(round(secs * SR))
    return n, np.arange(n) / SR


def shaped_noise(n, lo, hi, seed, tilt=0.0):
    """White noise band-limited to lo..hi Hz in the frequency domain (circular = loops seamlessly), peak 1.
    tilt < 0 leans toward the low end (e.g. -1 = pink-ish). (tools/sky_ships/make_sounds.py's)"""
    rng = np.random.default_rng(seed)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    gain = ((f >= lo) & (f <= hi)).astype(float)
    edge = 0.15
    gain = np.where((f > lo * (1 - edge)) & (f < lo), (f - lo * (1 - edge)) / (lo * edge), gain)
    gain = np.where((f > hi) & (f < hi * (1 + edge)), 1 - (f - hi) / (hi * edge), gain)
    with np.errstate(divide='ignore'):
        gain = gain * np.where(f > 0, (np.maximum(f, 1) / max(lo, 1)) ** (tilt / 2), 0)
    x = np.fft.irfft(spec * gain, n)
    return x / (np.max(np.abs(x)) + 1e-12)


def env(t, a, d):
    """0 before t = 0, a linear attack of a s, then an exponential decay with time constant d s"""
    return np.clip(t / max(a, 1e-4), 0, 1) * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))


def smooth(x):
    """smoothstep: 0 -> 1 as x goes 0 -> 1, flat at both ends"""
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def glide_phase(t, f0, f1, k):
    """the phase of an exponential glide f(t) = f1 + (f0 - f1) e^(-k t)"""
    return 2 * np.pi * (f1 * t + (f0 - f1) / k * (1 - np.exp(-k * t)))


def loop_sine(t, f, T, phase=0.0):
    """a sine that completes WHOLE cycles in a loop of T s (asserted), so the loop's seam cannot click"""
    assert abs(f * T - round(f * T)) < 1e-9, '%s Hz does not complete whole cycles in a %s s loop' % (f, T)
    return np.sin(2 * np.pi * f * t + phase)


def delay(x, secs, gain, lp=None):
    """an echo: x later by secs, scaled by gain, optionally darkened (a gentle low-pass at lp Hz)"""
    d = int(secs * SR)
    y = np.zeros_like(x)
    y[d:] = x[:-d] * gain
    if lp:
        f = np.fft.rfftfreq(len(y), 1.0 / SR)
        y = np.fft.irfft(np.fft.rfft(y) / (1 + (f / lp) ** 2), len(y))
    return y


def sweep_band(x, fc, q):
    """x through a band-pass whose centre follows fc (Hz, one value per sample): a trapezoidal state-variable filter
    (Simper's), stable while it moves; unity gain at the centre"""
    k = 1.0 / q
    g = np.tan(np.pi * np.clip(fc, 20.0, 0.45 * SR) / SR)
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    xs, A1, A2, A3 = x.tolist(), a1.tolist(), a2.tolist(), a3.tolist()
    out = [0.0] * len(xs)
    ic1 = ic2 = 0.0
    for i in range(len(xs)):
        v3 = xs[i] - ic2
        v1 = A1[i] * ic1 + A2[i] * v3
        v2 = ic2 + A2[i] * ic1 + A3[i] * v3
        ic1 = 2.0 * v1 - ic1
        ic2 = 2.0 * v2 - ic2
        out[i] = k * v1
    return np.array(out)


# Struck-note timbres: (ratio to the fundamental, level, share of the decay time). A close doublet on the fundamental
# (real bells ring in pairs of modes) gives each note a slow shimmer instead of a flat electronic sine.
GLOCK = ((1.0, 1.0, 1.0), (1.0016, 0.32, 0.92), (2.0, 0.14, 0.5), (2.756, 0.24, 0.4), (5.404, 0.08, 0.2),
         (8.933, 0.03, 0.1))                                         # a bright bell / glockenspiel bar
SOFT = ((1.0, 1.0, 1.0), (1.0012, 0.3, 0.9), (2.0, 0.12, 0.45), (3.0, 0.035, 0.3), (4.16, 0.02, 0.22))   # celesta-soft
METAL = ((1.0, 1.0, 1.0), (1.0023, 0.55, 0.9), (2.32, 0.42, 0.62), (3.18, 0.3, 0.5), (4.25, 0.2, 0.4),
         (5.43, 0.1, 0.3))                                           # a metallic ring (the "ching")
TINK = ((1.0, 1.0, 1.0), (2.32, 0.25, 0.45))                          # a glass shard / star twinkle
COIN = ((1.0, 1.0, 1.0), (1.36, 0.7, 0.8), (1.83, 0.5, 0.6), (2.41, 0.3, 0.45))   # a coin: inharmonic, bright


def strike(n, t0, f0, partials, tau, amp=1.0, attack=0.004, wrap=False, jitter=None):
    """One struck note at t0 s in an n-sample buffer: each partial a sine decaying with time constant tau x its share,
    all under a raised-cosine attack (no click); partials at or above 17 kHz are dropped. It rings to ~-60 dB (seven
    time constants) or the end of the buffer; wrap=True folds whatever passes the end back to the start (a loop's
    event crossing its seam stays seamless). jitter: optional per-partial ratio multipliers (no two coins alike)."""
    i0 = int(round(t0 * SR))
    L = int(7 * tau * max(p[2] for p in partials) * SR) + 1
    if not wrap:
        L = min(L, n - i0)
        if L <= 0:
            return np.zeros(n)
    k = np.arange(L) / SR
    y = np.zeros(L)
    for j, (r, a, d) in enumerate(partials):
        f = f0 * r * (jitter[j] if jitter is not None else 1.0)
        if f >= 17000:
            continue
        y += a * np.sin(2 * np.pi * f * k) * np.exp(-k / (tau * d))
    y *= np.where(k < attack, 0.5 - 0.5 * np.cos(np.pi * k / attack), 1.0) * amp
    out = np.zeros(n)
    if wrap:
        np.add.at(out, (i0 + np.arange(L)) % n, y)
    else:
        out[i0:i0 + L] += y
    return out


def crackle_loop(n, seed, rate, lo, hi):
    """a soft fire crackle for a loop: short pops of lo..hi band noise (4-22 ms, a 0.5 ms rise, a fast fall) spread
    over the loop at `rate` per second, mostly small ones; a pop crossing the end folds back to the start (the band
    noise is circular itself, so the folded pop is continuous)"""
    rng = np.random.default_rng(seed)
    band = shaped_noise(n, lo, hi, seed + 1)
    out = np.zeros(n)
    for _ in range(int(round(rate * n / SR))):
        i0 = int(rng.integers(0, n))
        L = int(rng.uniform(0.004, 0.022) * SR)
        k = np.arange(L)
        shape = np.minimum(k / (0.0005 * SR), 1.0) * np.exp(-k / (0.22 * L))
        idx = (i0 + k) % n
        out[idx] += band[idx] * shape * rng.uniform(0.25, 1.0) ** 2
    return out


def twinkles(n, seed, count, t_from, t_span, f_lo, f_hi, tau_lo, tau_hi, fall, skew=1.5):
    """a sparkle: `count` soft high twinkles thinning out from t_from over t_span s (denser early: skew > 1), pitches
    log-uniform f_lo..f_hi, each fainter the later it comes (exp(-delay / fall))"""
    rng = np.random.default_rng(seed)
    out = np.zeros(n)
    for _ in range(count):
        t0 = t_from + t_span * rng.random() ** skew
        f0 = f_lo * (f_hi / f_lo) ** rng.random()
        out += strike(n, t0, f0, TINK, rng.uniform(tau_lo, tau_hi),
                      rng.uniform(0.35, 1.0) * np.exp(-(t0 - t_from) / fall), attack=0.002)
    return out


# ------------------------------------------------------------------------------------------------------ finishing
def one_shot(x, fade_out, fade_in=0.003):
    """a one-shot's finish: DC-blocked by a zero-phase high-pass (|H| = f^2 / (f^2 + 16^2), zero-padded on both sides
    so nothing wraps and no timing moves), then raised-cosine fades so the first and last samples are exactly 0"""
    pad = SR
    y = np.concatenate([np.zeros(pad), x, np.zeros(pad)])
    f = np.fft.rfftfreq(len(y), 1.0 / SR)
    y = np.fft.irfft(np.fft.rfft(y) * (f * f / (f * f + 16.0 ** 2)), len(y))[pad:pad + len(x)]
    n = len(y)
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    g = np.ones(n)
    g[:fi] = 0.5 - 0.5 * np.cos(np.pi * np.arange(fi) / fi)
    g[n - fo:] = 0.5 + 0.5 * np.cos(np.pi * np.arange(1, fo + 1) / fo)
    return y * g


def loop(x):
    """a loop's finish: only its mean removed (no fades - a fade would put a dip at the seam)"""
    return x - np.mean(x)


def encode(x):
    """peak -1.5 dBFS, mono 48 kHz 16-bit PCM wav bytes"""
    x = x / (np.max(np.abs(x)) + 1e-12) * 10 ** (PEAK_DB / 20)
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype('<i2')
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


# ------------------------------------------------------------------------------------------------ THE LUCKY METEOR
def meteor_announce():
    """2D, 1.8 s: an airy whoosh rising 400 Hz -> 4 kHz over 1.2 s and fading, then E6 and B6 bell chimes"""
    n, t = timeline(1.8)
    fc = 400.0 * 10.0 ** np.clip(t / 1.2, 0, 1)                      # an exponential sweep: even in pitch
    # in over 0.35 s; it gives way as the chime enters (the sweep crosses the chime's 1.3-2 kHz right then) and is
    # gone by 1.2 s. The input is band-limited so the band-pass's low skirt adds no rumble: airy, not boomy.
    swell = smooth(t / 0.35) * (1 - smooth((t - 0.42) / 0.78))
    whoosh = sweep_band(shaped_noise(n, 250, 16000, 101), fc, 3.0) * swell * (fc / 400.0) ** -0.25
    whoosh /= np.max(np.abs(whoosh))
    air = shaped_noise(n, 2500, 9000, 102, tilt=-0.4) * smooth((t - 0.15) / 0.4) * (1 - smooth((t - 0.45) / 0.7))
    chime = (strike(n, 0.45, 1318.51, GLOCK, 0.36, 0.62, attack=0.012)          # E6, a soft 12 ms attack
             + strike(n, 0.62, 1975.53, GLOCK, 0.40, 0.56, attack=0.012))       # B6
    return one_shot(0.9 * whoosh + 0.18 * air + chime, fade_out=0.25)


def meteor_loop():
    """3D loop, exactly 2 s: a burning rock far away - roar, flame, crackle, shimmer"""
    T = 2.0
    n, t = timeline(T)
    roar = shaped_noise(n, 50, 400, 201, tilt=-0.7) * (0.74 + 0.26 * shaped_noise(n, 0.5, 7.0, 202))    # turbulence
    flame = shaped_noise(n, 280, 1500, 203, tilt=-1.0) * (0.6 + 0.4 * shaped_noise(n, 2.0, 14.0, 204))
    crack = crackle_loop(n, 205, 10, 1500, 6500)
    shimmer = shaped_noise(n, 5000, 11000, 207) * (0.8 + 0.2 * loop_sine(t, 3.0, T))
    return loop(roar + 0.32 * flame + 0.3 * crack + 0.06 * shimmer)


def meteor_burst():
    """3D, 2.6 s: a deep falling boom, a crystalline shatter on top, a sparkling tail, a rumble with echoes"""
    n, t = timeline(2.6)
    ph = glide_phase(t, 80.0, 35.0, 4.5)                              # 80 -> 35 Hz
    boom = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)) * env(t, 0.004, 0.55)   # harmonics: small speakers
    thump = shaped_noise(n, 35, 260, 302, tilt=-1.0) * env(t, 0.003, 0.16)
    low = np.tanh(1.5 * (boom + 0.75 * thump)) / 1.5                  # a soft saturation: weight, not just a peak
    blast = shaped_noise(n, 180, 2600, 303, tilt=-0.7) * env(t, 0.002, 0.07)
    snap = shaped_noise(n, 1500, 9500, 304) * env(t, 0.0008, 0.022)
    rng = np.random.default_rng(301)
    shatter = np.zeros(n)                     # glassy shards, densest at the break but spread over the 0.6 s (a pile-up
    for _ in range(46):                       # of rings right at the start was the file's peak: ~1 dB of loudness lost)
        u = rng.random()
        shatter += strike(n, 0.006 + 0.6 * u ** 1.25, 2000.0 * 4.5 ** rng.random(), TINK, rng.uniform(0.02, 0.085),
                          rng.uniform(0.35, 1.0) * (1 - 0.25 * u), attack=0.0004)
    hiss = shaped_noise(n, 3500, 12000, 305) * env(t, 0.002, 0.1)
    sparkle = twinkles(n, 306, 22, 0.45, 1.65, 3000, 7800, 0.05, 0.15, 0.8)
    shine = shaped_noise(n, 6000, 13000, 307) * env(t, 0.1, 0.55)
    rumble = shaped_noise(n, 22, 140, 308, tilt=-1.0) * env(t, 0.06, 0.9)
    dry = (low + 0.45 * blast + 0.5 * snap + 0.36 * shatter + 0.12 * hiss + 0.16 * sparkle + 0.035 * shine
           + 0.5 * rumble)
    wet = dry + delay(dry, 0.23, 0.3, lp=900) + delay(dry, 0.51, 0.17, lp=500)   # the echoes carry the low end only
    return one_shot(wet, fade_out=0.4)


def clover_fall():
    """3D loop, exactly 1 s: an airy whistle-shimmer with a gentle tremolo (6 whole cycles) and a faint glitter"""
    T = 1.0
    n, t = timeline(T)
    trem = 0.8 + 0.2 * loop_sine(t, 6.0, T)
    air = shaped_noise(n, 2000, 5000, 401, tilt=-0.6)                # leaning low in the band: airy, not shrill
    whistle = shaped_noise(n, 3050, 3380, 402)                       # a narrow band reads as a breathy whistle
    tone = np.sin(2 * np.pi * 3200.0 * t + 1.6 * loop_sine(t, 5.0, T))   # a faint pure whistle, +-8 Hz vibrato
    loop_sine(t, 3200.0, T)                                           # (asserts the carrier closes the loop too)
    glitter = shaped_noise(n, 6500, 11000, 403) * (0.55 + 0.45 * loop_sine(t, 20.0, T))
    return loop((0.8 * air + 0.38 * whistle + 0.07 * tone) * trem + 0.14 * glitter)


def clover_land():
    """3D, 1.2 s: a soft thump and a rising C6-E6-G6 bell arpeggio 70 ms apart, into a sparkle tail"""
    n, t = timeline(1.2)
    ph = glide_phase(t, 100.0, 86.0, 30.0)                            # ~90 Hz, settling
    thump = (np.sin(ph) + 0.3 * np.sin(2 * ph)) * env(t, 0.003, 0.055)
    puff = shaped_noise(n, 90, 700, 502, tilt=-1.0) * env(t, 0.002, 0.03)
    arp = sum(strike(n, 0.03 + 0.07 * i, f, GLOCK, tau, a, attack=0.0025)
              for i, (f, tau, a) in enumerate(((1046.50, 0.30, 0.50), (1318.51, 0.32, 0.55), (1567.98, 0.42, 0.62))))
    sparkle = twinkles(n, 501, 14, 0.2, 0.8, 3000, 7000, 0.04, 0.11, 0.5, skew=1.3)
    shine = shaped_noise(n, 5000, 11000, 503) * env(t - 0.15, 0.1, 0.35)
    return one_shot(0.85 * thump + 0.35 * puff + arp + 0.2 * sparkle + 0.05 * shine, fade_out=0.15)


# ----------------------------------------------------------------------------------------------- THE GOLDEN ZOMBIE
G_PENTA = (392.00, 440.00, 493.88, 587.33, 659.26, 783.99, 880.00, 987.77, 1174.66, 1318.51, 1567.98)   # G4 .. G6


def golden_spawn():
    """2D, 1.6 s: a soft bell glissando up G major pentatonic over a warm chord, then a gentle "cha-ching" """
    n, t = timeline(1.6)
    gliss = sum(strike(n, 0.02 + 0.047 * i, f, SOFT, 0.34 + 0.02 * i, 0.3 + 0.03 * i, attack=0.007)
                for i, f in enumerate(G_PENTA))
    pad = sum(a * (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * (f + 0.7) * t))      # slowly beating pairs
              for f, a in ((196.00, 0.5), (246.94, 0.35), (293.66, 0.35), (392.00, 0.25)))
    pad *= smooth(t / 0.4) * (1 - smooth((t - 0.6) / 0.95))
    cha = (strike(n, 0.60, 1174.66, METAL, 0.05, 0.3, attack=0.0008)                # the short "cha" on D6
           + shaped_noise(n, 2500, 9000, 601) * env(t - 0.60, 0.0006, 0.012) * 0.25)
    ching = (strike(n, 0.71, 1567.98, METAL, 0.42, 0.42, attack=0.0015)             # the "ching" ringing on G6
             + shaped_noise(n, 3000, 10000, 602) * env(t - 0.71, 0.0006, 0.015) * 0.3)
    shimmer = shaped_noise(n, 4500, 10000, 603) * smooth(t / 0.5) * np.exp(-np.maximum(t - 0.55, 0) / 0.4)
    return one_shot(gliss + 0.1 * pad + 0.9 * cha + ching + 0.05 * shimmer, fade_out=0.25)


def golden_loop():
    """3D loop, exactly 2 s: sparse soft twinkles over a faint airy hum"""
    T = 2.0
    n, t = timeline(T)
    rng = np.random.default_rng(701)
    tw = np.zeros(n)
    for j in range(7):                                                # one per seventh of the loop: never bunched
        t0 = (j + rng.uniform(0.1, 0.9)) * T / 7
        tw += strike(n, t0, 2500.0 * 2.4 ** rng.random(), TINK, rng.uniform(0.05, 0.13), rng.uniform(0.45, 1.0),
                     attack=0.003, wrap=True)
    hum = (0.45 * loop_sine(t, 196.0, T) + 0.35 * loop_sine(t, 196.5, T)          # G3, one slow beat per loop
           + 0.3 * loop_sine(t, 293.5, T) + 0.2 * loop_sine(t, 392.0, T))         # D4, G4
    hum *= 0.8 + 0.2 * loop_sine(t, 0.5, T)
    air = shaped_noise(n, 1200, 4000, 702, tilt=-0.5) * (0.7 + 0.3 * loop_sine(t, 1.0, T, 1.3))
    return loop(tw + 0.1 * hum + 0.1 * air)


def golden_death():
    """3D, 1.8 s: a soft pop, one bright chime and a cascade of coin clinks, denser at first"""
    n, t = timeline(1.8)
    ph = glide_phase(t, 160.0, 70.0, 25.0)
    pop = (np.sin(ph) * env(t, 0.002, 0.07) * 0.5
           + shaped_noise(n, 120, 1800, 802, tilt=-0.8) * env(t, 0.0015, 0.045) * 0.55)
    chime = (strike(n, 0.015, 1567.98, GLOCK, 0.5, 0.5, attack=0.002)
             + strike(n, 0.015, 3135.96, TINK, 0.22, 0.12, attack=0.002))
    tick = shaped_noise(n, 4000, 12000, 803)                          # the metal-on-metal edge of each impact
    rng = np.random.default_rng(801)
    coins = np.zeros(n)
    for _ in range(34):
        u = rng.random()
        t0 = 0.03 + 1.0 * u ** 1.7                                     # gravity: most land early
        f0 = 2600.0 * (4000.0 / 2600.0) ** rng.random()
        jit = rng.uniform(0.97, 1.03, len(COIN))
        tau = rng.uniform(0.05, 0.16)
        a = rng.uniform(0.4, 1.0) * (1 - 0.4 * u)
        hits = [(t0, a)]
        if rng.random() < 0.3:                                         # a bounce
            hits.append((t0 + rng.uniform(0.018, 0.045), 0.45 * a))
        for th, ah in hits:
            coins += strike(n, th, f0, COIN, tau, ah, attack=0.0003, jitter=jit)
            coins += tick * env(t - th, 0.0002, 0.0022) * 0.5 * ah
    shine = shaped_noise(n, 6000, 12000, 804) * env(t, 0.05, 0.5)
    return one_shot(pop + chime + 0.42 * coins + 0.04 * shine, fade_out=0.2)


def golden_jackpot():
    """2D, 1.5 s: a G5-B5-D6-G6 bell arpeggio 90 ms apart into a sparkle tail"""
    n, t = timeline(1.5)
    notes = ((783.99, 0.30, 0.52), (987.77, 0.32, 0.56), (1174.66, 0.34, 0.60), (1567.98, 0.55, 0.78))
    arp = sum(strike(n, 0.01 + 0.09 * i, f, GLOCK, tau, a, attack=0.003) for i, (f, tau, a) in enumerate(notes))
    arp += strike(n, 0.28, 783.99, SOFT, 0.5, 0.22, attack=0.004)    # the octave under the top note: body
    arp += strike(n, 0.28, 3135.96, TINK, 0.2, 0.1, attack=0.002)    # and a glint over it
    sparkle = twinkles(n, 901, 16, 0.3, 0.9, 4000, 8000, 0.04, 0.1, 0.45, skew=1.3)
    shine = shaped_noise(n, 5000, 12000, 902) * env(t - 0.28, 0.05, 0.4)
    return one_shot(arp + 0.2 * sparkle + 0.05 * shine, fade_out=0.2)


# ------------------------------------------------------------------------------------------------------ the aliases
# name, synth, kind ('2d' one-shot | '3d' one-shot | '3d_loop'), VolMin/VolMax, (DistMin, DistMaxDry, DistMaxWet)
SOUNDS = [
    ('tod_luck_meteor_announce', meteor_announce, '2d', 88, None),
    ('tod_luck_meteor_loop', meteor_loop, '3d_loop', 80, (2500, 20000, 22000)),
    ('tod_luck_meteor_burst', meteor_burst, '3d', 92, (3500, 32000, 36000)),
    ('tod_luck_clover_fall', clover_fall, '3d_loop', 78, (400, 6000, 7000)),
    ('tod_luck_clover_land', clover_land, '3d', 86, (300, 3000, 3500)),
    ('tod_luck_golden_spawn', golden_spawn, '2d', 80, None),
    ('tod_luck_golden_loop', golden_loop, '3d_loop', 70, (150, 1500, 1800)),
    ('tod_luck_golden_death', golden_death, '3d', 92, (400, 4000, 4500)),
    ('tod_luck_golden_jackpot', golden_jackpot, '2d', 86, None),
]
LOOP_SECS = {'tod_luck_meteor_loop': 2.0, 'tod_luck_clover_fall': 1.0, 'tod_luck_golden_loop': 2.0}


def render():
    """name -> wav bytes, all nine synthesised in memory"""
    out = {}
    for name, synth, kind, _, _ in SOUNDS:
        x = synth()
        if kind == '3d_loop':
            want = int(round(LOOP_SECS[name] * SR))
            assert len(x) == want, '%s is %d samples, not exactly %d' % (name, len(x), want)
        out[name] = encode(x)
    return out


def alias_csv():
    """sound/aliases/tod_luck.csv as bytes: tod_ui.csv's header row verbatim, one row per sound, CRLF like its siblings"""
    header_line = HEADER_FROM.read_text(encoding='utf-8-sig').splitlines()[0]
    header = next(csv.reader([header_line]))
    col = {h: i for i, h in enumerate(header)}
    lines = [header_line]
    for name, _, kind, vol, dist in SOUNDS:
        r = [''] * len(header)
        r[col['Name']] = name
        r[col['FileSpec']] = 'tod\\luck\\' + name + '.wav'
        r[col['Template']] = 'UIN_MOD'
        r[col['VolMin']] = r[col['VolMax']] = str(vol)
        # EVERY row on the effects bus: these are world sounds (a meteor, a golden zombie, a drop). Left empty, the
        # UIN_MOD template puts them on bus_ui / grp_menu - the menu's bus - which every other in-world 3D sound in this
        # map avoids (tod_jump.csv rides BUS_FX).
        r[col['Bus']] = 'BUS_FX'
        if kind == '2d':                                              # tod_jump.csv's tod_jt_boom
            r[col['PanType']] = '2d'
        else:                                                         # tod_sky.csv's tod_sky_worm_burst / tod_sky_drone
            r[col['DistMin']], r[col['DistMaxDry']], r[col['DistMaxWet']] = (str(d) for d in dist)
            r[col['PitchMin']] = r[col['PitchMax']] = '0'
            r[col['PanType']] = '3d'
        r[col['Looping']] = 'LOOPING' if kind == '3d_loop' else 'NONLOOPING'
        assert not any(c in v for v in r for c in ',"\r\n'), name + ': a field would need csv quoting'
        lines.append(','.join(r))
    return ('\r\n'.join(lines) + '\r\n').encode('utf-8')


def szc_loads_luck(text):
    """does the sound zone config load tod_luck.csv as an ALIAS source?"""
    try:
        data = json.loads(text)
    except ValueError:
        return False
    return any(isinstance(s, dict) and s.get('Type') == 'ALIAS' and str(s.get('Filename', '')).lower() == 'tod_luck.csv'
               for s in data.get('Sources', []))


def szc_register():
    """add the tod_luck ALIAS source if it is missing: a text copy of the tod_sky entry (so the file keeps whatever
    style it has) placed right after tod_jump (the generated feature banks sit together at the top). True if added."""
    raw = SZC.read_bytes()
    bom = b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
    text = raw[len(bom):].decode('utf-8')
    if szc_loads_luck(text):
        return False

    def entry(filename):
        return re.search(r'([ \t]*)(\{[^{}]*"Filename"\s*:\s*"' + re.escape(filename) + r'"[^{}]*\})', text)

    tpl = entry('tod_sky.csv')
    if not tpl:
        raise SystemExit('LUCKY SOUNDS: no tod_sky entry in %s to copy - add the tod_luck ALIAS source by hand' % SZC)
    anchor = entry('tod_jump.csv') or tpl
    nl = '\r\n' if '\r\n' in text else '\n'
    clone = tpl.group(2).replace('"tod_sky.csv"', '"tod_luck.csv"').replace('"tod_sky"', '"tod_luck"')
    new = text[:anchor.end()] + ',' + nl + tpl.group(1) + clone + text[anchor.end():]
    if not szc_loads_luck(new):
        raise SystemExit('LUCKY SOUNDS: %s would not parse with tod_luck added - left untouched' % SZC)
    SZC.write_bytes(bom + new.encode('utf-8'))
    return True


def describe(data):
    with wave.open(io.BytesIO(data)) as w:
        return '%.3f s, %d ch, %d Hz' % (w.getnframes() / w.getframerate(), w.getnchannels(), w.getframerate())


def main():
    args = sys.argv[1:]
    wavs = render()
    if '--out' in args:                                               # a preview: the wavs only, somewhere else
        out_dir = pathlib.Path(args[args.index('--out') + 1])
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, data in wavs.items():
            (out_dir / (name + '.wav')).write_bytes(data)
            print('LUCKY SOUND PREVIEW', out_dir / (name + '.wav'), describe(data))
        return
    csv_bytes = alias_csv()
    if '--check' in args:
        bad = []
        for name, data in wavs.items():
            p = WAV_DIR / (name + '.wav')
            if not p.exists():
                bad.append(name + '.wav missing')
            elif p.read_bytes() != data:
                bad.append(name + '.wav differs')
        norm = lambda b: b.replace(b'\r\n', b'\n')
        if not CSV_PATH.exists():
            bad.append('sound/aliases/tod_luck.csv missing')
        elif norm(CSV_PATH.read_bytes()) != norm(csv_bytes):
            bad.append('sound/aliases/tod_luck.csv differs')
        if not SZC.exists() or not szc_loads_luck(SZC.read_bytes().decode('utf-8-sig')):
            bad.append('sound/zoneconfig/zm_tod2_cybercity.szc does not load tod_luck.csv')
        if bad:
            print('LUCKY SOUNDS STALE: ' + '; '.join(bad) + ' - ' + FIX)
            sys.exit(1)
        print('LUCKY SOUNDS OK: %d sounds' % len(wavs))
        return
    WAV_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in wavs.items():
        p = WAV_DIR / (name + '.wav')
        same = p.exists() and p.read_bytes() == data
        if not same:
            p.write_bytes(data)
        print('LUCKY SOUND', p.name, describe(data), '(unchanged)' if same else '(written)')
    if not (CSV_PATH.exists() and CSV_PATH.read_bytes() == csv_bytes):
        CSV_PATH.write_bytes(csv_bytes)
    print('LUCKY ALIASES sound/aliases/tod_luck.csv', [s[0] for s in SOUNDS])
    if szc_register():
        print('LUCKY SOUNDS: registered tod_luck.csv in sound/zoneconfig/zm_tod2_cybercity.szc')


if __name__ == '__main__':
    main()
