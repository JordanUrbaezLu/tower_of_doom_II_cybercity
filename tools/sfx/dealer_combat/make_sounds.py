"""THE DEALER'S COMBAT + SIGNATURE SOUNDS (asset pack PK10, 2026-10-04): one owner for every sound the Dealer makes
that is not a spoken line.

THE GAP (verified 2026-10-04): his state-one scythe cuts, attack grunts, teleports, intro and outtro carried Sound
notes naming Revelations' Keeper-Protector aliases (zmb_keeperprot_*, zmb_vocals_keeperprot_*, keeper_teleport_*,
keeper_spawn_*) and his state-two ground swipes the notetrack name "zombie_melee" as a Sound: no alias table this map
loads defines any of them, so every swing was SILENT. His spawn, half-health MASK CRACK and death all played the
Necromancer's borrowed zm_island skull scream (evt_zombie_skull_scream). This tool makes his own set:

  tod_dealer_scythe_swing   x4  state one's cut: a huge curved blade's deep whoosh with a short metal ring
  tod_dealer_scythe_hit     x3  his melee LANDS (either state): a slashing bite into armour and flesh
  tod_dealer_claw_swing     x3  state two's ground swipes (the cracked mask, gun in hand): a heavy coat-sleeve whip
  tod_dealer_attack_vox     x3  the effort on a swing: HIS OWN VOICE (the shipping dealer voice) through THE MASK
                                (tools/black_market_vo/mask_tone.py, the chain every one of his lines ships through)
  tod_dealer_bamf_out           he vanishes: an inward rush collapsing into an electric pop
  tod_dealer_bamf_in            he appears: the air tears open, a bass thump and a red crackle
  tod_dealer_spawn              the rift he rises from: a tearing roar, a sub boom, a low synthetic choir
  tod_dealer_mask_crack         half health: one hard porcelain snap, sparking failure, a feedback shriek cut dead
                                (+ tod_dealer_mask_crack_2d: the SAME file as a 2D row, the crack sting for a far player)
  tod_dealer_death              the end: a glitching electronic scream that pitches down and breaks apart, a thud
  tod_dealer_levitate_lp        state one LEVITATES: a seamless low anti-gravity hum (3D LOOPING)

THE PIPELINE (the tools/ability_fx/make_sounds.py pattern): every cue is generated at most MAX_TAKES times by
ElevenLabs (sound generation for the effects; the dealer's saved voice through text-to-speech for the grunts), every
take is measured and scored against the cue's profile, and the best ships. A MULTI cue asks for several separated
events in ONE take (four swings, three hits, three efforts) and slices them apart, so a four-variant cue costs one or
two calls, never four. Every shipped file is mono 48 kHz 16-bit, trimmed to its sound, DC-blocked, faded at both ends,
held inside its length window, levelled to the cue's BS.1770 loudness target beside its shipped neighbours (the boss
melee cues sit near -16 LUFS, the skull scream these replace near -11) under a soft limiter at -1.5 dBFS, and recorded
with its sha256 in sounds_manifest.json. The loop is cut and equal-power crossfaded into itself (no seam).

The alias table sound/aliases/tod_dealer.csv is REGENERATED whole (tod_ui.csv's header verbatim; the row shape of
tod_arena_gate - UIN_MOD, BUS_FX, no context columns - with each cue's own volume, distance, limits and pitch spread).

  python tools/sfx/dealer_combat/make_sounds.py generate [--cue NAME] [--takes N]   call ElevenLabs, score, write takes.json
  python tools/sfx/dealer_combat/make_sounds.py rescore  [--cue NAME]               re-measure the kept takes
  python tools/sfx/dealer_combat/make_sounds.py pick     [--cue NAME] [--out-root DIR]
                                    render the best events, write the wavs + tod_dealer.csv under DIR (default the repo)
                                    and register tod_dealer.csv in DIR's zone config; the manifest stays beside this tool
  python tools/sfx/dealer_combat/make_sounds.py desk                                the listening desk + spectrogram sheet
  python tools/sfx/dealer_combat/make_sounds.py --check [--root DIR]                the build gate (no API, no DSP)

THE GATE (`--check`) reads DIR (default the repo): every manifest wav present with its sha, mono 48 kHz 16-bit, inside
its cue's length window, peak under -1.4 dBFS; tod_dealer.csv exactly as this tool writes it; the zone config loads it;
AND the two places that NAME these aliases agree with the table: every Sound note in source_data/tod_dealer.gdt that
names a tod_dealer_* alias is a defined row and no note still names a retired Keeper-Protector alias (the remap in
tools/dealer_boss/install.py), and every TOD_DEALER_SND_* define in _tod_dealer_finale.gsc names a defined row (a
named-but-undefined alias is exactly the silence this pack fixed).

The key is ELEVENLABS_API_KEY (via tools/black_market_vo/eleven.py: never printed, never stored). Takes are kept under
tmp/asset_prod/PK10-dealer-combat-sfx/takes/ (not in git).
"""
import argparse, hashlib, io, json, os, re, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(REPO, "tools", "black_market_vo"))

