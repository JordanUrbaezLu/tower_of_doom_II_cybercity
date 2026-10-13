"""THE SKY FLEET sounds (docs/192): synthesised, deterministic, re-runnable.

  python tools/sky_ships/make_sounds.py

  sound_assets/tod/sfx/tod_sky_drone.wav   a capital ship's engines: beating low tones over a band of engine
                                           noise, slowly breathing. A SEAMLESS 8 s loop (every tone completes
                                           whole cycles and the noise is shaped in the frequency domain, which is
                                           circular), played on the ship so it grows and fades as it passes.
  sound_assets/tod/sfx/tod_sky_jet.wav     a fighter wing's jet hiss, seamless 4 s loop, played on the wing lead.
  v3 THE WORMHOLE (docs/192 s10), one-shots played at the rift (3D, heard across the sky, under combat):
  sound_assets/tod/sfx/tod_sky_worm_open.wav   the rift tearing open: a sub swell, a rising resonant whoosh, electric
                                               crackle building to the burst (1.6 s in), then a humming tail
  sound_assets/tod/sfx/tod_sky_worm_burst.wav  the ship bursting through: an electric crack, a deep falling boom, a passing
                                               whoosh, a long rumbling tail with a late echo
  sound_assets/tod/sfx/tod_sky_worm_close.wav  the collapse: a reverse suck rising in pitch, a pop, a fizzle
  sound/aliases/tod_sky.csv                the aliases (columns taken from tod_ui.csv's header).

Levels sit UNDER combat on purpose (ships are scenery). The v1 warp boom is RETIRED with v2 (ships arrive from
far away); its wav and aliases are removed by this script.
Mono 48 kHz 16-bit (3D sources). Replace any wav with a recorded sound of the same name to upgrade it.
"""
import csv, io, pathlib, sys, wave
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
SR = 48000
OUT = ROOT / 'sound_assets/tod/sfx'


def shaped_noise(n, lo, hi, seed, tilt=0.0):
    """White noise band-limited to lo..hi Hz in the frequency domain (circular = loops seamlessly).
    tilt < 0 leans toward the low end (e.g. -1 = pink-ish)."""
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


def chirp(t, f0, f1, k):
    """Exponential glide f(t) = f1 + (f0 - f1) e^(-k t), integrated to a phase."""
    phase = 2 * np.pi * (f1 * t + (f0 - f1) / k * (1 - np.exp(-k * t)))
    return np.sin(phase)


def delay(x, secs, gain, lp=None):
    d = int(secs * SR)
    y = np.zeros_like(x)
    y[d:] = x[:-d] * gain
    if lp:
        spec = np.fft.rfft(y)
        f = np.fft.rfftfreq(len(y), 1.0 / SR)
        y = np.fft.irfft(spec / (1 + (f / lp) ** 2), len(y))
    return y


def write(name, x, peak_db):
    x = x / (np.max(np.abs(x)) + 1e-12) * (10 ** (peak_db / 20))
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype('<i2')
    path = OUT / (name + '.wav')
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return path




def drone():
    n = 8 * SR; t = np.arange(n) / SR                 # 8 s: 41, 41.5, 82, 123 Hz and the 0.25 Hz breath all close
    tones = (0.36 * np.sin(2 * np.pi * 41 * t) + 0.26 * np.sin(2 * np.pi * 41.5 * t)
             + 0.16 * np.sin(2 * np.pi * 82 * t) + 0.08 * np.sin(2 * np.pi * 123 * t))
    body = shaped_noise(n, 55, 320, 21, tilt=-1.0) * 0.55
    hiss = shaped_noise(n, 900, 2600, 22) * 0.06
    breath = 0.82 + 0.18 * np.sin(2 * np.pi * 0.25 * t)
    return write('tod_sky_drone', (tones + body + hiss) * breath, -3.0)


def jet():
    n = 4 * SR; t = np.arange(n) / SR
    hiss = shaped_noise(n, 500, 5200, 31, tilt=-0.6)
    roar = shaped_noise(n, 70, 420, 32, tilt=-1.0) * 0.55
    whine = 0.07 * np.sin(2 * np.pi * (1150 * t + 6 * np.sin(2 * np.pi * 0.5 * t)))   # vibrato closes in 4 s
    pulse = 0.9 + 0.1 * np.sin(2 * np.pi * 1.0 * t)
    return write('tod_sky_jet', (hiss + roar + whine) * pulse, -3.0)


