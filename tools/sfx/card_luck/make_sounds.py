"""THE CARD + LUCK STINGS (asset pack PK17, 2026-10-04): the authored sounds of the card system's big moments.

Nine cues, one pipeline (ElevenLabs takes, measured, scored, fitted, levelled, sha-pinned):

  THE CLASS TIER PROMOTION  (_tod_upgrades.gsc tier_up, the new tier gun handed over)
    tod_tier_sting       sfx/   STEREO, ~2 s   a heavy mechanical lock-in, then a rising power swell that lands a sub drop.
                                               Its own sound: until now the promotion borrowed the 0.86 s RARE/EPIC sting.
  THE NEAR MISS + THE HOT STREAK (docs/201) - they REPLACE the synthesised placeholders BY NAME. Same files, same alias
  rows (sound/aliases/tod_near.csv stays tools/near_miss/make_sounds.py's), EXACT lengths (the spin and the card pull
  are timed to them):
    tod_spin_teeter      near/  0.50 s   STOPPED SHORT: the reel strains on the seam of a better tile, cut off unresolved
    tod_spin_near        near/  0.80 s   the "so close": a deflating fall
    tod_pull_reach       near/  0.66 s   THE REACH: a swell toward the next rung, held at full tension to the cut
    tod_pull_reach_fail  near/  0.45 s   SO CLOSE: the swell let go
    tod_pull_break       near/  0.90 s   BREAK THROUGH: a crack, then a bright rising burst
    tod_heat_up          near/  0.80 s   HEATING UP: an ignition whoosh with crackle
    tod_heat_fire        near/  1.30 s   ON FIRE: a big whoosh into a roaring blaze
    tod_heat_out         near/  0.70 s   the streak ends: a hiss falling away

Every near file is mono 48 kHz 16-bit, EXACTLY the placeholder's sample count, faded in 3 ms, ending on silence,
levelled to the placeholder's loudness target (the same numbers tools/near_miss/make_sounds.py SOUNDS carries, which
sit inside the card-reveal kit's -8.6 .. -13.7 LUFS) under a look-ahead limiter at -1.5 dBFS. The tier sting is
stereo 48 kHz 16-bit, 1.5 - 2.5 s, starting on its first sample, at tod_super_sting's -8.6 LUFS under -1.0 dBFS.

  python tools/sfx/card_luck/make_sounds.py generate [--cue NAME] [--takes N]   ElevenLabs takes (at most 3 per cue)
  python tools/sfx/card_luck/make_sounds.py rescore  [--cue NAME]               re-measure the kept takes
  python tools/sfx/card_luck/make_sounds.py pick     [--cue NAME] [--out-root DIR]
                                                     fit + level the chosen take per cue, write the wavs under DIR
                                                     (default: the repo), the manifest, and DIR/tools/near_miss/authored.json
                                                     (the near_miss tool's authored lane: name -> sha)
  python tools/sfx/card_luck/make_sounds.py review                              spectrogram sheet + listening desk
  python tools/sfx/card_luck/make_sounds.py --check [--root DIR]                the build gate (no API, no DSP)

The gate: every manifest file present with its sha and the right format/length, tools/near_miss/authored.json naming
the same eight shas, the tod_tier_sting row in sound/aliases/tod_ui.csv (UIN_MOD, 95/95, 2d, NONLOOPING, no context),
tod_ui.csv in the sound zone config, and a script that plays "tod_tier_sting".

The key is ELEVENLABS_API_KEY (tools/black_market_vo/eleven.py: never printed, never stored). Takes live under
tmp/asset_prod/PK17-card-luck-stings/takes/ (not in git). The user's override: picks.json beside takes.json,
{"tod_heat_up": "take_2"}.
"""
import argparse, csv, hashlib, io, json, os, re, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(REPO, "tools", "black_market_vo"))

SR = 48000
PACK = "PK17-card-luck-stings"
WORK = os.path.join(REPO, "tmp", "asset_prod", PACK)
TAKES_DIR = os.path.join(WORK, "takes")
TAKES_JSON = os.path.join(TAKES_DIR, "takes.json")
PICKS_JSON = os.path.join(TAKES_DIR, "picks.json")
MANIFEST = os.path.join(HERE, "sounds_manifest.json")
AUTHORED_REL = "tools/near_miss/authored.json"
UI_CSV_REL = "sound/aliases/tod_ui.csv"
SZC_REL = "sound/zoneconfig/zm_tod2_cybercity.szc"
MAX_TAKES = 3
PROMPT_INFLUENCE = 0.7
FIX = "run: python tools/sfx/card_luck/make_sounds.py pick"

