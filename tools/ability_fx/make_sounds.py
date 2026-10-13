"""THE ABILITY SOUNDS (docs/206, 2026-10-03): one owner for every cue _tod_ability_fx.gsc plays.

The first pass (docs/203) borrowed every cue from another feature (a Fury whoosh for the dash, the sky
fleet's jet for the Fusion launch, the hot streak's heat-out for Demon Slayer's end). This tool replaces
them with sounds MADE FOR THE MOVE, two sources, one pipeline:

  * ELEVENLABS sound generation (the user: "you have eleven labs API ... maybe you can get it to do
    that better than I can"): every cue is generated TAKES times from a written prompt, every take is
    measured (onset, decay, peak position, low-end share, tail, clipping, tonality) and scored against
    the cue's PROFILE (an impact must hit at once and die fast; a whoosh must build and pass; a sting
    must swell and ring; a fade must start loud and die slowly), and the best take ships. The others
    stay on the listening desk (tmp/ability_sfx/desk.html) so the user can overrule a pick.
  * UPPBEAT (the user: "upbeat has the highest quality sounds ... tell me what to search"): a
    downloaded clip dropped as tmp/ability_sfx/drop/<cue>.wav|.mp3|.flac|.ogg (a variant: <cue>_2.wav)
    REPLACES the generated take for that cue on the next `pick`; same trim / fade / loudness pipeline.
    The search terms per cue are printed by `--brief` (and in docs/206).
  * SYNTHESISED where a machine is better than a model: the C4 arming beep (a pure tone loop) and the kit's
    refused-press "nope" (PK18: an exact 0.25 s two-pulse UI cue that must never read as the PaP buzzer).

Every shipped file is mono 48 kHz 16-bit, trimmed to its sound, DC-blocked, faded at both ends, levelled
to the cue's loudness target (BS.1770 integrated) under a soft limiter at -1 dBFS, and recorded with its
sha256 in sounds_manifest.json. The alias table sound/aliases/tod_ability.csv is REGENERATED whole (the
header verbatim, the three row shapes copied from the first pass's own rows: a 2D player row, a 3D
world row, a 3D LOOPING row). The build gate (`--check`) needs no API and no DSP: every manifest file
present with its sha, wav headers right, the csv exactly as this tool writes it, the csv in the .szc.

  python tools/ability_fx/make_sounds.py generate [--cue NAME] [--takes N]   call ElevenLabs, score, write takes.json
  python tools/ability_fx/make_sounds.py rescore  [--cue NAME]               re-measure the kept takes after a profile change
  python tools/ability_fx/make_sounds.py pick     [--cue NAME]               ship the best (or dropped) take per cue
  python tools/ability_fx/make_sounds.py desk                                write the listening desk (tmp/ability_sfx/desk.html)
  python tools/ability_fx/make_sounds.py brief                               print the Uppbeat search list
  python tools/ability_fx/make_sounds.py --check                             the build gate

The key is ELEVENLABS_API_KEY (process or Windows user environment, via tools/black_market_vo/eleven.py:
never printed, never stored). Every generated take is kept under tmp/ability_sfx/takes/ (not in git).
"""
import argparse, csv, hashlib, io, json, math, os, re, struct, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "tools", "black_market_vo"))

SR = 48000
WAV_DIR = os.path.join(REPO, "sound_assets", "tod", "abfx")
WAV_REL = "tod\\abfx\\"
CSV_PATH = os.path.join(REPO, "sound", "aliases", "tod_ability.csv")
SZC = os.path.join(REPO, "sound", "zoneconfig", "zm_tod2_cybercity.szc")
MANIFEST = os.path.join(HERE, "sounds_manifest.json")
WORK = os.path.join(REPO, "tmp", "ability_sfx")
TAKES_DIR = os.path.join(WORK, "takes")
DROP_DIR = os.path.join(WORK, "drop")
TAKES_JSON = os.path.join(WORK, "takes.json")
PICKS_JSON = os.path.join(WORK, "picks.json")          # the user's overrides: {cue: "take_2" | "drop:<file>"}
DESK = os.path.join(WORK, "desk.html")
FIX = "run: python tools/ability_fx/make_sounds.py pick"
PEAK_DB = -1.0
PROMPT_INFLUENCE = 0.6
DEFAULT_TAKES = 3

