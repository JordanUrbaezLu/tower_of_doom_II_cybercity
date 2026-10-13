#!/usr/bin/env python
"""With You: keep the vocal's MELODY, lose the voice (user 2026-10-01: "the vocals give it another layer of
melody that I still want to keep, but I don't want the vocals").

Three steps, each a subcommand, all offline:
  transcribe  the separated VOCAL stem -> MIDI (Spotify basic-pitch, pitch bends kept, short blips dropped)
  render      MIDI -> a synth layer that fits a melodic-house track: three detuned band-limited saws + a sine
              sub, amp/filter envelopes, delayed vibrato, chorus, a convolution reverb from a synthetic
              exponentially-decaying IR, high-passed at 150 Hz so it never fights the (bass-cut) low end
  mix         instrumental + synth layer, the layer sat N LU under the instrumental (measured, not guessed)
              -> the file tools/music_master.py masters as tod_music_withyou

Runs in the separation venv (scratchpad/sepenv): python <venv>/Scripts/python.exe tools/music_vocal_melody.py ...
"""
import argparse, math, os, re, subprocess, sys
import numpy as np

SR = 48000


# ----------------------------------------------------------------------------- transcribe
def transcribe(vocal_wav, out_mid, onset=0.5, frame=0.3, min_ms=110, fmin=140.0, fmax=1400.0):
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
    model_output, midi_data, note_events = predict(
        vocal_wav, ICASSP_2022_MODEL_PATH,
        onset_threshold=onset, frame_threshold=frame, minimum_note_length=min_ms,
        minimum_frequency=fmin, maximum_frequency=fmax, multiple_pitch_bends=False, melodia_trick=True)
    midi_data.write(out_mid)
    notes = [n for inst in midi_data.instruments for n in inst.notes]
    print('transcribed %d notes, %.1f s of melody -> %s' % (len(notes), sum(n.end - n.start for n in notes), out_mid))


# ----------------------------------------------------------------------------- render
def _notes(mid_path, min_len=0.11, min_vel=20, legato_gap=0.06):
    import pretty_midi
    pm = pretty_midi.PrettyMIDI(mid_path)
    notes = sorted((n for inst in pm.instruments for n in inst.notes if n.velocity >= min_vel and n.end - n.start >= min_len),
                   key=lambda n: n.start)
    # legato: a note that ends just before the next one starts is extended into it (sung lines slur)
    for i in range(len(notes) - 1):
        gap = notes[i + 1].start - notes[i].end
        if 0 < gap < legato_gap:
            notes[i].end = notes[i + 1].start
    return notes


def _saw(freq_env, sr, max_hz=12000.0, nh=48):
    """Band-limited saw by additive synthesis over a time-varying frequency (array)."""
    phase = np.cumsum(freq_env) / sr
    out = np.zeros_like(freq_env)
    fmax = float(np.max(freq_env))
    for k in range(1, nh + 1):
        if k * fmax > max_hz:
            break
        out += np.sin(2 * np.pi * k * phase) * ((-1) ** (k + 1)) / k
    return out * (2 / np.pi)


def _env(n, sr, a, d, s, r, gate_n):
    """ADSR over n samples; the gate is open for gate_n samples, then release."""
    t = np.arange(n) / sr
    env = np.ones(n) * s
    an, dn = int(a * sr), int(d * sr)
    if an:
        env[:an] = np.linspace(0, 1, an)
    if dn:
        env[an:an + dn] = np.linspace(1, s, dn)[:max(0, min(dn, n - an))]
    rn = n - gate_n
    if rn > 0:
        env[gate_n:] *= np.exp(-np.arange(rn) / sr / (r / 4.0))
    return env


def _lowpass(x, sr, hz):
    from scipy.signal import butter, sosfilt
    sos = butter(2, hz / (sr / 2), output='sos')
    return sosfilt(sos, x)


def _highpass(x, sr, hz):
    from scipy.signal import butter, sosfilt
    sos = butter(2, hz / (sr / 2), output='sos')
    return sosfilt(sos, x, axis=0) if x.ndim == 2 else sosfilt(sos, x)


