"""THE FIRST JUMP'S CRASH - its sounds (docs/196 §4), GENERATED - never hand-edit the wavs.

  python tools/jump_title/make_sounds.py [--out DIR]    write sound_assets/tod/jump/tod_jt_*.wav
  python tools/jump_title/make_sounds.py --check        FAIL if an output is missing or not the shape and loudness the
                                                        aliases and the scene expect (length, channels, level, where
                                                        the energy sits in time)

Second pass (2026-09-30, the user after playing it: "the explosion should use an actual loud boom instead of the nuke
sfx. And the ships should have some sound effect before the boom of flying spaceships"). What the first pass got
wrong, measured: its boom was built on the zombies Nuke power-up, whose real bang lands 1.5 s AFTER the flash (the
recording's own lead-in), and the ships were 7..20 dB under the balcony music (-9..-11 LUFS, the map's music never
ducks): an idle jet hiss at alias volume 74 and ~8,000 u away, a -15.5 LUFS charge. Every cue below is mixed to read
OVER that music. Real recordings already on this machine (read-only) carry the body of each; numpy shapes, glides and
pans them (scipy for the filters), ffmpeg decodes and masters:

  tod_jt_boom    THE crash: a real explosion that hits ON the flash. Treyarch's rocket explosion (the crack of the hulls
                 meeting), the Bazooka's big multi-stage blast a whole tone lower (the body and its rolling tail), the
                 large explosion the user picked for the C4 four semitones lower and spread wide (the size), the Mahem
                 blast under 150 Hz and an LFE drop (the chest hit), and the stock 'firey' blast for the burning debris.
                 Its loudest moment is inside the first 0.25 s; nothing of the Nuke is left.
  tod_jt_rumble  its rolling tail: the thunder recording a fourth lower, darkened, with two echoes (unchanged).
  tod_jt_warp    a gunship WARPING IN (mono: the alias pans it from the ship): the Fury's teleport bamf a third lower,
                 map 1's teleport warp and the LFE sweep hit (the first pass), plus its engines lighting as it drops out
                 of the warp (the Stinger's rocket ignition five semitones lower).
  tod_jt_engine  NEW - a gunship's engines while it hovers in the standoff (mono, a SEAMLESS 8 s loop, 3D on each
                 ship): the fleet's capital-ship drone underneath, the Bazooka's rocket motor (flattened, a fourth
                 lower, laid round the loop with crossfades so it never repeats audibly), a turbine whine with a slow
                 vibrato and a band of jet wash. Every tone completes whole cycles in 8 s and the noise is shaped in the
                 frequency domain, so the loop point is inaudible.
  tod_jt_charge  both engines flaring into the ram (stereo, 1.35 s: the impact lands at 1.2 s, the rest hides under the
                 boom): an afterburner kick from each side, then each ship's rocket roar climbing seven semitones as it
                 closes (the left ship from the left, the right from the right, both sweeping to the centre where they
                 meet), a turbine scream rising under them, a jet-wash whoosh sweeping up the spectrum and a sub swell.
  tod_jt_ignite  the sign's power surge: the electric zap, a thunk, SoE's machine power-up, a neon hum (unchanged).
"""
import json, os, pathlib, re, shutil, subprocess, sys, wave

import numpy as np