# ---- the cues -------------------------------------------------------------------------------------
# name: the wav / alias stem (tod_abfx_<name>); rows: which alias rows ship ("plr" = 2D to the caster,
# "3d" = positional for the teammates' ears, "loop" = a 3D looping row); profile: the scoring shape;
# secs: the ElevenLabs duration asked for; lufs: the loudness target; vol: (2D VolMin/Max, 3D VolMin/Max);
# dist: the 3D row's (DistMin, DistMax); variants: how many shipped files (the alias rows randomise);
# prompt: the ElevenLabs text; uppbeat: what to search there.
CUES = {
    "dash": dict(rows=("plr", "3d"), profile="whoosh", secs=0.7, lufs=-16.0, vol=(84, 80), dist=(300, 1800), variants=3,
                 prompt="fast sci-fi sword dash whoosh, a sharp cutting air swipe with a faint electric sizzle, short and dry, no music",
                 uppbeat="sword whoosh swing fast; energy blade swipe"),
    "impact": dict(rows=("plr", "3d"), profile="impact", secs=0.9, lufs=-13.0, vol=(88, 84), dist=(300, 2400), variants=1,
                   prompt="heavy cybernetic shockwave slam on a metal floor, a deep sub bass thump with a short metallic ring and scattering debris, no music",
                   uppbeat="shockwave impact bass; heavy slam metal thud"),
    "pulse": dict(rows=("plr", "3d"), profile="swell", secs=1.5, lufs=-15.0, vol=(86, 82), dist=(300, 2400), variants=1,
                  prompt="a ghostly soul wave bursting outward, a deep ethereal whoosh with whispering spectral voices and a cold wind tail, dark, no music",
                  uppbeat="ghost whoosh ethereal; dark magic burst spectral"),
    "launch": dict(rows=("plr", "3d"), profile="burst", secs=0.9, lufs=-14.0, vol=(86, 82), dist=(300, 2000), variants=1,
                   prompt="an explosive rocket jump launch, a fiery blast burst with a quick rising whoosh of flame, close, no music",
                   uppbeat="rocket launch blast whoosh; jetpack boost"),
    "land": dict(rows=("plr", "3d"), profile="impact", secs=0.8, lufs=-14.0, vol=(86, 82), dist=(300, 1800), variants=1,
                 prompt="a heavy armored soldier landing hard on a metal floor, a deep thud with dust and a short metal rattle, no music",
                 uppbeat="heavy landing thud metal; body land impact"),
    "heal": dict(rows=("plr",), profile="swell", secs=0.9, lufs=-17.0, vol=(84, 80), dist=(0, 0), variants=1,
                 prompt="a warm healing energy pulse, a soft rising glowing chime with crackling embers, brief, no music",
                 uppbeat="healing chime magic; health restore glow"),
    "demon_on": dict(rows=("plr", "3d"), profile="burst", secs=1.2, lufs=-14.0, vol=(88, 84), dist=(300, 2400), variants=1,
                     prompt="a demonic power surge, a deep guttural roar burst with dark energy igniting and a sub bass hit, no music",
                     uppbeat="demon roar power up; dark energy surge"),
    "demon_off": dict(rows=("plr",), profile="fade", secs=1.0, lufs=-18.0, vol=(82, 78), dist=(0, 0), variants=1,
                      prompt="dark demonic energy dissipating, a low fading exhale with dying embers, no music",
                      uppbeat="power down dissipate dark; energy fade out"),
    "dive": dict(rows=("plr", "3d"), profile="rising", shape="reverse", secs=1.1, lufs=-16.0, vol=(92, 88), dist=(300, 2000), variants=1,
                 prompt="starts from complete silence: a body plummeting from a great height, the wind rush builds from nothing and a thin whistle climbs higher and louder for one full second, then stops dead at the very end with no impact and no echo, dry cinematic sound effect, no music, no voice",
                 uppbeat="falling whoosh rising; dive wind rush"),
    "charged": dict(rows=("plr",), profile="sting", secs=1.0, lufs=-17.0, vol=(82, 78), dist=(0, 0), variants=1,
                    prompt="a clean electric tone rising in pitch over half a second then locking into a bright bell-like ping, a sci-fi weapon charged and ready, tonal and musical, no noise, no music",
                    uppbeat="energy charge complete ping; weapon ready sci-fi"),
    "cloak_on": dict(rows=("plr", "3d"), profile="sweep", secs=1.0, lufs=-16.0, vol=(84, 80), dist=(300, 1800), variants=1,
                     prompt="a sci-fi stealth cloak activating, a phasing shimmer sweep dissolving into near silence, no music",
                     uppbeat="cloak activate shimmer; stealth phase sci-fi"),
    "cloak_off": dict(rows=("plr", "3d"), profile="sweep", secs=0.9, lufs=-16.0, vol=(84, 80), dist=(300, 1800), variants=1,
                      prompt="a stealth cloak deactivating, a reverse shimmer sweep snapping back into reality with a soft thump, no music",
                      uppbeat="decloak shimmer reverse; teleport in sci-fi"),
    "shield_break": dict(rows=("plr", "3d"), profile="shatter", secs=1.1, lufs=-13.0, vol=(90, 86), dist=(300, 2400), variants=1,
                         prompt="a riot shield shattering, one hard low crack and thump then glass shards scattering across a metal floor, no music",
                         uppbeat="shield shatter glass break; armor crack"),
    "shield_back": dict(rows=("plr",), profile="swell", secs=1.1, lufs=-16.0, vol=(84, 80), dist=(0, 0), variants=1,
                        prompt="a futuristic energy shield rematerializing, a rising hum swelling into a solid metallic clunk and lock, no music",
                        uppbeat="shield recharge power up; energy shield activate"),
    "card_1": dict(rows=("3d",), profile="sting", secs=0.9, lufs=-17.0, vol=(80, 78), dist=(200, 1600), variants=1,
                   prompt="a short soft synth chime confirming a selection, modest and clean, no music",
                   uppbeat="ui confirm chime soft; select pickup"),
    "card_2": dict(rows=("3d",), profile="sting", secs=1.0, lufs=-16.5, vol=(82, 80), dist=(200, 1800), variants=1,
                   prompt="a bright two-note rising synth sting with a glassy shimmer, a rare reward, no music",
                   uppbeat="rare item sting; level up chime short"),
    "card_3": dict(rows=("3d",), profile="sting", secs=1.1, lufs=-16.0, vol=(84, 82), dist=(200, 2000), variants=1,
                   prompt="a bright powerful three-note rising synth stinger with a sparkling shimmer tail, an epic reward, mid and high frequencies, no sub bass, no music",
                   uppbeat="epic reward sting; power up fanfare short"),
    "card_4": dict(rows=("3d",), profile="sting", secs=1.4, lufs=-15.0, vol=(88, 86), dist=(200, 2400), variants=1,
                   prompt="a legendary reward stinger, a golden choir shimmer rising with a bright bell strike and a sub bass hit, grand but short, no music",
                   uppbeat="legendary reward fanfare; jackpot sting choir"),
    "pierce": dict(rows=("3d",), profile="impact", secs=0.5, lufs=-15.0, vol=(80, 80), dist=(200, 1500), variants=1,
                   prompt="an arrow punching through flesh with a wet crunch and a sharp whip, short, no music",
                   uppbeat="arrow flesh impact; stab wet crunch short"),
    "draw": dict(rows=("plr",), profile="tick", secs=0.6, lufs=-19.0, vol=(80, 76), dist=(0, 0), variants=1,
                 prompt="a bowstring pulled to full tension, a taut creak ending in a soft solid click, no music",
                 uppbeat="bow string tension creak; bow draw click"),
    # synthesised: a two-pip arming beep, 1.0 s loop (LOOPING 3D alias on the stuck charge)
    "c4_loop": dict(rows=("loop",), profile="synth", secs=1.0, lufs=-20.0, vol=(0, 72), dist=(80, 700), variants=1,
                    prompt=None, uppbeat="(none: synthesised)"),
    # ---- THE KIT CUES (PK18, 2026-10-04): READY = a charge or cooldown came back, REFUSED = a press the kit
    # cannot honour. 2D to the player only (tod_ability_fx::kit_ready / kit_deny). Before these, Bash, the Cloak,
    # the Soul Pulse and the Breacher's round refill came back silently and every refused press was silent.
    "pulse_charged": dict(rows=("plr",), profile="sting", secs=0.9, lufs=-17.0, vol=(82, 78), dist=(0, 0), variants=1,
                          prompt="a dark soul power fully charged: a cold ghostly breath swells into one deep ethereal glass bell tone with a soft shimmering spectral tail, eerie, tonal and clean, no voice, no music",
                          uppbeat="ghost chime ethereal; dark magic ready sting"),
    "bash_ready": dict(rows=("plr",), profile="ping", secs=0.5, lufs=-17.0, vol=(82, 78), dist=(0, 0), variants=1,
                       prompt="a short bright sword blade ring, a single clean steel ping as a blade is readied, a crisp metallic shimmer that fades fast, close and dry, no music",
                       uppbeat="sword ring ping short; blade shing metal"),
    "cloak_ready": dict(rows=("plr",), profile="sweep", secs=0.6, lufs=-17.5, vol=(82, 78), dist=(0, 0), variants=1,
                        prompt="a soft airy breath-like shimmer, a quick wisp of wind with a faint glassy sparkle that swells and vanishes, a subtle stealth magic ready cue, quiet and delicate, no voice, no music",
                        uppbeat="magic shimmer airy short; stealth ready whoosh soft"),
    "refill": dict(rows=("plr",), profile="rack", secs=0.6, lufs=-17.0, vol=(82, 78), dist=(0, 0), variants=1,
                   prompt="two quick heavy mechanical clacks, explosive charges slotted and locked into a metal tactical rig, a satisfying rack and latch, dry close foley, no music",
                   uppbeat="gear rack clack metal; magazine slot latch"),
    # synthesised: a short muted two-pulse "nope" (a falling fourth on a low filtered square), never the PaP buzzer
    # (the stock zmb_no_purchase is a 0.6 s continuous 660 Hz buzz: this is 0.25 s, two pulses, 311 -> 233 Hz - synth_deny
    # makes its own length; secs is the brief's ceiling). lufs -19 here = about -17 heard: lufs() pads a sound shorter
    # than its 400 ms block with silence (~ -1.7 dB at 0.25 s)
    "deny": dict(rows=("plr",), profile="synth", secs=0.27, lufs=-19.0, vol=(80, 76), dist=(0, 0), variants=1,
                 prompt=None, uppbeat="(none: synthesised)"),
}
# the ORDER the csv lists them (stable; the gate compares the csv text)
ORDER = list(CUES.keys())