SR = 48000
PEAK_DB = -1.5
WAV_SUB = os.path.join("sound_assets", "tod", "dealer")
WAV_REL = "tod\\dealer\\"
CSV_SUB = os.path.join("sound", "aliases", "tod_dealer.csv")
HEADER_SUB = os.path.join("sound", "aliases", "tod_ui.csv")
SZC_SUB = os.path.join("sound", "zoneconfig", "zm_tod2_cybercity.szc")
GDT_SUB = os.path.join("source_data", "tod_dealer.gdt")
GSC_SUB = os.path.join("scripts", "zm", "zm_tod2_cybercity", "_tod_dealer_finale.gsc")
MANIFEST = os.path.join(HERE, "sounds_manifest.json")
WORK = os.path.join(REPO, "tmp", "asset_prod", "PK10-dealer-combat-sfx")
TAKES_DIR = os.path.join(WORK, "takes")
TAKES_JSON = os.path.join(WORK, "takes.json")
PICKS_JSON = os.path.join(WORK, "picks.json")      # overrides: {cue: ["take_2#1", "take_1#3"]}
FIX = "run: python tools/sfx/dealer_combat/make_sounds.py pick"
MAX_TAKES = 3
PROMPT_INFLUENCE = 0.55
SFX_MODEL = "eleven_text_to_sound_v2"
SFX_FORMAT = "mp3_44100_192"
# the Keeper-Protector aliases the pack's notes name; none may survive the remap (tools/dealer_boss/install.py)
RETIRED_NOTE = re.compile(r"^(zmb_keeperprot_|zmb_vocals_keeperprot_|keeper_teleport_|keeper_spawn_)")

# ---- the cues ------------------------------------------------------------------------------------------------------
# alias: the alias (and file stem); n: shipped variants; src: "sfx" (sound generation) | "tts" (his voice + the mask);
# multi: events asked for in one take (sliced apart); secs: the duration asked for; win: the shipped length window (s);
# lufs: the loudness target; profile: the scoring shape; row: the alias row (vol, dist min / dry / wet, limit,
# limit type, entity limit, entity limit type, pitch min / max in cents, pan, looping); prompt / text: what is asked.
CUES = {
    "scythe_swing": dict(
        alias="tod_dealer_scythe_swing", n=4, src="sfx", multi=4, secs=6.5, win=(0.38, 0.62), lufs=-16.0, profile="swing",
        row=dict(vol=86, dist=(150, 2600, 3000), limit=(4, "oldest", 2, "oldest"), pitch=(-80, 60), pan="3d", loop=False),
        prompt="Four separate heavy scythe swings, one after another, each followed by a full second of complete silence: "
               "each swing is a fast, deep, powerful whoosh of a huge curved steel blade cutting the air, ending in a short "
               "bright metallic ring. Close, dry, cinematic sound effect, no music, no voice."),
    "scythe_hit": dict(
        alias="tod_dealer_scythe_hit", n=3, src="sfx", multi=3, secs=5.0, win=(0.28, 0.52), lufs=-15.0, profile="hit",
        row=dict(vol=84, dist=(100, 1800, 2200), limit=(4, "oldest", 1, "oldest"), pitch=(-60, 60), pan="3d", loop=False),
        prompt="Three separate vicious blade strikes, each followed by a full second of complete silence: a heavy steel scythe "
               "slashing into armor and flesh, a sharp metallic slice with a dense meaty thud, short and brutal. Close, dry, "
               "cinematic sound effect, no music, no voice."),
    "claw_swing": dict(
        alias="tod_dealer_claw_swing", n=3, src="sfx", multi=3, secs=5.0, win=(0.32, 0.62), lufs=-16.5, profile="swing",
        row=dict(vol=84, dist=(150, 2400, 2800), limit=(4, "oldest", 2, "oldest"), pitch=(-80, 60), pan="3d", loop=False),
        prompt="Three separate fast heavy arm swipes, each followed by a full second of complete silence: a long heavy leather "
               "coat sleeve whipping hard through the air, a deep cloth whoosh with a short crackle of red electricity at the "
               "end. No metal, no blade, no impact. Close, dry, cinematic sound effect, no music, no voice."),
    "attack_vox": dict(
        alias="tod_dealer_attack_vox", n=3, src="tts", multi=3, secs=0, win=(0.42, 1.0), lufs=-16.0, profile="vox",
        row=dict(vol=84, dist=(200, 3000, 3500), limit=(3, "oldest", 1, "reject"), pitch=(-40, 30), pan="3d", loop=False),
        text="[growls] Hhrraah! [pause] [pause] [snarls] Hah! [pause] [pause] [grunts] Hnnngh-HAH! [pause] [pause] [growls] Rrrah!",
        settings={"stability": 0.25, "similarity": 0.75, "style": 0.6, "speed": 1.0}),
    "bamf_out": dict(
        alias="tod_dealer_bamf_out", n=1, src="sfx", multi=1, secs=1.2, win=(0.75, 1.2), lufs=-15.0, profile="suck",
        row=dict(vol=90, dist=(300, 4000, 4500), limit=(2, "oldest", 1, "oldest"), pitch=(0, 0), pan="3d", loop=False),
        prompt="A dark sorcerer vanishing in a teleport: a sharp inward rush of air and a reversed whoosh that collapses into a "
               "tight electric pop and a brief digital glitch stutter, then silence. Dry, cinematic sound effect, no music, no voice."),
    "bamf_in": dict(
        alias="tod_dealer_bamf_in", n=1, src="sfx", multi=1, secs=1.1, win=(0.75, 1.2), lufs=-15.0, profile="burst",
        row=dict(vol=90, dist=(300, 4000, 4500), limit=(2, "oldest", 1, "oldest"), pitch=(0, 0), pan="3d", loop=False),
        prompt="A dark sorcerer appearing out of a teleport: the air tears open with a deep bass thump and a crackling burst of red "
               "electricity, a brief glitch stutter, then a short fading hiss. Dry, cinematic sound effect, no music, no voice."),
    "spawn": dict(
        alias="tod_dealer_spawn", n=1, src="sfx", multi=1, secs=2.2, win=(1.45, 2.0), lufs=-12.5, profile="rift",
        row=dict(vol=92, dist=(300, 6500, 6500), limit=(2, "oldest", 1, "oldest"), pitch=(0, 0), pan="3d", loop=False),
        prompt="A rift in reality ripping open: a deep tearing roar of torn air, a heavy sub bass boom, and a low eerie synthetic "
               "choir of dark voices swelling and dying away, ominous and supernatural. No melody, no words, no music."),
    "mask_crack": dict(
        alias="tod_dealer_mask_crack", n=1, src="sfx", multi=1, secs=1.5, win=(1.0, 1.5), lufs=-12.5, profile="crack",
        row=dict(vol=92, dist=(300, 6500, 6500), limit=(2, "oldest", 1, "oldest"), pitch=(0, 0), pan="3d", loop=False),
        row2d=dict(alias="tod_dealer_mask_crack_2d", vol=70),
        prompt="A hard porcelain mask cracking apart with one loud sharp snap, then sparking electrical failure and a crackling "
               "short circuit, ending in a distorted digital shriek of feedback that cuts out abruptly. No voice, no words, no music."),
    "death": dict(
        alias="tod_dealer_death", n=1, src="sfx", multi=1, secs=2.8, win=(2.0, 3.0), lufs=-13.0, profile="collapse",
        row=dict(vol=92, dist=(300, 6500, 6500), limit=(2, "oldest", 1, "oldest"), pitch=(0, 0), pan="3d", loop=False),
        prompt="A cyborg demon dying: a distorted glitching electronic scream that pitches down and breaks apart into digital "
               "stutters and crackling sparks, a heavy thud, then a low electrical hum fading out. No words, no music."),
    "levitate_lp": dict(
        alias="tod_dealer_levitate_lp", n=1, src="sfx", multi=1, secs=5.0, win=(2.0, 4.0), lufs=-26.0, profile="hum", loop=True,
        row=dict(vol=66, dist=(60, 800, 1000), limit=(2, "oldest", 1, "oldest"), pitch=(0, 0), pan="3d", loop=True),
        prompt="A low steady hovering hum: a dark anti-gravity drone with a faint electrical buzz and a slow gentle pulse, "
               "constant and even, no music."),
}
ORDER = list(CUES.keys())


