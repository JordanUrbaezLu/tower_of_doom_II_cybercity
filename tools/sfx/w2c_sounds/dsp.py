"""Shared DSP for tools/sfx/w2c_sounds (wave 2 sounds, 2026-10-05). Deterministic numpy/scipy only.

Every array is float64 shaped (n, ch) at SR. Loudness is BS.1770-4 (K-weighting, 400 ms blocks at 75 % overlap,
-70 abs / -10 rel gates, channels summed with weight 1; a sound shorter than a block is padded to one block, which
reads ~1-2 dB low for a 0.2-0.3 s cue - targets below are set in that unit, as tools/ability_fx/make_sounds.py does).
"""
import io, hashlib, subprocess, wave
import numpy as np

SR = 48000


def as2d(x):
    x = np.asarray(x, dtype=np.float64)
    return x[:, None] if x.ndim == 1 else x


def mono(x):
    x = as2d(x)
    return x.mean(axis=1)


def to_ch(x, ch):
    x = as2d(x)
    if x.shape[1] == ch:
        return x
    if ch == 1:
        return x.mean(axis=1, keepdims=True)
    return np.repeat(x[:, :1], ch, axis=1) if x.shape[1] == 1 else x[:, :ch]


def decode(path, ch=2):
    """any audio file -> (n, ch) float64 at SR (ffmpeg on PATH)"""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype="<f4").astype(np.float64).reshape(-1, ch)


def pcm_stereo_to_wav(raw):
    """ElevenLabs pcm_48000 = 16-bit stereo interleaved: wrap it in a wav header"""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(raw[: len(raw) // 4 * 4])
    return buf.getvalue()


def lufs(x):
    from scipy.signal import lfilter
    x = as2d(x)
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], x, axis=0)
    y = lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y, axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    if len(y) < blk:
        y = np.concatenate([y, np.zeros((blk - len(y), y.shape[1]))])
    ms = np.array([np.sum(np.mean(y[i:i + blk] ** 2, axis=0)) for i in range(0, len(y) - blk + 1, hop)])
    l = -0.691 + 10 * np.log10(ms + 1e-20)
    ms = ms[l > -70]
    if ms.size == 0:
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(ms)) - 10
    ms = ms[(-0.691 + 10 * np.log10(ms)) > rel]
    return float(-0.691 + 10 * np.log10(np.mean(ms))) if ms.size else -70.0


def punch(x, win=0.05):
    """the loudness of a HIT: the loudest 50 ms K-weighted RMS (dB). BS.1770's 400 ms blocks pad a 60 ms impact with
    silence and read it 10 dB low; variants of one hit are matched on this instead"""
    from scipy.signal import lfilter
    x = as2d(x)
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], x, axis=0)
    y = lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y, axis=0)
    p = np.sum(y ** 2, axis=1)
    n, hop = int(win * SR), int(0.005 * SR)
    if len(p) < n:
        p = np.concatenate([p, np.zeros(n - len(p))])
    c = np.concatenate([[0.0], np.cumsum(p)])
    w = (c[n::hop] - c[:-n:hop]) / n if len(p) > n else np.array([c[-1] / n])
    return float(10 * np.log10(np.max(w) + 1e-20))


def db(v):
    return 20 * np.log10(np.maximum(v, 1e-12))


def envelope(x, frame=0.010):
    m = mono(x)
    n = max(1, int(frame * SR))
    k = len(m) // n
    if k == 0:
        return np.array([np.sqrt(np.mean(m ** 2) + 1e-20)])
    return np.sqrt(np.mean(m[:k * n].reshape(k, n) ** 2, axis=1) + 1e-20)


def trim_head(x, head_db=-40.0, pre=0.0):
    e = envelope(x, 0.001)
    above = np.where(db(e / (e.max() + 1e-20)) > head_db)[0]
    if above.size == 0:
        return x
    a = max(0, above[0] * int(0.001 * SR) - int(pre * SR))
    return x[a:]