# ---- audio helpers -----------------------------------------------------------------------------------
def ffmpeg_decode(path):
    """any audio file -> mono float32 at SR (ffmpeg on PATH)"""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype="<f4").astype(np.float64)


def lufs(x):
    """BS.1770-4 integrated loudness, mono 48 kHz (K-weighting, 400 ms blocks, 75 % overlap, -70 abs / -10 rel gates)"""
    from scipy.signal import lfilter
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], x)
    y = lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    if len(y) < blk:
        y = np.concatenate([y, np.zeros(blk - len(y))])
    ms = np.array([np.mean(y[i:i + blk] ** 2) for i in range(0, len(y) - blk + 1, hop)])
    l = -0.691 + 10 * np.log10(ms + 1e-20)
    ms = ms[l > -70]
    if ms.size == 0:
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(ms)) - 10
    ms = ms[(-0.691 + 10 * np.log10(ms)) > rel]
    if ms.size == 0:
        return -70.0
    return float(-0.691 + 10 * np.log10(np.mean(ms)))


def envelope(x, frame=0.010):
    n = max(1, int(frame * SR))
    k = len(x) // n
    if k == 0:
        return np.array([np.sqrt(np.mean(x ** 2) + 1e-20)])
    return np.sqrt(np.mean(x[:k * n].reshape(k, n) ** 2, axis=1) + 1e-20)