# ---- audio helpers (the ability_fx set) -----------------------------------------------------------------------------
def ffmpeg_decode(path, af=None):
    """any audio file -> mono float64 at SR (an optional ffmpeg filter chain first)"""
    cmd = ["ffmpeg", "-v", "error", "-i", path]
    if af:
        cmd += ["-af", af]
    cmd += ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype="<f4").astype(np.float64)


def lufs(x):
    """BS.1770-4 integrated loudness, mono 48 kHz"""
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


def trim(x, head_db=-50.0, tail_db=-55.0, pre=0.004, post=0.05):
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
    if 0 < a < len(x):
        x[:a] *= np.linspace(0, 1, a)
    if 0 < b < len(x):
        x[-b:] *= np.linspace(1, 0, b) ** 2
    return x


def clamp_len(x, hi):
    """hold a sound inside its window: past `hi` it is cut with a smooth 20 % fade (never a click)"""
    n = int(hi * SR)
    if len(x) <= n:
        return x
    y = x[:n].copy()
    f = int(0.2 * n)
    y[-f:] *= np.linspace(1, 0, f) ** 2
    return y


def level_to(x, target_lufs, peak_db=PEAK_DB):
    """gain onto the loudness target, then a tanh knee so no sample passes the ceiling"""
    cur = lufs(x)
    y = x * 10 ** ((target_lufs - cur) / 20)
    ceil = 10 ** (peak_db / 20)
    pk = np.max(np.abs(y)) + 1e-12
    if pk > ceil:
        d = pk / ceil
        y = np.tanh(y * d / pk) / np.tanh(d) * ceil
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


# ---- slicing a multi-event take -------------------------------------------------------------------------------------
def events(x, gate_db=-36.0, min_gap=0.14, min_len=0.10):
    """-> [(start, end)] sample ranges of the separate sounds in a take (a gap of min_gap under the gate splits them)"""
    e = envelope(x, 0.005)
    pk = e.max()
    if pk <= 1e-6:
        return []
    on = db(e / pk) > gate_db
    n5 = int(0.005 * SR)
    segs, i = [], 0
    while i < len(on):
        if not on[i]:
            i += 1
            continue
        j = i
        while j < len(on) and on[j]:
            j += 1
        segs.append([i, j])
        i = j
    merged = []
    for s in segs:
        if merged and (s[0] - merged[-1][1]) * 0.005 < min_gap:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    out = []
    for k, (a, b) in enumerate(merged):
        lo = max(0, a * n5 - int(0.012 * SR))
        nxt = merged[k + 1][0] * n5 - int(0.012 * SR) if k + 1 < len(merged) else len(x)
        hi = min(nxt, b * n5 + int(0.45 * SR))   # the tail rides on under the gate until the next sound
        if (b - a) * 0.005 >= min_len:
            out.append((lo, hi))
    return out