# ---- the cues -------------------------------------------------------------------------------------------------
# dir: sound_assets/tod/<dir>/; ch: 1 mono / 2 stereo; secs: the EXACT shipped length (None = the take's own, inside
# span); ask: the duration ElevenLabs is asked for (a cue that must hold to its cut is asked LONGER and cut);
# fit: "cut" (a short 12 ms fade at the cut: the next sound takes over) | "ring" (a squared fade over fade_out s);
# lufs / peak: the level; profile: the scoring shape; prompt: the text.
CUES = {
    "tod_tier_sting": dict(dir="sfx", ch=2, secs=None, span=(1.5, 2.5), ask=2.2, fit="ring", fade_out=0.35, lufs=-8.6, peak=-1.0,
        profile="tier",
        prompt="a heavy sci-fi weapon class promotion: a massive metallic mechanical lock-in clunk, then a rising electric "
               "power surge that swells upward and slams into a deep booming sub bass drop with a glittering electric tail, "
               "cinematic cyberpunk game rank up sting, no music, no voice"),
    "tod_spin_teeter": dict(dir="near", ch=1, secs=0.50, ask=0.8, fit="cut", fade_out=0.012, lufs=-13.0, peak=-1.5,
        profile="rising",
        prompt="a slot machine reel straining against its stop: a fast mechanical ratchet of clicks speeding up under a "
               "tense rising electric whine that trembles, building suspense that never resolves, dry and close, no music"),
    "tod_spin_near": dict(dir="near", ch=1, secs=0.80, ask=0.8, fit="ring", fade_out=0.12, lufs=-12.5, peak=-1.5,
        profile="fall",
        prompt="a short disappointed near miss game sound: two soft glassy synth chime notes falling in pitch, the second "
               "one bending down and fading out with a small sigh of air, deflated, clean, no music"),
    "tod_pull_reach": dict(dir="near", ch=1, secs=0.66, ask=1.0, fit="cut", fade_out=0.015, lufs=-11.5, peak=-1.5,
        profile="rising",
        prompt="a tense magical energy riser: a shimmering airy swell climbing in pitch under a high trembling crystal tone "
               "hovering at maximum tension, suspense, about to break, game card reveal, no music"),
    "tod_pull_reach_fail": dict(dir="near", ch=1, secs=0.45, ask=0.5, fit="ring", fade_out=0.08, lufs=-12.5, peak=-1.5,
        profile="fall",
        prompt="a quick deflating power down: a synth tone sliding down in pitch fast into a soft muffled thump and a small "
               "puff of air, letdown, short game UI sound, no music"),
    "tod_pull_break": dict(dir="near", ch=1, secs=0.90, ask=1.0, fit="ring", fade_out=0.18, lufs=-10.0, peak=-1.5,
        profile="burst",
        prompt="a magical crystal barrier shattering: a sharp glassy crack and a punchy sub thump that burst into a bright "
               "rising sparkling chime arpeggio, triumphant breakthrough, game reward, no music"),
    "tod_heat_up": dict(dir="near", ch=1, secs=0.80, ask=0.8, fit="ring", fade_out=0.12, lufs=-11.5, peak=-1.5,
        profile="whoosh",
        prompt="a fire igniting: a quick rising whoosh of flame catching with a few bright crackling sparks, short and "
               "punchy, close, no music"),
    "tod_heat_fire": dict(dir="near", ch=1, secs=1.30, ask=1.4, fit="ring", fade_out=0.22, lufs=-10.0, peak=-1.5,
        profile="blaze",
        prompt="a huge fireball igniting: a big rising flame whoosh that erupts into a deep roaring blaze with dense "
               "crackling embers and a bright rising heroic synth sting on top, on fire power up, no music"),
    "tod_heat_out": dict(dir="near", ch=1, secs=0.70, ask=0.7, fit="ring", fade_out=0.15, lufs=-14.0, peak=-1.5,
        profile="fade",
        prompt="a fire snuffed out: a sharp steam hiss fading away with a soft descending tone and a few dying embers, "
               "short, no music"),
}
ORDER = list(CUES.keys())
NEAR = [c for c in ORDER if CUES[c]["dir"] == "near"]

