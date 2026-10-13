"""THE ARENA + HOUSE CUES, AUTHORED (asset pack PK16, 2026-10-04): the seven cues the Battle Arena (docs/185 v2.1)
and the Dealer's House (docs/207) shipped as seeded-numpy STAND-INS, re-made from ElevenLabs sound generation and
composed onto the game's own timeline. Same files, same alias rows: the stand-in generators
(tools/battle_arena/make_sounds.py, tools/dealer_house/make_sounds.py) keep writing their alias tables and gate
these files through their AUTHORED LANE (authored_sounds.json beside each: a sha256 per cue, checked instead of the
re-render).

THE CUES AND THE MOMENTS THEY SIT ON (read from the shipping GSC, not guessed):
  tod_arena_wave    2D  1.90 s  a wave begins (_tod_arena.gsc spawn_wave; also the Dealer fight's horn,
                                _tod_house.gsc:759). A war horn swells INTO a huge drum hit at 0.55 s.
  tod_arena_clear   2D  1.35 s  a wave is cleared (never the level's last). Two bright rising bell notes + shimmer.
  tod_arena_level   2D  2.85 s  the level is cleared (arena_win). A rising brass fanfare, a held note, a sub, a tail.
  tod_arena_gate    3D  1.75 s  an elite's gate charges for TOD_ARENA_GATE_TELL_SECS (1.0) and the elite rises with
                                the tod_tp_flash: latch clack at 0, a rising electric whine, the HEAVY CLANK AT 1.00 s.
  tod_house_cursed  2D  1.70 s  the last roll lands CURSED (_tod_shop.gsc house_roll): the banner stamps, the red
                                flash and the shake are drawn THAT frame (TodSpinReel landCursed), so the DEAD THUD +
                                glass crack land at 0.07 s (a 70 ms reversed suck-in ahead of it), then a sour bell
                                bends down and dies. (The stand-in put its thud 0.55 s after the stamp.)
  tod_house_drain   2D  6.50 s  THE DRAIN (_tod_house.gsc drain): one play at the start, then a cut every 0.6 s
                                (TOD_HOUSE_DRAIN_SECS 6.0 / STEPS 10, ticks of 0.1): cuts at 0.6, 1.2 ... 6.0. A low
                                drone rises under the Dealer's monologue (a 1-3.5 kHz pocket keeps his words clear),
                                and the heartbeat LANDS ON THE CUTS and quickens with them: every second cut (1.2 s),
                                every cut (0.6 s), then twice a cut (0.3 s) to the last cut at 6.0 = ONE HP, then the
                                drone dies and a breath of silence.
  tod_house_cut     2D  0.38 s  one bite of the drain (the HUD flicker frame). A short dark electrical bite that falls.

THE PIPELINE (the ability_fx pattern, docs/206):
  generate  ElevenLabs /v1/sound-generation, AT MOST 3 calls per cue in total (a layered cue spends its three across
            its layers). Every take is kept under tmp/asset_prod/PK16-arena-house-cues/takes/ (not in git), measured
            (onset, peak position, decay, tail, low share, tonality, pitch trend, onset count) and scored against its
            layer's profile.
  pick      per cue: the user's override (picks.json), a DROPPED file (drop/<cue>.wav replaces the whole cue,
            drop/<cue>__<layer>.wav one layer: any wav / mp3 / flac / ogg) or the best-scoring take per layer; the
            layers composed on the cue's timeline (above); DC-blocked, faded at both ends, levelled to the cue's
            loudness target (BS.1770) under a soft limiter at -1.5 dBFS; mono 48 kHz 16-bit; written under --out-root
            (default the repo) with the two authored_sounds.json manifests.
  verify    every shipped file against its contract (format, length, peak, loudness, the sync points above).
  desk      tmp/asset_prod/PK16-arena-house-cues/desk.html: the stand-in, the authored cue and every take side by side
            + _review.png (envelope + spectrogram of stand-in vs authored, the sync markers drawn).
  --check   the files under --out-root match their manifests (no API, no DSP). The BUILD gate is the stand-in
            generators' own --check (build_map.ps1), which reads the same manifests.

  python tools/sfx/arena_house/make_sounds.py generate [--cue NAME] [--out-root DIR]
  python tools/sfx/arena_house/make_sounds.py pick     [--cue NAME] [--out-root DIR]
  python tools/sfx/arena_house/make_sounds.py verify   [--out-root DIR]
  python tools/sfx/arena_house/make_sounds.py desk     [--out-root DIR]
  python tools/sfx/arena_house/make_sounds.py --check  [--out-root DIR]

The key is ELEVENLABS_API_KEY via tools/black_market_vo/eleven.py (never printed, never stored).
"""
import argparse, hashlib, io, json, os, re, subprocess, sys, wave

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(REPO, "tools", "black_market_vo"))

SR = 48000
PEAK_DB = -1.5
PACK = "PK16-arena-house-cues"
WORK = os.path.join(REPO, "tmp", "asset_prod", PACK)
TAKES_DIR = os.path.join(WORK, "takes")
DROP_DIR = os.path.join(WORK, "drop")
TAKES_JSON = os.path.join(TAKES_DIR, "takes.json")
PICKS_JSON = os.path.join(WORK, "picks.json")          # {cue: {layer: "take_2"}}
MAX_CALLS = 3                                           # per cue, all layers together
PROMPT_INFLUENCE = 0.6
TOOL = "tools/sfx/arena_house/make_sounds.py"

GROUPS = {
    "arena": dict(dir="sound_assets/tod/arena", manifest="tools/battle_arena/authored_sounds.json",
                  gate="python -B tools/battle_arena/make_sounds.py --check"),
    "house": dict(dir="sound_assets/tod/house", manifest="tools/dealer_house/authored_sounds.json",
                  gate="python -B tools/dealer_house/make_sounds.py --check"),
}