# ---- the measurements + the profile scores -------------------------------------------------------------------------
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
    tail_db = float(db(e[-max(1, 5):].mean() / pk))
    hot = (np.abs(x) >= 0.999).astype(np.int8)
    runs = np.convolve(hot, np.ones(4, dtype=np.int8), "valid") >= 4
    clip = float(np.mean(runs)) if runs.size else 0.0
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    tot = spec.sum() + 1e-12
    low_share = float(spec[f < 180].sum() / tot)
    hi_share = float(spec[f > 4000].sum() / tot)
    s = spec[(f > 60) & (f < 12000)] + 1e-12
    flat = float(np.exp(np.mean(np.log(s))) / np.mean(s))
    # steadiness (the hum): envelope spread over the middle 80 %
    mid = e[int(0.1 * len(e)):max(int(0.1 * len(e)) + 1, int(0.9 * len(e)))]
    steady = float(np.std(db(mid / pk))) if mid.size > 4 else 99.0
    return dict(dur=dur, onset=onset, peak_at=float(t[ip] / max(dur, 1e-6)), decay=decay, tail_db=tail_db, clip=clip,
                low=low_share, hi=hi_share, flat=flat, steady=steady, peak=float(pk))


def closeness(v, lo, hi, soft):
    if lo <= v <= hi:
        return 1.0
    d = (lo - v) if v < lo else (v - hi)
    return max(0.0, 1.0 - d / soft)


def score(cue, ft):
    if ft is None:
        return -1.0, {"dead": True}
    spec = CUES[cue]
    p = spec["profile"]
    lo, hi = spec["win"]
    s = {"length": closeness(ft["dur"], lo * 0.85, hi * 1.25, 0.6 * hi),
         "clip": 1.0 - min(1.0, ft["clip"] * 50)}
    if p != "hum":
        s["tail"] = closeness(ft["tail_db"], -90, -26, 14)
    if p == "swing":      # front-loaded: the note sits on the strike frame, so the air must move at once
        s["onset"] = closeness(ft["onset"], 0.0, 0.12, 0.2)
        s["peak_at"] = closeness(ft["peak_at"], 0.03, 0.45, 0.3)
        s["decay"] = closeness(ft["decay"], 0.08, 0.5, 0.4)
    elif p == "hit":
        s["onset"] = closeness(ft["onset"], 0.0, 0.04, 0.12)
        s["decay"] = closeness(ft["decay"], 0.05, 0.4, 0.4)
        s["peak_at"] = closeness(ft["peak_at"], 0.0, 0.25, 0.3)
        s["low"] = closeness(ft["low"], 0.06, 1.0, 0.1)
    elif p == "vox":
        s["onset"] = closeness(ft["onset"], 0.0, 0.2, 0.3)
        s["decay"] = closeness(ft["decay"], 0.08, 0.8, 0.5)
        s["voiced"] = closeness(ft["flat"], 0.0, 0.35, 0.3)       # a voice is tonal; a breath is noise
    elif p == "suck":     # builds, then the pop
        s["peak_at"] = closeness(ft["peak_at"], 0.35, 0.92, 0.3)
        s["onset"] = closeness(ft["onset"], 0.05, 0.75, 0.3)
    elif p == "burst":
        s["onset"] = closeness(ft["onset"], 0.0, 0.1, 0.2)
        s["decay"] = closeness(ft["decay"], 0.12, 0.9, 0.5)
        s["low"] = closeness(ft["low"], 0.06, 1.0, 0.1)
    elif p == "rift":
        s["onset"] = closeness(ft["onset"], 0.0, 0.5, 0.4)
        s["decay"] = closeness(ft["decay"], 0.4, 1.8, 0.6)
        s["low"] = closeness(ft["low"], 0.08, 1.0, 0.1)
    elif p == "crack":    # the snap first: his "My FACE!" lands on it, so the crack cannot be late
        s["onset"] = closeness(ft["onset"], 0.0, 0.03, 0.1)
        s["peak_at"] = closeness(ft["peak_at"], 0.0, 0.2, 0.3)
        s["hi"] = closeness(ft["hi"], 0.08, 1.0, 0.1)
    elif p == "collapse": # front-loaded: his last calm line follows at once, so the scream is over early
        s["onset"] = closeness(ft["onset"], 0.0, 0.25, 0.3)
        s["peak_at"] = closeness(ft["peak_at"], 0.0, 0.4, 0.3)
        s["decay"] = closeness(ft["decay"], 0.3, 2.0, 0.6)
    elif p == "hum":
        s["steady"] = closeness(ft["steady"], 0.0, 3.0, 4.0)
        s["low"] = closeness(ft["low"], 0.15, 1.0, 0.15)
    return float(sum(s.values()) / len(s)), s


# ---- the shaping per source ------------------------------------------------------------------------------------------
def mask_filter():
    """the shipping mask (tools/black_market_vo/mask_tone.py FILTER: v6, the pitch kept for his deep voice)"""
    import mask_tone
    return mask_tone.FILTER