# ---- the takes: what each ElevenLabs generation is FOR -----------------------------------------------------------
# A cue is a DESIGN (see DESIGNS below): recorded-quality textures from ElevenLabs (an ignition, a shatter, a clank, a
# hiss) layered with tonal parts written in the card-reveal kit's key (D major: the rungs ring D5 / F#5 / A5 / C#6,
# the LEGENDARY flip is a D major chord, the reel's crawl climbs A4 -> C#5 and its stop rings A5). take_N is generated
# from PLAN[cue][N-1]; `reverse` marks a take recorded as a decay to be played backwards (a model puts the loudest
# moment first whatever the prompt says, so a swell is a reversed burst). At most MAX_TAKES per cue.
PLAN = {
    "tod_tier_sting": [
        dict(role="whole (reference)", ask=2.2, prompt=CUES["tod_tier_sting"]["prompt"]),
        dict(role="the lock-in", ask=1.0,
             prompt="a single heavy mechanical lock-in: a massive steel bolt slamming home into its lock with a deep "
                    "metallic clunk and a short bright metal ring, close and dry, one hit only, no music"),
        dict(role="the swell (reversed)", ask=1.6, reverse=True,
             prompt="a powerful electric energy discharge: a bright crackling burst of electricity with arcing sparks "
                    "and a deep hum that decays away into a shimmering electric tail, sci-fi, no music"),
    ],
    "tod_spin_teeter": [
        dict(role="ratchet (reference)", ask=0.8, prompt=CUES["tod_spin_teeter"]["prompt"]),
        dict(role="the strain", ask=1.0,
             prompt="a tense high-pitched electric motor whine straining under load, trembling and wavering, about to "
                    "stall, sustained without stopping, no clicks, no music"),
    ],
    "tod_spin_near": [
        dict(role="tone (reference)", ask=0.8, prompt=CUES["tod_spin_near"]["prompt"]),
        dict(role="the sigh of air", ask=0.8,
             prompt="a soft short breath of air, a gentle breathy whoosh that fades away, quiet and close, no voice, "
                    "no music"),
        dict(role="the air (take_2 came back a tone)", ask=0.8,
             prompt="a soft short whoosh of air, a gentle breeze puff passing by, airy noise only, no tone, no music"),
    ],
    "tod_pull_reach": [
        dict(role="the shimmer", ask=1.0, prompt=CUES["tod_pull_reach"]["prompt"]),
        dict(role="the swell (reversed)", ask=1.2, reverse=True,
             prompt="a deep airy cinematic boom swoosh that decays away with a long rumbling shimmering tail, "
                    "suspense, no music"),
    ],
    "tod_pull_reach_fail": [
        dict(role="the slide down", ask=0.5, prompt=CUES["tod_pull_reach_fail"]["prompt"]),
        dict(role="the muffled thump", ask=0.5,
             prompt="a soft muffled low thump with a small puff of air, like a fist hitting a pillow, short and dry, "
                    "no music"),
    ],
    "tod_pull_break": [
        dict(role="the crack", ask=1.0, prompt=CUES["tod_pull_break"]["prompt"]),
        dict(role="the sparkle", ask=1.0,
             prompt="a bright magical sparkle burst, glittering chimes and shimmering twinkles scattering and fading "
                    "out, a reward, no music"),
    ],
    "tod_heat_up": [
        dict(role="ignition A", ask=0.8, prompt=CUES["tod_heat_up"]["prompt"]),
        dict(role="ignition B", ask=0.8,
             prompt="a gas burner igniting with a soft whoomp and a rush of flame, a few crackles, short, close, "
                    "no music"),
        dict(role="the crackle (take_2 came back silent)", ask=0.8,
             prompt="close crackling fire embers popping and sparking, sharp dry crackles and pops, no whoosh, no music"),
    ],
    "tod_heat_fire": [
        dict(role="blaze A", ask=1.4, prompt=CUES["tod_heat_fire"]["prompt"]),
        dict(role="blaze B", ask=1.5,
             prompt="a large fireball igniting with a big whoomp, roaring up into a blazing fire with crackling "
                    "embers, powerful, close, no music"),
    ],
    "tod_heat_out": [
        dict(role="hiss A", ask=0.7, prompt=CUES["tod_heat_out"]["prompt"]),
        dict(role="embers dying", ask=0.8,
             prompt="a small fire dying out, embers fizzling with a soft fading sizzle and a couple of last quiet "
                    "crackles, no music"),
    ],
}


# ---- audio helpers --------------------------------------------------------------------------------------------
def decode(path, ch):
    """any audio file -> float64 array (n, ch) at SR (ffmpeg on PATH)"""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype="<f4").astype(np.float64).reshape(-1, ch)


def lufs(x):
    """BS.1770-4 integrated loudness of (n, ch) at 48 kHz: K-weighting, 400 ms blocks at 75 % overlap, the -70 abs and
    -10 rel gates, channels summed with weight 1 (a sound shorter than a block is padded to one)"""
    from scipy.signal import lfilter
    if x.ndim == 1:
        x = x[:, None]
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


def mono(x):
    return x.mean(axis=1) if x.ndim == 2 else x


def envelope(x, frame=0.010):
    m = mono(x)
    n = max(1, int(frame * SR))
    k = len(m) // n
    if k == 0:
        return np.array([np.sqrt(np.mean(m ** 2) + 1e-20)])
    return np.sqrt(np.mean(m[:k * n].reshape(k, n) ** 2, axis=1) + 1e-20)


def db(v):
    return 20 * np.log10(np.maximum(v, 1e-12))


def trim_head(x, head_db=-40.0):
    """start ON the sound: drop what comes before the first 1 ms frame within head_db of the peak frame"""
    e = envelope(x, 0.001)
    above = np.where(db(e / (e.max() + 1e-20)) > head_db)[0]
    if above.size == 0:
        return x
    return x[above[0] * int(0.001 * SR):]


def trim_tail(x, tail_db=-60.0, post=0.03):
    e = envelope(x, 0.005)
    above = np.where(db(e / (e.max() + 1e-20)) > tail_db)[0]
    if above.size == 0:
        return x
    end = min(len(x), (above[-1] + 1) * int(0.005 * SR) + int(post * SR))
    return x[:end]


def dc_block(x):
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    return np.fft.irfft(np.fft.rfft(x, axis=0) * (f >= 25)[:, None], len(x), axis=0)