REPO = pathlib.Path(os.environ.get('TOD_REPO') or pathlib.Path(__file__).resolve().parents[2])
PRIVATE = pathlib.Path(os.environ.get('TOD_PRIVATE_TOOLS', r'C:\BO3Tools\TOD2Cybercity'))   # the workspace's own copy (read-only here)
MODTOOLS = pathlib.Path(os.environ.get('TOD_MODTOOLS', r'C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130'))
STOCK = PRIVATE if (PRIVATE / 'sound_assets').exists() else MODTOOLS
SRC = {
    'rocket_exp':  STOCK / 'sound_assets/skye_ports/t6_common/wpn_t6_rocket_explosion.wav',
    'bazooka_exp': STOCK / 'sound_assets/skye_ports/s2_bazooka/fire/wpn_s2_bazooka_explosion.wav',
    'mahem_exp':   STOCK / 'sound_assets/skye_ports/s1_mahem/fire/wpn_s1_mahem_explosion.wav',
    'bazooka_shot': STOCK / 'sound_assets/skye_ports/s2_bazooka/fire/wpn_s2_bazooka_shot.wav',
    'stinger_shot': STOCK / 'sound_assets/skye_ports/s1_stingerm7/fire/wpn_s1_stingerm7_shot.wav',
    'firey':       STOCK / 'sound_assets/exp/firey/exp_firey_03.wav',
    'sub3':        STOCK / 'sound_assets/evt/lfe_sweep_hits/lfe_sweep_hit_03.wav',
    'machine':     STOCK / 'sound_assets/zmb/level/zm_zod/beastmode/power/machine_start.wav',
    'bamf':        STOCK / 'sound_assets/zmb/ai/fury/bamf/bamf_in.wav',
    'c4':          REPO / 'sound_assets/tod/sfx/tod_c4_explode.wav',        # the user's "explosion large distant" (their C4)
    'thunder':     REPO / 'sound_assets/acc/fx/cj_thunder.wav',
    'drone':       REPO / 'sound_assets/tod/sfx/tod_sky_drone.wav',         # the sky fleet's capital-ship engines (8 s loop)
    'warp':        REPO / 'sound_assets/acc/fx/teleport_warp.wav',
    'zap':         REPO / 'sound_assets/acc/fx/electric_zap.wav',
}
OUT = REPO / 'sound_assets/tod/jump'
SR = 48000
# name -> (min s, max s, channels, measure, LUFS window, true peak dBFS max): what the aliases and the scene expect. The
# measure is 'I' (integrated) for beds and loops, 'M' (the loudest 400 ms) for the one-shots that must HIT: a boom
# judged by its average would be pushed flat into the limiter. The LUFS floors are the point of the second pass: the
# balcony music plays at -9..-11 LUFS integrated and never ducks.
SHAPE = {'tod_jt_warp':   (1.5, 2.0, 1, 'I', (-12.5, -8.5), -0.5),
         'tod_jt_engine': (7.99, 8.01, 1, 'I', (-14.0, -10.0), -0.5),
         'tod_jt_charge': (1.3, 1.4, 2, 'M', (-8.5, -5.5), -0.5),
         'tod_jt_boom':   (4.5, 5.5, 2, 'M', (-7.5, -4.5), -0.3),
         'tod_jt_rumble': (7.0, 9.5, 2, 'I', (-17.0, -12.0), -1.0),
         'tod_jt_ignite': (2.0, 3.0, 2, 'I', (-18.0, -12.0), -1.0)}

def _jp_secs(name):
    """a #define from _tod_jumppad.gsc (READ, never copied: a retimed ram re-times the charge on the next generation)."""
    src = (REPO / 'scripts/zm/zm_tod2_cybercity/_tod_jumppad.gsc').read_text(encoding='utf-8')
    m = re.search(r'(?m)^#define\s+' + name + r'\s+\(?\s*(-?[\d.]+)', src)
    assert m, '_tod_jumppad.gsc: #define %s not found' % name
    return float(m.group(1))


CHARGE_HIT = round(_jp_secs('TOD_JUMPPAD_CINE_IMPACT_AT') - _jp_secs('TOD_JUMPPAD_CINE_SHIPS_AT'), 3)   # the ram's length = the impact
                        # beat - the charge beat (= _tod_jump_title.csc TOD_JT_RUN_SECS, gated); 1.2 until the fifth pass, 1.1 since
ENGINE_LOOP = 8.0       # the engine loop's length: every tone below completes whole cycles in it
FF = shutil.which('ffmpeg') or 'ffmpeg'
FP = shutil.which('ffprobe') or 'ffprobe'


# ---- plumbing ------------------------------------------------------------------------------------------------------
def load(key, ch=2):
    """a source as float64 (n, ch) at 48 kHz."""
    r = subprocess.run([FF, '-v', 'error', '-i', str(SRC[key]), '-ac', str(ch), '-ar', str(SR), '-f', 'f32le', '-'],
                       capture_output=True)
    if r.returncode or not r.stdout:
        raise SystemExit('ffmpeg could not decode ' + str(SRC[key]) + ': ' + r.stderr.decode(errors='replace')[-400:])
    return np.frombuffer(r.stdout, np.float32).astype(np.float64).reshape(-1, ch)


def seg(x, t0, t1=None):
    return x[int(t0 * SR):(None if t1 is None else int(t1 * SR))]