def db(v):
    return 20 * np.log10(np.maximum(v, 1e-9))


def trim(x, head_db=-50.0, tail_db=-55.0, pre=0.005, post=0.06):
    """cut the silence a model pads with: keep `pre` before the first sound and `post` after the last"""
    e = envelope(x, 0.005)
    peak = e.max()
    if peak <= 1e-6:
        return x
    above = np.where(db(e / peak) > head_db)[0]
    if above.size == 0:
        return x
    n5 = int(0.005 * SR)
    start = max(0, above[0] * n5 - int(pre * SR))
    tail = np.where(db(e / peak) > tail_db)[0]
    end = min(len(x), (tail[-1] + 1) * n5 + int(post * SR))
    return x[start:end]


def dc_block(x):
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    return np.fft.irfft(np.fft.rfft(x) * (f >= 25), len(x))


def fades(x, fin, fout):
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a > 0 and a < len(x):
        x[:a] *= np.linspace(0, 1, a)
    if b > 0 and b < len(x):
        x[-b:] *= np.linspace(1, 0, b) ** 2
    return x


def level_to(x, target_lufs):
    """gain onto the loudness target, then a soft limiter so no sample passes PEAK_DB (a transient cue
    comes in hot: the tanh knee trades a little of its crest for the target, never the ceiling)"""
    cur = lufs(x)
    g = 10 ** ((target_lufs - cur) / 20)
    y = x * g
    ceil = 10 ** (PEAK_DB / 20)
    pk = np.max(np.abs(y)) + 1e-12
    if pk > ceil:
        d = pk / ceil
        y = np.tanh(y * d / pk) / np.tanh(d) * ceil   # the identity below the knee, the ceiling at the peak
    return y


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


# ---- the measurements + the profile scores ------------------------------------------------------------
def shape(cue, x):
    """per-cue shaping before scoring AND rendering (docs/206): "reverse" turns an impact-first take into a
    rise that stops dead (the dive: the model puts the loudest moment first whatever the prompt says)"""
    if CUES[cue].get("shape") == "reverse":
        return np.ascontiguousarray(x[::-1])
    return x


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
    low = np.where(after <= 0.1 * pk)[0]
    decay = float(low[0] * 0.010) if low.size else float(dur - t[ip])
    tail_db = float(db(e[-max(1, int(0.05 / 0.010)):].mean() / pk))
    hot = (np.abs(x) >= 0.999).astype(np.int8)
    runs = np.convolve(hot, np.ones(4, dtype=np.int8), "valid") >= 4   # 4+ full-scale samples in a row = a flat top
    clip = float(np.mean(runs)) if runs.size else 0.0
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    tot = spec.sum() + 1e-12
    low_share = float(spec[f < 180].sum() / tot)
    hi_share = float(spec[f > 4000].sum() / tot)
    s = spec[(f > 60) & (f < 12000)] + 1e-12
    flatness = float(np.exp(np.mean(np.log(s))) / np.mean(s))   # 1 = noise, -> 0 = tonal
    smooth = float(np.mean(np.abs(np.diff(e, 2))) / (pk + 1e-12))
    return dict(dur=dur, onset=onset, peak_at=float(t[ip] / max(dur, 1e-6)), decay=decay, tail_db=tail_db,
                clip=clip, low=low_share, hi=hi_share, flat=flatness, smooth=smooth, peak=float(pk))


def closeness(v, lo, hi, soft):
    """1 inside [lo, hi], falling to 0 `soft` outside it"""
    if lo <= v <= hi:
        return 1.0
    d = (lo - v) if v < lo else (v - hi)
    return max(0.0, 1.0 - d / soft)