def fit(cue, x):
    """the take -> the shipped shape (unlevelled): starts on the sound with a 3 ms fade, exact length (near) or its
    own length inside span (the tier sting), the cue's fade at the end, DC-blocked"""
    spec = CUES[cue]
    x = trim_head(x)
    x = dc_block(x)
    if spec["secs"] is not None:
        n = int(round(spec["secs"] * SR))
        if len(x) >= n:
            x = x[:n].copy()
        else:
            x = np.concatenate([x, np.zeros((n - len(x), x.shape[1]))])
    else:
        x = trim_tail(x)
        lo, hi = spec["span"]
        n = min(len(x), int(round(hi * SR)))
        n = max(n, int(round(lo * SR)))
        x = x[:n].copy() if len(x) >= n else np.concatenate([x, np.zeros((n - len(x), x.shape[1]))])
    a = int(0.003 * SR)
    x[:a] *= np.linspace(0.0, 1.0, a)[:, None]
    b = min(len(x) - a, int(spec["fade_out"] * SR))
    if spec["fit"] == "cut":
        x[-b:] *= np.linspace(1.0, 0.0, b)[:, None]
    else:
        x[-b:] *= (np.linspace(1.0, 0.0, b) ** 2)[:, None]
    x[-1] = 0.0
    return x


def limiter_gain(x, ceil, look=0.003, rel=0.08):
    """a look-ahead peak limiter's gain curve: never above ceil at any sample, smooth attack (the min over +-look,
    averaged over +-look: every averaged value covers the sample, so it stays under the need) and a one-pole release"""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    pk = np.max(np.abs(x), axis=1) + 1e-12
    need = np.minimum(1.0, ceil / pk)
    w = max(1, int(look * SR))
    g = minimum_filter1d(need, size=2 * w + 1, mode="nearest")
    g = uniform_filter1d(g, size=2 * w + 1, mode="nearest")
    g = np.minimum(g, need)
    a = 1.0 - np.exp(-1.0 / (rel * SR))
    out = g.tolist()
    for i in range(1, len(out)):
        prev = out[i - 1]
        if out[i] > prev:
            out[i] = prev + (out[i] - prev) * a
    return np.array(out)


def level(x, target, peak_db):
    """gain onto the loudness target under the limiter; iterate (the limiter takes some of the gain back)"""
    ceil = 10 ** (peak_db / 20)
    g_db = target - lufs(x)
    y = x
    for _ in range(8):
        z = x * 10 ** (g_db / 20)
        gr = limiter_gain(z, ceil)
        y = z * gr[:, None]
        err = target - lufs(y)
        if abs(err) < 0.03:
            break
        g_db += err
    y = np.clip(y, -ceil, ceil)
    return y, float(-db(gr.min()))


def encode(x):
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


def sha256(b):
    return hashlib.sha256(b).hexdigest()