def render(mid_path, out_wav, sr=SR, patch='glass', detune_cents=9.0, vibrato_hz=5.2, vibrato_cents=5.0,
           chorus_wet=0.45, reverb_wet_db=-13.0, rt60=2.2, pre_delay=0.02, hp_hz=150.0):
    notes = _notes(mid_path)
    if not notes:
        raise SystemExit('no notes to render')
    length = max(n.end for n in notes) + rt60 + 1.0
    N = int(length * sr)
    L = np.zeros(N)
    R = np.zeros(N)
    rel = 0.28
    for n in notes:
        dur = n.end - n.start
        gate_n = int(dur * sr)
        total_n = gate_n + int(rel * sr)
        t = np.arange(total_n) / sr
        f0 = 440.0 * 2 ** ((n.pitch - 69) / 12.0)
        # delayed vibrato, like a sung note
        vib_depth = vibrato_cents * np.clip((t - 0.15) / 0.25, 0, 1)
        vib = 2 ** ((vib_depth * np.sin(2 * np.pi * vibrato_hz * t)) / 1200.0)
        env = _env(total_n, sr, 0.018, 0.22, 0.78, rel, gate_n)
        # filter envelope: bright at the attack, settling darker (two renders crossfaded)
        fenv = 0.35 + 0.65 * np.exp(-t / 0.35)
        vel = 0.45 + 0.55 * (n.velocity / 127.0)
        voices = []
        for cents, pan in ((-detune_cents, -0.6), (0.0, 0.0), (detune_cents, 0.6)):
            fr = f0 * vib * 2 ** (cents / 1200.0)
            s = _saw(fr, sr)
            bright = _lowpass(s, sr, min(5200.0, sr * 0.45))
            dark = _lowpass(s, sr, 1300.0)
            v = dark + (bright - dark) * fenv
            voices.append((v, pan))
        sub = np.sin(2 * np.pi * np.cumsum(f0 * 0.5 * np.ones(total_n)) / sr) * 0.22
        mono_l = np.zeros(total_n)
        mono_r = np.zeros(total_n)
        for v, pan in voices:
            gl = math.cos((pan + 1) * math.pi / 4)
            gr = math.sin((pan + 1) * math.pi / 4)
            mono_l += v * gl
            mono_r += v * gr
        mono_l += sub * 0.707
        mono_r += sub * 0.707
        sig_l = mono_l * env * vel * 0.18
        sig_r = mono_r * env * vel * 0.18
        i0 = int(n.start * sr)
        i1 = min(N, i0 + total_n)
        L[i0:i1] += sig_l[:i1 - i0]
        R[i0:i1] += sig_r[:i1 - i0]
    st = np.stack([L, R], axis=1)
    st = _highpass(st, sr, hp_hz)
    # chorus: two modulated delays
    def chorus(x, base_ms, depth_ms, rate_hz, phase):
        tt = np.arange(len(x)) / sr
        d = (base_ms + depth_ms * np.sin(2 * np.pi * rate_hz * tt + phase)) * sr / 1000.0
        idx = np.arange(len(x)) - d
        i0 = np.floor(idx).astype(int)
        frac = idx - i0
        i0c = np.clip(i0, 0, len(x) - 1)
        i1c = np.clip(i0 + 1, 0, len(x) - 1)
        return x[i0c] * (1 - frac) + x[i1c] * frac
    wet = np.stack([chorus(st[:, 0], 12.0, 2.2, 0.31, 0.0), chorus(st[:, 1], 19.0, 2.6, 0.42, 1.7)], axis=1)
    st = st * (1 - chorus_wet * 0.5) + wet * chorus_wet
    # reverb: synthetic stereo IR, exponential decay to RT60, darkened, pre-delayed
    from scipy.signal import fftconvolve
    rng = np.random.default_rng(7)
    ir_n = int(rt60 * sr)
    tt = np.arange(ir_n) / sr
    decay = np.exp(-6.91 * tt / rt60)
    ir = np.stack([rng.standard_normal(ir_n), rng.standard_normal(ir_n)], axis=1) * decay[:, None]
    ir = np.stack([_lowpass(ir[:, 0], sr, 6000.0), _lowpass(ir[:, 1], sr, 6000.0)], axis=1)
    ir = np.concatenate([np.zeros((int(pre_delay * sr), 2)), ir], axis=0)
    ir /= np.sqrt(np.sum(ir ** 2, axis=0, keepdims=True)) + 1e-9
    rv = np.stack([fftconvolve(st[:, 0], ir[:, 0])[:N], fftconvolve(st[:, 1], ir[:, 1])[:N]], axis=1)
    st = st + rv * (10 ** (reverb_wet_db / 20.0))
    peak = float(np.max(np.abs(st))) or 1.0
    st = st / peak * 0.5
    import soundfile as sf
    sf.write(out_wav, st.astype(np.float32), sr, subtype='FLOAT')
    print('rendered %d notes, %.1f s -> %s (peak -6 dB)' % (len(notes), N / sr, out_wav))


# ----------------------------------------------------------------------------- mix
def _lufs(path):
    r = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', 'ebur128=framelog=quiet', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return float(re.search(r'^\s+I:\s+(-?[\d.]+) LUFS', r.stderr, re.M).group(1))


def mix(instrumental, layer, out, under_lu=7.0):
    li, ll = _lufs(instrumental), _lufs(layer)
    gain = (li - under_lu) - ll
    af = '[1:a]volume=%.2fdB,aresample=%d:resampler=soxr[l];[0:a]aresample=%d:resampler=soxr[i];[i][l]amix=inputs=2:duration=first:normalize=0' % (gain, SR, SR)
    r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', instrumental, '-i', layer, '-filter_complex', af,
                        '-ar', str(SR), '-ac', '2', '-c:a', 'pcm_f32le', out], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    print('instrumental %.1f LUFS, layer %.1f -> +%.1f dB so it sits %.1f LU under -> %s (%.1f LUFS)' % (li, ll, gain, under_lu, out, _lufs(out)))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    t = sub.add_parser('transcribe'); t.add_argument('vocal'); t.add_argument('out_mid')
    t.add_argument('--onset', type=float, default=0.5); t.add_argument('--frame', type=float, default=0.3); t.add_argument('--min-ms', type=int, default=110)
    r = sub.add_parser('render'); r.add_argument('mid'); r.add_argument('out_wav')
    r.add_argument('--reverb-db', type=float, default=-13.0); r.add_argument('--detune', type=float, default=9.0)
    m = sub.add_parser('mix'); m.add_argument('instrumental'); m.add_argument('layer'); m.add_argument('out'); m.add_argument('--under-lu', type=float, default=7.0)
    a = ap.parse_args()
    if a.cmd == 'transcribe':
        transcribe(a.vocal, a.out_mid, onset=a.onset, frame=a.frame, min_ms=a.min_ms)
    elif a.cmd == 'render':
        render(a.mid, a.out_wav, reverb_wet_db=a.reverb_db, detune_cents=a.detune)
    else:
        mix(a.instrumental, a.layer, a.out, under_lu=a.under_lu)


if __name__ == '__main__':
    main()