def score(cue, ft):
    if ft is None:
        return -1.0, {"dead": True}
    p = CUES[cue]["profile"]
    want = CUES[cue]["secs"]
    s = {}
    s["length"] = closeness(ft["dur"], 0.55 * want, 1.3 * want, 0.8 * want)
    s["tail"] = closeness(ft["tail_db"], -90, -28, 14)            # ends on silence, never cut off
    s["clip"] = 1.0 - min(1.0, ft["clip"] * 50)                   # 2 % flat-topped samples = zero (a loud master is not clipping)
    if p == "impact":
        s["onset"] = closeness(ft["onset"], 0.0, 0.06, 0.15)
        s["decay"] = closeness(ft["decay"], 0.05, 0.7, 0.6)
        s["low"] = closeness(ft["low"], 0.12, 1.0, 0.12)
        s["peak_at"] = closeness(ft["peak_at"], 0.0, 0.25, 0.3)
    elif p == "burst":
        s["onset"] = closeness(ft["onset"], 0.0, 0.14, 0.25)
        s["decay"] = closeness(ft["decay"], 0.1, 1.0, 0.7)
        s["low"] = closeness(ft["low"], 0.08, 1.0, 0.1)
    elif p == "whoosh":
        s["onset"] = closeness(ft["onset"], 0.03, 0.4, 0.3)
        s["peak_at"] = closeness(ft["peak_at"], 0.15, 0.7, 0.3)
        s["smooth"] = closeness(ft["smooth"], 0.0, 0.07, 0.1)
        s["low"] = closeness(ft["low"], 0.0, 0.35, 0.3)
    elif p == "rising":
        s["onset"] = closeness(ft["onset"], 0.15, 0.9, 0.4)
        s["peak_at"] = closeness(ft["peak_at"], 0.5, 1.0, 0.3)
        s["tail"] = closeness(ft["tail_db"], -40, 0, 14)   # a rise STOPS DEAD at the floor: a loud last frame is the point, not a cut
        s["smooth"] = closeness(ft["smooth"], 0.0, 0.08, 0.12)
    elif p == "shatter":
        s["onset"] = closeness(ft["onset"], 0.0, 0.08, 0.15)
        s["decay"] = closeness(ft["decay"], 0.05, 0.9, 0.6)
        s["hi"] = closeness(ft["hi"], 0.15, 1.0, 0.15)
        s["peak_at"] = closeness(ft["peak_at"], 0.0, 0.3, 0.3)
    elif p == "swell":
        s["peak_at"] = closeness(ft["peak_at"], 0.2, 0.9, 0.3)
        s["decay"] = closeness(ft["decay"], 0.15, 2.0, 0.5)
        s["tonal"] = closeness(ft["flat"], 0.0, 0.5, 0.3)
    elif p == "sting":
        s["onset"] = closeness(ft["onset"], 0.0, 0.5, 0.4)
        s["decay"] = closeness(ft["decay"], 0.2, 1.6, 0.6)
        s["tonal"] = closeness(ft["flat"], 0.0, 0.5, 0.3)
        s["bright"] = closeness(ft["low"], 0.0, 0.55, 0.3)          # a sting is heard, not felt: no sub-only pulses
    elif p == "sweep":
        s["smooth"] = closeness(ft["smooth"], 0.0, 0.03, 0.05)
        s["decay"] = closeness(ft["decay"], 0.1, 1.2, 0.6)
    elif p == "fade":
        s["onset"] = closeness(ft["onset"], 0.0, 0.12, 0.2)
        s["decay"] = closeness(ft["decay"], 0.35, 2.0, 0.4)
        s["peak_at"] = closeness(ft["peak_at"], 0.0, 0.3, 0.3)
    elif p == "tick":
        s["onset"] = closeness(ft["onset"], 0.0, 0.5, 0.4)
        s["decay"] = closeness(ft["decay"], 0.02, 0.4, 0.4)
        s["hi"] = closeness(ft["hi"], 0.08, 1.0, 0.1)
    elif p == "ping":     # PK18: a short struck ring (the Bash charge back): hits at once, rings briefly, bright, never a thud
        s["onset"] = closeness(ft["onset"], 0.0, 0.06, 0.12)
        s["decay"] = closeness(ft["decay"], 0.06, 0.45, 0.3)
        s["hi"] = closeness(ft["hi"], 0.12, 1.0, 0.15)
        s["low"] = closeness(ft["low"], 0.0, 0.3, 0.25)
    elif p == "rack":     # PK18: mechanical foley (the Breacher's refill): quick transients, short, dry, mid / high
        s["onset"] = closeness(ft["onset"], 0.0, 0.08, 0.15)
        s["decay"] = closeness(ft["decay"], 0.02, 0.3, 0.3)
        s["hi"] = closeness(ft["hi"], 0.08, 1.0, 0.12)
        s["low"] = closeness(ft["low"], 0.0, 0.45, 0.3)
    total = sum(s.values()) / len(s)
    return float(total), s


# ---- ElevenLabs -----------------------------------------------------------------------------------
def generate(cues, takes):
    import eleven
    os.makedirs(TAKES_DIR, exist_ok=True)
    data = json.load(open(TAKES_JSON)) if os.path.exists(TAKES_JSON) else {}
    for cue in cues:
        spec = CUES[cue]
        if spec["prompt"] is None:
            continue
        d = os.path.join(TAKES_DIR, cue)
        os.makedirs(d, exist_ok=True)
        rows = data.get(cue, [])
        have = len(rows)
        for i in range(have, have + takes):
            name = "take_%d" % (i + 1)
            mp3 = os.path.join(d, name + ".mp3")
            raw = eleven.call("POST", "/v1/sound-generation",
                              body={"text": spec["prompt"], "duration_seconds": spec["secs"], "prompt_influence": PROMPT_INFLUENCE})
            if not isinstance(raw, (bytes, bytearray)):
                sys.exit("%s: unexpected response %r" % (cue, raw))
            open(mp3, "wb").write(raw)
            x = shape(cue, ffmpeg_decode(mp3))
            ft = features(x)
            sc, parts = score(cue, ft)
            rows.append(dict(name=name, file=os.path.relpath(mp3, REPO).replace("\\", "/"), features=ft, score=sc, parts=parts, prompt=spec["prompt"]))
            print("%-13s %s score %.3f %s" % (cue, name, sc, "" if ft else "(silent)"))
        data[cue] = rows
        json.dump(data, open(TAKES_JSON, "w"), indent=1)
    return data