# ---- measurement + the profile scores -------------------------------------------------------------------------
def features(x):
    m = mono(x)
    if len(m) < int(0.05 * SR) or np.max(np.abs(m)) < 1e-4:
        return None
    e = envelope(x)
    pk = e.max()
    dur = len(m) / SR
    t = np.arange(len(e)) * 0.010
    ip = int(np.argmax(e))
    onset = float(t[np.where(e >= 0.5 * pk)[0][0]])
    after = e[ip:]
    low = np.where(after <= 0.1 * pk)[0]
    decay = float(low[0] * 0.010) if low.size else float(dur - t[ip])
    tail_db = float(db(e[-max(1, 5):].mean() / pk))
    third = max(1, len(e) // 3)
    rise_db = float(db(e[-third:].mean() / (e[:third].mean() + 1e-12)))
    hot = (np.abs(m) >= 0.999).astype(np.int8)
    runs = np.convolve(hot, np.ones(4, dtype=np.int8), "valid") >= 4
    clip = float(np.mean(runs)) if runs.size else 0.0
    spec = np.abs(np.fft.rfft(m * np.hanning(len(m))))
    f = np.fft.rfftfreq(len(m), 1.0 / SR)
    tot = spec.sum() + 1e-12
    s = spec[(f > 60) & (f < 12000)] + 1e-12
    # the brightness trend: the spectral centroid of the last half vs the first half (a fall sinks, a riser climbs)
    def centroid(seg):
        if len(seg) < 512:
            return 0.0
        sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        ff = np.fft.rfftfreq(len(seg), 1.0 / SR)
        return float((sp * ff).sum() / (sp.sum() + 1e-12))
    h = len(m) // 2
    c1, c2 = centroid(m[:h]), centroid(m[h:])
    # the second swell (the tier sting): the loudest 10 ms after 0.45 s, relative to the peak
    late = e[int(0.45 / 0.010):]
    late_db = float(db(late.max() / pk)) if late.size else -60.0
    return dict(dur=dur, onset=onset, peak_at=float(t[ip] / max(dur, 1e-6)), decay=decay, tail_db=tail_db,
                rise_db=rise_db, clip=clip, low=float(spec[f < 180].sum() / tot), hi=float(spec[f > 4000].sum() / tot),
                flat=float(np.exp(np.mean(np.log(s))) / np.mean(s)), c_trend=float(np.log2((c2 + 1) / (c1 + 1))),
                late_db=late_db)


def closeness(v, lo, hi, soft):
    if lo <= v <= hi:
        return 1.0
    d = (lo - v) if v < lo else (v - hi)
    return max(0.0, 1.0 - d / soft)


def score(cue, ft, raw_dur):
    """how well a FITTED take fits its role (0..1): the shape, plus how much of the take survives the fit"""
    if ft is None:
        return -1.0, {"dead": True}
    p = CUES[cue]["profile"]
    s = {"clip": 1.0 - min(1.0, ft["clip"] * 50)}
    want = CUES[cue]["secs"] or CUES[cue]["ask"]
    s["length"] = closeness(raw_dur, 0.8 * want, 2.0 * want, 0.6 * want)    # the take has to fill the slot
    if p == "rising":
        s["rise"] = closeness(ft["rise_db"], 4.0, 40.0, 6.0)
        s["peak_at"] = closeness(ft["peak_at"], 0.45, 1.0, 0.3)
        s["held"] = closeness(ft["tail_db"], -16.0, 0.0, 12.0)          # still strong at the cut: held, not released
        s["climb"] = closeness(ft["c_trend"], 0.0, 3.0, 0.6)
    elif p == "fall":
        s["onset"] = closeness(ft["onset"], 0.0, 0.08, 0.15)
        s["peak_at"] = closeness(ft["peak_at"], 0.0, 0.4, 0.3)
        s["sink"] = closeness(ft["c_trend"], -3.0, -0.05, 0.5)
        s["tonal"] = closeness(ft["flat"], 0.0, 0.45, 0.3)
        s["ends"] = closeness(ft["tail_db"], -90.0, -24.0, 12.0)
    elif p == "burst":
        s["onset"] = closeness(ft["onset"], 0.0, 0.06, 0.12)
        s["bright"] = closeness(ft["hi"], 0.08, 1.0, 0.08)
        s["body"] = closeness(ft["low"], 0.03, 1.0, 0.05)
        s["ring"] = closeness(ft["decay"], 0.15, 1.0, 0.3)
        s["ends"] = closeness(ft["tail_db"], -90.0, -24.0, 12.0)
    elif p == "whoosh":
        s["onset"] = closeness(ft["onset"], 0.02, 0.3, 0.25)
        s["peak_at"] = closeness(ft["peak_at"], 0.1, 0.6, 0.3)
        s["ends"] = closeness(ft["tail_db"], -90.0, -24.0, 12.0)
        s["noise"] = closeness(ft["flat"], 0.15, 1.0, 0.15)
    elif p == "blaze":
        s["onset"] = closeness(ft["onset"], 0.0, 0.35, 0.3)
        s["peak_at"] = closeness(ft["peak_at"], 0.08, 0.6, 0.3)
        s["body"] = closeness(ft["low"], 0.06, 1.0, 0.08)
        s["ends"] = closeness(ft["tail_db"], -90.0, -24.0, 12.0)
    elif p == "fade":
        s["onset"] = closeness(ft["onset"], 0.0, 0.1, 0.15)
        s["peak_at"] = closeness(ft["peak_at"], 0.0, 0.35, 0.3)
        s["hiss"] = closeness(ft["hi"], 0.15, 1.0, 0.15)
        s["ends"] = closeness(ft["tail_db"], -90.0, -24.0, 12.0)
    elif p == "tier":
        s["onset"] = closeness(ft["onset"], 0.0, 0.08, 0.15)            # the lock-in hits at once
        s["swell"] = closeness(ft["late_db"], -6.0, 0.0, 6.0)            # a second big moment after the clunk
        s["sub"] = closeness(ft["low"], 0.12, 1.0, 0.1)                  # the drop is felt
        s["span"] = closeness(ft["dur"], 1.5, 2.5, 0.3)
        s["ends"] = closeness(ft["tail_db"], -90.0, -24.0, 12.0)
    total = sum(s.values()) / len(s)
    return float(total), s


# ---- ElevenLabs ------------------------------------------------------------------------------------------------
def load(path, default):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1)
        f.write("\n")


def request_take(prompt, secs):
    """one ElevenLabs sound generation -> (bytes, extension); the best format this account serves"""
    import eleven
    body = {"text": prompt, "duration_seconds": max(0.5, secs), "prompt_influence": PROMPT_INFLUENCE}
    last = None
    for fmt, ext in (("mp3_44100_192", ".mp3"), ("mp3_44100_128", ".mp3")):
        try:
            raw = eleven.call("POST", "/v1/sound-generation", body=body, query={"output_format": fmt})
        except RuntimeError as e:   # a format this tier does not serve: fall back
            last = e
            if "-> 4" in str(e):
                continue
            raise
        if isinstance(raw, (bytes, bytearray)):
            return bytes(raw), ext, fmt
        last = RuntimeError("unexpected response %r" % (raw,))
    raise last


def plan_of(cue, name):
    i = int(name.split("_")[1]) - 1
    plan = PLAN.get(cue, [])
    return plan[i] if i < len(plan) else dict(role="?", ask=CUES[cue]["ask"], prompt=CUES[cue]["prompt"])


def take_audio(cue, name, ch=None):
    """a kept take, decoded at SR, reversed if its plan says so (ch defaults to the cue's)"""
    p = os.path.join(TAKES_DIR, cue, name + ".mp3")
    x = decode(p, ch or CUES[cue]["ch"])
    return np.ascontiguousarray(x[::-1]) if plan_of(cue, name).get("reverse") else x


def take_entry(cue, path, name, fmt):
    plan = plan_of(cue, name)
    x = take_audio(cue, name)
    raw_dur = len(trim_tail(trim_head(x))) / SR
    ft = features(trim_tail(trim_head(x)))
    return dict(name=name, role=plan["role"], file=os.path.relpath(path, REPO).replace("\\", "/"), format=fmt,
                raw_dur=round(raw_dur, 3), features=ft, prompt=plan["prompt"], reverse=bool(plan.get("reverse")))