def decode_take(cue, path):
    if CUES[cue]["src"] == "tts":
        return ffmpeg_decode(path, af=mask_filter())
    return ffmpeg_decode(path)


# ---- ElevenLabs ------------------------------------------------------------------------------------------------------
def load(path, default):
    return json.load(open(path)) if os.path.exists(path) else default


def take_events(cue, x):
    """the events in a decoded take: the whole take for a single-event cue, the slices for a multi cue"""
    if CUES[cue]["multi"] <= 1:
        return [(0, len(x))]
    return events(x)


def measure_take(cue, rel):
    x = decode_take(cue, os.path.join(REPO, rel))
    out = []
    for k, (a, b) in enumerate(take_events(cue, x)):
        ft = features(x[a:b])
        sc, parts = score(cue, ft)
        out.append(dict(idx=k + 1, start=a, end=b, features=ft, score=sc, parts=parts))
    return out


def generate(cues, takes):
    import eleven
    data = load(TAKES_JSON, {})
    for cue in cues:
        spec = CUES[cue]
        d = os.path.join(TAKES_DIR, cue)
        os.makedirs(d, exist_ok=True)
        rows = data.get(cue, [])
        have = len(rows)
        want = min(MAX_TAKES, have + takes)
        for i in range(have, want):
            name = "take_%d" % (i + 1)
            if spec["src"] == "tts":
                voice = json.load(open(os.path.join(REPO, "tmp", "black_market_vo", "voice.json")))["voice_id"]
                seed = 4100 + 37 * i
                raw = eleven.tts(voice, spec["text"], model_id="eleven_v4", seed=seed, output_format="pcm_48000", **spec["settings"])
                path = os.path.join(d, name + ".wav")
                pcm = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
                open(path, "wb").write(encode(pcm))
                meta = dict(voice=voice, seed=seed, text=spec["text"], settings=spec["settings"], model="eleven_v4")
            else:
                body = {"text": spec["prompt"], "duration_seconds": spec["secs"], "prompt_influence": PROMPT_INFLUENCE, "model_id": SFX_MODEL}
                if spec.get("loop"):
                    body["loop"] = True
                raw = eleven.call("POST", "/v1/sound-generation", body=body, query={"output_format": SFX_FORMAT})
                if not isinstance(raw, (bytes, bytearray)):
                    sys.exit("%s: unexpected response %r" % (cue, raw))
                path = os.path.join(d, name + ".mp3")
                open(path, "wb").write(raw)
                meta = dict(prompt=spec["prompt"], secs=spec["secs"], model=SFX_MODEL, loop=bool(spec.get("loop")))
            rel = os.path.relpath(path, REPO).replace("\\", "/")
            evs = measure_take(cue, rel)
            rows.append(dict(name=name, file=rel, meta=meta, events=evs))
            print("%-13s %s: %d event(s) %s" % (cue, name, len(evs), " ".join("#%d %.2f (%.2fs)" % (e["idx"], e["score"], e["features"]["dur"] if e["features"] else 0) for e in evs)))
            data[cue] = rows
            json.dump(data, open(TAKES_JSON, "w"), indent=1)
    return data


def rescore(cues):
    data = load(TAKES_JSON, {})
    for cue in cues:
        for r in data.get(cue, []):
            if os.path.exists(os.path.join(REPO, r["file"])):
                r["events"] = measure_take(cue, r["file"])
        rows = data.get(cue, [])
        print("%-13s %s" % (cue, " | ".join("%s: %s" % (r["name"], " ".join("#%d %.2f" % (e["idx"], e["score"]) for e in r["events"])) for r in rows)))
    json.dump(data, open(TAKES_JSON, "w"), indent=1)


# ---- the pick + the shipping render ----------------------------------------------------------------------------------
def candidates(cue, data):
    out = []
    for r in data.get(cue, []):
        for e in r.get("events", []):
            if e.get("features"):
                out.append(("%s#%d" % (r["name"], e["idx"]), r, e))
    return out


def choose(cue, data, picks):
    """the events to ship, best first: the override list, then the best scores (never the same event twice)"""
    n = CUES[cue]["n"]
    cands = candidates(cue, data)
    by_id = {cid: (r, e) for cid, r, e in cands}
    out = [cid for cid in picks.get(cue, []) if cid in by_id]
    for cid, r, e in sorted(cands, key=lambda c: -c[2]["score"]):
        if cid not in out:
            out.append(cid)
    return [(cid, by_id[cid][0], by_id[cid][1]) for cid in out[:n]]


def loop_render(x, spec):
    """a seamless loop: a window from the steady middle, its head equal-power crossfaded with what follows it"""
    lo, hi = spec["win"]
    xf = int(0.35 * SR)
    start = int(0.4 * SR)
    L = int(min(hi, max(lo, (len(x) - start - xf) / SR - 0.05)) * SR)
    if start + L + xf > len(x):
        start = max(0, len(x) - L - xf)
    seg = x[start:start + L].copy()
    tail = x[start + L:start + L + xf]
    w = np.linspace(0, 1, xf)
    seg[:xf] = seg[:xf] * np.sqrt(w) + tail * np.sqrt(1 - w)
    return seg