# ---- the pick + the shipping render ---------------------------------------------------------------------
def rescore(cues):
    """re-measure every kept take (a profile or metric changed)"""
    data = json.load(open(TAKES_JSON)) if os.path.exists(TAKES_JSON) else {}
    for cue in cues:
        for r in data.get(cue, []):
            p = os.path.join(REPO, r["file"])
            if not os.path.exists(p):
                continue
            ft = features(shape(cue, ffmpeg_decode(p)))
            r["features"] = ft
            r["score"], r["parts"] = score(cue, ft)
    json.dump(data, open(TAKES_JSON, "w"), indent=1)
    for cue in cues:
        rows = data.get(cue, [])
        if rows:
            print("%-13s %s" % (cue, " ".join("%s %.2f" % (r["name"], r["score"]) for r in rows)))


def drop_files(cue):
    if not os.path.isdir(DROP_DIR):
        return []
    out = []
    for f in sorted(os.listdir(DROP_DIR)):
        stem, ext = os.path.splitext(f)
        if ext.lower() not in (".wav", ".mp3", ".flac", ".ogg", ".m4a"):
            continue
        if stem == cue or re.fullmatch(re.escape(cue) + r"_\d+", stem):
            out.append(os.path.join(DROP_DIR, f))
    return out


def synth_c4_loop():
    n = SR  # 1.0 s loop
    t = np.arange(n) / SR
    x = np.zeros(n)
    for t0 in (0.020, 0.110):
        a, b = int(t0 * SR), int((t0 + 0.045) * SR)
        seg = t[a:b] - t0
        env = np.minimum(1.0, seg / 0.004) * np.minimum(1.0, (0.045 - seg) / 0.008)
        x[a:b] = 0.8 * env * (np.sin(2 * np.pi * 2600 * seg) + 0.25 * np.sin(2 * np.pi * 5200 * seg))
    return x


def synth_deny():
    """PK18, the REFUSED press (0.25 s): two short pulses a falling fourth apart (Eb4 311 Hz -> Bb3 233 Hz: "nuh-uh"),
    each a band-limited square (odd harmonics to the 9th) that sags 3 % in pitch, with a light 45 Hz flutter (the
    buzz) and a 3 ms attack, then two one-pole low-passes at 2.2 kHz (muted: a UI no, never a buzzer). Deterministic.
    Distinct from the stock zmb_no_purchase on every axis: that one is a 0.6 s continuous 660 Hz buzz, centroid 2.4 kHz."""
    from scipy.signal import lfilter
    n = int(0.25 * SR)
    x = np.zeros(n)
    for t0, dur, f0, amp in ((0.000, 0.085, 311.13, 1.0), (0.120, 0.110, 233.08, 0.9)):
        a, m = int(round(t0 * SR)), int(round(dur * SR))
        t = np.arange(m) / SR
        ph = 2 * np.pi * np.cumsum(f0 * (1.0 - 0.03 * t / dur)) / SR
        tone = sum(np.sin(k * ph) / k for k in (1, 3, 5, 7, 9))
        flutter = 1.0 - 0.25 * (0.5 + 0.5 * np.sin(2 * np.pi * 45 * t))
        env = np.minimum(1.0, t / 0.003) * np.exp(-t / (dur * 0.9)) * np.clip((dur - t) / 0.02, 0, 1)
        x[a:a + m] += amp * tone * flutter * env
    alpha = 1 - np.exp(-2 * np.pi * 2200 / SR)
    for _ in range(2):
        x = lfilter([alpha], [1, -(1 - alpha)], x)
    return x


SYNTHS = {"c4_loop": synth_c4_loop, "deny": synth_deny}


def render_cue(cue, source):
    """-> (wav bytes, info) for one shipped file; source = ('take', path) | ('drop', path) | ('synth', None)"""
    spec = CUES[cue]
    kind, path = source
    if kind == "synth":
        x = SYNTHS[cue]()
        if "loop" in spec["rows"]:
            y = x * 10 ** (-6 / 20)   # a loop: no trim, no fades (the silence is its own loop seam), a plain -6 dB level
            return encode(y), dict(source="synth", dur=len(y) / SR)
        y = level_to(fades(x, 0.002, 0.02), spec["lufs"])   # a one-shot synth: levelled like every take
        return encode(y), dict(source="synth", dur=len(y) / SR, lufs=round(lufs(y), 2), peak_db=round(float(db(np.max(np.abs(y)) + 1e-12)), 2))
    x = shape(cue, ffmpeg_decode(path))
    x = trim(x)
    x = dc_block(x)
    fout = {"impact": 0.03, "burst": 0.05, "tick": 0.03}.get(spec["profile"], 0.08)
    x = fades(x, 0.003, fout)
    y = level_to(x, spec["lufs"])
    return encode(y), dict(source="%s:%s" % (kind, os.path.relpath(path, REPO).replace("\\", "/")), dur=len(y) / SR,
                           lufs=round(lufs(y), 2), peak_db=round(float(db(np.max(np.abs(y)) + 1e-12)), 2))