def resample_at(x, pos):
    """x (n, ch) read at fractional sample positions pos (linear interpolation)."""
    pos = np.clip(pos, 0, len(x) - 1.000001)
    i = pos.astype(np.int64)
    f = (pos - i)[:, None]
    return x[i] * (1 - f) + x[i + 1] * f


def pitch(x, semis):
    """play x faster / slower: + semitones = higher and shorter."""
    r = 2.0 ** (semis / 12.0)
    return resample_at(x, np.arange(int(len(x) / r)) * r)


def glide(x, rate, n):
    """n samples of x read at a time-varying rate (1 = as recorded): a pitch glide. rate: (n,) array."""
    pos = np.concatenate([[0.0], np.cumsum(rate[:-1])])
    return resample_at(x, pos)


def filt(x, kind, fc, order=4):
    from scipy import signal                                  # generating only: --check needs numpy alone
    sos = signal.butter(order, fc, btype=kind, fs=SR, output='sos')
    return signal.sosfiltfilt(sos, x, axis=0)


def fade(x, t_in=0.0, t_out=0.0):
    y = x.copy()
    n = len(y)
    if t_in > 0:
        k = min(n, int(t_in * SR))
        y[:k] *= (np.sin(np.linspace(0, np.pi / 2, k)) ** 2)[:, None]
    if t_out > 0:
        k = min(n, int(t_out * SR))
        y[n - k:] *= (np.cos(np.linspace(0, np.pi / 2, k)) ** 2)[:, None]
    return y


def place(dst, x, t, gain=1.0):
    i = int(round(t * SR))
    if i >= len(dst):
        return
    k = min(len(x), len(dst) - i)
    dst[i:i + k] += x[:k] * gain


def stereo(x, pan=0.0):
    """mono (n, 1) or (n,) -> (n, 2), equal-power pan -1 (left) .. +1 (right)."""
    m = x.reshape(-1)
    a = (pan + 1) * np.pi / 4
    return np.stack([m * np.cos(a), m * np.sin(a)], axis=1)


def flatten(x, win=0.12):
    """divide out the slow loudness envelope: a steady texture from a recording that swells and decays."""
    m = np.sqrt(np.mean(x ** 2, axis=1))
    w = int(win * SR)
    env = np.sqrt(np.convolve(m ** 2, np.ones(w) / w, mode='same')) + 1e-4
    y = x / env[:, None]
    return y / (np.max(np.abs(y)) + 1e-12)


def shaped_noise(n, lo, hi, seed, tilt=0.0):
    """white noise band-limited in the frequency domain (circular: it loops seamlessly at length n)."""
    rng = np.random.default_rng(seed)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    gain = np.clip(np.minimum((f - lo * 0.8) / (lo * 0.2), (hi * 1.2 - f) / (hi * 0.2)), 0, 1)
    with np.errstate(divide='ignore'):
        gain = gain * np.where(f > 0, (np.maximum(f, 1) / max(lo, 1)) ** (tilt / 2), 0)
    y = np.fft.irfft(spec * gain, n)
    return y / (np.max(np.abs(y)) + 1e-12)


