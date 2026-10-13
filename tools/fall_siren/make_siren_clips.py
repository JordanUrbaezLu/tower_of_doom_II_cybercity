"""THE FALL SIREN, CUT FOR A TRUE LOOP (2026-09-29, user: "The Alarm does not stay on forever like
it should. It stops at some point and we need it to loop ... Should stop once door is bought").

Reads the 30 s nuclear-siren master sound_assets/tod/sfx/tod_fall_siren.wav (the user's YouTube
"Nuclear Alarm Siren", 0.7-30.7 s of the source; see docs/160 section 10.8) and WRITES three clips
beside it. Never hand-edit the outputs; change this script and re-run it.

  tod_fall_siren_start.wav  the wind-up: the master from 0 s to LOOP_START + XFADE, the last XFADE
                            seconds fading out. _tod_fall.gsc plays it, waits LOOP_START, then
                            starts the loop with PlayLoopSound( alias, XFADE ), so the two cross.
  tod_fall_siren_loop.wav   one seamless loop of whole wail cycles. The loop points are CHOSEN BY
                            MEASUREMENT (the pair of moments whose short spectra match best, then
                            aligned to the sample by cross-correlation) and the seam is a short
                            equal-gain crossfade into the audio that precedes the start point, so
                            the end flows into the start exactly as the recording flows.
  tod_fall_siren_stop.wav   the wind-down played when the escape gate is bought: steady siren tone
                            read with a falling playback rate (a motor spinning down: pitch and
                            level drop together) to silence.

Prints the chosen points and a seam check; `--check` re-derives everything in memory and fails if
the files on disk differ (the build does not run this; it is the recipe and its proof).
"""
import argparse
import os
import sys

import numpy as np
from scipy.io import wavfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SFX = os.path.join(ROOT, 'sound_assets', 'tod', 'sfx')
MASTER = os.path.join(SFX, 'tod_fall_siren.wav')
OUT = {k: os.path.join(SFX, 'tod_fall_siren_' + k + '.wav') for k in ('start', 'loop', 'stop')}

XFADE = 0.35             # s: wind-up -> loop handover (LOCKSTEP: TOD_FALL_SIREN_XFADE in _tod_fall.gsc)
SEAM = 0.30              # s: the loop's own seam crossfade (inside the loop file)
SEARCH_T0 = (2.6, 9.0)   # s: loop start candidates: after the wind-up has reached its steady tone
PERIODS = ((9.8, 12.6), (20.0, 23.8))   # s: one or two wail cycles (the pitch track repeats every ~11 s)
LOOP_END_MAX = 28.0      # s: the master fades from ~28.5 s; the loop never reaches the fade
STOP_SRC = (4.6, 8.4)    # s: steady tone the wind-down is read from
STOP_SECS = 3.2          # s: wind-down length (LOCKSTEP: TOD_FALL_SIREN_STOP_SECS in _tod_fall.gsc)
STOP_RATE_END = 0.28     # playback rate at the end of the wind-down (pitch falls to ~28 %)


def load():
    sr, x = wavfile.read(MASTER)
    if x.dtype != np.int16 or x.ndim != 2:
        sys.exit('master must be 16-bit stereo: ' + MASTER)
    return sr, x.astype(np.float64) / 32768.0


def spectra(mono, sr, t_list, win=4096):
    w = np.hanning(win)
    out = []
    for t in t_list:
        s = int(t * sr) - win // 2
        seg = mono[s:s + win]
        mag = np.abs(np.fft.rfft(seg * w))
        out.append(np.log1p(mag[:1200]))   # up to ~14 kHz at 48 kHz / 4096
    return np.array(out)


def choose_loop(x, sr):
    mono = x.mean(axis=1)
    step = 0.02
    grid = np.arange(SEARCH_T0[0], LOOP_END_MAX, step)
    S = spectra(mono, sr, grid)
    idx = {round(t, 2): i for i, t in enumerate(grid)}
    ctx = int(0.30 / step)   # compare 300 ms of context after each point
    best = None
    for i0, t0 in enumerate(grid):
        if t0 > SEARCH_T0[1]:
            break
        for lo, hi in PERIODS:
            for i1 in range(i0 + int(lo / step), min(len(grid) - ctx, i0 + int(hi / step) + 1)):
                t1 = grid[i1]
                if t1 > LOOP_END_MAX - 0.5:
                    break
                d = np.mean(np.abs(S[i0:i0 + ctx] - S[i1:i1 + ctx]))
                if best is None or d < best[0]:
                    best = (d, t0, t1)
    d, t0, t1 = best
    # sample-accurate alignment: shift the end point so the waveform just after it matches the start
    a = int(t0 * sr)
    b = int(t1 * sr)
    n = int(0.05 * sr)
    ref = mono[a:a + n]
    lag_max = int(0.006 * sr)
    scores = [(np.dot(ref, mono[b + k:b + k + n]) / (np.linalg.norm(ref) * np.linalg.norm(mono[b + k:b + k + n]) + 1e-12), k)
              for k in range(-lag_max, lag_max + 1)]
    corr, k = max(scores)
    return a, b + k, d, corr