def render_event(cue, r, e):
    spec = CUES[cue]
    x = decode_take(cue, os.path.join(REPO, r["file"]))[e["start"]:e["end"]]
    x = dc_block(x)
    if spec.get("loop"):
        y = loop_render(x, spec)
        y = level_to(y, spec["lufs"])
        return y
    x = trim(x)
    x = clamp_len(x, spec["win"][1])
    fout = {"hit": 0.03, "swing": 0.05, "vox": 0.05, "crack": 0.06}.get(spec["profile"], 0.10)
    x = fades(x, 0.002, fout)
    return level_to(x, spec["lufs"])


def stems(cue):
    spec = CUES[cue]
    if spec["n"] == 1:
        return [spec["alias"]]
    return ["%s_%02d" % (spec["alias"], i + 1) for i in range(spec["n"])]


def pick(cues, out_root):
    data = load(TAKES_JSON, {})
    picks = load(PICKS_JSON, {})
    man = load(MANIFEST, {})
    wav_dir = os.path.join(out_root, WAV_SUB)
    os.makedirs(wav_dir, exist_ok=True)
    for cue in cues:
        chosen = choose(cue, data, picks)
        if len(chosen) < CUES[cue]["n"]:
            print("%-13s ONLY %d of %d events available - generate more takes" % (cue, len(chosen), CUES[cue]["n"]))
            continue
        files = []
        for stem, (cid, r, e) in zip(stems(cue), chosen):
            y = render_event(cue, r, e)
            b = encode(y)
            p = os.path.join(wav_dir, stem + ".wav")
            if not os.path.exists(p) or open(p, "rb").read() != b:
                open(p, "wb").write(b)
            info = dict(file=stem + ".wav", sha256=sha256(b), source="%s/%s" % (r["file"], cid), score=round(e["score"], 3),
                        dur=round(len(y) / SR, 3), lufs=round(lufs(y), 2), peak_db=round(float(db(np.max(np.abs(y)) + 1e-12)), 2))
            files.append(info)
            print("%-13s %-32s %-18s %.2fs %.1f LUFS peak %.2f" % (cue, info["file"], cid, info["dur"], info["lufs"], info["peak_db"]))
        man[cue] = dict(alias=CUES[cue]["alias"], files=files)
    json.dump(man, open(MANIFEST, "w"), indent=1, sort_keys=True)
    open(MANIFEST, "a").write("\n")
    write_csv(man, out_root)
    if szc_register(out_root):
        print("registered tod_dealer.csv in", os.path.join(out_root, SZC_SUB))
    print("manifest + csv written under", out_root)


# ---- the alias table ---------------------------------------------------------------------------------------------------
def header(root):
    h = open(os.path.join(root, HEADER_SUB), encoding="utf-8-sig").read().split("\n")[0].rstrip("\r")
    assert h.startswith("Name,Behavior,Storage,FileSpec,"), "tod_ui.csv header moved"
    return h


def row_text(cols, values):
    cells = [""] * len(cols)
    for k, v in values.items():
        cells[cols.index(k)] = str(v)
    return ",".join(cells)


def csv_text(man, root):
    h = header(root)
    cols = h.split(",")
    lines = [h]
    for cue in ORDER:
        if cue not in man:
            continue
        spec = CUES[cue]
        r = spec["row"]
        for f in man[cue]["files"]:
            v = {"Name": spec["alias"], "FileSpec": WAV_REL + f["file"], "Template": "UIN_MOD", "Bus": "BUS_FX",
                 "VolMin": r["vol"], "VolMax": r["vol"], "PanType": r["pan"], "Looping": "LOOPING" if r["loop"] else "NONLOOPING",
                 "DistMin": r["dist"][0], "DistMaxDry": r["dist"][1], "DistMaxWet": r["dist"][2],
                 "LimitCount": r["limit"][0], "LimitType": r["limit"][1], "EntityLimitCount": r["limit"][2], "EntityLimitType": r["limit"][3],
                 "PitchMin": r["pitch"][0], "PitchMax": r["pitch"][1]}
            lines.append(row_text(cols, v))
        if spec.get("row2d"):
            r2 = spec["row2d"]
            for f in man[cue]["files"]:
                lines.append(row_text(cols, {"Name": r2["alias"], "FileSpec": WAV_REL + f["file"], "Template": "UIN_MOD", "Bus": "BUS_FX",
                                             "VolMin": r2["vol"], "VolMax": r2["vol"], "PanType": "2d", "Looping": "NONLOOPING"}))
    return "\n".join(lines) + "\n"


def write_csv(man, root):
    text = csv_text(man, root)
    out = os.path.join(root, CSV_SUB)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if not os.path.exists(out) or open(out, encoding="utf-8").read() != text:
        open(out, "w", encoding="utf-8", newline="").write(text)


def all_aliases():
    out = set()
    for spec in CUES.values():
        out.add(spec["alias"])
        if spec.get("row2d"):
            out.add(spec["row2d"]["alias"])
    return out


# ---- the zone config ---------------------------------------------------------------------------------------------------
def szc_loads(text):
    try:
        data = json.loads(text)
    except ValueError:
        return False
    return any(isinstance(s, dict) and s.get("Type") == "ALIAS" and str(s.get("Filename", "")).lower() == "tod_dealer.csv"
               for s in data.get("Sources", []))