# ---- the cues ---------------------------------------------------------------------------------------
# layer: id, prompt, secs (asked of the model), takes (calls), profile (scoring shape)
CUES = {
    "tod_arena_wave": dict(group="arena", secs=1.90, tol=0.06, lufs=-16.0, layers=[
        dict(id="horn", takes=2, secs=1.6, profile="swell",
             prompt="a deep ominous war horn blast swelling louder and louder, low brass, a gladiator arena call to battle, "
                    "dark and cinematic, one sustained note, no drums, no music melody, no voice"),
        dict(id="drum", takes=1, secs=1.5, profile="boom",
             prompt="a single huge cinematic drum hit, a deep taiko boom with heavy sub bass and a short dark metallic "
                    "tail, trailer impact, one hit only, no music, no voice"),
    ]),
    "tod_arena_clear": dict(group="arena", secs=1.35, tol=0.25, lufs=-16.5, layers=[
        dict(id="chime", takes=3, secs=1.5, profile="chime2",
             prompt="two quick bright bell chimes rising in pitch, a clean ding then a higher ding, crystal tone with a "
                    "short sparkling shimmer tail, video game wave cleared reward, no music, no voice"),
    ]),
    "tod_arena_level": dict(group="arena", secs=2.85, tol=0.3, lufs=-15.0, layers=[
        dict(id="fanfare", takes=3, secs=3.0, profile="fanfare",
             prompt="a short heroic brass fanfare stinger, three quick rising notes then one long held triumphant note, "
                    "a deep sub bass boom under the held note and a glittering crystal chime tail, video game level "
                    "complete, orchestral, no voice"),
    ]),
    "tod_arena_gate": dict(group="arena", secs=1.75, tol=0.06, lufs=-18.0, layers=[
        dict(id="clack", takes=1, secs=0.6, profile="click",
             prompt="a heavy steel latch unlocking, one sharp mechanical metal clack with a short bright metallic ring, "
                    "dry, close, no music"),
        dict(id="whine", takes=1, secs=1.2, profile="riser",
             prompt="an electric power charge-up whine rising quickly in pitch, a sci-fi teleporter gate energizing "
                    "with a low electrical hum shudder, building intensity, no impact at the end, no music"),
        dict(id="clank", takes=1, secs=0.9, profile="boom",
             prompt="a massive heavy iron gate slamming open, one deep metallic clank impact with a short reverberant "
                    "metal ring in a large stone arena, no music"),
    ]),
    "tod_house_cursed": dict(group="house", secs=1.70, tol=0.06, lufs=-16.5, layers=[
        dict(id="hit", takes=2, secs=1.0, profile="boom",
             prompt="a dead heavy thud with a sharp glass crack, a dull lifeless sub bass knock and a pane of glass "
                    "cracking at the same instant, dark and dry, one impact only, no music, no voice"),
        dict(id="sour", takes=1, secs=1.6, profile="sour",
             prompt="a sour detuned bell chime bending downward in pitch, a broken casino jackpot jingle falling out of "
                    "tune and dying away, eerie and dissonant, dark, no voice"),
    ]),
    "tod_house_drain": dict(group="house", secs=6.50, tol=0.002, lufs=-19.0, layers=[
        dict(id="drone", takes=1, secs=7.0, profile="drone",
             prompt="a low dark ominous drone slowly rising in pitch and intensity, a corrupted energy field draining "
                    "life, deep sub rumble with a gritty electrical texture, horror atmosphere, no heartbeat, no drums, "
                    "no music, no voice"),
        dict(id="beat", takes=2, secs=0.8, profile="beat",
             prompt="a single heavy human heartbeat, one deep lub-dub thump, close and dry, no music, no voice"),
    ]),
    "tod_house_cut": dict(group="house", secs=0.38, tol=0.02, lufs=-18.5, layers=[
        dict(id="bite", takes=3, secs=0.5, profile="zap",
             prompt="a short dark electrical bite, a quick vicious zap with a falling pitch, a burst of corrupted energy "
                    "biting into flesh, dry, no music, no voice"),
    ]),
}
ORDER = list(CUES)

# the sync points the composer places and verify checks (seconds)
WAVE_HIT = 0.55
GATE_CLANK = 1.00
CURSED_HIT = 0.07
DRAIN_CUTS = [round(0.6 * k, 3) for k in range(1, 11)]
DRAIN_BEATS = [0.6, 1.8, 3.0, 3.6, 4.2, 4.8, 5.1, 5.4, 5.7, 6.0]   # 1.2 s, then 0.6 s, then 0.3 s; every one on the cut grid


# ---- audio helpers ----------------------------------------------------------------------------------
def decode(path):
    """any audio file -> mono float64 at SR. A stereo source is folded with downmix() (the model's takes come back as
    wide stereo: a plain L+R lost up to 5.8 dB, mostly the low end, on the drum and the drone)"""
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels",
                            "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout.strip()
    ch = 2 if probe.startswith("2") else 1
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(out, dtype="<f4").astype(np.float64)
    if ch == 1:
        return x
    return downmix(x[0::2], x[1::2])


def downmix(l, r):
    """a power-preserving fold to mono: per STFT bin the sum (L+R)/2 is scaled back up to the channels' mean power
    (capped at +12 dB), and where the sum has cancelled (anti-phase content) the bin takes the left channel's phase
    at that power instead. In-phase material comes out exactly as (L+R)/2."""
    n = min(len(l), len(r))
    l, r = l[:n], r[:n]
    nper = 2048
    if n < nper:
        return (l + r) / 2
    _, _, L = signal.stft(l, SR, nperseg=nper, noverlap=nper * 3 // 4, boundary="even")
    _, _, R = signal.stft(r, SR, nperseg=nper, noverlap=nper * 3 // 4, boundary="even")
    M = (L + R) / 2
    T = np.sqrt((np.abs(L) ** 2 + np.abs(R) ** 2) / 2)
    am = np.abs(M)
    g = np.minimum(T / (am + 1e-12), 4.0)
    out = M * g
    dead = am < 0.25 * T
    out[dead] = T[dead] * np.exp(1j * np.angle(L[dead]))
    _, y = signal.istft(out, SR, nperseg=nper, noverlap=nper * 3 // 4, boundary=True)
    y = y[:n]
    return np.concatenate([y, np.zeros(n - len(y))]) if len(y) < n else y


def lufs(x):
    """BS.1770-4 integrated loudness, mono 48 kHz (a cue under 0.4 s is measured in one zero-padded block)"""
    y = signal.lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], x)
    y = signal.lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    if len(y) < blk:
        y = np.concatenate([y, np.zeros(blk - len(y))])
    ms = np.array([np.mean(y[i:i + blk] ** 2) for i in range(0, len(y) - blk + 1, hop)])
    ms = ms[(-0.691 + 10 * np.log10(ms + 1e-20)) > -70]
    if ms.size == 0:
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(ms)) - 10
    ms = ms[(-0.691 + 10 * np.log10(ms)) > rel]
    return float(-0.691 + 10 * np.log10(np.mean(ms))) if ms.size else -70.0


def envelope(x, frame=0.010):
    n = max(1, int(frame * SR))
    k = len(x) // n
    if k == 0:
        return np.array([np.sqrt(np.mean(x ** 2) + 1e-20)])
    return np.sqrt(np.mean(x[:k * n].reshape(k, n) ** 2, axis=1) + 1e-20)


def db(v):
    return 20 * np.log10(np.maximum(v, 1e-12))


def highpass(x, fc=28.0):
    return signal.sosfiltfilt(signal.butter(2, fc, btype="highpass", fs=SR, output="sos"), x)