def generate(cues, takes):
    data = load(TAKES_JSON, {})
    for cue in cues:
        spec = CUES[cue]
        rows = data.get(cue, [])
        n = min(takes, MAX_TAKES - len(rows))
        if n <= 0:
            print("%-20s already has %d takes (the pack's cap is %d)" % (cue, len(rows), MAX_TAKES))
            continue
        d = os.path.join(TAKES_DIR, cue)
        os.makedirs(d, exist_ok=True)
        for i in range(len(rows), len(rows) + n):
            name = "take_%d" % (i + 1)
            plan = plan_of(cue, name)
            raw, ext, fmt = request_take(plan["prompt"], plan["ask"])
            path = os.path.join(d, name + ext)
            open(path, "wb").write(raw)
            r = take_entry(cue, path, name, fmt)
            rows.append(r)
            print("%-20s %s %-22s raw %.2fs %s" % (cue, name, r["role"], r["raw_dur"], fmt))
            data[cue] = rows
            save(TAKES_JSON, data)
    return data


def rescore(cues):
    data = load(TAKES_JSON, {})
    for cue in cues:
        for i, r in enumerate(data.get(cue, [])):
            p = os.path.join(REPO, r["file"])
            if os.path.exists(p):
                data[cue][i] = take_entry(cue, p, r["name"], r.get("format", "?"))
        rows = data.get(cue, [])
        print("%-20s %s" % (cue, "  ".join("%s %.3f" % (r["name"], r["score"]) for r in rows)))
    save(TAKES_JSON, data)


# ---- the pick ---------------------------------------------------------------------------------------------------
def chosen(cue, data, picks):
    rows = data.get(cue, [])
    if not rows:
        return None
    ov = picks.get(cue)
    if ov:
        for r in rows:
            if r["name"] == ov:
                return r
        sys.exit("%s: picks.json names %s, which is not a take" % (cue, ov))
    return max(rows, key=lambda r: r["score"])


def render(cue, row):
    spec = CUES[cue]
    x = fit(cue, decode(os.path.join(REPO, row["file"]), spec["ch"]))
    y, gr = level(x, spec["lufs"], spec["peak"])
    b = encode(y)
    return b, dict(file="%s/%s.wav" % (spec["dir"], cue), source=row["file"], take=row["name"], sha256=sha256(b),
                   channels=spec["ch"], frames=len(y), secs=round(len(y) / SR, 4), lufs=round(lufs(y), 2),
                   peak_db=round(float(db(np.max(np.abs(y)))), 2), limiter_gr_db=round(gr, 2))