def szc_register(root):
    """add the tod_dealer ALIAS source if it is missing: a text copy of the tod_house entry, placed right after it"""
    path = os.path.join(root, SZC_SUB)
    raw = open(path, "rb").read()
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    text = raw[len(bom):].decode("utf-8")
    if szc_loads(text):
        return False
    tpl = re.search(r'([ \t]*)(\{[^{}]*"Filename"\s*:\s*"tod_house\.csv"[^{}]*\})', text)
    if not tpl:
        raise SystemExit("DEALER SOUNDS: no tod_house entry in %s to copy - add the tod_dealer ALIAS source by hand" % path)
    nl = "\r\n" if "\r\n" in text else "\n"
    clone = tpl.group(2).replace('"tod_house.csv"', '"tod_dealer.csv"').replace('"tod_house"', '"tod_dealer"')
    new = text[:tpl.end()] + "," + nl + tpl.group(1) + clone + text[tpl.end():]
    if not szc_loads(new):
        raise SystemExit("DEALER SOUNDS: %s would not parse with tod_dealer added - left untouched" % path)
    open(path, "wb").write(bom + new.encode("utf-8"))
    return True


# ---- the desk + the spectrogram sheet ------------------------------------------------------------------------------------
def desk(root):
    data = load(TAKES_JSON, {})
    man = load(MANIFEST, {})
    wav_dir = os.path.join(root, WAV_SUB)
    rel_wav = os.path.relpath(wav_dir, WORK).replace("\\", "/")
    h = ["<!doctype html><meta charset=utf-8><title>Dealer combat sounds desk (PK10)</title>",
         "<style>body{font:14px system-ui;background:#111;color:#ddd;margin:24px}h2{margin:26px 0 6px;color:#f88}"
         "td{padding:3px 10px;border-bottom:1px solid #333;vertical-align:middle}.pick{color:#6f6;font-weight:bold}"
         "code{color:#fc8}audio{height:28px}img{max-width:100%}</style>",
         "<h1>The Dealer: combat and signature sounds (PK10)</h1>",
         "<p>Override a pick: <code>%s</code> as <code>{\"scythe_swing\": [\"take_2#1\", ...]}</code>, then "
         "<code>python tools/sfx/dealer_combat/make_sounds.py pick --out-root ...</code>.</p>" % os.path.relpath(PICKS_JSON, REPO).replace("\\", "/"),
         "<img src='_review.png'>"]
    for cue in ORDER:
        spec = CUES[cue]
        h.append("<h2>%s <small>(%s, %d shipped)</small></h2><p><i>%s</i></p><table>" % (spec["alias"], spec["profile"], spec["n"],
                                                                                        spec.get("prompt") or spec.get("text")))
        shipped = set()
        for f in man.get(cue, {}).get("files", []):
            shipped.add(f["source"].split("/")[-1])
            h.append("<tr><td class=pick>SHIPPED</td><td>%s</td><td>%s</td><td>%.2fs %.1f LUFS</td><td><audio controls src='%s/%s'></audio></td></tr>"
                     % (f["file"], f["source"].split("/")[-1], f["dur"], f["lufs"], rel_wav, f["file"]))
        for r in data.get(cue, []):
            ev = " ".join(("<b>#%d %.2f</b>" if "%s#%d" % (r["name"], e["idx"]) in shipped else "#%d %.2f") % (e["idx"], e["score"]) for e in r["events"])
            h.append("<tr><td>%s</td><td colspan=3>%s</td><td><audio controls src='%s'></audio></td></tr>"
                     % (r["name"], ev, os.path.relpath(os.path.join(REPO, r["file"]), WORK).replace("\\", "/")))
        h.append("</table>")
    open(os.path.join(WORK, "desk.html"), "w", encoding="utf-8").write("\n".join(h))
    sheet(man, wav_dir)
    print("desk:", os.path.join(WORK, "desk.html"))