def lowpass(x, fc, order=2):
    return signal.sosfiltfilt(signal.butter(order, fc, fs=SR, output="sos"), x)


def bandpass(x, lo, hi, order=2):
    return signal.sosfiltfilt(signal.butter(order, [lo, hi], btype="bandpass", fs=SR, output="sos"), x)


def trim(x, head_db=-48.0, tail_db=-60.0, pre=0.004, post=0.05):
    """cut the silence a model pads with: keep `pre` before the first sound and `post` after the last"""
    e = envelope(x, 0.005)
    pk = e.max()
    if pk <= 1e-7:
        return x
    rel = db(e / pk)
    above = np.where(rel > head_db)[0]
    tail = np.where(rel > tail_db)[0]
    n5 = int(0.005 * SR)
    start = max(0, above[0] * n5 - int(pre * SR))
    end = min(len(x), (tail[-1] + 1) * n5 + int(post * SR))
    return x[start:end]


def fade(x, fin, fout, curve="cos"):
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if 0 < a < len(x):
        x[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if 0 < b < len(x):
        x[-b:] *= np.cos(np.linspace(0, np.pi / 2, b)) ** 2
    return x


def norm_peak(x, peak=1.0):
    return x / (np.max(np.abs(x)) + 1e-12) * peak


def place(n, start, piece):
    """add `piece` into a zero buffer of n samples so its sample 0 sits at `start` seconds (negative = head cut)"""
    out = np.zeros(n)
    i = int(round(start * SR))
    a = max(0, -i)
    i = max(0, i)
    k = min(len(piece) - a, n - i)
    if k > 0:
        out[i:i + k] = piece[a:a + k]
    return out


def glide(x, r0, r1, span=None):
    """variable-rate playback: the read speed goes r0 -> r1 over `span` seconds of OUTPUT (pitch and speed together,
    a tape glide); stops when the source runs out"""
    n_src = len(x)
    span_n = int((span or (len(x) / SR)) * SR)
    k = np.clip(np.arange(n_src * 2) / max(span_n, 1), 0, 1)
    rate = r0 + (r1 - r0) * k
    pos = np.cumsum(rate) - rate[0]
    pos = pos[pos < n_src - 1]
    return np.interp(pos, np.arange(n_src), x)


def hit_time(x):
    """the sample time (s) of the cue's main transient: the steepest rise into the loudest region"""
    n5 = int(0.005 * SR)
    e = envelope(x, 0.005)
    pk = e.max()
    best, bi = -1.0, int(np.argmax(e))
    for i in range(1, len(e)):
        if e[i] < 0.45 * pk:
            continue
        prev = np.mean(e[max(0, i - 8):i]) if i > 0 else 0.0
        jump = (e[i] - prev) / pk
        if jump > best:
            best, bi = jump, i
    lo = max(0, (bi - 3) * n5)
    hi = min(len(x), (bi + 2) * n5)
    seg = np.abs(x[lo:hi])
    if seg.size == 0:
        return bi * n5 / SR
    loc = np.max(np.abs(x[lo:min(len(x), hi + int(0.02 * SR))]))
    first = np.where(seg >= 0.25 * loc)[0]
    return (lo + (first[0] if first.size else 0)) / SR


def peak_time(x, smooth=0.05):
    e = envelope(x, 0.010)
    k = max(1, int(smooth / 0.010))
    e = np.convolve(e, np.ones(k) / k, "same")
    return float(np.argmax(e)) * 0.010


def soft_limit(y, peak_db=PEAK_DB, knee=0.55):
    """identity below knee * ceiling, a tanh shoulder above it that never reaches the ceiling (a soft-knee peak
    limiter on the sample, so the body of the sound is untouched and only the transient tips are rounded)"""
    ceil = 10 ** (peak_db / 20)
    k = knee * ceil
    a = np.abs(y)
    over = a > k
    out = y.copy()
    out[over] = np.sign(y[over]) * (k + (ceil - k) * np.tanh((a[over] - k) / (ceil - k)))
    return out


def level_to(x, target):
    """gain onto the loudness target under the limiter, iterated so the limiter's loss is made back exactly"""
    g = 10 ** ((target - lufs(x)) / 20)
    for _ in range(6):
        y = soft_limit(x * g)
        err = target - lufs(y)
        if abs(err) < 0.03:
            break
        g *= 10 ** (err / 20)
    return y


def limit_db(x, target):
    """how hard the limiter worked at that target: the pre-limit peak over the ceiling, dB (0 = untouched)"""
    g = 10 ** ((target - lufs(x)) / 20)
    return max(0.0, float(db(np.max(np.abs(x * g)))) - PEAK_DB)


def encode(x):
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


def sha256(b):
    return hashlib.sha256(b).hexdigest()


# ---- measurement + scoring --------------------------------------------------------------------------
def pitch_track(x, lo=70.0, hi=5000.0, frame=2048, hop=1024):
    """the dominant spectral peak per frame (Hz) where the frame is loud enough to matter; [] if none"""
    if len(x) < frame:
        x = np.concatenate([x, np.zeros(frame - len(x))])
    win = np.hanning(frame)
    f = np.fft.rfftfreq(frame, 1.0 / SR)
    band = (f >= lo) & (f <= hi)
    rms_all = np.sqrt(np.mean(x ** 2)) + 1e-12
    out = []
    for i in range(0, len(x) - frame + 1, hop):
        seg = x[i:i + frame]
        if np.sqrt(np.mean(seg ** 2)) < 0.3 * rms_all:
            continue
        s = np.abs(np.fft.rfft(seg * win))[band]
        out.append(float(f[band][int(np.argmax(s))]))
    return out


def pitch_trend(x):
    """the ratio of the median dominant frequency in the last third of the sound to the first third"""
    tr = pitch_track(x)
    if len(tr) < 3:
        return 1.0
    k = max(1, len(tr) // 3)
    return float(np.median(tr[-k:]) / max(np.median(tr[:k]), 1e-6))


def onset_count(x):
    """distinct attacks: envelope rises of 6 dB+ within 30 ms into the loud half, at least 90 ms apart"""
    e = envelope(x, 0.010)
    pk = e.max()
    ed = db(e / pk)
    hits, last = [], -99
    for i in range(3, len(e)):
        if ed[i] > -12 and ed[i] - np.min(ed[i - 3:i]) > 6 and i - last >= 9:
            hits.append(i * 0.010)
            last = i
    return hits


def features(x):
    x = trim(x)
    if len(x) < int(0.05 * SR):
        return None
    e = envelope(x)
    pk = e.max()
    dur = len(x) / SR
    t = np.arange(len(e)) * 0.010
    ip = int(np.argmax(e))
    onset = float(t[np.where(e >= 0.5 * pk)[0][0]])
    after = e[ip:]
    low10 = np.where(after <= 0.1 * pk)[0]
    decay = float(low10[0] * 0.010) if low10.size else float(dur - t[ip])
    tail_db = float(db(e[-5:].mean() / pk))
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    tot = spec.sum() + 1e-12
    s = spec[(f > 60) & (f < 12000)] + 1e-12
    hot = (np.abs(x) >= 0.999).astype(np.int8)
    runs = np.convolve(hot, np.ones(4, dtype=np.int8), "valid") >= 4
    return dict(dur=round(dur, 3), onset=round(onset, 3), peak_at=round(float(t[ip] / max(dur, 1e-6)), 3),
                decay=round(decay, 3), tail_db=round(tail_db, 1), low=round(float(spec[f < 180].sum() / tot), 3),
                hi=round(float(spec[f > 4000].sum() / tot), 3),
                flat=round(float(np.exp(np.mean(np.log(s))) / np.mean(s)), 3),
                trend=round(pitch_trend(x), 3), onsets=len(onset_count(x)),
                clip=round(float(np.mean(runs)) if runs.size else 0.0, 4))


def near(v, lo, hi, soft):
    if lo <= v <= hi:
        return 1.0
    d = (lo - v) if v < lo else (v - hi)
    return max(0.0, 1.0 - d / soft)


def score(profile, want_secs, ft):
    if ft is None:
        return -1.0, {"dead": 1.0}
    s = {"clip": 1.0 - min(1.0, ft["clip"] * 50), "tail": near(ft["tail_db"], -120, -26, 14)}
    if profile == "swell":
        s["peak_at"] = near(ft["peak_at"], 0.35, 0.85, 0.3)
        s["onset"] = near(ft["onset"], 0.12, 1.2, 0.3)
        s["low"] = near(ft["low"], 0.10, 1.0, 0.12)
        s["length"] = near(ft["dur"], 0.8 * want_secs, 1.6 * want_secs, 0.8)
    elif profile == "boom":
        s["onset"] = near(ft["onset"], 0.0, 0.05, 0.12)
        s["peak_at"] = near(ft["peak_at"], 0.0, 0.2, 0.3)
        s["decay"] = near(ft["decay"], 0.08, 0.9, 0.6)
        s["low"] = near(ft["low"], 0.10, 1.0, 0.12)
        s["onsets"] = near(ft["onsets"], 1, 2, 2)
    elif profile == "click":
        s["onset"] = near(ft["onset"], 0.0, 0.04, 0.1)
        s["decay"] = near(ft["decay"], 0.01, 0.35, 0.3)
        s["hi"] = near(ft["hi"], 0.05, 1.0, 0.08)
        s["onsets"] = near(ft["onsets"], 1, 2, 2)
    elif profile == "riser":
        s["peak_at"] = near(ft["peak_at"], 0.55, 1.0, 0.3)
        s["rise"] = near(ft["trend"], 1.15, 4.0, 0.3)
        s["tonal"] = near(ft["flat"], 0.0, 0.45, 0.3)
        s["onsets"] = near(ft["onsets"], 0, 2, 3)
    elif profile == "chime2":
        s["onset"] = near(ft["onset"], 0.0, 0.08, 0.15)
        s["two"] = near(ft["onsets"], 2, 3, 2)
        s["rise"] = near(ft["trend"], 1.05, 3.0, 0.15)
        s["tonal"] = near(ft["flat"], 0.0, 0.35, 0.3)
        s["length"] = near(ft["dur"], 0.9, 2.0, 0.8)
    elif profile == "fanfare":
        s["notes"] = near(ft["onsets"], 3, 6, 2)
        s["rise"] = near(ft["trend"], 1.05, 3.0, 0.2)
        s["tonal"] = near(ft["flat"], 0.0, 0.35, 0.3)
        s["held"] = near(ft["decay"], 0.6, 3.0, 0.5)
        s["length"] = near(ft["dur"], 2.2, 3.6, 1.0)
    elif profile == "sour":
        s["fall"] = near(ft["trend"], 0.3, 0.97, 0.15)
        s["tonal"] = near(ft["flat"], 0.0, 0.45, 0.3)
        s["length"] = near(ft["dur"], 0.8, 2.4, 0.8)
    elif profile == "drone":
        s["length"] = near(ft["dur"], 6.2, 9.0, 1.5)
        s["low"] = near(ft["low"], 0.15, 1.0, 0.15)
        s["sustain"] = near(ft["peak_at"], 0.3, 1.0, 0.3)
        s["calm"] = near(ft["onsets"], 0, 3, 4)
    elif profile == "beat":
        s["onset"] = near(ft["onset"], 0.0, 0.05, 0.12)
        s["low"] = near(ft["low"], 0.25, 1.0, 0.2)
        s["beats"] = near(ft["onsets"], 1, 2, 2)
        s["length"] = near(ft["dur"], 0.25, 1.0, 0.6)
    elif profile == "zap":
        s["onset"] = near(ft["onset"], 0.0, 0.03, 0.08)
        s["fall"] = near(ft["trend"], 0.2, 0.95, 0.2)
        s["decay"] = near(ft["decay"], 0.05, 0.35, 0.3)
        s["onsets"] = near(ft["onsets"], 1, 2, 2)
    return float(sum(s.values()) / len(s)), s


# ---- the takes --------------------------------------------------------------------------------------
def load_takes():
    return json.load(open(TAKES_JSON, encoding="utf-8")) if os.path.exists(TAKES_JSON) else {}


def save_takes(data):
    os.makedirs(TAKES_DIR, exist_ok=True)
    with open(TAKES_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1)
        f.write("\n")


def calls_spent(data, cue):
    return sum(len(v) for v in data.get(cue, {}).values())


def request(prompt, secs):
    """one generation; pcm_48000 first (no codec, no resample), mp3 192 if the tier refuses it"""
    import eleven
    body = {"text": prompt, "duration_seconds": max(0.5, secs), "prompt_influence": PROMPT_INFLUENCE}
    for fmt in ("pcm_48000", "mp3_44100_192"):
        try:
            raw = eleven.call("POST", "/v1/sound-generation", body=body, query={"output_format": fmt})
        except RuntimeError as e:
            m = re.search(r"-> (\d{3})", str(e))
            if fmt == "pcm_48000" and m and m.group(1) in ("400", "403", "422"):
                print("  pcm_48000 refused (HTTP %s) - falling back to mp3_44100_192" % m.group(1))
                continue
            raise
        if not isinstance(raw, (bytes, bytearray)):
            raise RuntimeError("unexpected response %r" % (raw,))
        return fmt, bytes(raw)
    raise RuntimeError("no output format accepted")


def generate(cues):
    data = load_takes()
    for cue in cues:
        spec = CUES[cue]
        want = sum(l["takes"] for l in spec["layers"])
        assert want <= MAX_CALLS, cue + ": the plan spends more than %d calls" % MAX_CALLS
        for lay in spec["layers"]:
            rows = data.setdefault(cue, {}).setdefault(lay["id"], [])
            while len(rows) < lay["takes"]:
                if calls_spent(data, cue) >= MAX_CALLS:
                    print("%-17s %-6s cap reached (%d calls) - not generating" % (cue, lay["id"], MAX_CALLS))
                    break
                n = len(rows) + 1
                d = os.path.join(TAKES_DIR, cue)
                os.makedirs(d, exist_ok=True)
                fmt, raw = request(lay["prompt"], lay["secs"])
                if fmt.startswith("pcm"):
                    # raw 16-bit PCM, no header: the model returns STEREO interleaved (measured 2026-10-04: every take
                    # was exactly 2x its asked length as mono, with Nyquist images); the byte count decides it
                    ch = 2 if abs(len(raw) / 4.0 / 48000 - lay["secs"]) < abs(len(raw) / 2.0 / 48000 - lay["secs"]) else 1
                    path = os.path.join(d, "%s_take_%d.wav" % (lay["id"], n))
                    with wave.open(path, "wb") as w:
                        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(48000); w.writeframes(raw[:len(raw) - len(raw) % (2 * ch)])
                    fmt += "/%dch" % ch
                else:
                    path = os.path.join(d, "%s_take_%d.mp3" % (lay["id"], n))
                    open(path, "wb").write(raw)
                ft = features(highpass(decode(path)))
                sc, parts = score(lay["profile"], lay["secs"], ft)
                rows.append(dict(name="take_%d" % n, file=os.path.relpath(path, REPO).replace("\\", "/"), format=fmt,
                                 prompt=lay["prompt"], secs=lay["secs"], features=ft, score=round(sc, 3),
                                 parts={k: round(v, 2) for k, v in parts.items()}))
                save_takes(data)
                print("%-17s %-6s take_%d  %s  score %.3f  %s" % (cue, lay["id"], n, fmt, sc, ft))
    save_takes(data)


def rescore(cues):
    data = load_takes()
    for cue in cues:
        for lay in CUES[cue]["layers"]:
            for r in data.get(cue, {}).get(lay["id"], []):
                ft = features(highpass(decode(os.path.join(REPO, r["file"]))))
                sc, parts = score(lay["profile"], lay["secs"], ft)
                r.update(features=ft, score=round(sc, 3), parts={k: round(v, 2) for k, v in parts.items()})
                print("%-17s %-6s %s score %.3f %s" % (cue, lay["id"], r["name"], sc, r["parts"]))
    save_takes(data)


def drop_file(stem):
    if not os.path.isdir(DROP_DIR):
        return None
    for f in sorted(os.listdir(DROP_DIR)):
        s, ext = os.path.splitext(f)
        if s == stem and ext.lower() in (".wav", ".mp3", ".flac", ".ogg", ".m4a"):
            return os.path.join(DROP_DIR, f)
    return None


def source_for(cue, lay, data, picks):
    """('drop'|'take', path, label) for one layer: a dropped layer, the user's pick, else the best score"""
    d = drop_file("%s__%s" % (cue, lay["id"]))
    if d:
        return "drop", d, "drop:" + os.path.basename(d)
    rows = data.get(cue, {}).get(lay["id"], [])
    ov = picks.get(cue, {}).get(lay["id"]) if isinstance(picks.get(cue), dict) else None
    if ov:
        for r in rows:
            if r["name"] == ov:
                return "take", os.path.join(REPO, r["file"]), "%s/%s (picked)" % (lay["id"], r["name"])
    rows = [r for r in rows if r.get("features")]
    if not rows:
        return None
    r = max(rows, key=lambda r: r["score"])
    return "take", os.path.join(REPO, r["file"]), "%s/%s (score %.2f)" % (lay["id"], r["name"], r["score"])


def prep(path):
    return trim(highpass(decode(path)))


# ---- the composers (one per cue: the game's timeline, seconds) -------------------------------------
def fit_tail(y, total, fout):
    """exactly `total` seconds: cut or zero-pad, then the end faded out over `fout` seconds"""
    n = int(round(total * SR))
    y = y[:n] if len(y) >= n else np.concatenate([y, np.zeros(n - len(y))])
    return fade(y, 0.004, fout)


def comp_wave(L):
    total = CUES["tod_arena_wave"]["secs"]
    n = int(round(total * SR))
    horn, drum = norm_peak(L["horn"]), norm_peak(L["drum"])
    # the horn culminates WITH the hit: its loudest moment 50 ms past the drum's transient
    start = WAVE_HIT + 0.05 - peak_time(horn)
    if start < 0:
        cut = int(-start * SR)
        horn = fade(horn[cut:], 0.12, 0.0)
        start = 0.0
    h = place(n, start, horn)
    # after the hit the horn sits under the drum's body (a 5 dB duck released over 0.4 s) and dies by the end
    t = np.arange(n) / SR
    duck = 1.0 - 0.44 * np.clip(1 - np.abs(t - (WAVE_HIT + 0.12)) / 0.4, 0, 1) * (t >= WAVE_HIT)
    h *= duck
    d = place(n, WAVE_HIT - hit_time(drum), drum)
    y = 0.58 * h + 1.0 * d
    return fit_tail(y, total, 0.32)


def comp_clear(L):
    spec = CUES["tod_arena_clear"]
    y = L["chime"]
    y = place(len(y) + int(0.01 * SR), 0.004 - min(hit_time(y), 0.03) if hit_time(y) < 0.03 else 0.0, y)
    total = min(max(len(trim(y)) / SR, spec["secs"] - spec["tol"]), spec["secs"] + spec["tol"])
    return fit_tail(y, round(total, 3), 0.28)


def comp_level(L):
    spec = CUES["tod_arena_level"]
    y = L["fanfare"]
    total = min(max(len(trim(y)) / SR, spec["secs"] - spec["tol"]), spec["secs"] + spec["tol"])
    return fit_tail(y, round(total, 3), 0.45)


def comp_gate(L):
    total = CUES["tod_arena_gate"]["secs"]
    n = int(round(total * SR))
    clack, whine, clank = norm_peak(L["clack"]), norm_peak(L["whine"]), norm_peak(L["clank"])
    # the latch at once
    c = place(n, 0.012 - hit_time(clack), clack)
    # the whine climbs INTO the clank: guaranteed to rise (a tape glide if the take is flat), its peak just before it
    tr = pitch_trend(whine)
    if tr < 1.15:
        whine = glide(whine, 1.0, float(np.clip(1.22 / max(tr, 0.5), 1.0, 1.3)))
    end = GATE_CLANK - 0.015
    start = end - peak_time(whine)
    if start < 0.03:
        cut = int((0.03 - start) * SR)
        whine = whine[cut:]
        start = 0.03
    whine = fade(whine, 0.08, 0.0)
    w = place(n, start, whine)
    t = np.arange(n) / SR
    w *= (0.30 + 0.70 * np.clip((t - 0.03) / (end - 0.03), 0, 1) ** 1.4)     # builds
    w *= np.where(t < GATE_CLANK, 1.0, np.exp(-(t - GATE_CLANK) / 0.035))   # the gate cuts it off
    k = place(n, GATE_CLANK - hit_time(clank), clank)
    y = 0.62 * c + 0.55 * norm_peak(w) + 1.0 * k
    return fit_tail(y, total, 0.25)


def comp_cursed(L):
    total = CUES["tod_house_cursed"]["secs"]
    n = int(round(total * SR))
    hit, sour = norm_peak(L["hit"]), norm_peak(L["sour"])
    # the jackpot's bell gone wrong: made to fall if the take does not
    tr = pitch_trend(sour)
    if tr > 0.94:
        sour = glide(sour, 1.0, float(np.clip(0.80 / max(tr, 0.5), 0.6, 1.0)))
    sour = sour[max(0, int(hit_time(sour) * SR) - int(0.004 * SR)):]
    # the 70 ms suck-in: the sour bell's own first 0.35 s reversed, squeezed under a rising curve, ending at the hit
    head = sour[:int(0.35 * SR)][::-1]
    suck = head[-int(CURSED_HIT * SR):] * np.linspace(0, 1, int(CURSED_HIT * SR)) ** 2
    s = place(n, 0.0, suck)
    h = place(n, CURSED_HIT - hit_time(hit), hit)
    o = place(n, CURSED_HIT + 0.035, fade(sour, 0.01, 0.0))
    y = 0.42 * norm_peak(s) * (np.max(np.abs(suck)) > 0) + 1.0 * h + 0.52 * o
    return fit_tail(y, total, 0.35)


def comp_drain(L):
    total = CUES["tod_house_drain"]["secs"]
    n = int(round(total * SR))
    t = np.arange(n) / SR
    drone = L["drone"]
    # the drone rises a little over two semitones across the drain (a tape glide), long enough for the whole cue
    drone = glide(drone, 1.0, 1.12, span=6.0)
    if len(drone) < n:   # never expected (7.0 s asked); a crossfaded repeat rather than a hole
        rep = int(0.5 * SR)
        drone = np.concatenate([drone[:-rep], drone[-rep:] * np.linspace(1, 0, rep) + drone[:rep] * np.linspace(0, 1, rep), drone[rep:]])
    drone = drone[:n] if len(drone) >= n else np.concatenate([drone, np.zeros(n - len(drone))])
    k = np.clip(t / 6.0, 0, 1)
    # the field opens as the health goes: a dark copy and a wider copy blended by k
    dark, wide = lowpass(drone, 520), lowpass(drone, 2600)
    dr = dark * (1 - k) + wide * k
    # a pocket for the Dealer's monologue (he talks over the whole drain): about -6 dB across 1-3.5 kHz
    dr = dr - 0.5 * bandpass(dr, 1000, 3500)
    dr = norm_peak(dr) * (0.45 + 0.55 * k ** 1.2)
    dr *= np.where(t < 6.0, 1.0, np.exp(-(t - 6.0) / 0.14))      # ONE HP: the field lets go with the last cut
    dr = fade(dr, 0.35, 0.0)
    # the heartbeat ON the cuts, quickening: one beat unit (a lub-dub), tightened for the fast beats
    unit = norm_peak(L["beat"])
    unit = unit[max(0, int(hit_time(unit) * SR) - int(0.002 * SR)):]
    beats = np.zeros(n)
    for i, bt in enumerate(DRAIN_BEATS):
        gap = (DRAIN_BEATS[i + 1] - bt) if i + 1 < len(DRAIN_BEATS) else 0.5
        u = unit
        if gap < 0.45:
            u = glide(unit, 1.10, 1.10)                    # a racing heart: a touch higher and tighter
        keep = min(len(u), int((gap - 0.01) * SR))
        u = fade(u[:keep], 0.001, min(0.07, keep / SR / 3))
        g = 0.55 + 0.45 * (i / (len(DRAIN_BEATS) - 1))
        if i == len(DRAIN_BEATS) - 1:
            g = 1.08                                         # the last cut, the heaviest beat
        beats += place(n, bt, g * u)
    y = 0.62 * dr + 0.95 * beats
    return fit_tail(y, total, 0.12)


def comp_cut(L):
    total = CUES["tod_house_cut"]["secs"]
    y = L["bite"]
    tr = pitch_trend(y)
    if tr > 0.92:
        y = glide(y, 1.0, float(np.clip(0.78 / max(tr, 0.5), 0.6, 1.0)), span=total)
    y = y[max(0, int(hit_time(y) * SR) - int(0.002 * SR)):]
    return fit_tail(y, total, 0.12)


COMPOSE = {"tod_arena_wave": comp_wave, "tod_arena_clear": comp_clear, "tod_arena_level": comp_level,
           "tod_arena_gate": comp_gate, "tod_house_cursed": comp_cursed, "tod_house_drain": comp_drain,
           "tod_house_cut": comp_cut}


# ---- pick: compose, level, write ----------------------------------------------------------------------
def render(cue, data, picks):
    """-> (wav bytes, info) or (None, reason)"""
    spec = CUES[cue]
    whole = drop_file(cue)
    if whole:
        y = prep(whole)
        y = fit_tail(y, min(len(y) / SR, spec["secs"] + spec["tol"]), 0.2)
        sources = ["drop:" + os.path.basename(whole)]
    else:
        L, sources = {}, []
        for lay in spec["layers"]:
            src = source_for(cue, lay, data, picks)
            if not src:
                return None, "no source for layer %s (generate it, or drop %s__%s.wav)" % (lay["id"], cue, lay["id"])
            L[lay["id"]] = prep(src[1])
            sources.append(src[2])
        y = COMPOSE[cue](L)
    y = fade(y - np.mean(y), 0.003, 0.004)
    lim = limit_db(y, spec["lufs"])
    y = level_to(y, spec["lufs"])
    b = encode(y)
    yq = np.frombuffer(b[44:], dtype="<i2").astype(np.float64) / 32767
    return b, dict(secs=round(len(yq) / SR, 4), lufs=round(lufs(yq), 2),
                   peak_db=round(float(db(np.max(np.abs(yq)))), 2), limit_db=round(lim, 1), sources=sources)


def manifest_path(root, group):
    return os.path.join(root, GROUPS[group]["manifest"].replace("/", os.sep))


def wav_path(root, cue):
    return os.path.join(root, GROUPS[CUES[cue]["group"]]["dir"].replace("/", os.sep), cue + ".wav")


def load_manifest(root, group):
    p = manifest_path(root, group)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def write_manifest(root, group, cues):
    man = dict(note="AUTHORED cues (asset pack PK16): these wavs are not the stand-in render. The stand-in generator's "
                    "--check verifies each one by its sha256 here; re-make them with " + TOOL + " (generate / pick), "
                    "never by hand.",
               tool=TOOL, cues=cues)
    p = manifest_path(root, group)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    text = json.dumps(man, indent=1) + "\n"
    cur = open(p, encoding="utf-8").read() if os.path.exists(p) else None
    if cur != text:
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)


def pick(cues, root):
    data = load_takes()
    picks = json.load(open(PICKS_JSON, encoding="utf-8")) if os.path.exists(PICKS_JSON) else {}
    mans = {g: (load_manifest(root, g) or {}).get("cues", {}) for g in GROUPS}
    for cue in cues:
        b, info = render(cue, data, picks)
        if b is None:
            print("%-17s NOT SHIPPED: %s" % (cue, info))
            continue
        p = wav_path(root, cue)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not os.path.exists(p) or open(p, "rb").read() != b:
            open(p, "wb").write(b)
        g = CUES[cue]["group"]
        mans[g][cue] = dict(file=GROUPS[g]["dir"] + "/" + cue + ".wav", sha256=sha256(b), secs=info["secs"],
                            lufs=info["lufs"], peak_db=info["peak_db"], limit_db=info["limit_db"], sources=info["sources"])
        print("%-17s %.3f s  %6.2f LUFS  peak %5.2f dBFS  limiter %4.1f dB  <- %s" % (
            cue, info["secs"], info["lufs"], info["peak_db"], info["limit_db"], ", ".join(info["sources"])))
    for g, cmap in mans.items():
        if cmap:
            ordered = {c: cmap[c] for c in ORDER if c in cmap}
            write_manifest(root, g, ordered)


# ---- verify: the contract of every shipped file -------------------------------------------------------
def read_wav(p):
    with wave.open(p, "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    return ch, sw, sr, np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32767


def verify(root, quiet=False):
    bad, rows = [], []
    for cue in ORDER:
        spec = CUES[cue]
        p = wav_path(root, cue)
        if not os.path.exists(p):
            bad.append(cue + ": missing")
            continue
        ch, sw, sr, x = read_wav(p)
        secs = len(x) / sr
        pk = float(db(np.max(np.abs(x))))
        lv = lufs(x)
        notes = []
        if (ch, sw, sr) != (1, 2, SR):
            bad.append("%s: not mono 48 kHz 16-bit" % cue)
        if abs(secs - spec["secs"]) > spec["tol"] + 1e-6:
            bad.append("%s: %.3f s, wants %.2f +- %.3f" % (cue, secs, spec["secs"], spec["tol"]))
        if pk > PEAK_DB + 0.05:
            bad.append("%s: peak %.2f dBFS over %.1f" % (cue, pk, PEAK_DB))
        if abs(lv - spec["lufs"]) > 0.6:
            bad.append("%s: %.2f LUFS, target %.1f" % (cue, lv, spec["lufs"]))
        if np.max(np.abs(x[:24])) > 0.02 or np.max(np.abs(x[-24:])) > 0.01:
            bad.append("%s: does not start and end on silence" % cue)
        if cue == "tod_arena_wave":
            ht = hit_time(x[int((WAVE_HIT - 0.25) * SR):]) + WAVE_HIT - 0.25
            notes.append("hit %.3f" % ht)
            if abs(ht - WAVE_HIT) > 0.03:
                bad.append("%s: the drum hit is at %.3f s, wants %.2f" % (cue, ht, WAVE_HIT))
        if cue == "tod_arena_gate":
            ht = hit_time(x[int((GATE_CLANK - 0.12) * SR):]) + GATE_CLANK - 0.12
            notes.append("clank %.3f" % ht)
            if abs(ht - GATE_CLANK) > 0.025:
                bad.append("%s: the clank is at %.3f s, wants %.2f (the elite's rise)" % (cue, ht, GATE_CLANK))
        if cue == "tod_house_cursed":
            ht = hit_time(x[:int(0.4 * SR)])
            notes.append("hit %.3f" % ht)
            if ht > 0.10:
                bad.append("%s: the thud is at %.3f s - it must land with the banner stamp" % (cue, ht))
        if cue == "tod_house_drain":
            e = envelope(lowpass(x, 160), 0.005)
            found = []
            for bt in DRAIN_BEATS:
                i0, i1 = int((bt - 0.03) / 0.005), int((bt + 0.06) / 0.005)
                pre = np.mean(e[max(0, i0 - 10):i0])
                found.append(float(db(np.max(e[i0:i1]) / (pre + 1e-9))))
            notes.append("beat rise dB min %.1f" % min(found))
            if min(found) < 3.0:
                bad.append("%s: a heartbeat on the cut grid is missing (rise %.1f dB)" % (cue, min(found)))
            tail = float(db(np.sqrt(np.mean(x[int(6.35 * SR):] ** 2)) / (np.sqrt(np.mean(x[int(5.0 * SR):int(6.0 * SR)] ** 2)) + 1e-12)))
            notes.append("tail %.1f dB" % tail)
            if tail > -20:
                bad.append("%s: the drain does not let go after the last cut (tail %.1f dB)" % (cue, tail))
        if cue in ("tod_house_cut", "tod_arena_clear", "tod_arena_level"):
            notes.append("onset %.3f" % hit_time(x[:int(0.3 * SR)]))
        rows.append("%-17s %5.3f s  %6.2f LUFS (target %5.1f)  peak %5.2f  %s" % (cue, secs, lv, spec["lufs"], pk, "  ".join(notes)))
    if not quiet:
        print("\n".join(rows))
    return bad


def check(root):
    """the files under root match their manifests (format + sha); no API, no DSP"""
    bad = []
    for g in GROUPS:
        man = load_manifest(root, g)
        if man is None:
            bad.append("%s missing" % GROUPS[g]["manifest"])
            continue
        for cue in [c for c in ORDER if CUES[c]["group"] == g]:
            ent = man["cues"].get(cue)
            if not ent:
                bad.append("%s not in %s" % (cue, GROUPS[g]["manifest"]))
                continue
            p = wav_path(root, cue)
            if not os.path.exists(p) or sha256(open(p, "rb").read()) != ent["sha256"]:
                bad.append("%s differs from its manifest" % cue)
    if bad:
        print("ARENA/HOUSE AUTHORED CUES STALE: " + "; ".join(bad) + " - run: python " + TOOL + " pick")
        sys.exit(1)
    print("ARENA/HOUSE AUTHORED CUES OK: %d cues match their manifests" % len(ORDER))


# ---- the desk + the review sheet --------------------------------------------------------------------------
def desk(root):
    data = load_takes()
    mans = {g: (load_manifest(root, g) or {}).get("cues", {}) for g in GROUPS}
    rel = lambda p: os.path.relpath(p, WORK).replace("\\", "/")
    h = ["<!doctype html><meta charset=utf-8><title>Arena + House cues desk (PK16)</title>",
         "<style>body{font:14px system-ui;background:#111;color:#ddd;margin:24px}h2{margin:26px 0 4px;color:#9ef}"
         "td{padding:3px 10px;border-bottom:1px solid #333;vertical-align:middle}.ship{color:#6f6;font-weight:bold}"
         "code{color:#fc8}audio{height:28px}small{color:#999}</style>",
         "<h1>Battle Arena + Dealer's House cues: stand-in vs authored</h1>",
         "<p>Override a layer: <code>picks.json</code> = <code>{\"tod_arena_wave\": {\"horn\": \"take_2\"}}</code>, or drop "
         "<code>drop/&lt;cue&gt;.wav</code> (whole cue) / <code>drop/&lt;cue&gt;__&lt;layer&gt;.wav</code>, then "
         "<code>python %s pick --out-root ...</code>.</p>" % TOOL]
    for cue in ORDER:
        spec = CUES[cue]
        ent = mans[spec["group"]].get(cue, {})
        h.append("<h2>%s <small>%.2f s, %.1f LUFS target</small></h2><table>" % (cue, spec["secs"], spec["lufs"]))
        h.append("<tr><td>STAND-IN (shipping today)</td><td></td><td><audio controls src='%s'></audio></td></tr>" %
                 rel(wav_path(REPO, cue)))
        h.append("<tr><td class=ship>AUTHORED</td><td><small>%s</small></td><td><audio controls src='%s'></audio></td></tr>" %
                 (", ".join(ent.get("sources", [])), rel(wav_path(root, cue))))
        for lay in spec["layers"]:
            for r in data.get(cue, {}).get(lay["id"], []):
                h.append("<tr><td>%s %s</td><td><small>score %.2f %s</small></td><td><audio controls src='%s'></audio></td></tr>" %
                         (lay["id"], r["name"], r["score"], r.get("parts", {}), rel(os.path.join(REPO, r["file"]))))
        h.append("</table>")
    with open(os.path.join(WORK, "desk.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(h) + "\n")
    review_png(root, os.path.join(WORK, "_review.png"))
    print("desk:", os.path.join(WORK, "desk.html"))


def _spectro(x, w, h):
    frame, hop = 1024, 256
    if len(x) < frame:
        x = np.concatenate([x, np.zeros(frame - len(x))])
    win = np.hanning(frame)
    cols = []
    for i in range(0, len(x) - frame + 1, hop):
        cols.append(np.abs(np.fft.rfft(x[i:i + frame] * win)))
    S = db(np.array(cols).T + 1e-9)
    f = np.fft.rfftfreq(frame, 1.0 / SR)
    ys = np.exp(np.linspace(np.log(16000), np.log(40), h))
    rows = np.array([S[np.argmin(np.abs(f - y))] for y in ys])
    rows = np.clip((rows - (rows.max() - 70)) / 70, 0, 1)
    idx = np.linspace(0, rows.shape[1] - 1, w).astype(int)
    return rows[:, idx]


def review_png(root, out):
    from PIL import Image, ImageDraw
    W, H, LBL = 900, 120, 16
    tmax = 6.6
    pxs = lambda t: int(t / tmax * (W - 20)) + 10
    sheet = Image.new("RGB", (2 * W + 30, len(ORDER) * (2 * H + 2 * LBL + 26) + 10), (24, 26, 32))
    dr = ImageDraw.Draw(sheet)
    y0 = 10
    marks = {"tod_arena_wave": [WAVE_HIT], "tod_arena_gate": [GATE_CLANK], "tod_house_cursed": [CURSED_HIT],
             "tod_house_drain": DRAIN_CUTS}
    for cue in ORDER:
        dr.text((10, y0), "%s   (markers: the game's sync points)" % cue, fill=(160, 220, 255))
        y0 += 18
        for col, (label, p) in enumerate((("stand-in (shipping)", wav_path(REPO, cue)), ("authored", wav_path(root, cue)))):
            x0 = 10 + col * (W + 10)
            dr.text((x0, y0), label, fill=(200, 200, 200))
            if not os.path.exists(p):
                continue
            _, _, _, x = read_wav(p)
            # envelope (dB, -48..0)
            e = db(envelope(x, 0.005) / 1.0)
            box = (x0, y0 + LBL, x0 + W, y0 + LBL + H)
            dr.rectangle(box, outline=(70, 70, 80))
            pts = [(x0 + pxs(i * 0.005), y0 + LBL + H - int(np.clip((v + 48) / 48, 0, 1) * H)) for i, v in enumerate(e)]
            dr.line(pts, fill=(110, 230, 140))
            # spectrogram
            spec_w = max(2, pxs(len(x) / SR) - 10)
            S = _spectro(x, spec_w, H)
            img = Image.fromarray((np.stack([S * 255, S * 180, (1 - S) * 60 + S * 90], -1)).astype(np.uint8))
            sheet.paste(img, (x0 + 10, y0 + 2 * LBL + H + 4))
            for m in marks.get(cue, []):
                xm = x0 + pxs(m)
                dr.line([(xm, y0 + LBL), (xm, y0 + 2 * LBL + 2 * H + 4)], fill=(255, 80, 80))
        y0 += 2 * H + 2 * LBL + 8
    sheet.save(out)
    print("review sheet:", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="")
    ap.add_argument("--cue", action="append")
    ap.add_argument("--out-root", default=REPO)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cues = a.cue or ORDER
    for c in cues:
        if c not in CUES:
            sys.exit("unknown cue %s" % c)
    root = os.path.abspath(a.out_root)
    if a.check or a.cmd == "check":
        check(root)
    elif a.cmd == "generate":
        generate(cues)
    elif a.cmd == "rescore":
        rescore(cues)
    elif a.cmd == "pick":
        pick(cues, root)
        bad = verify(root)
        if bad:
            print("VERIFY FAILED:\n  " + "\n  ".join(bad))
            sys.exit(1)
    elif a.cmd == "verify":
        bad = verify(root)
        print("VERIFY " + ("OK" if not bad else "FAILED:\n  " + "\n  ".join(bad)))
        sys.exit(1 if bad else 0)
    elif a.cmd == "desk":
        desk(root)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