def choose(cue, data, picks):
    """the sources to ship for a cue, best first: the user's override, dropped files, then the best takes"""
    spec = CUES[cue]
    if spec["profile"] == "synth":
        return [("synth", None)]
    want = spec["variants"]
    out = []
    ov = picks.get(cue)
    if ov:
        if ov.startswith("drop:"):
            out.append(("drop", os.path.join(DROP_DIR, ov[5:])))
        else:
            for r in data.get(cue, []):
                if r["name"] == ov:
                    out.append(("take", os.path.join(REPO, r["file"])))
    for f in drop_files(cue):
        if ("drop", f) not in out:
            out.append(("drop", f))
    rows = sorted([r for r in data.get(cue, []) if r.get("features")], key=lambda r: -r["score"])
    for r in rows:
        src = ("take", os.path.join(REPO, r["file"]))
        if src not in out:
            out.append(src)
    return out[:want]


def pick(cues):
    data = json.load(open(TAKES_JSON)) if os.path.exists(TAKES_JSON) else {}
    picks = json.load(open(PICKS_JSON)) if os.path.exists(PICKS_JSON) else {}
    man = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    os.makedirs(WAV_DIR, exist_ok=True)
    for cue in cues:
        sources = choose(cue, data, picks)
        if not sources:
            print("%-13s NO SOURCE (generate it, or drop an Uppbeat clip in %s)" % (cue, os.path.relpath(DROP_DIR, REPO)))
            continue
        files = []
        for i, src in enumerate(sources):
            stem = "tod_abfx_%s" % cue + ("" if i == 0 else "_%d" % (i + 1))
            b, info = render_cue(cue, src)
            p = os.path.join(WAV_DIR, stem + ".wav")
            if not os.path.exists(p) or open(p, "rb").read() != b:
                open(p, "wb").write(b)
            info.update(file=stem + ".wav", sha256=sha256(b))
            files.append(info)
            print("%-13s %-28s %-40s %.2fs %s" % (cue, stem + ".wav", info["source"], info["dur"],
                                                   ("%.1f LUFS" % info["lufs"]) if "lufs" in info else ""))
        man[cue] = dict(files=files, rows=list(CUES[cue]["rows"]))
    json.dump(man, open(MANIFEST, "w"), indent=1)
    write_csv(man)
    print("manifest + csv written")


# ---- the alias table -----------------------------------------------------------------------------------
# The three row shapes, copied from the first pass's own rows (sound/aliases/tod_ability.csv as of
# docs/203): a 2D row heard by the caster, a 3D row for the world, and the 3D row as a loop.
PLR_ROW = ("{name},,loaded,{file},,,,,,,,BUS_HDRFX,grp_hdrfx,snp_hdrfx,,10,92,{vol},{vol},0,10000,10000,allon,default,allon,default,8,priority,8,oldest,"
           "-120,60,40,90,0.25,1,no,2d,wpn_all,,nonlooping,,1,0,0,0,0,0.25,,yes,,0,,no,,,,,,,,,yes,no,no,0,0,,no,,,,,,no,no,yes,,,,,,,,,,,,,800,3000,,no,no,no,no,no,no,no,,,,")
W3D_ROW = ("{name},,loaded,{file},,,,,,,,BUS_HDRFX,grp_hdrfx,snp_hdrfx,,10,0,{vol},{vol},{dmin},{dmax},{dmax},allon,default,allon,default,4,priority,8,oldest,"
           "-120,60,40,90,0.25,1,no,3d,default,,{loop},,1,0,50,150,89,0.25,,yes,,0,,no,,,,,,,,,yes,no,no,0,0,,no,,,,,,no,no,yes,,,,,,,,,,,,,800,3000,,no,no,no,no,no,no,no,,,,")


def csv_text(man):
    header = open(CSV_PATH, encoding="utf-8-sig").read().split("\n")[0].rstrip("\r")
    assert header.startswith("Name,Behavior,Storage,FileSpec,"), "tod_ability.csv header moved"
    lines = [header]
    for cue in ORDER:
        if cue not in man:
            continue
        spec = CUES[cue]
        files = [f["file"] for f in man[cue]["files"]]
        for row in spec["rows"]:
            for f in files:
                fs = WAV_REL + f
                if row == "plr":
                    lines.append(PLR_ROW.format(name="tod_abfx_%s_plr" % cue, file=fs, vol=spec["vol"][0]))
                elif row == "3d":
                    lines.append(W3D_ROW.format(name="tod_abfx_%s_3d" % cue, file=fs, vol=spec["vol"][1], dmin=spec["dist"][0], dmax=spec["dist"][1], loop="nonlooping"))
                elif row == "loop":
                    lines.append(W3D_ROW.format(name="tod_abfx_%s" % cue, file=fs, vol=spec["vol"][1], dmin=spec["dist"][0], dmax=spec["dist"][1], loop="looping"))
    return "\n".join(lines) + "\n"


def write_csv(man):
    text = csv_text(man)
    out = os.environ.get("TOD_ABFX_CSV_OUT") or CSV_PATH   # a staging path while a peer build runs (docs/206); the gate reads CSV_PATH
    cur = open(out, encoding="utf-8").read() if os.path.exists(out) else None
    if cur != text:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8", newline="").write(text)