def env(t, a, d):
    """attack a s, then an exponential-ish decay over d s"""
    return np.clip(t / max(a, 1e-4), 0, 1) * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))


def crackle(n, seed, rate, lo=1800, hi=7000, start=0.0, ramp=None):
    """electric crackle: sparse short bursts of band noise, density rising along `ramp` (0..1 per sample)"""
    rng = np.random.default_rng(seed)
    band = shaped_noise(n, lo, hi, seed + 1)
    out = np.zeros(n)
    t = np.arange(n) / SR
    dens = ramp if ramp is not None else np.ones(n)
    i = int(start * SR)
    while i < n - 1:
        gap = rng.exponential(1.0 / (rate * max(dens[i], 0.05)))
        i += max(1, int(gap * SR))
        if i >= n:
            break
        L = int(rng.uniform(0.004, 0.03) * SR)
        seg = slice(i, min(n, i + L))
        k = np.arange(seg.stop - seg.start)
        out[seg] += band[seg] * np.exp(-k / (0.25 * L + 1)) * rng.uniform(0.4, 1.0) * dens[i]
    return out


def worm_open():
    n = int(2.4 * SR); t = np.arange(n) / SR
    rise = np.clip(t / 1.6, 0, 1)
    sub = np.sin(2 * np.pi * (34 * t + 9 * t * t)) * (0.2 + 0.8 * rise ** 1.5) * np.exp(-np.maximum(t - 1.7, 0) / 0.5)
    whoosh = shaped_noise(n, 120, 2600, 41, tilt=-0.6)
    # a rising resonance: the band noise through a sweeping comb (a pitched "tear")
    f = 180 + 900 * rise ** 2
    phase = 2 * np.pi * np.cumsum(f) / SR
    tear = whoosh * (0.55 + 0.45 * np.sin(phase)) * (0.15 + 0.85 * rise ** 2) * np.exp(-np.maximum(t - 1.6, 0) / 0.35)
    shimmer = 0.12 * np.sin(2 * np.pi * (620 * t + 4 * np.sin(2 * np.pi * 7 * t))) * rise * np.exp(-np.maximum(t - 1.6, 0) / 0.6)
    crack = crackle(n, 43, 26, start=0.2, ramp=0.2 + 0.8 * rise ** 1.3) * 0.7
    hum = 0.18 * np.sin(2 * np.pi * 55 * t) * np.clip((t - 1.4) / 0.3, 0, 1) * np.exp(-np.maximum(t - 1.7, 0) / 0.4)
    fade = np.clip((2.4 - t) / 0.3, 0, 1) * np.clip(t / 0.05, 0, 1)
    return write('tod_sky_worm_open', (0.9 * sub + 0.8 * tear + shimmer + crack + hum) * fade, -2.0)


def worm_burst():
    n = int(3.0 * SR); t = np.arange(n) / SR
    snap = crackle(n, 51, 400, 1500, 9000, 0.0, ramp=np.exp(-t / 0.08)) * 1.2
    boom = np.sin(2 * np.pi * (30 * t + (85 - 30) / 3.5 * (1 - np.exp(-3.5 * t)))) * env(t, 0.006, 0.55)
    thump = shaped_noise(n, 30, 240, 52, tilt=-1.0) * env(t, 0.004, 0.25)
    # a passing whoosh: band noise whose centre falls (a doppler sweep) and fades
    hiss = shaped_noise(n, 400, 6000, 53, tilt=-0.4)
    sweep = hiss * env(t, 0.03, 0.5) * (0.6 + 0.4 * np.sin(2 * np.pi * (6 * t)))
    rumble = shaped_noise(n, 25, 160, 54, tilt=-1.0) * env(t, 0.05, 1.4) * 0.8
    dry = snap + 1.1 * boom + 0.8 * thump + 0.5 * sweep + rumble
    wet = dry + delay(dry, 0.23, 0.35, lp=900) + delay(dry, 0.51, 0.2, lp=500)
    fade = np.clip((3.0 - t) / 0.4, 0, 1)
    return write('tod_sky_worm_burst', wet * fade, -1.0)