def pick(cues, out_root):
    data = load(TAKES_JSON, {})
    picks = load(PICKS_JSON, {})
    man = load(MANIFEST, {})
    for cue in cues:
        row = chosen(cue, data, picks)
        if row is None:
            print("%-20s NO TAKE - generate first" % cue)
            continue
        b, info = render(cue, row)
        p = os.path.join(out_root, "sound_assets", "tod", info["file"].replace("/", os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not (os.path.exists(p) and open(p, "rb").read() == b):
            open(p, "wb").write(b)
        man[cue] = info
        print("%-20s %-10s %.3fs %d ch %6.2f LUFS peak %6.2f dB  limiter %4.1f dB  <- %s" % (
            cue, info["take"], info["secs"], info["channels"], info["lufs"], info["peak_db"], info["limiter_gr_db"], info["source"]))
    man = {c: man[c] for c in ORDER if c in man}
    save(MANIFEST, man)
    authored = {c: {"sha256": man[c]["sha256"], "frames": man[c]["frames"], "by": "tools/sfx/card_luck/make_sounds.py"}
                for c in NEAR if c in man}
    save(os.path.join(out_root, AUTHORED_REL.replace("/", os.sep)), authored)
    print("manifest %s + %s written" % (os.path.relpath(MANIFEST, REPO), os.path.join(out_root, AUTHORED_REL)))


# ---- review: a spectrogram sheet of every take + a listening desk -----------------------------------------------
def spectro_panel(x, label, sub, maxs, w=760, h=150, wh=44):
    from PIL import Image, ImageDraw
    m = mono(x)
    n, hop = 2048, 128
    pad = np.concatenate([np.zeros(n // 2), m, np.zeros(n)])
    frames = np.array([pad[i:i + n] * np.hanning(n) for i in range(0, max(1, len(m)), hop)])
    S = np.abs(np.fft.rfft(frames, axis=1)).T + 1e-9
    f = np.fft.rfftfreq(n, 1 / SR)
    rows = np.geomspace(40, 16000, h)
    D = 20 * np.log10(S[np.clip(np.searchsorted(f, rows), 0, len(f) - 1)] / S.max())
    D = np.clip((D + 80) / 80, 0, 1)[::-1]
    lut = np.array([[int(255 * min(1, 2.2 * v)), int(255 * max(0, min(1, 2 * v - 0.5))), int(255 * max(0, 3 * v - 2))]
                    for v in np.linspace(0, 1, 256)], dtype=np.uint8)
    cols = max(1, int(w * (len(m) / SR) / maxs))
    img = Image.fromarray(lut[(D * 255).astype(int)]).resize((cols, h))
    c = Image.new("RGB", (w + 300, h + wh + 4), (16, 16, 20))
    c.paste(img, (0, 0))
    d = ImageDraw.Draw(c)
    for k in range(int(maxs * 10) + 1):
        xx = int(w * k / 10 / maxs)
        d.line([(xx, h), (xx, h + (10 if k % 5 == 0 else 4))], fill=(150, 150, 150))
    seg = max(1, len(m) // cols)
    y0 = h + 4 + wh // 2
    for i in range(cols):
        a = np.max(np.abs(m[i * seg:(i + 1) * seg])) if (i + 1) * seg <= len(m) else 0.0
        d.line([(i, y0 - int(a * (wh // 2 - 1))), (i, y0 + int(a * (wh // 2 - 1)))], fill=(110, 190, 250))
    d.text((w + 8, 6), label, fill=(255, 255, 255))
    for j, line in enumerate(sub):
        d.text((w + 8, 24 + 14 * j), line, fill=(190, 190, 190))
    return c


def review():
    from PIL import Image, ImageDraw
    data = load(TAKES_JSON, {})
    man = load(MANIFEST, {})
    out_dir = os.path.join(WORK, "review")
    os.makedirs(out_dir, exist_ok=True)
    panels = []
    for cue in ORDER:
        first = len(panels)
        spec = CUES[cue]
        maxs = 2.6 if spec["dir"] == "sfx" else 1.5
        ref = os.path.join(REPO, "sound_assets", "tod", spec["dir"], cue + ".wav")
        refs = [ref] if os.path.exists(ref) else []
        if cue == "tod_tier_sting":
            refs = [os.path.join(REPO, "sound_assets/tod/sfx/tod_super_sting.wav")]
        for rp in refs:
            x = decode(rp, 1)
            panels.append(spectro_panel(x, cue + "  [SHIPPED NOW]", [os.path.relpath(rp, REPO).replace("\\", "/"),
                                        "%.3f s  %.1f LUFS" % (len(x) / SR, lufs(x))], maxs))
        for r in data.get(cue, []):
            y = fit(cue, decode(os.path.join(REPO, r["file"]), spec["ch"]))
            mark = " <- PICK" if man.get(cue, {}).get("take") == r["name"] else ""
            parts = " ".join("%s %.2f" % (k, v) for k, v in sorted(r["parts"].items()) if isinstance(v, float))
            panels.append(spectro_panel(y, "%s %s  %.3f%s" % (cue, r["name"], r["score"], mark),
                                        [parts[:46], parts[46:92], parts[92:138], "raw %.2fs" % r["raw_dur"]], maxs))
        mine = panels[first:]
        if mine:
            one = Image.new("RGB", (mine[0].width, sum(p.height + 3 for p in mine)), (0, 0, 0))
            yy = 0
            for p in mine:
                one.paste(p, (0, yy))
                yy += p.height + 3
            one.save(os.path.join(out_dir, cue + ".png"))
    if not panels:
        print("nothing to review")
        return
    W = panels[0].width
    sheet = Image.new("RGB", (W, sum(p.height + 3 for p in panels)), (0, 0, 0))
    y = 0
    for p in panels:
        sheet.paste(p, (0, y))
        y += p.height + 3
    sp = os.path.join(out_dir, "takes_spectrograms.png")
    sheet.save(sp)
    # the listening desk
    h = ["<!doctype html><meta charset=utf-8><title>PK17 card + luck stings</title>",
         "<style>body{font:14px system-ui;background:#111;color:#ddd;margin:24px}h2{color:#9ef;margin:26px 0 4px}"
         "td{padding:4px 10px;border-bottom:1px solid #333}.pick{color:#6f6;font-weight:bold}audio{height:28px}</style>",
         "<h1>PK17: the tier sting + the near-miss / hot-streak cues</h1>",
         "<p>Override a pick in <code>tmp/asset_prod/PK17-card-luck-stings/takes/picks.json</code>, then <code>pick</code>.</p>"]
    stage = os.path.join(WORK, "stage", "sound_assets", "tod")
    for cue in ORDER:
        spec = CUES[cue]
        h.append("<h2>%s</h2><p><i>%s</i></p><table>" % (cue, spec["prompt"]))
        now = os.path.join(REPO, "sound_assets", "tod", spec["dir"], cue + ".wav")
        if os.path.exists(now):
            h.append("<tr><td>REPO NOW</td><td></td><td><audio controls src='%s'></audio></td></tr>" % os.path.relpath(now, out_dir).replace("\\", "/"))
        st = os.path.join(stage, spec["dir"], cue + ".wav")
        if os.path.exists(st):
            h.append("<tr><td class=pick>STAGED</td><td>%s</td><td><audio controls src='%s'></audio></td></tr>" % (
                man.get(cue, {}).get("take", ""), os.path.relpath(st, out_dir).replace("\\", "/")))
        for r in data.get(cue, []):
            h.append("<tr><td>%s</td><td>%.3f</td><td><audio controls src='%s'></audio></td></tr>" % (
                r["name"], r["score"], os.path.relpath(os.path.join(REPO, r["file"]), out_dir).replace("\\", "/")))
        h.append("</table>")
    open(os.path.join(out_dir, "desk.html"), "w", encoding="utf-8").write("\n".join(h))
    print("review:", sp, "+ desk.html")


# ---- the gate ---------------------------------------------------------------------------------------------------
TIER_ROW = {"Name": "tod_tier_sting", "FileSpec": "tod\\sfx\\tod_tier_sting.wav", "Template": "UIN_MOD", "VolMin": "95",
            "VolMax": "95", "PanType": "2d", "Looping": "NONLOOPING"}


def check(root):
    bad = []
    man = load(MANIFEST, None)
    if not man:
        print("CARD LUCK SOUNDS STALE: no manifest - " + FIX)
        sys.exit(1)
    for cue in ORDER:
        info = man.get(cue)
        if not info:
            bad.append("%s not shipped" % cue)
            continue
        p = os.path.join(root, "sound_assets", "tod", info["file"].replace("/", os.sep))
        if not os.path.exists(p):
            bad.append("missing " + info["file"])
            continue
        b = open(p, "rb").read()
        if sha256(b) != info["sha256"]:
            bad.append("changed " + info["file"])
        try:
            with wave.open(io.BytesIO(b)) as w:
                spec = CUES[cue]
                if (w.getnchannels(), w.getframerate(), w.getsampwidth()) != (spec["ch"], SR, 2):
                    bad.append("%s is not %d ch 48 kHz 16-bit" % (info["file"], spec["ch"]))
                if spec["secs"] is not None and w.getnframes() != int(round(spec["secs"] * SR)):
                    bad.append("%s is %d frames, the timing wants %d" % (info["file"], w.getnframes(), int(round(spec["secs"] * SR))))
                if spec["secs"] is None and not (spec["span"][0] <= w.getnframes() / SR <= spec["span"][1]):
                    bad.append("%s is %.2f s (want %.1f - %.1f)" % (info["file"], w.getnframes() / SR, spec["span"][0], spec["span"][1]))
        except wave.Error as e:
            bad.append("%s unreadable: %s" % (info["file"], e))
    authored = load(os.path.join(root, AUTHORED_REL.replace("/", os.sep)), {})
    for cue in NEAR:
        if cue in man and authored.get(cue, {}).get("sha256") != man[cue]["sha256"]:
            bad.append("%s does not name %s's sha" % (AUTHORED_REL, cue))
    ui = os.path.join(root, UI_CSV_REL.replace("/", os.sep))
    try:
        rows = list(csv.reader(open(ui, encoding="utf-8-sig").read().splitlines()))
        col = {k: i for i, k in enumerate(rows[0])}
        mine = [r for r in rows[1:] if r and r[0] == "tod_tier_sting"]
        if len(mine) != 1:
            bad.append("%s has %d tod_tier_sting rows (want 1)" % (UI_CSV_REL, len(mine)))
        else:
            r = mine[0]
            for k, v in TIER_ROW.items():
                if r[col[k]] != v:
                    bad.append("tod_tier_sting row %s=%r (want %r)" % (k, r[col[k]], v))
            for k in ("ContextType", "ContextValue"):
                if k in col and r[col[k]]:
                    bad.append("tod_tier_sting row carries a %s (a context makes a sound silent here)" % k)
    except (OSError, IndexError, KeyError) as e:
        bad.append("%s unreadable: %s" % (UI_CSV_REL, e))
    try:
        szc = json.loads(open(os.path.join(root, SZC_REL.replace("/", os.sep)), encoding="utf-8-sig").read())
        if not any(isinstance(s, dict) and str(s.get("Filename", "")).lower() == "tod_ui.csv" for s in szc.get("Sources", [])):
            bad.append("tod_ui.csv not loaded by the sound zone config")
    except (OSError, ValueError) as e:
        bad.append("szc unreadable: %s" % e)
    played = False
    for dp, _, fs in os.walk(os.path.join(root, "scripts")):
        for fn in fs:
            if fn.endswith(".gsc") and re.search(r'PlayLocalSound\(\s*"tod_tier_sting"\s*\)', open(os.path.join(dp, fn), encoding="utf-8", errors="replace").read()):
                played = True
    if not played:
        bad.append('no script plays "tod_tier_sting" (the tier_up feedback line in _tod_upgrades.gsc)')
    if bad:
        print("CARD LUCK SOUNDS STALE: " + "; ".join(bad[:8]) + " - " + FIX)
        sys.exit(1)
    print("CARD LUCK SOUNDS OK: %d cues (1 tier sting + %d near-miss / hot-streak), tod_tier_sting row + wiring" % (len(man), len(NEAR)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", default="")
    ap.add_argument("--cue", action="append")
    ap.add_argument("--takes", type=int, default=MAX_TAKES)
    ap.add_argument("--out-root", default=REPO)
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cues = a.cue or ORDER
    for c in cues:
        if c not in CUES:
            sys.exit("unknown cue " + c)
    if a.check or a.cmd == "check":
        check(os.path.abspath(a.root))
    elif a.cmd == "generate":
        generate(cues, a.takes)
    elif a.cmd == "rescore":
        rescore(cues)
    elif a.cmd == "pick":
        pick(cues, os.path.abspath(a.out_root))
    elif a.cmd == "review":
        review()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