def trim_tail(x, tail_db=-60.0, post=0.03):
    e = envelope(x, 0.005)
    above = np.where(db(e / (e.max() + 1e-20)) > tail_db)[0]
    if above.size == 0:
        return x
    end = min(len(x), (above[-1] + 1) * int(0.005 * SR) + int(post * SR))
    return x[:end]


def dc_block(x, hz=25.0):
    x = as2d(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    return np.fft.irfft(np.fft.rfft(x, axis=0) * (f >= hz)[:, None], len(x), axis=0)


def band(x, lo, hi):
    """zero-phase FFT band-pass (lo/hi in Hz; 0 / None = open)"""
    x = as2d(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1.0 / (1.0 + (lo / np.maximum(f, 1e-3)) ** 4)
    if hi:
        g *= 1.0 / (1.0 + (f / hi) ** 4)
    return np.fft.irfft(np.fft.rfft(x, axis=0) * g[:, None], len(x), axis=0)


def tilt_lowpass(x, f_start, f_end, seg=0.05):
    """a lowpass whose corner glides f_start -> f_end (Hz, log) across the sound: one-pole sections per 50 ms block
    with the state carried, so it is click-free (the receding power wave)"""
    from scipy.signal import lfilter
    x = as2d(x)
    n = len(x)
    out = np.zeros_like(x)
    blk = int(seg * SR)
    zi = [np.zeros(1) for _ in range(x.shape[1] * 2)]
    for i in range(0, n, blk):
        t = i / max(1, n - 1)
        fc = f_start * (f_end / f_start) ** t
        a = 1 - np.exp(-2 * np.pi * fc / SR)
        for c in range(x.shape[1]):
            y, zi[2 * c] = lfilter([a], [1, -(1 - a)], x[i:i + blk, c], zi=zi[2 * c])
            y, zi[2 * c + 1] = lfilter([a], [1, -(1 - a)], y, zi=zi[2 * c + 1])
            out[i:i + blk, c] = y
    return out


def fade_in(x, secs):
    x = as2d(x).copy()
    a = min(len(x), int(secs * SR))
    if a > 0:
        x[:a] *= np.linspace(0.0, 1.0, a)[:, None]
    return x


def fade_out(x, secs, squared=True):
    x = as2d(x).copy()
    b = min(len(x), int(secs * SR))
    if b > 0:
        r = np.linspace(1.0, 0.0, b)
        x[-b:] *= (r ** 2 if squared else r)[:, None]
    return x


def fit_len(x, n):
    x = as2d(x)
    if len(x) >= n:
        return x[:n].copy()
    return np.concatenate([x, np.zeros((n - len(x), x.shape[1]))])


def limiter_gain(x, ceil, look=0.003, rel=0.08):
    """look-ahead peak limiter gain curve (card_luck's): never above ceil, smooth attack, one-pole release"""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    x = as2d(x)
    pk = np.max(np.abs(x), axis=1) + 1e-12
    need = np.minimum(1.0, ceil / pk)
    w = max(1, int(look * SR))
    g = minimum_filter1d(need, size=2 * w + 1, mode="nearest")
    g = uniform_filter1d(g, size=2 * w + 1, mode="nearest")
    g = np.minimum(g, need)
    a = 1.0 - np.exp(-1.0 / (rel * SR))
    out = g.copy()
    for i in range(1, len(out)):
        if out[i] > out[i - 1]:
            out[i] = out[i - 1] + (out[i] - out[i - 1]) * a
    return out


def _limit(z, ceil, loop):
    if loop:
        pad = int(0.1 * SR)
        zz = np.concatenate([z[-pad:], z, z[:pad]])
        return limiter_gain(zz, ceil)[pad:pad + len(z)]
    return limiter_gain(z, ceil)


def level(x, target, peak_db, loop=False, max_gr=6.0):
    """gain onto the loudness target under the limiter (iterated: the limiter takes some gain back), but the limiter
    never takes more than max_gr dB off any sample: a transient cue that cannot reach its target cleanly lands as
    loud as it can WITHOUT being crushed (a 0.3 s impact at -15 LUFS under a -1 dBFS ceiling would need 20+ dB of
    limiting - a square wave). A loop's limiter curve wraps (the seam must not pump)."""
    x = as2d(x)
    ceil = 10 ** (peak_db / 20)
    g_db = target - lufs(x)
    pk_db = float(db(np.max(np.abs(x)) + 1e-12))
    g_cap = (peak_db + max_gr) - pk_db          # the gain at which the peak needs exactly max_gr of limiting
    g_db = min(g_db, g_cap)
    y = x
    gr = np.ones(len(x))
    for _ in range(12):
        z = x * 10 ** (g_db / 20)
        gr = _limit(z, ceil, loop)
        y = z * gr[:, None]
        err = target - lufs(y)
        if abs(err) < 0.03:
            break
        nxt = min(g_db + err, g_cap)
        if abs(nxt - g_db) < 0.01:
            break
        g_db = nxt
    y = np.clip(y, -ceil, ceil)
    return y, float(-db(gr.min()))


def compress(x, ratio, thresh_rel_db=-12.0, attack=0.002, release=0.06):
    """a feed-forward compressor (peak detector with attack / release smoothing, the threshold relative to the
    sound's own peak, no makeup): lifts the BODY of a transient cue toward its loudness target so the limiter never
    has to crush the attack. ratio 1 = the identity."""
    x = as2d(x)
    if ratio <= 1.0:
        return x
    d = np.max(np.abs(x), axis=1)
    a_at = 1 - np.exp(-1.0 / (attack * SR))
    a_rl = 1 - np.exp(-1.0 / (release * SR))
    env = np.empty_like(d)
    e = 0.0
    dl = d.tolist()
    for i, v in enumerate(dl):
        e = e + (v - e) * (a_at if v > e else a_rl)
        env[i] = e
    thr = np.max(d) * 10 ** (thresh_rel_db / 20)
    over = np.maximum(env / (thr + 1e-12), 1.0)
    g = over ** (1.0 / ratio - 1.0)
    return x * g[:, None]


def level_dense(x, target, peak_db, max_ratio=1.0, max_gr=6.0):
    """level(), and if the cue cannot reach its target cleanly, compress it a step at a time (1.5 / 2 / 3 / 4, up to
    max_ratio) until it does - the first ratio that lands within 0.5 dB wins. -> (y, limiter dB, ratio used)"""
    best = None
    for ratio in (1.0, 1.5, 2.0, 3.0, 4.0):
        if ratio > max_ratio + 1e-9:
            break
        y, gr = level(compress(x, ratio), target, peak_db, max_gr=max_gr)
        cand = (y, gr, ratio)
        if best is None or lufs(y) > lufs(best[0]) + 0.05:
            best = cand
        if lufs(y) >= target - 0.5:
            return cand
    # a POP-heavy texture (crackle, ratchet clicks: sub-millisecond peaks a compressor's attack never catches) still
    # short: a soft clip on the pops first (tanh(d x) / tanh(d) on the peak-normalised sound - the identity for small
    # samples, the near-miss placeholders' own loudness stage), then the same capped limiter
    if max_ratio >= 6.0:
        xn = as2d(x) / (np.max(np.abs(x)) + 1e-12)
        for d in (1.0, 2.0, 3.0, 4.5):
            y, gr = level(np.tanh(d * xn) / np.tanh(d), target, peak_db, max_gr=max_gr)
            cand = (y, gr, 10.0 + d)
            if lufs(y) > lufs(best[0]) + 0.05:
                best = cand
            if lufs(y) >= target - 0.5:
                return cand
    return best


def eq_match(src, ref, max_db=9.0, smooth_oct=0.33):
    """src re-voiced to ref's long-term spectrum (1/3-octave smoothed magnitude ratio, clamped): two takes of one bed
    joined into one loop must sound like one place"""
    src, ref = as2d(src), as2d(ref)

    def ltas(x):
        n = 8192
        m = mono(x)
        segs = [m[i:i + n] * np.hanning(n) for i in range(0, len(m) - n, n // 2)]
        return np.mean([np.abs(np.fft.rfft(s)) for s in segs], axis=0)
    f = np.fft.rfftfreq(8192, 1.0 / SR)
    a, b = ltas(ref), ltas(src)
    lf = np.log2(np.maximum(f, 20.0))
    sm = lambda v: np.array([np.mean(v[np.abs(lf - lf[i]) <= smooth_oct / 2]) for i in range(len(v))])
    r = sm(a) / (sm(b) + 1e-12)
    g = np.clip(20 * np.log10(r + 1e-12), -max_db, max_db)
    g -= np.median(g[(f > 200) & (f < 4000)])      # match the SHAPE; the level is the leveller's job
    F = np.fft.rfftfreq(len(src), 1.0 / SR)
    G = 10 ** (np.interp(F, f, g) / 20)
    return np.fft.irfft(np.fft.rfft(src, axis=0) * G[:, None], len(src), axis=0)


def encode(x):
    x = as2d(x)
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


def read_wav(b):
    with wave.open(io.BytesIO(b)) as w:
        ch, n = w.getnchannels(), w.getnframes()
        a = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float64) / 32768.0
    return a.reshape(-1, ch)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


# ---- loops ----------------------------------------------------------------------------------------------------
def make_loop(x, secs, xfade, start=0.25):
    """a seamless loop of `secs` from x: the segment [start, start+secs+xfade); the overhang past `secs` is
    equal-power crossfaded over the head, so the last sample flows into the first (the wrap is the crossfade's own
    continuation). Returns (loop, seam_score) - seam_score = the wrap's sample step / the median step (1 ~ seamless)."""
    x = as2d(x)
    a = int(start * SR)
    n = int(round(secs * SR))
    xf = int(round(xfade * SR))
    if a + n + xf > len(x):
        a = max(0, len(x) - n - xf)
    if a + n + xf > len(x):
        raise ValueError("take too short for a %.2f s loop with a %.2f s crossfade (%.2f s)" % (secs, xfade, len(x) / SR))
    seg = x[a:a + n + xf]
    out = seg[:n].copy()
    t = np.linspace(0.0, np.pi / 2, xf)[:, None]
    out[:xf] = seg[:xf] * np.sin(t) + seg[n:n + xf] * np.cos(t)
    return out, seam_score(out)


def make_loop_best(x, secs, xfade, lo=0.3, hop=0.2):
    """make_loop at the start (from lo, every hop s) whose wrap is cleanest: the smallest loudness jump across the
    seam, then the smallest sample step (deterministic: the first best wins)"""
    x = as2d(x)
    n = int(round(secs * SR)) + int(round(xfade * SR))
    best, best_k = None, None
    t = lo
    while int(t * SR) + n <= len(x):
        lp, s = make_loop(x, secs, xfade, start=t)
        k = s["jump_db"] + 0.05 * min(s["step"], 20.0)
        if best_k is None or k < best_k - 1e-9:
            best, best_k = (lp, s, t), k
        t += hop
    if best is None:
        lp, s = make_loop(x, secs, xfade, start=0.0)
        return lp, s, 0.0
    return best


def seam_score(loop):
    loop = as2d(loop)
    m = mono(loop)
    step = np.abs(np.diff(m))
    med = np.median(step) + 1e-9
    wrap = abs(m[0] - m[-1])
    # and the loudness either side of the wrap (50 ms) - a pump at the seam is a seam
    w = int(0.05 * SR)
    l1 = np.sqrt(np.mean(m[-w:] ** 2) + 1e-20)
    l2 = np.sqrt(np.mean(m[:w] ** 2) + 1e-20)
    return dict(step=float(wrap / med), jump_db=float(abs(db(l1) - db(l2))))


def steady(x, win=0.5):
    """how steady a bed is: the spread (dB) of 0.5 s RMS windows (p90 - p10)"""
    m = mono(x)
    n = int(win * SR)
    if len(m) < 2 * n:
        return 0.0
    r = [np.sqrt(np.mean(m[i:i + n] ** 2) + 1e-20) for i in range(0, len(m) - n, n // 2)]
    d = db(np.array(r))
    return float(np.percentile(d, 90) - np.percentile(d, 10))


def even_out(x, win=1.0, max_db=3.0):
    """ride a bed's slow loudness toward its median, at most max_db either way (a gust swell stays a swell, a model
    take that fades out at its end does not become a 6 dB dip in the loop)"""
    x = as2d(x)
    m = mono(x)
    n = int(win * SR)
    if len(m) < 3 * n:
        return x
    centers, r = [], []
    for i in range(0, len(m) - n + 1, n // 2):
        centers.append(i + n // 2)
        r.append(db(np.sqrt(np.mean(m[i:i + n] ** 2) + 1e-20)))
    r = np.array(r)
    med = np.median(r)
    corr = np.clip(med - r, -max_db, max_db)
    g = np.interp(np.arange(len(m)), centers, corr)
    return x * (10 ** (g / 20))[:, None]


# ---- synthesis building blocks --------------------------------------------------------------------------------
def tl(secs):
    n = int(round(secs * SR))
    return n, np.arange(n) / SR


def noise(n, seed, lo=None, hi=None):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    if lo or hi:
        x = band(x, lo, hi)[:, 0]
    return x / (np.max(np.abs(x)) + 1e-12)


def blip(secs, f0, f1=None, attack=0.004, decay=0.06, harm=(1.0, 0.25, 0.08)):
    """a short UI blip: a sine (glide f0 -> f1) with two quiet harmonics, a fast attack and an exponential decay"""
    n, t = tl(secs)
    f1 = f0 if f1 is None else f1
    f = f0 + (f1 - f0) * np.clip(t / max(secs * 0.5, 1e-3), 0, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = sum(a * np.sin((k + 1) * ph) for k, a in enumerate(harm))
    env = np.clip(t / attack, 0, 1) * np.exp(-t / decay)
    return tone * env


def sub_drop(secs, f0, f1, tau, attack=0.003):
    """a sine sliding f0 -> f1 (exp) with an exponential decay: the felt part of a drop / a thump"""
    n, t = tl(secs)
    f = f0 * (f1 / f0) ** np.clip(t / secs, 0, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.clip(t / attack, 0, 1) * np.exp(-t / tau)


def place(dst, src, t0, gain=1.0):
    """mix src (n, ch) into dst (m, ch) at t0 seconds (clipped to dst)"""
    dst = as2d(dst)
    src = to_ch(as2d(src), dst.shape[1])
    a = int(round(t0 * SR))
    if a >= len(dst):
        return dst
    b = min(len(dst), a + len(src))
    dst[a:b] += src[:b - a] * gain
    return dst


def stereo_spread(x, delay_ms=11.0, seed=0, loop=False):
    """mono -> a gentle wide stereo (a Haas-style decorrelation: the right channel a few ms late), for a 2D cue built
    from mono parts. loop=True wraps the delay (a loop stays a loop); a ONE-SHOT part is delayed into silence - a
    wrapped one-shot drops its own last milliseconds onto the right channel's first sample (the power wave's swell
    ends at full level, and its wrapped tail was a hard pop 1.5 s before the grid came on; fixed 2026-10-05)"""
    m = mono(x)
    d = int(delay_ms * SR / 1000)
    if d <= 0:
        r = m.copy()
    elif loop:
        r = np.concatenate([m[-d:], m[:-d]])
    else:
        r = np.concatenate([np.zeros((d,) + m.shape[1:]), m[:-d]])
    return np.stack([m, r], axis=1)