def build(x, sr):
    a, b, dist, corr = choose_loop(x, sr)
    seam = int(SEAM * sr)
    # the loop is x[a:b]; its last `seam` samples cross into the audio just before `a`, so the
    # wrap (end -> start) continues the recording's own flow into x[a]
    loop = x[a:b].copy()
    ramp = np.linspace(0.0, 1.0, seam)[:, None]
    loop[-seam:] = loop[-seam:] * (1.0 - ramp) + x[a - seam:a] * ramp

    xf = int(XFADE * sr)
    start = x[:a + xf].copy()
    start[a:a + xf] *= np.linspace(1.0, 0.0, xf)[:, None]
    start[:int(0.004 * sr)] *= np.linspace(0.0, 1.0, int(0.004 * sr))[:, None]   # click-free first sample

    # the wind-down: variable-rate read of a steady stretch (rate 1 -> STOP_RATE_END, exponential)
    src = x[int(STOP_SRC[0] * sr):int(STOP_SRC[1] * sr)]
    n_out = int(STOP_SECS * sr)
    t = np.arange(n_out) / n_out
    rate = STOP_RATE_END ** t
    pos = np.cumsum(rate)
    pos -= pos[0]
    if pos[-1] >= len(src) - 2:
        sys.exit('wind-down source too short')
    i0 = pos.astype(np.int64)
    fr = (pos - i0)[:, None]
    stop = src[i0] * (1 - fr) + src[i0 + 1] * fr
    env = (1.0 - t) ** 1.6   # level falls with the motor
    stop *= env[:, None]
    stop[:int(0.004 * sr)] *= np.linspace(0.0, 1.0, int(0.004 * sr))[:, None]

    # seam proof: the wrap step must look like any ordinary sample step of the loop
    wrap = np.abs(loop[0] - loop[-1]).max()
    steps = np.abs(np.diff(loop, axis=0)).max(axis=1)
    info = {
        'loop_start_s': a / sr, 'loop_end_s': b / sr, 'loop_len_s': (b - a) / sr,
        'spectral_distance': float(dist), 'alignment_corr': float(corr),
        'wrap_step': float(wrap), 'p99_step': float(np.percentile(steps, 99)),
        'start_len_s': len(start) / sr, 'stop_len_s': len(stop) / sr,
    }
    return {'start': start, 'loop': loop, 'stop': stop}, info


def to16(y):
    return np.clip(np.round(y * 32768.0), -32768, 32767).astype(np.int16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='re-derive and compare with the files on disk')
    o = ap.parse_args()
    sr, x = load()
    clips, info = build(x, sr)
    for k, v in info.items():
        print(f'{k:18s} {v:.4f}')
    if info['wrap_step'] > 2.0 * info['p99_step']:
        sys.exit('FAIL: the loop seam is a visible step (%.4f vs p99 %.4f)' % (info['wrap_step'], info['p99_step']))
    bad = 0
    for k, y in clips.items():
        data = to16(y)
        if o.check:
            if not os.path.exists(OUT[k]):
                print('MISSING', OUT[k]); bad += 1; continue
            sr2, d2 = wavfile.read(OUT[k])
            same = sr2 == sr and d2.shape == data.shape and np.array_equal(d2, data)
            print(('ok   ' if same else 'DIFF ') + OUT[k]); bad += 0 if same else 1
        else:
            wavfile.write(OUT[k], sr, data)
            print('wrote', OUT[k], f'{len(data) / sr:.3f} s')
    if bad:
        sys.exit(1)
    print('XFADE', XFADE, 'LOOP_START', round(info['loop_start_s'], 4), 'STOP_SECS', STOP_SECS)


if __name__ == '__main__':
    main()