def sweep_noise(n, fc, bw_oct, seed):
    """noise through a band-pass whose centre follows fc (n,) Hz: an STFT filter (Hann, 75% overlap)."""
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n + 4096)
    N, hop = 2048, 512
    win = np.hanning(N)
    out = np.zeros(n + 4096)
    norm = np.zeros(n + 4096)
    f = np.fft.rfftfreq(N, 1.0 / SR)
    for s in range(0, n, hop):
        c = fc[min(n - 1, s + N // 2)]
        g = np.exp(-0.5 * (np.log2(np.maximum(f, 1) / c) / (bw_oct / 2)) ** 2)
        blk = np.fft.irfft(np.fft.rfft(x[s:s + N] * win) * g, N)
        out[s:s + N] += blk * win
        norm[s:s + N] += win ** 2
    y = out[:n] / np.maximum(norm[:n], 1e-6)
    return y / (np.max(np.abs(y)) + 1e-12)


def saturate(x, drive):
    """a soft clip (tanh) against the loudest 0.5% of the mix: denser, louder, the envelope kept (a real blast
    overloads the air and the microphone the same way)."""
    ref = np.percentile(np.abs(x), 99.5) + 1e-12
    return np.tanh(drive * x / ref) / np.tanh(drive)


def write_wav(path, x):
    x = np.clip(x, -1.0, 1.0)
    pcm = (x * 32767.0).round().astype('<i2')
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def loudness(p):
    """-> (integrated LUFS, true peak dBFS, momentary max LUFS) of a wav."""
    r = subprocess.run([FF, '-hide_banner', '-nostats', '-i', str(p), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True)
    s = r.stderr[r.stderr.rfind('Summary:'):]
    i = re.findall(r'I:\s+(-?[\d.]+) LUFS', s)
    pk = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', s)
    mom = [float(v) for v in re.findall(r'M:\s*(-?[\d.]+)', r.stderr[:r.stderr.rfind('Summary:')])]
    return (float(i[0]) if i else None), (float(pk[0]) if pk else None), (max(mom) if mom else None)


def master(x, out, target, ceiling_db, loop=False, by="I", max_gr=4.0):
    """gain to hit `target` LUFS (by "I" integrated, or "M" the loudest 400 ms: a one-shot keeps its own decay)
    through a look-ahead limiter (ffmpeg alimiter, never pushed more than `max_gr` dB past its ceiling so a hit keeps
    its punch), then a trim so the TRUE peak sits under `ceiling_db`. A loop is limited as three copies end to end
    and the middle one kept, so the limiter has no edge at the loop point."""
    tmp = out.with_suffix('.mix.wav')
    lim = out.with_suffix('.lim.wav')
    gain_db, limit = 0.0, 10 ** ((ceiling_db - 0.6) / 20)
    top = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
    for _ in range(8):
        gain_db = min(gain_db, (ceiling_db - 0.6 + max_gr) - top)
        y = x * 10 ** (gain_db / 20)
        src = np.concatenate([y, y, y]) if loop else y
        peak = np.max(np.abs(src))
        pre = 0.98 / peak if peak > 0.98 else 1.0            # the float mix may exceed full scale: the limiter gets it all
        write_wav(tmp, src * pre)
        run(['-i', str(tmp), '-af', f'volume={1 / pre:.6f},alimiter=limit={limit:.4f}:attack=1:release=60:level=0:asc=1',
             '-ar', str(SR), '-c:a', 'pcm_f32le', str(lim)])
        y2 = read_f32(lim)
        if loop:
            n = len(x)
            y2 = y2[n:2 * n]
        write_wav(out, y2)
        i, pk, m = loudness(out)
        if pk is not None and pk > ceiling_db:                # an intersample over: trim it away
            y2 = y2 * 10 ** ((ceiling_db - 0.05 - pk) / 20)
            write_wav(out, y2)
            i, pk, m = loudness(out)
        i = m if by == 'M' else i
        capped = gain_db >= (ceiling_db - 0.6 + max_gr) - top - 1e-6
        if i is None or abs(i - target) < 0.3 or (capped and i < target):
            break
        gain_db += target - i
    for p in (tmp, lim):
        p.unlink(missing_ok=True)


def read_f32(p):
    """any wav (16-bit or float) as float64 (n, ch), through ffmpeg."""
    r = subprocess.run([FP, '-v', 'error', '-show_entries', 'stream=channels', '-of', 'csv=p=0', str(p)], capture_output=True, text=True)
    ch = int(r.stdout.strip().splitlines()[0])
    r = subprocess.run([FF, '-v', 'error', '-i', str(p), '-f', 'f32le', '-'], capture_output=True)
    return np.frombuffer(r.stdout, np.float32).astype(np.float64).reshape(-1, ch)


def run(args):
    r = subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y'] + args, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit('ffmpeg failed: ' + r.stderr[-800:])


# ---- the cues ------------------------------------------------------------------------------------------------------
def boom(out):
    n = int(5.0 * SR)
    mix = np.zeros((n, 2))
    place(mix, filt(load('rocket_exp'), 'highpass', 160), 0.000, 0.85)                  # the crack: the hulls meet
    body = pitch(load('bazooka_exp'), -2.0)                                              # the body and its rolling tail,
    tb = np.arange(len(body)) / SR                                                       # held for the first hit, then rolling
    body *= np.where(tb < 0.35, 1.0, np.exp(-(tb - 0.35) / 0.9) * 0.8 + 0.2 * np.exp(-(tb - 0.35) / 3.0))[:, None]
    place(mix, body, 0.004, 1.00)
    c4 = filt(pitch(load('c4', 1), -4.0), 'highpass', 45)
    wide = np.stack([c4[:, 0], np.concatenate([np.zeros(int(0.011 * SR)), c4[:-int(0.011 * SR), 0]])], axis=1)
    place(mix, wide, 0.020, 0.62)                                                       # the size, spread wide
    place(mix, filt(load('mahem_exp'), 'lowpass', 150), 0.000, 1.10)                    # the chest hit
    place(mix, stereo(filt(load('sub3', 1), 'lowpass', 120)), 0.000, 0.70)               # the LFE drop
    place(mix, filt(pitch(load('firey'), -3.0), 'highpass', 250), 0.30, 0.45)            # burning debris
    tm = np.arange(n) / SR                                                              # a blast, then its roll: the hit stays on top
    roll = 9.0 * np.clip((tm - 0.2) / 0.8, 0, 1) + 9.0 * np.clip((tm - 1.0) / 1.5, 0, 2.0)   # -9 dB by 1 s, -18 by 2.5
    mix *= 10 ** (-roll / 20)[:, None]
    mix = saturate(fade(mix, 0.0, 1.2), 1.6)
    master(mix, out, target=-6.0, ceiling_db=-0.8, by='M', max_gr=8.0)


def rumble(out):
    run(['-i', str(SRC['thunder']), '-filter_complex',
         '[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asetrate=36000,aresample=48000,lowpass=f=700,'
         'aecho=0.85:0.55:110|190:0.35|0.25,afade=t=in:st=0:d=0.45,afade=t=out:st=5.2:d=3.0,volume=2.6,'
         'alimiter=limit=0.79:level=0,atrim=0:8.2',
         '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', str(out)])


def warp(out):
    n = int(1.8 * SR)
    mix = np.zeros((n, 1))
    place(mix, pitch(load('bamf', 1), -4.0), 0.0, 1.0)                                  # the Fury's bamf, ship-sized
    place(mix, seg(load('warp', 1), 0, 1.6), 0.0, 1.6)                                  # the electric tear
    place(mix, filt(seg(load('sub3', 1), 0, 1.6), 'lowpass', 160), 0.0, 0.85)           # the sub hit
    ign = filt(fade(pitch(load('stinger_shot', 1), -5.0), 0.04, 0.5), 'lowpass', 6000)
    place(mix, ign, 0.18, 0.55)                                                         # its engines light up
    mix = fade(mix, 0.0, 0.45)
    master(mix, out, target=-10.5, ceiling_db=-1.0, max_gr=7.0)


def engine(out):
    L = ENGINE_LOOP
    n = int(L * SR)
    t = np.arange(n) / SR
    bed = load('drone', 1)[:n, 0]                                                       # the fleet's capital-ship drone (8 s loop)
    bed = np.pad(bed, (0, max(0, n - len(bed))))
    # the rocket motor, flattened and a fourth lower, laid round the loop three times with crossfades (circular)
    motor = flatten(seg(load('bazooka_shot', 1), 0.40, 3.40))
    motor = filt(pitch(motor, -5.0), 'lowpass', 5200)[:, 0]
    tex = np.zeros(n)
    cnt, xf = 3, int(0.55 * SR)
    span = n // cnt
    w = np.ones(span + xf)
    w[:xf] = np.sin(np.linspace(0, np.pi / 2, xf)) ** 2
    w[-xf:] = np.cos(np.linspace(0, np.pi / 2, xf)) ** 2
    for k in range(cnt):
        start = int((0.12 * k) * SR)
        grain = motor[start:start + span + xf]
        grain = np.pad(grain, (0, span + xf - len(grain))) * w
        idx = (np.arange(span + xf) + k * span) % n
        np.add.at(tex, idx, grain)
    # a turbine whine with a slow vibrato (whole cycles in 8 s: 312.5 Hz x 8 = 2500, vibrato 4.5 Hz x 8 = 36)
    ph = 2 * np.pi * 312.5 * t - (2.2 / 4.5) * np.cos(2 * np.pi * 4.5 * t)          # f = 312.5 + 2.2 sin(2 pi 4.5 t)
    whine = 0.6 * np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
    whine *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.625 * t)                                 # 5 swells per loop
    # the engines' pulse: a slow throb on the low end (1.25 Hz x 8 = 10 whole cycles)
    throb = 0.8 + 0.2 * np.sin(2 * np.pi * 1.25 * t)
    wash = shaped_noise(n, 300, 2400, seed=196, tilt=-1.0)                              # the jet wash (circular)
    mix = (0.55 * bed * throb + 0.60 * tex / (np.max(np.abs(tex)) + 1e-9) + 0.17 * whine + 0.22 * wash)
    master(mix[:, None], out, target=-11.5, ceiling_db=-1.0, loop=True, max_gr=6.0)


def charge(out):
    T, hit = 1.35, CHARGE_HIT
    n = int(T * SR)
    t = np.arange(n) / SR
    x = np.clip(t / hit, 0, 1)
    mix = np.zeros((n, 2))
    # 1. the afterburner kick on each side (the right ship a beat later)
    kick = filt(filt(fade(seg(load('bazooka_shot', 1), 0.0, 0.5), 0.0, 0.2), 'lowpass', 5000), 'highpass', 90)
    place(mix, stereo(kick, -0.75), 0.000, 0.16)
    place(mix, stereo(kick, 0.75), 0.035, 0.16)
    # 2. each ship's rocket roar climbing seven semitones as it closes, panned from its side to the centre
    motor = flatten(seg(load('bazooka_shot', 1), 0.40, 3.40))
    amp = (0.16 + 0.84 * x ** 2.2) * np.where(t < hit, 1.0, np.clip(1 - (t - hit) / 0.12, 0, 1))
    for side, off, detune in ((-1, 0.0, 1.0), (1, 0.45, 1.035)):
        rate = 2.0 ** ((-4.0 + 7.0 * x ** 1.6) / 12.0) * detune
        roar = filt(filt(glide(seg(motor, off), rate, n), 'lowpass', 7000), 'highpass', 110)[:, 0] * amp
        pan = side * (0.85 - 0.6 * x ** 1.3)
        a = (pan + 1) * np.pi / 4
        mix += np.stack([roar * np.cos(a), roar * np.sin(a)], axis=1) * 0.75
    # 3. the turbine scream rising under them (slightly detuned left / right: two engines)
    for ch, det in ((0, 1.0), (1, 1.012)):
        f = 150.0 * (520.0 / 150.0) ** (x ** 1.4) * det
        ph = 2 * np.pi * np.cumsum(f) / SR
        buzz = sum(np.sin(h * ph) / h ** 0.9 for h in range(1, 7))
        mix[:, ch] += buzz * (0.05 + 0.40 * x ** 2) * amp
    # 4. the jet wash sweeping up the spectrum, and 5. a sub swell as the mass closes
    wash = sweep_noise(n, 500.0 * (5000.0 / 500.0) ** (x ** 1.3), 1.6, seed=4) * (0.08 + 0.7 * x ** 2.5) * amp
    mix += stereo(wash[:, None], 0.0) * 0.9
    sub = np.sin(2 * np.pi * np.cumsum(38.0 + 16.0 * x) / SR) * (0.1 + 0.5 * x ** 2) * amp
    mix += stereo(sub[:, None], 0.0) * 0.35
    master(saturate(mix, 1.3), out, target=-7.0, ceiling_db=-1.0, by='M', max_gr=6.0)


def ignite(out):
    hum = ('aevalsrc=(0.5*sin(2*PI*110*t)+0.3*sin(2*PI*220*t)+0.18*sin(2*PI*330*t)+0.12*sin(2*PI*440*t)'
           '+0.08*sin(2*PI*660*t))*(0.85+0.15*sin(2*PI*9*t))*min(1\\,t/0.55)*exp(-0.45*t):s=48000')
    st = lambda i: f'[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo'
    run(['-i', str(SRC['zap']),
         '-f', 'lavfi', '-t', '2.6', '-i', hum,
         '-f', 'lavfi', '-t', '0.35', '-i', 'aevalsrc=0.9*sin(2*PI*68*t)*exp(-11*t):s=48000',
         '-i', str(SRC['machine']),
         '-filter_complex',
         st(0) + ',volume=1.0[a];'
         '[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=0.45,'
         'afade=t=out:st=1.7:d=0.9[b];'
         '[2:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=0.9[c];'
         + st(3) + ',afade=t=out:st=2.1:d=0.5,volume=0.8[e];'
         '[a][b][c][e]amix=inputs=4:duration=longest:normalize=0,alimiter=limit=0.79:level=0,atrim=0:2.6',
         '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', str(out)])


# ---- the gate ------------------------------------------------------------------------------------------------------
def probe(p):
    r = subprocess.run([FP, '-v', 'error', '-show_entries', 'stream=sample_rate,channels,duration', '-of', 'json', str(p)],
                       capture_output=True, text=True)
    s = json.loads(r.stdout)['streams'][0]
    return int(s['sample_rate']), int(s['channels']), float(s['duration'])


def envelope(p, hop=0.05):
    x = read_f32(p)
    m = np.sqrt(np.mean(x ** 2, axis=1))
    k = int(hop * SR)
    return np.array([np.sqrt(np.mean(m[i:i + k] ** 2)) for i in range(0, len(m) - k + 1, k)])


def check(out_dir):
    bad = []
    for name, (lo, hi, want_ch, how, (lu_lo, lu_hi), pk_max) in SHAPE.items():
        p = out_dir / (name + '.wav')
        if not p.exists():
            bad.append(name + ' missing')
            continue
        sr, ch, dur = probe(p)
        if sr != 48000 or ch != want_ch or not (lo <= dur <= hi):
            bad.append(f'{name}: {sr} Hz {ch} ch {dur:.2f} s (want 48000 Hz {want_ch} ch {lo}..{hi} s)')
            continue
        i, pk, m = loudness(p)
        lu = m if how == 'M' else i
        if lu is None or not (lu_lo <= lu <= lu_hi) or pk is None or pk > pk_max:
            what = 'loudest 400 ms' if how == 'M' else 'integrated'
            bad.append(f'{name}: {what} {lu} LUFS / true peak {pk} dBFS (want {lu_lo}..{lu_hi} LUFS, peak <= {pk_max})')
        env = envelope(p)
        loud = int(np.argmax(env)) * 0.05
        if name == 'tod_jt_boom' and loud > 0.25:
            bad.append(f'tod_jt_boom: its loudest moment is {loud:.2f} s in (a boom must hit ON the flash, <= 0.25 s; the '
                       'first pass peaked at 1.50 s: the Nuke recording\'s own lead-in)')
        if name == 'tod_jt_charge':
            pre, end = env[:int(0.3 / 0.05)].mean(), env[int(1.0 / 0.05):int(CHARGE_HIT / 0.05)].mean()
            if not end > 2.0 * pre:
                bad.append(f'tod_jt_charge: it does not build into the impact (the last 0.2 s only {end / pre:.2f}x the start)')
        if name == 'tod_jt_engine':
            x = read_f32(p)[:, 0]
            k = int(0.05 * SR)
            step = np.percentile(np.abs(np.diff(x)), 99.9)                  # the largest ordinary sample-to-sample step
            jump = abs(float(x[-1]) - float(x[0]))                          # the step the loop point makes
            ra, rb = np.sqrt(np.mean(x[-k:] ** 2)), np.sqrt(np.mean(x[:k] ** 2))
            if jump > 1.5 * step or abs(20 * np.log10(ra / rb)) > 3.0:
                bad.append(f'tod_jt_engine: the loop point clicks or jumps (edge step {jump:.3f} vs {step:.3f}, level '
                           f'{20 * np.log10(ra / rb):+.1f} dB)')
    if bad:
        print('JUMP TITLE SOUNDS BAD: ' + '; '.join(bad))
        sys.exit(1)
    print('JUMP TITLE SOUNDS OK', len(SHAPE))


def main():
    out_dir = OUT
    if '--out' in sys.argv:
        out_dir = pathlib.Path(sys.argv[sys.argv.index('--out') + 1])
    if '--check' in sys.argv:
        check(out_dir)
        return
    missing = [k + ': ' + str(p) for k, p in SRC.items() if not p.exists()]
    if missing:
        raise SystemExit('missing sources: ' + '; '.join(missing))
    out_dir.mkdir(parents=True, exist_ok=True)
    only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None
    for name, fn in (('tod_jt_warp', warp), ('tod_jt_engine', engine), ('tod_jt_charge', charge), ('tod_jt_boom', boom),
                     ('tod_jt_rumble', rumble), ('tod_jt_ignite', ignite)):
        if only and name not in only:
            continue
        p = out_dir / (name + '.wav')
        fn(p)
        sr, ch, dur = probe(p)
        i, pk, m = loudness(p)
        print(f'{name}: {dur:.2f} s {sr} Hz {ch} ch, {i} LUFS (loudest 400 ms {m}), peak {pk} dBFS')


if __name__ == '__main__':
    main()