def worm_close():
    n = int(1.7 * SR); t = np.arange(n) / SR
    suck = np.clip(t / 0.6, 0, 1) ** 2
    rev = shaped_noise(n, 200, 4000, 61, tilt=-0.5) * suck * (t < 0.62)
    f = 120 + 700 * suck
    tone = 0.3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * suck * (t < 0.62)
    tp = np.maximum(t - 0.62, 0)
    pop = (np.sin(2 * np.pi * (60 * tp + (140 - 60) / 6 * (1 - np.exp(-6 * tp)))) * env(tp, 0.002, 0.18) * (t >= 0.62)
           + shaped_noise(n, 800, 5000, 62) * env(tp, 0.001, 0.05) * (t >= 0.62) * 0.6)
    fizz = crackle(n, 63, 60, 2500, 9000, 0.62, ramp=np.exp(-tp / 0.35)) * 0.5
    fade = np.clip((1.7 - t) / 0.2, 0, 1)
    return write('tod_sky_worm_close', (0.8 * rev + tone + 1.2 * pop + fizz) * fade, -2.0)


# ALIAS PITCH IS IN CENT (stock rows: -200 / 200 = +-2 semitones). The first cut wrote 92/106, 100/100 ...
# as if they were percentages, which played every sky sound about a semitone sharp.
ALIASES = [
    # name, file, looping, vol, dist_min, dist_max_dry, dist_max_wet, pitch_min (cents), pitch_max (cents)
    ('tod_sky_drone', 'tod_sky_drone.wav', True, 72, 2500, 20000, 22000, 0, 0),
    ('tod_sky_jet', 'tod_sky_jet.wav', True, 66, 1200, 11000, 12000, -60, 60),
    # v3 the rift (a far event: the rift is drawn 5,000..12,000 units away, so it carries across the sky, under combat)
    ('tod_sky_worm_open', 'tod_sky_worm_open.wav', False, 80, 3500, 30000, 34000, -80, 80),
    ('tod_sky_worm_burst', 'tod_sky_worm_burst.wav', False, 86, 3500, 32000, 36000, -60, 60),
    ('tod_sky_worm_close', 'tod_sky_worm_close.wav', False, 76, 3500, 28000, 32000, -80, 80),
]


def aliases():
    header = next(csv.reader(io.StringIO((ROOT / 'sound/aliases/tod_ui.csv').read_text(encoding='utf-8').splitlines()[0])))
    col = {h: i for i, h in enumerate(header)}
    rows = [header]
    for name, wav, loop, vol, dmin, ddry, dwet, pmin, pmax in ALIASES:
        r = [''] * len(header)
        r[col['Name']] = name
        r[col['FileSpec']] = 'tod\\sfx\\' + wav
        r[col['Template']] = 'UIN_MOD'
        r[col['VolMin']] = r[col['VolMax']] = str(vol)
        r[col['DistMin']] = str(dmin)
        r[col['DistMaxDry']] = str(ddry)
        r[col['DistMaxWet']] = str(dwet)
        r[col['PitchMin']] = str(pmin)
        r[col['PitchMax']] = str(pmax)
        r[col['PanType']] = '3d'
        r[col['Looping']] = 'LOOPING' if loop else 'NONLOOPING'
        rows.append(r)
    buf = io.StringIO()
    csv.writer(buf, lineterminator='\n').writerows(rows)
    (ROOT / 'sound/aliases/tod_sky.csv').write_text(buf.getvalue(), encoding='utf-8')


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    old = OUT / 'tod_sky_warp.wav'                  # retired with v2 (ships no longer warp in)
    if old.exists():
        old.unlink()
        print('SKY SOUND RETIRED', old.name)
    if '--out' in sys.argv:                          # a preview: write the wavs somewhere else, no aliases
        OUT = pathlib.Path(sys.argv[sys.argv.index('--out') + 1]); OUT.mkdir(parents=True, exist_ok=True)
        globals()['OUT'] = OUT
        for p in (drone(), jet(), worm_open(), worm_burst(), worm_close()):
            print('SKY SOUND PREVIEW', p)
        sys.exit(0)
    made = [drone(), jet(), worm_open(), worm_burst(), worm_close()]
    aliases()
    for p in made:
        with wave.open(str(p)) as w:
            print('SKY SOUND', p.name, '%.2f s' % (w.getnframes() / w.getframerate()))
    print('SKY ALIASES sound/aliases/tod_sky.csv', [a[0] for a in ALIASES])