def sheet(man, wav_dir):
    """_review.png: every shipped file's waveform-scaled spectrogram on one sheet (ffmpeg showspectrumpic + PIL)"""
    from PIL import Image, ImageDraw
    tiles = []
    tmp = os.path.join(WORK, "_spec")
    os.makedirs(tmp, exist_ok=True)
    for cue in ORDER:
        for f in man.get(cue, {}).get("files", []):
            src = os.path.join(wav_dir, f["file"])
            png = os.path.join(tmp, f["file"] + ".png")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-lavfi",
                            "showspectrumpic=s=480x160:legend=0:scale=log:fscale=log:color=intensity", png], check=True)
            tiles.append((f, Image.open(png).convert("RGB")))
    if not tiles:
        return
    cols = 3
    tw, th = 480, 160 + 22
    rows = (len(tiles) + cols - 1) // cols
    img = Image.new("RGB", (cols * tw + (cols + 1) * 8, rows * th + (rows + 1) * 8 + 30), (14, 14, 18))
    d = ImageDraw.Draw(img)
    d.text((8, 8), "PK10 - the Dealer's combat + signature sounds: log-frequency spectrograms (time left to right)", fill=(240, 120, 120))
    for i, (f, t) in enumerate(tiles):
        x = 8 + (i % cols) * (tw + 8)
        y = 38 + (i // cols) * (th + 8)
        d.text((x, y), "%s  %.2fs  %.1f LUFS  pk %.1f" % (f["file"], f["dur"], f["lufs"], f["peak_db"]), fill=(220, 220, 220))
        img.paste(t, (x, y + 18))
    img.save(os.path.join(WORK, "_review.png"))


# ---- the gate ------------------------------------------------------------------------------------------------------------
def gdt_sound_notes(text):
    """every (clip, lane, alias) a Sound custom note names in a GDT text"""
    out = []
    for m in re.finditer(r'\t"([^"]+)" \( "xanim\.gdf" \)\r?\n\t\{\r?\n(.*?)\r?\n\t\}', text, re.S):
        f = dict(re.findall(r'"([^"]+)" "([^"]*)"', m.group(2)))
        for k, v in f.items():
            if re.fullmatch(r"(?:sound_)?customnote\d+action", k) and v == "Sound":
                out.append((m.group(1), k[:-len("action")], f.get(k[:-len("action")] + "actionparam1", "")))
    return out


def check(root):
    bad = []
    man = load(MANIFEST, None)
    if not man:
        bad.append("no manifest")
        man = {}
    for cue in ORDER:
        if cue not in man:
            bad.append("cue %s not shipped" % cue)
            continue
        if len(man[cue]["files"]) != CUES[cue]["n"]:
            bad.append("%s ships %d files, wants %d" % (cue, len(man[cue]["files"]), CUES[cue]["n"]))
        lo, hi = CUES[cue]["win"]
        for f in man[cue]["files"]:
            p = os.path.join(root, WAV_SUB, f["file"])
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
                    if secs < lo - 0.02 or secs > hi + 0.02:
                        bad.append("%s length %.2fs outside %.2f-%.2f" % (f["file"], secs, lo, hi))
                    pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
                    if pcm.size and 20 * np.log10(np.max(np.abs(pcm.astype(np.float64))) / 32768.0 + 1e-12) > -1.4:
                        bad.append("%s peaks over -1.4 dBFS" % f["file"])
            except wave.Error as e:
                bad.append("%s unreadable: %s" % (f["file"], e))
    csv_path = os.path.join(root, CSV_SUB)
    if not os.path.exists(csv_path):
        bad.append("tod_dealer.csv missing")
    elif man and open(csv_path, encoding="utf-8").read() != csv_text(man, root):
        bad.append("tod_dealer.csv differs from the generated table")
    try:
        if not szc_loads(open(os.path.join(root, SZC_SUB), "rb").read().decode("utf-8-sig")):
            bad.append("tod_dealer.csv not loaded by the sound zone config")
    except OSError:
        bad.append("szc unreadable")
    names = all_aliases()
    # the GDT's notes: the remap landed, and every Dealer alias a note names is a row
    try:
        notes = gdt_sound_notes(open(os.path.join(root, GDT_SUB), encoding="utf-8", errors="replace").read())
        mine = 0
        for clip, lane, alias in notes:
            if RETIRED_NOTE.match(alias):
                bad.append("%s %s still names the retired %s (re-run tools/dealer_boss/install.py)" % (clip, lane, alias))
            if alias.startswith("tod_dealer_"):
                mine += 1
                if alias not in names:
                    bad.append("%s %s names %s, which tod_dealer.csv does not define" % (clip, lane, alias))
        if mine == 0:
            bad.append("tod_dealer.gdt names no tod_dealer_* sound note (the install.py remap is missing)")
    except OSError:
        bad.append("tod_dealer.gdt unreadable")
    # the script's defines: each names a row, and the borrowed scream is gone
    try:
        gsc = open(os.path.join(root, GSC_SUB), encoding="utf-8", errors="replace").read()
        snd = re.findall(r'^#define\s+TOD_DEALER_SND_\w+\s+"([^"]+)"', gsc, re.M)
        if not snd:
            bad.append("_tod_dealer_finale.gsc defines no TOD_DEALER_SND_* alias")
        for a in snd:
            if a not in names:
                bad.append("_tod_dealer_finale.gsc names %s, which tod_dealer.csv does not define" % a)
        if "evt_zombie_skull_scream" in gsc:
            bad.append("_tod_dealer_finale.gsc still plays the borrowed skull scream")
    except OSError:
        bad.append("_tod_dealer_finale.gsc unreadable")
    if bad:
        print("DEALER SOUNDS STALE: " + "; ".join(bad[:10]) + " - " + FIX)
        sys.exit(1)
    n = sum(len(v["files"]) for v in man.values())
    print("DEALER SOUNDS OK: %d cues, %d files, %d alias rows; the GDT notes and the script defines name only defined rows"
          % (len(man), n, csv_text(man, root).count("\n") - 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="")
    ap.add_argument("--cue", action="append")
    ap.add_argument("--takes", type=int, default=1)
    ap.add_argument("--out-root", default=REPO)
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cues = a.cue or ORDER
    for c in cues:
        if c not in CUES:
            sys.exit("unknown cue %s" % c)
    if a.check or a.cmd == "check":
        check(os.path.abspath(a.root))
    elif a.cmd == "generate":
        generate(cues, a.takes)
    elif a.cmd == "rescore":
        rescore(cues)
    elif a.cmd == "pick":
        pick(cues, os.path.abspath(a.out_root))
    elif a.cmd == "desk":
        desk(os.path.abspath(a.out_root))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