# ---- the desk + the brief ----------------------------------------------------------------------------------
def desk():
    data = json.load(open(TAKES_JSON)) if os.path.exists(TAKES_JSON) else {}
    man = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    picks = json.load(open(PICKS_JSON)) if os.path.exists(PICKS_JSON) else {}
    h = ["<!doctype html><meta charset=utf-8><title>Ability sounds desk</title>",
         "<style>body{font:14px system-ui;background:#111;color:#ddd;margin:24px}h2{margin:28px 0 6px;color:#9ef}"
         "table{border-collapse:collapse}td{padding:4px 10px;border-bottom:1px solid #333;vertical-align:top}.pick{color:#6f6;font-weight:bold}"
         "code{color:#fc8}audio{height:28px}</style>",
         "<h1>Ability sounds: every take, the pick, the drop</h1>",
         "<p>Override a pick: write <code>tmp/ability_sfx/picks.json</code> as <code>{\"dash\": \"take_2\", \"pulse\": \"drop:pulse.wav\"}</code>, then "
         "<code>python tools/ability_fx/make_sounds.py pick</code>. An Uppbeat file dropped as <code>tmp/ability_sfx/drop/&lt;cue&gt;.wav</code> wins automatically.</p>"]
    for cue in ORDER:
        spec = CUES[cue]
        h.append("<h2>%s <small>(%s, %s)</small></h2><p><i>%s</i><br>Uppbeat: <code>%s</code></p><table>" %
                 (cue, spec["profile"], ", ".join(spec["rows"]), spec["prompt"] or "synthesised", spec["uppbeat"]))
        shipped = [f["source"] for f in man.get(cue, {}).get("files", [])]
        for f in man.get(cue, {}).get("files", []):
            h.append("<tr><td class=pick>SHIPPED</td><td>%s</td><td>%s</td><td><audio controls src='../../sound_assets/tod/abfx/%s'></audio></td></tr>" %
                     (f["file"], f["source"], f["file"]))
        for r in data.get(cue, []):
            rel = r["file"]
            mark = "pick" if any(rel in s for s in shipped) else ""
            parts = " ".join("%s %.2f" % (k, v) for k, v in sorted((r.get("parts") or {}).items()) if isinstance(v, float))
            h.append("<tr><td class='%s'>%s</td><td>score %.3f</td><td><small>%s</small></td><td><audio controls src='../../%s'></audio></td></tr>" %
                     (mark, r["name"], r["score"], parts, rel))
        for f in drop_files(cue):
            h.append("<tr><td>DROP</td><td>%s</td><td></td><td><audio controls src='drop/%s'></audio></td></tr>" % (os.path.basename(f), os.path.basename(f)))
        h.append("</table>")
    os.makedirs(WORK, exist_ok=True)
    open(DESK, "w", encoding="utf-8").write("\n".join(h))
    print("desk:", DESK)


def brief():
    print("UPPBEAT SEARCH LIST - drop a download as tmp/ability_sfx/drop/<cue>.wav (or .mp3), then `pick`:")
    for cue in ORDER:
        spec = CUES[cue]
        if spec["profile"] == "synth":
            continue
        print("  %-13s ~%.1fs  %s" % (cue, spec["secs"], spec["uppbeat"]))


# ---- the gate ----------------------------------------------------------------------------------------------
def check():
    bad = []
    if not os.path.exists(MANIFEST):
        bad.append("no manifest")
        man = {}
    else:
        man = json.load(open(MANIFEST))
    for cue in ORDER:
        if cue not in man:
            bad.append("cue %s not shipped" % cue)
            continue
        for f in man[cue]["files"]:
            p = os.path.join(WAV_DIR, f["file"])
            if not os.path.exists(p):
                bad.append("missing %s" % f["file"])
                continue
            b = open(p, "rb").read()
            if sha256(b) != f["sha256"]:
                bad.append("changed %s" % f["file"])
            try:
                with wave.open(io.BytesIO(b)) as w:
                    if w.getnchannels() != 1 or w.getframerate() != SR or w.getsampwidth() != 2:
                        bad.append("%s is not mono 48 kHz 16-bit" % f["file"])
                    secs = w.getnframes() / float(SR)
                    if secs < 0.1 or secs > 4.0:
                        bad.append("%s length %.2fs" % (f["file"], secs))
            except wave.Error as e:
                bad.append("%s unreadable: %s" % (f["file"], e))
    if os.path.exists(CSV_PATH) and man:
        if open(CSV_PATH, encoding="utf-8").read() != csv_text(man):
            bad.append("tod_ability.csv differs from the generated table")
    else:
        bad.append("tod_ability.csv missing")
    try:
        if '"Filename": "tod_ability.csv"' not in open(SZC, encoding="utf-8").read():
            bad.append("tod_ability.csv not loaded by the sound zone config")
    except OSError:
        bad.append("szc unreadable")
    if bad:
        print("ABILITY SOUNDS STALE: " + "; ".join(bad[:8]) + " - " + FIX)
        sys.exit(1)
    n = sum(len(v["files"]) for v in man.values())
    print("ABILITY SOUNDS OK: %d cues, %d files, %d alias rows" % (len(man), n, csv_text(man).count("\n") - 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="")
    ap.add_argument("--cue", action="append")
    ap.add_argument("--takes", type=int, default=DEFAULT_TAKES)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cues = a.cue or ORDER
    for c in cues:
        if c not in CUES:
            sys.exit("unknown cue %s" % c)
    if a.check or a.cmd == "check":
        check()
    elif a.cmd == "generate":
        generate(cues, a.takes)
    elif a.cmd == "pick":
        pick(cues)
    elif a.cmd == "rescore":
        rescore(cues)
    elif a.cmd == "desk":
        desk()
    elif a.cmd == "brief":
        brief()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
