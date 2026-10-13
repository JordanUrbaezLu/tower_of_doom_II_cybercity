"""THE END-OF-RUN MUSIC (asset pack PK03, 2026-10-04): the two music cues a run ends on.

  tod_music_gameover   THE LOSS. Every run that does not escape ends on the GAME OVER - FLOOR N screen and the 60 s
                       restart menu. Until now that screen played whatever stock's own "game_over" music state found
                       (_zm.gsc end_game -> zm_audio playState -> music state "gameover"): a stock sting this map does
                       not own, or nothing. A 14 - 18 s dark-synth fall: a heavy minor chord hit on the first beat, a
                       descending line powering down, one last low chord into silence. 2D, STREAMED, NONLOOPING, on
                       its own emitter (_tod_atmosphere::gameover_play, from music_end_watch after the channel stops);
                       _tod_atmosphere::snd_play_state_override takes the stock "game_over" state so exactly ONE
                       game-over cue plays. Never on a win (level.tod_escaped).
  tod_house_victory    BEATING THE DEALER (Battle Arena level 10, docs/207). Until now his death played the same
                       2.85 s level-clear fanfare as arena levels 1-9 while the boss track ("115") kept looping.
                       A 16 - 20 s dark-synth resolution: a quiet, low opening that sits UNDER his 6.25 s death line
                       (arena_win starts the cue ~1.75 s into it), a rising arpeggio that lifts minor -> major, a
                       triumphant major chord with a shimmering tail. 2D, STREAMED, NONLOOPING on its own emitter
                       (_tod_atmosphere::house_victory_start): "115" fades under its first second, and the music
                       CHANNEL is held (every request parked) for TOD_HOUSE_VICTORY_SECS = this manifest's hold_secs
                       (the music + its tail), then the newest parked request (the ride home's band) plays.

WHY BOTH ARE ONE-SHOTS AND NOT THE CHANNEL'S LOOPING-AND-STOPPED SHAPE: the script clock stops when a solo server
pauses, and the audio does not (UIN_MOD rows are Pauseable no). The game-over restart menu IS a pause in solo (it opens
3 s in), and a pause menu during the victory's card deal is the same: a LOOPING cue would wrap and replay under it. A
NONLOOPING cue plays once whatever the clock does; neither cue ever needs a mid-play stop (nothing follows the game
over; the victory only parks the channel).

The Dealer's fight THEME is not made here (the user's music pick; docs/207 kept the arena track on purpose).

One pipeline, the tools/ability_fx/make_sounds.py pattern: ElevenLabs MUSIC (POST /v1/music, music_v2_5) takes from a
written composition plan (chunks with their own durations, a fixed seed per take) or, for the third take, a prompt with
instrumental forced. Every take is measured (BS.1770 momentary loudness curve: where the hit lands, where the climax
lands, how much quieter the opening is, whether it falls or rises, how it ends; the tonality - Krumhansl key profiles,
major vs minor; clipping; and, when a separator is available, how much VOICE a vocal-stem model finds) and scored
against the cue's PROFILE. The best take is mastered like the bands (tools/music_master.py's chain: soxr 48 k, the
user's -6 dB low shelf under 200 Hz, makeup gain toward the bands' -11.5 LUFS with the limiter's work capped at
MAX_LIM dB, a 4x oversampled true-peak limiter at -1.0 dBTP, soxr back to 48 k with triangular dither, 16-bit), STEREO
like every music wav, and sha-pinned in sounds_manifest.json.

  python tools/sfx/end_of_run_music/make_sounds.py generate [--cue NAME] [--takes N]   ElevenLabs takes (at most 3 per cue)
  python tools/sfx/end_of_run_music/make_sounds.py vocals --separator EXE [--cue NAME] measure the voice in every take
                     (audio-separator + BS-RoFormer ep_317; optional - a take never measured is scored without it)
  python tools/sfx/end_of_run_music/make_sounds.py rescore  [--cue NAME]               re-measure the kept takes
  python tools/sfx/end_of_run_music/make_sounds.py pick     [--cue NAME] [--out-root DIR]
                     master the chosen take per cue into DIR/sound_assets/tod/music/, write the manifest, add the two
                     alias rows to DIR/sound/aliases/tod_ui.csv if missing (that file's own line endings) and write
                     the review set (desk.html, the loudness sheet, both cues in context)
  python tools/sfx/end_of_run_music/make_sounds.py review   [--out-root DIR]          rebuild the review set only
  python tools/sfx/end_of_run_music/make_sounds.py --check  [--root DIR]               the build gate (no API, no DSP)

The gate: both wavs present with their manifest sha, stereo 48 kHz 16-bit, lengths in range; the two rows in
sound/aliases/tod_ui.csv exactly as this tool writes them (the header's column count); tod_ui.csv in the sound zone
config; and the LOCKSTEP: _tod_atmosphere.gsc names both aliases, takes the stock game_over state, and its
TOD_HOUSE_VICTORY_SECS equals the manifest's hold_secs (re-picking a different take changes the hold on purpose: the
define must follow, or the band comes back over the cue's tail or late); _tod_arena.gsc starts the victory.

The key is ELEVENLABS_API_KEY (tools/black_market_vo/eleven.py: never printed, never stored). Takes live under
tmp/asset_prod/PK03-end-of-run-music/takes/ (not in git). The user's override: takes/picks.json, {"victory": "take_2"};
an authored or licensed file dropped as takes/drop/<cue>.wav|.mp3|.flac wins the pick (the same mastering chain).
"""
import argparse, glob, hashlib, html, io, json, math, os, re, shutil, subprocess, sys, tempfile, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(REPO, "tools", "black_market_vo"))

SR = 48000
PACK = "PK03-end-of-run-music"
WORK = os.path.join(REPO, "tmp", "asset_prod", PACK)
TAKES_DIR = os.path.join(WORK, "takes")
DROP_DIR = os.path.join(TAKES_DIR, "drop")
TAKES_JSON = os.path.join(TAKES_DIR, "takes.json")
PICKS_JSON = os.path.join(TAKES_DIR, "picks.json")
REVIEW_DIR = os.path.join(WORK, "review")
MANIFEST = os.path.join(HERE, "sounds_manifest.json")
MUSIC_REL = "sound_assets/tod/music"
UI_CSV_REL = "sound/aliases/tod_ui.csv"
SZC_REL = "sound/zoneconfig/zm_tod2_cybercity.szc"
ATMO_REL = "scripts/zm/zm_tod2_cybercity/_tod_atmosphere.gsc"
ARENA_REL = "scripts/zm/zm_tod2_cybercity/_tod_arena.gsc"
DEATH_LINE_REL = "sound_assets/tod/sfx/tod_house_vo_death.wav"
BAND_REL = "sound_assets/tod/music/tod_music_eclipse.wav"
MAX_TAKES = 3
MODEL = "music_v2_5"
OUTPUT_FORMATS = ["mp3_48000_320", "mp3_48000_192"]   # the best the plan allows first
SHELF_HZ, BASS_DB = 200, -6.0          # tools/music_master.py: the user's "50% less bass", on every music wav
CEIL_DB = -1.0                          # the pack rule: soft-limited at -1 dBFS (true peak, 4x oversampled)
MAX_LIM = 4.0                           # the limiter may take at most this much off a peak (else the gain backs off)
HOLD_MARGIN = 0.5                       # TOD_HOUSE_VICTORY_SECS = the music's end + this (its last reverb, then the band)
DEATH_LINE_OFFSET = 1.75                # arena_win runs ~1.5-2.0 s after the Dealer's death line starts (fight(): poll 0.5 + wait 1.5)
SEPARATOR_MODEL = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
SEPARATOR_MODELS_DIR = "C:/tmp/audio-separator-models"

# ---- the cues -------------------------------------------------------------------------------------------------
# file: the wav stem + alias name; profile: the scoring shape; secs: the length asked for; lo/hi: the shipped music's
# allowed length; lufs: the loudness target (the bands, tools/music_master.py); vol: the alias VolMin/Max (the bands'
# 100: both cues are mastered to the bands' loudness); fade: the fade-out used when a take ends abruptly. plan: the
# music_v2_5 composition plan (chunks: "[name] {directions}" text, no lyrics = instrumental); prompt: the take-3 text.
NEG = ["vocals", "singing", "choir", "vocal chops", "spoken word", "lyrics", "lo-fi", "acoustic guitar"]
CUES = {
    "gameover": dict(
        file="tod_music_gameover", profile="fall", secs=16.0, lo=12.0, hi=20.0, lufs=-11.5, vol=100, fade=1.6,
        plan=[
            dict(text="[The Fall] {instrumental: on the very first beat a heavy detuned analog synth chord and a deep sub "
                      "bass boom slam in together, a distorted low impact, the floor gives way}",
                 duration_ms=4000,
                 positive_styles=["dark synthwave", "cyberpunk", "ominous cinematic", "massive low impact",
                                  "detuned analog synth chord", "deep sub bass drop", "minor key", "slow tempo"],
                 negative_styles=NEG + ["upbeat", "major key", "drum groove"]),
            dict(text="[Power Down] {instrumental: a slow descending minor melody on a cold detuned lead synth, its "
                      "pitch sinking like a machine powering down, a ticking pulse slowing to a stop}",
                 duration_ms=6000,
                 positive_styles=["dark synthwave", "descending minor melody", "cold analog lead synth",
                                  "tape stop pitch drop", "melancholic", "dark analog pads", "sparse"],
                 negative_styles=NEG + ["drum groove", "upbeat", "major key"]),
            dict(text="[Flatline] {instrumental: one last low minor chord rings out, its long dark reverb tail fades "
                      "into complete silence}",
                 duration_ms=6000,
                 positive_styles=["dark synthwave", "final low minor chord", "long dark reverb tail",
                                  "fade to silence", "dark ambient", "defeat"],
                 negative_styles=NEG + ["drums", "new melody", "major key"]),
        ],
        prompt=("Instrumental dark synthwave game-over sting, about 16 seconds, minor key, slow. It opens on the very "
                "first beat with a heavy detuned analog synth chord and a deep sub bass boom, then a cold lead synth "
                "plays a slow descending minor melody whose pitch sinks like a machine powering down, and it ends on one "
                "last low minor chord whose long dark reverb tail fades to complete silence. Cyberpunk, ominous, "
                "defeated. No vocals, no drum groove."),
    ),
    "victory": dict(
        file="tod_house_victory", profile="rise", secs=18.0, lo=14.0, hi=22.0, lufs=-11.5, vol=100, fade=2.0,
        # a baked TUCK under his last word: the line ends 4.25-4.75 s into the cue (arena_win runs 1.5-2.0 s after
        # it starts) and the take's swell was only 2-3 dB under it in the voice band there; -4 dB until 4.75 s,
        # released by 6.0 s (an equal-power ramp), so the swell still reads as one rise
        tuck=dict(db=-4.0, until=4.75, release=6.0),
        # written in MUSIC terms (a key, a tempo, a progression), not sound-design words: the game-over takes showed
        # that "slam / boom / impact / drop" buys trailer hits with no harmony. D minor -> Bb -> C -> D major.
        plan=[
            dict(text="[Aftermath]\n{instrumental, very soft: a dark sustained synth pad on D minor over a low drone, "
                      "slow and sparse, no drums}",
                 duration_ms=4500,
                 positive_styles=["dark synthwave", "ambient", "soft sustained pad", "D minor", "100 BPM", "very quiet",
                                  "cinematic", "tense"],
                 negative_styles=NEG + ["drums", "loud", "lead melody", "bass groove"]),
            dict(text="[Rise]\n{a bright analog synth arpeggio enters and climbs, the chords move Bb then C, a snare "
                      "roll and a riser build}",
                 duration_ms=5000,
                 positive_styles=["synthwave", "analog arpeggiator", "build-up", "uplifting", "snare roll", "100 BPM",
                                  "anticipation"],
                 negative_styles=NEG),
            dict(text="[Triumph]\n{triumphant resolution on D major: a soaring synth lead melody over supersaw chords and "
                      "warm 80s synth brass, big drums}\n{the last D major chord rings out and fades}",
                 duration_ms=8500,
                 positive_styles=["triumphant synthwave", "heroic", "D major", "soaring synth lead melody",
                                  "supersaw chords", "80s synth brass", "cinematic outro", "100 BPM"],
                 negative_styles=NEG + ["sad", "minor key"]),
        ],
        prompt=("Instrumental synthwave victory cue for defeating a final boss, 100 BPM, about 18 seconds. The first four "
                "seconds are very soft: a dark sustained synth pad on D minor over a low drone, no drums. Then a bright "
                "analog arpeggio enters and climbs while the chords move Bb then C and a snare roll builds, and it "
                "resolves on D major: a soaring heroic synth lead melody over supersaw chords, warm 80s synth brass and "
                "big drums, and the final D major chord rings out and fades to silence. Cyberpunk, heroic, earned. "
                "No vocals."),
    ),
}
ORDER = ["gameover", "victory"]

# the alias rows: tod_fall_intro's row in sound/aliases/tod_ui.csv with the name, file, volume and looping changed.
# 37 fields to PanType, then Pan, Futz, Looping, then the 61 empty fields that close the header's 102 columns.
ROW = ("{name},,STREAMED,tod\\music\\{name}.wav,,,UIN_MOD,,,,,BUS_MUSIC,grp_music,snp_never_duck,,,,{vol},{vol}"
       ",,,,,,,,,,,,,,,,,,,2d,,,NONLOOPING" + "," * 61)
ROW_AFTER = "tod_boss_music,"           # the rows go into the music block, after the boss track (the finale row they once
                                        # followed retired whole 2026-10-05, W2E)
HEADER_COLS = 102


def row_text(cue):
    c = CUES[cue]
    return ROW.format(name=c["file"], vol=c["vol"])


def at_root(root, rel):
    """root's copy of a repo file, or the repo's when root (a stage) does not carry that file"""
    p = os.path.join(root, rel)
    return p if os.path.exists(p) else os.path.join(REPO, rel)


# ---- audio helpers --------------------------------------------------------------------------------------------
def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")


def decode(path):
    """any audio file -> stereo float64 (n, 2) at SR"""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", "aresample=48000:resampler=soxr:precision=28",
                          "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype="<f4").astype(np.float64).reshape(-1, 2)


def kweight(x):
    from scipy.signal import lfilter
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], x, axis=0)
    return lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y, axis=0)


def loud_curve(x, win=0.4, hop=0.1):
    """BS.1770 loudness (LUFS) of each window: (times at the window centre, values)"""
    y = kweight(x)
    p = np.sum(y ** 2, axis=1)
    w, h = int(win * SR), int(hop * SR)
    if len(p) < w:
        p = np.concatenate([p, np.zeros(w - len(p))])
    c = np.concatenate([[0.0], np.cumsum(p)])
    starts = np.arange(0, len(p) - w + 1, h)
    ms = (c[starts + w] - c[starts]) / w
    return (starts + w / 2) / SR, -0.691 + 10 * np.log10(ms + 1e-20)


def integrated(x):
    t, l = loud_curve(x, 0.4, 0.1)
    ms = 10 ** ((l + 0.691) / 10)
    ms = ms[l > -70]
    if ms.size == 0:
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(ms)) - 10
    ms = ms[(-0.691 + 10 * np.log10(ms)) > rel]
    return float(-0.691 + 10 * np.log10(np.mean(ms))) if ms.size else -70.0


def env_db(x, frame=0.010):
    m = np.mean(x, axis=1) if x.ndim == 2 else x
    n = int(frame * SR)
    k = len(m) // n
    e = np.sqrt(np.mean(m[:k * n].reshape(k, n) ** 2, axis=1) + 1e-20)
    return 20 * np.log10(e / (e.max() + 1e-20) + 1e-12)


def closeness(v, lo, hi, soft):
    if lo <= v <= hi:
        return 1.0
    d = (lo - v) if v < lo else (v - hi)
    return max(0.0, 1.0 - d / soft)


def ebur128(path):
    r = run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=framelog=quiet:peak=true", "-f", "null", "-"])
    I = float(re.search(r"^\s+I:\s+(-?[\d.]+) LUFS", r.stderr, re.M).group(1))
    lra = float(re.search(r"^\s+LRA:\s+(-?[\d.]+) LU", r.stderr, re.M).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", r.stderr).group(1).replace("-inf", "-200"))
    return I, lra, tp


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def wav_bytes(pcm16):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm16.astype("<i2").tobytes())
    return buf.getvalue()


def write_f32_wav(path, x):
    """a float stereo file for ffmpeg (IEEE float WAV, written by hand: the wave module is PCM only)"""
    data = x.astype("<f4").tobytes()
    hdr = b"RIFF" + (36 + len(data)).to_bytes(4, "little") + b"WAVEfmt " + (16).to_bytes(4, "little")
    hdr += (3).to_bytes(2, "little") + (2).to_bytes(2, "little") + SR.to_bytes(4, "little")
    hdr += (SR * 8).to_bytes(4, "little") + (8).to_bytes(2, "little") + (32).to_bytes(2, "little")
    open(path, "wb").write(hdr + b"data" + len(data).to_bytes(4, "little") + data)


# ---- tonality: Krumhansl-Kessler key profiles over a pitch-class chroma -----------------------------------------
KK_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KK_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
PCS = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def chroma(x):
    m = np.mean(x, axis=1) if x.ndim == 2 else x
    n, hop = 8192, 2048
    if len(m) < n:
        m = np.concatenate([m, np.zeros(n - len(m))])
    win = np.hanning(n)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    sel = (f >= 60) & (f <= 2000)
    pc = (np.round(12 * np.log2(f[sel] / 440.0) + 69).astype(int)) % 12
    acc = np.zeros(12)
    for s in range(0, len(m) - n + 1, hop):
        mag = np.abs(np.fft.rfft(m[s:s + n] * win))[sel]
        np.add.at(acc, pc, mag)
    return acc / (acc.sum() + 1e-12)


def key_of(x):
    """-> (best major corr, best minor corr, 'Key mode')"""
    ch = chroma(x)
    best = {}
    for mode, prof in (("major", KK_MAJ), ("minor", KK_MIN)):
        cs = [float(np.corrcoef(ch, np.roll(prof, k))[0, 1]) for k in range(12)]
        k = int(np.argmax(cs))
        best[mode] = (cs[k], PCS[k])
    mode = "major" if best["major"][0] >= best["minor"][0] else "minor"
    return round(best["major"][0], 3), round(best["minor"][0], 3), "%s %s" % (best[mode][1], mode)


# ---- the measurements + the profile scores --------------------------------------------------------------------
def head_tail(x):
    """-> (start, end) samples of the music: the first frame within 45 dB of the peak, the last within 55 dB"""
    e = env_db(x, 0.005)
    n5 = int(0.005 * SR)
    above = np.where(e > -45)[0]
    tail = np.where(e > -55)[0]
    if above.size == 0:
        return 0, len(x)
    s = max(0, above[0] * n5 - int(0.005 * SR))
    end = min(len(x), (tail[-1] + 1) * n5 + int(0.05 * SR))
    return s, end


def features(x):
    s, e = head_tail(x)
    x = x[s:e]
    dur = len(x) / SR
    if dur < 3.0:
        return None
    t, m = loud_curve(x, 0.4, 0.1)
    pk = float(m.max())
    tpk = float(t[int(np.argmax(m))])
    hit = float(t[np.where(m >= pk - 6)[0][0]])

    def seg_mean(a, b):
        sel = (t >= a) & (t < b)
        return float(10 * np.log10(np.mean(10 ** (m[sel] / 10)))) if sel.any() else -70.0
    third = dur / 3
    first3, last3 = seg_mean(0, third), seg_mean(2 * third, dur)
    open4 = seg_mean(0, min(4.0, dur * 0.3))
    tail = float(np.max(env_db(x, 0.01)[-30:]))           # the loudest 10 ms frame of the last 0.3 s, re the peak frame
    mono = np.mean(x, axis=1)
    hot = (np.abs(x) >= 0.999).any(axis=1).astype(np.int8)
    runs = np.convolve(hot, np.ones(4, dtype=np.int8), "valid") >= 4
    clip = float(np.mean(runs)) if runs.size else 0.0
    spec = np.abs(np.fft.rfft(mono * np.hanning(len(mono))))
    f = np.fft.rfftfreq(len(mono), 1.0 / SR)
    sel = spec[(f > 60) & (f < 12000)] + 1e-12
    flat = float(np.exp(np.mean(np.log(sel))) / np.mean(sel))
    L, R = x[:, 0], x[:, 1]
    corr = float(np.dot(L, R) / (np.sqrt(np.dot(L, L) * np.dot(R, R)) + 1e-12))
    kmaj, kmin, key = key_of(x)
    emaj, emin, ekey = key_of(x[int(2 * third * SR):])      # the ending: what the cue resolves to
    return dict(dur=round(dur, 3), integrated=round(integrated(x), 2), peak_mom=round(pk, 2), peak_at=round(tpk / dur, 3),
                peak_t=round(tpk, 2), hit_t=round(hit, 2), first3=round(first3 - pk, 2), last3=round(last3 - pk, 2),
                open4=round(open4 - pk, 2), tail_db=round(tail, 1), clip=round(clip, 5), flat=round(flat, 4),
                stereo_corr=round(corr, 3), key=key, maj=kmaj, min=kmin, end_key=ekey, end_maj=emaj, end_min=emin)


def score(cue, ft, vocal_db=None):
    if ft is None:
        return -1.0, {"dead": 1.0}
    c = CUES[cue]
    s = {}
    s["length"] = closeness(ft["dur"], c["lo"], c["hi"], 6.0)
    s["clip"] = 1.0 - min(1.0, ft["clip"] * 100)
    s["tonal"] = closeness(ft["flat"], 0.0, 0.35, 0.3)
    if c["profile"] == "fall":
        s["hit"] = closeness(ft["hit_t"], 0.0, 1.2, 2.0)            # the loss lands at once
        s["fall"] = closeness(ft["first3"] - ft["last3"], 6.0, 40.0, 6.0)   # and falls away
        s["peak_at"] = closeness(ft["peak_at"], 0.0, 0.35, 0.3)
        s["ends"] = closeness(ft["tail_db"], -90, -30, 20)            # on silence, not cut off
        s["minor"] = closeness(ft["min"] - ft["maj"], 0.0, 1.0, 0.25)  # it is a defeat
    else:
        s["quiet_open"] = closeness(ft["open4"], -40, -9.0, 8.0)      # under the Dealer's last words
        s["climax"] = closeness(ft["peak_at"], 0.45, 0.92, 0.3)       # the triumph lands late
        s["rise"] = closeness(ft["last3"] - ft["first3"], 6.0, 40.0, 6.0)
        s["ends"] = closeness(ft["tail_db"], -90, -24, 20)
        s["major_end"] = closeness(ft["end_maj"] - ft["end_min"], 0.0, 1.0, 0.25)   # it resolves bright
    if vocal_db is not None:
        s["no_voice"] = closeness(vocal_db, -90, -20, 10)             # a vocal stem 20 dB under the mix is a synth's leak
    return round(float(sum(s.values()) / len(s)), 4), {k: round(v, 3) for k, v in s.items()}


# ---- ElevenLabs -----------------------------------------------------------------------------------------------
def load_json(p, default):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def compose(body):
    """POST /v1/music in the best output format the plan accepts -> (mp3 bytes, format)"""
    import eleven
    err = None
    for fmt in OUTPUT_FORMATS:
        try:
            raw = eleven.call("POST", "/v1/music", body=body, query={"output_format": fmt})
        except RuntimeError as e:
            err = e
            if " 4" in str(e).split("->")[-1][:4] and fmt != OUTPUT_FORMATS[-1]:
                print("  %s refused (%s): trying the next format" % (fmt, str(e)[:160]))
                continue
            raise
        if not isinstance(raw, (bytes, bytearray)) or len(raw) < 1000:
            sys.exit("unexpected response %r" % (raw if not isinstance(raw, (bytes, bytearray)) else len(raw)))
        return raw, fmt
    raise err


def plan_ok(c):
    """the API's own limits on a plan, checked before a call is spent: every text line <= 200 chars, 3-120 s chunks"""
    for ch in c["plan"]:
        for line in ch["text"].split("\n"):
            assert len(line) <= 200, "plan line over 200 characters: %r" % line
        assert 3000 <= ch["duration_ms"] <= 120000, ch["duration_ms"]
    assert len(c["prompt"]) <= 2000


def generate(cues, takes):
    for cue in cues:
        plan_ok(CUES[cue])
    os.makedirs(TAKES_DIR, exist_ok=True)
    data = load_json(TAKES_JSON, {})
    for cue in cues:
        c = CUES[cue]
        rows = data.get(cue, [])
        d = os.path.join(TAKES_DIR, cue)
        os.makedirs(d, exist_ok=True)
        for i in range(len(rows), min(MAX_TAKES, len(rows) + takes)):
            name = "take_%d" % (i + 1)
            if i < 2:                     # takes 1-2: the composition plan (the timeline), a fixed seed per take
                body = dict(composition_plan=dict(chunks=c["plan"]), model_id=MODEL, seed=1103 + 1000 * i)
                how = "plan seed %d" % body["seed"]
            else:                         # take 3: the prompt, instrumental forced (a seed is refused with a prompt)
                body = dict(prompt=c["prompt"], music_length_ms=int(c["secs"] * 1000), model_id=MODEL, force_instrumental=True)
                how = "prompt"
            raw, fmt = compose(body)
            mp3 = os.path.join(d, name + ".mp3")
            open(mp3, "wb").write(raw)
            ft = features(decode(mp3))
            sc, parts = score(cue, ft)
            rows.append(dict(name=name, file=os.path.relpath(mp3, REPO).replace("\\", "/"), how=how, model=MODEL,
                             format=fmt, features=ft, score=sc, parts=parts))
            print("%-9s %s (%s, %s) score %.3f %s" % (cue, name, how, fmt, sc, json.dumps(ft)))
            data[cue] = rows
            json.dump(data, open(TAKES_JSON, "w", encoding="utf-8"), indent=1)
        if len(rows) >= MAX_TAKES:
            print("%-9s %d takes (the cap)" % (cue, len(rows)))
    return data


def vocals(cues, separator):
    """the voice a vocal-stem model finds in each take: its integrated loudness re the take's (dB)"""
    data = load_json(TAKES_JSON, {})
    with tempfile.TemporaryDirectory() as td:
        for cue in cues:
            for r in data.get(cue, []):
                src = os.path.join(REPO, r["file"])
                wav_in = os.path.join(td, "%s_%s.wav" % (cue, r["name"]))
                x = decode(src)
                write_f32_wav(wav_in, x)
                out = os.path.join(td, "out_%s_%s" % (cue, r["name"]))
                os.makedirs(out, exist_ok=True)
                p = run([separator, wav_in, "-m", SEPARATOR_MODEL, "--model_file_dir", SEPARATOR_MODELS_DIR,
                         "--output_dir", out, "--output_format", "WAV", "--single_stem", "Vocals"])
                stems = glob.glob(os.path.join(out, "*Vocals*.wav"))
                if p.returncode != 0 or not stems:
                    print("%-9s %s: separation failed (%s)" % (cue, r["name"], (p.stderr or p.stdout)[-300:]))
                    continue
                v = decode(stems[0])
                r["vocal_db"] = round(integrated(v) - integrated(x), 1)
                r["score"], r["parts"] = score(cue, r["features"], r["vocal_db"])
                print("%-9s %s vocal stem %+.1f dB re the mix -> score %.3f" % (cue, r["name"], r["vocal_db"], r["score"]))
    json.dump(data, open(TAKES_JSON, "w", encoding="utf-8"), indent=1)


def rescore(cues):
    data = load_json(TAKES_JSON, {})
    for cue in cues:
        for r in data.get(cue, []):
            p = os.path.join(REPO, r["file"])
            if os.path.exists(p):
                r["features"] = features(decode(p))
                r["score"], r["parts"] = score(cue, r["features"], r.get("vocal_db"))
        print("%-9s %s" % (cue, "  ".join("%s %.3f %s" % (r["name"], r["score"], r["parts"]) for r in data.get(cue, []))))
    json.dump(data, open(TAKES_JSON, "w", encoding="utf-8"), indent=1)


# ---- the master -----------------------------------------------------------------------------------------------
def drop_file(cue):
    if not os.path.isdir(DROP_DIR):
        return None
    for f in sorted(os.listdir(DROP_DIR)):
        stem, ext = os.path.splitext(f)
        if stem == cue and ext.lower() in (".wav", ".mp3", ".flac", ".ogg"):
            return os.path.join(DROP_DIR, f)
    return None


def choose(cue):
    """-> (kind, path, why) of the source to ship: an override in picks.json ("take_2" or {"take": "take_2", "why":
    "..."}: a judgement the scores cannot make, recorded in the manifest), a dropped file, then the best score"""
    data = load_json(TAKES_JSON, {})
    picks = load_json(PICKS_JSON, {})
    ov = picks.get(cue)
    why = None
    if isinstance(ov, dict):
        ov, why = ov.get("take"), ov.get("why")
    if ov:
        for r in data.get(cue, []):
            if r["name"] == ov:
                return "take", os.path.join(REPO, r["file"]), (why or "picks.json override")
    d = drop_file(cue)
    if d:
        return "drop", d, "a dropped file wins"
    rows = sorted([r for r in data.get(cue, []) if r.get("features")], key=lambda r: -r["score"])
    return ("take", os.path.join(REPO, rows[0]["file"]), "the best score %.3f" % rows[0]["score"]) if rows else (None, None, None)


def master(cue, src):
    """-> (wav bytes, info). The music_master chain on the trimmed take."""
    c = CUES[cue]
    x = decode(src)
    s, e = head_tail(x)
    x = x[s:e]
    if len(x) / SR > c["hi"]:                                  # an over-long take: cut at the ceiling, faded
        x = x[:int(c["hi"] * SR)]
    abrupt = float(np.max(env_db(x, 0.01)[-30:])) > -24
    fout = c["fade"] if abrupt else 0.4
    a, b = int(0.004 * SR), int(fout * SR)
    x = x.copy()
    x[:a] *= np.linspace(0, 1, a)[:, None]
    x[-b:] *= (np.linspace(1, 0, b) ** 2)[:, None]
    tk = c.get("tuck")
    if tk:                                                     # the cue time is the trimmed file's time
        g = np.ones(len(x))
        u, r = int(tk["until"] * SR), int(tk["release"] * SR)
        low = 10 ** (tk["db"] / 20)
        g[:u] = low
        ramp = np.sin(np.linspace(0, np.pi / 2, max(1, r - u))) ** 2   # low -> 1 over until..release
        g[u:r] = low + (1 - low) * ramp[:len(g[u:r])]
        x *= g[:, None]
    from scipy.signal import butter, sosfilt
    x = sosfilt(butter(2, 20, "highpass", fs=SR, output="sos"), x, axis=0)   # DC / rumble
    with tempfile.TemporaryDirectory() as td:
        f0, f1, f2 = (os.path.join(td, n) for n in ("in.wav", "shelf.wav", "out.wav"))
        write_f32_wav(f0, x)
        r = run(["ffmpeg", "-v", "error", "-y", "-i", f0, "-af", "lowshelf=f=%d:g=%s:width_type=q:w=0.7" % (SHELF_HZ, BASS_DB),
                 "-c:a", "pcm_f32le", f1])
        assert r.returncode == 0, r.stderr
        I0, _, tp0 = ebur128(f1)
        gain = c["lufs"] - I0
        work = tp0 + gain - CEIL_DB
        if work > MAX_LIM:                                      # never squash the hit: back the gain off instead
            gain -= work - MAX_LIM
        af = ("volume=%.2fdB,aresample=192000:resampler=soxr:precision=28,"
              "alimiter=limit=%.5f:attack=5:release=200:level=disabled:latency=1,"
              "aresample=48000:resampler=soxr:precision=28:dither_method=triangular_hp") % (gain, 10 ** (CEIL_DB / 20))
        r = run(["ffmpeg", "-v", "error", "-y", "-i", f1, "-af", af, "-ar", "48000", "-sample_fmt", "s16", "-ac", "2",
                 "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", f2])
        assert r.returncode == 0, r.stderr
        with wave.open(f2) as w:
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, 2)
        b = wav_bytes(pcm)                                      # a plain RIFF: no encoder tags, no LIST chunk
        open(f2, "wb").write(b)
        I, lra, tp = ebur128(f2)
    music_secs = len(pcm) / SR
    info = dict(file=c["file"] + ".wav", sha256=sha256(b), secs=round(music_secs, 4), lufs=I, lra=lra, true_peak_db=tp,
                gain_db=round(gain, 2), limiter_db=round(max(0.0, tp0 + gain - CEIL_DB), 2), abrupt_end=bool(abrupt),
                fade_out=fout, vol=c["vol"], looping=False)
    if c.get("tuck"):
        info["tuck"] = c["tuck"]
    if cue == "victory":
        info["hold_secs"] = round(math.ceil((music_secs + HOLD_MARGIN) * 10) / 10, 1)
    return b, info


def patch_csv(root):
    """the two rows into root's tod_ui.csv (after the boss track row), in that file's own line endings; idempotent"""
    p = os.path.join(root, UI_CSV_REL)
    raw = open(p, "rb").read()
    nl = b"\r\n" if b"\r\n" in raw else b"\n"
    lines = raw.split(nl)
    want = [row_text(cue).encode() for cue in ORDER]
    names = {CUES[cue]["file"].encode() + b"," for cue in ORDER}
    kept = [l for l in lines if not any(l.startswith(n) for n in names) or l in want]   # a stale row of ours goes
    missing = [w for w in want if w not in kept]
    if not missing and kept == lines:
        return False
    at = next((i for i, l in enumerate(kept) if l.startswith(ROW_AFTER.encode())), None)
    at = (len(kept) - 1) if at is None else at + 1
    for w in missing:
        kept.insert(at, w)
        at += 1
    open(p, "wb").write(nl.join(kept))
    return True


def pick(cues, root):
    man = load_json(MANIFEST, {})
    out = os.path.join(root, MUSIC_REL)
    os.makedirs(out, exist_ok=True)
    for cue in cues:
        kind, src, why = choose(cue)
        if not src:
            print("%-9s NO SOURCE (generate it, or drop a file in %s)" % (cue, os.path.relpath(DROP_DIR, REPO)))
            continue
        b, info = master(cue, src)
        info["source"] = "%s:%s" % (kind, os.path.relpath(src, REPO).replace("\\", "/"))
        info["why"] = why
        p = os.path.join(out, info["file"])
        if not os.path.exists(p) or open(p, "rb").read() != b:
            open(p, "wb").write(b)
        man[cue] = info
        print("%-9s %-24s %-58s %.2fs  %.1f LUFS  LRA %.1f  TP %.1f  limiter %.1f dB%s" % (
            cue, info["file"], info["source"], info["secs"], info["lufs"], info["lra"], info["true_peak_db"],
            info["limiter_db"], ("  hold %.1fs" % info["hold_secs"]) if "hold_secs" in info else ""))
    json.dump(man, open(MANIFEST, "w", encoding="utf-8"), indent=1)
    if patch_csv(root):
        print("tod_ui.csv: rows written")
    review(root)


# ---- the review set -------------------------------------------------------------------------------------------
NEIGHBOURS = [("tod_fall_intro (the cue precedent)", "sound_assets/tod/music/tod_fall_intro.wav", 0, 30),
              ("tod_boss_music (what the victory replaces)", "sound_assets/tod/music/tod_boss_music.wav", 0, 30),
              ("tod_music_eclipse (a band)", BAND_REL, 0, 30)]


def review(root):
    """desk.html (every take, the shipped files, the neighbours) + loudness.png (the momentary loudness of the shipped
    cues against the neighbours on one scale) + victory_over_death_line.wav and gameover_after_band.wav (what the
    player hears)"""
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(REVIEW_DIR, exist_ok=True)
    man = load_json(MANIFEST, {})
    data = load_json(TAKES_JSON, {})
    # the loudness sheet
    W, H, L, T = 1400, 760, 70, 40
    im = Image.new("RGB", (W, H), (14, 16, 24))
    dr = ImageDraw.Draw(im)
    font = ImageFont.load_default()
    xmax, ylo, yhi = 30.0, -45.0, -3.0
    X = lambda s: L + (W - L - 20) * s / xmax
    Y = lambda v: T + (H - T - 60) * (yhi - max(ylo, min(yhi, v))) / (yhi - ylo)
    for v in range(int(ylo), int(yhi) + 1, 6):
        dr.line([(L, Y(v)), (W - 20, Y(v))], fill=(40, 44, 60))
        dr.text((8, Y(v) - 6), "%d LUFS" % v, fill=(140, 150, 170), font=font)
    for s in range(0, int(xmax) + 1, 2):
        dr.line([(X(s), T), (X(s), H - 60)], fill=(30, 34, 48))
        dr.text((X(s) - 6, H - 52), "%ds" % s, fill=(140, 150, 170), font=font)
    dr.line([(L, Y(-11.5)), (W - 20, Y(-11.5))], fill=(90, 90, 40))
    dr.text((W - 220, Y(-11.5) - 14), "bands' integrated -11.5", fill=(200, 200, 90), font=font)
    curves = []
    for label, rel, a, b in NEIGHBOURS:
        p = os.path.join(REPO, rel)
        if os.path.exists(p):
            curves.append((label, decode(p)[int(a * SR):int(b * SR)], (110, 120, 140)))
    colours = {"gameover": (240, 80, 80), "victory": (90, 220, 255)}
    for cue in ORDER:
        if cue in man:
            p = os.path.join(root, MUSIC_REL, man[cue]["file"])
            if os.path.exists(p):
                curves.append(("SHIPPED " + man[cue]["file"], decode(p), colours[cue]))
    dp = os.path.join(REPO, DEATH_LINE_REL)
    for i, (label, x, col) in enumerate(curves):
        t, m = loud_curve(x, 0.4, 0.1)
        pts = [(X(tt), Y(v)) for tt, v in zip(t, m) if tt <= xmax]
        if len(pts) > 1:
            dr.line(pts, fill=col, width=2 if label.startswith("SHIPPED") else 1)
        dr.text((L + 10, T + 4 + 14 * i), label, fill=col, font=font)
    if "victory" in man and os.path.exists(dp):
        d = decode(dp)
        a = DEATH_LINE_OFFSET
        t, m = loud_curve(d[int(a * SR):], 0.4, 0.1)
        pts = [(X(tt), Y(v)) for tt, v in zip(t, m) if tt <= xmax]
        if len(pts) > 1:
            dr.line(pts, fill=(200, 120, 255), width=1)
        dr.rectangle([X(0), H - 40, X(len(d) / SR - a), H - 30], fill=(200, 120, 255))
        dr.text((X(len(d) / SR - a) + 6, H - 42), "the Dealer's death line still speaking (victory starts ~%.2f s into it)" % a,
                fill=(200, 120, 255), font=font)
        if "hold_secs" in man["victory"]:
            hx = X(man["victory"]["hold_secs"])
            dr.line([(hx, T), (hx, H - 60)], fill=(90, 220, 255))
            dr.text((hx + 4, T + 70), "hold ends: the band", fill=(90, 220, 255), font=font)
    dr.text((L, 8), "PK03 end-of-run music: momentary loudness (0.4 s) of the shipped cues against their neighbours", fill=(230, 230, 240), font=font)
    im.save(os.path.join(REVIEW_DIR, "loudness.png"))
    # the victory under his last words (the line is bus_fx 94, the cue BUS_MUSIC 100: mixed 1:1 here)
    if "victory" in man and os.path.exists(dp):
        v = decode(os.path.join(root, MUSIC_REL, man["victory"]["file"]))
        d = decode(dp)
        off = int(DEATH_LINE_OFFSET * SR)
        n = max(len(v) + off, len(d))
        mix = np.zeros((n, 2))
        mix[:len(d)] += d
        mix[off:off + len(v)] += v
        mix /= max(1.0, np.max(np.abs(mix)) / 0.95)
        open(os.path.join(REVIEW_DIR, "victory_over_death_line.wav"), "wb").write(
            wav_bytes(np.clip(np.round(mix * 32767), -32768, 32767)))
    # the game over as it lands: 6 s of a band, the channel's hard cut, the cue
    bp = os.path.join(REPO, BAND_REL)
    if "gameover" in man and os.path.exists(bp):
        g = decode(os.path.join(root, MUSIC_REL, man["gameover"]["file"]))
        band = decode(bp)[int(60 * SR):int(66 * SR)]
        mix = np.concatenate([band, g])
        mix /= max(1.0, np.max(np.abs(mix)) / 0.95)
        open(os.path.join(REVIEW_DIR, "gameover_after_band.wav"), "wb").write(
            wav_bytes(np.clip(np.round(mix * 32767), -32768, 32767)))
    # the desk
    h = ["<!doctype html><meta charset=utf-8><title>PK03 end-of-run music desk</title>",
         "<style>body{font:14px system-ui;background:#101218;color:#dde;margin:24px;max-width:1200px}h2{color:#9ef;margin-top:28px}"
         "td{padding:4px 10px;border-bottom:1px solid #2a2e3a;vertical-align:top}.pick{color:#6f6;font-weight:bold}code{color:#fc8}"
         "audio{height:30px;width:320px}img{max-width:100%;border:1px solid #333}</style>",
         "<h1>End-of-run music: the takes, the picks, the neighbours</h1>",
         "<p>Override a pick: <code>tmp/asset_prod/%s/takes/picks.json</code> = <code>{\"victory\": \"take_2\"}</code>, then "
         "<code>python tools/sfx/end_of_run_music/make_sounds.py pick --out-root &lt;root&gt;</code> (and copy the new "
         "<code>hold_secs</code> into TOD_HOUSE_VICTORY_SECS). A file dropped as <code>takes/drop/&lt;cue&gt;.wav</code> wins.</p>" % PACK,
         "<img src='loudness.png'>"]
    for f, title in (("victory_over_death_line.wav", "In context: the victory under the Dealer's death line"),
                     ("gameover_after_band.wav", "In context: a band, the game-over cut, the loss cue")):
        if os.path.exists(os.path.join(REVIEW_DIR, f)):
            h.append("<h2>%s</h2><audio controls src='%s'></audio>" % (title, f))
    for cue in ORDER:
        c = CUES[cue]
        h.append("<h2>%s <small>(%s, NONLOOPING, plays once)</small></h2><p><i>%s</i></p><table>" % (
            c["file"], c["profile"], html.escape(c["prompt"])))
        if cue in man:
            f = man[cue]
            rel = os.path.relpath(os.path.join(root, MUSIC_REL, f["file"]), REVIEW_DIR).replace("\\", "/")
            h.append("<tr><td class=pick>SHIPPED</td><td>%s<br><small>%.2f s  %.1f LUFS  LRA %.1f  TP %.1f%s<br>why: %s</small></td>"
                     "<td><audio controls src='%s'></audio></td></tr>" % (html.escape(f["source"]), f["secs"], f["lufs"],
                     f["lra"], f["true_peak_db"], ("  hold %.1f s" % f["hold_secs"]) if "hold_secs" in f else "",
                     html.escape(f.get("why") or ""), rel))
        for r in data.get(cue, []):
            rel = os.path.relpath(os.path.join(REPO, r["file"]), REVIEW_DIR).replace("\\", "/")
            mark = "pick" if cue in man and r["file"] in man[cue]["source"] else ""
            h.append("<tr><td class='%s'>%s</td><td>%s - score %.3f%s<br><small>%s<br>%s</small></td><td><audio controls src='%s'></audio></td></tr>"
                     % (mark, r["name"], html.escape(r.get("how", "")), r["score"],
                        (" - vocal stem %+.1f dB" % r["vocal_db"]) if "vocal_db" in r else "",
                        html.escape(json.dumps(r["parts"])), html.escape(json.dumps(r["features"])), rel))
        h.append("</table>")
    h.append("<h2>Neighbours</h2><table>")
    for label, rel, a, b in NEIGHBOURS:
        h.append("<tr><td>%s</td><td><audio controls src='%s'></audio></td></tr>" % (html.escape(label),
                 os.path.relpath(os.path.join(REPO, rel), REVIEW_DIR).replace("\\", "/")))
    h.append("<tr><td>tod_house_vo_death (his last words)</td><td><audio controls src='%s'></audio></td></tr></table>" %
             os.path.relpath(os.path.join(REPO, DEATH_LINE_REL), REVIEW_DIR).replace("\\", "/"))
    open(os.path.join(REVIEW_DIR, "desk.html"), "w", encoding="utf-8").write("\n".join(h))
    print("review:", os.path.relpath(REVIEW_DIR, REPO))


# ---- the gate -------------------------------------------------------------------------------------------------
def check(root):
    bad = []
    man = load_json(MANIFEST, None)
    if not man:
        bad.append("no manifest")
        man = {}
    for cue in ORDER:
        c = CUES[cue]
        if cue not in man:
            bad.append("cue %s not shipped" % cue)
            continue
        f = man[cue]
        p = at_root(root, os.path.join(MUSIC_REL, f["file"]))
        if not os.path.exists(p):
            bad.append("missing %s" % f["file"])
            continue
        b = open(p, "rb").read()
        if sha256(b) != f["sha256"]:
            bad.append("changed %s" % f["file"])
        try:
            with wave.open(io.BytesIO(b)) as w:
                if w.getnchannels() != 2 or w.getframerate() != SR or w.getsampwidth() != 2:
                    bad.append("%s is not stereo 48 kHz 16-bit" % f["file"])
                secs = w.getnframes() / float(SR)
                if not (c["lo"] - 0.5 <= secs <= c["hi"] + 0.5):
                    bad.append("%s length %.2fs outside %.0f-%.0f" % (f["file"], secs, c["lo"], c["hi"]))
        except wave.Error as e:
            bad.append("%s unreadable: %s" % (f["file"], e))
    if "victory" in man and not (man["victory"]["secs"] < man["victory"].get("hold_secs", 0) <= man["victory"]["secs"] + 1.0):
        bad.append("the victory's hold %.1fs does not cover its music %.2fs" % (man["victory"].get("hold_secs", 0), man["victory"]["secs"]))
    try:
        csv_lines = open(at_root(root, UI_CSV_REL), encoding="utf-8").read().splitlines()
        if csv_lines and len(csv_lines[0].split(",")) != HEADER_COLS:
            bad.append("tod_ui.csv header is not %d columns (the row template must follow it)" % HEADER_COLS)
        for cue in ORDER:
            if len(row_text(cue).split(",")) != HEADER_COLS:
                bad.append("the %s row template is not %d columns" % (cue, HEADER_COLS))
            if row_text(cue) not in csv_lines:
                bad.append("tod_ui.csv lacks the %s row this tool writes" % CUES[cue]["file"])
            if sum(1 for l in csv_lines if l.startswith(CUES[cue]["file"] + ",")) != 1:
                bad.append("tod_ui.csv must define %s exactly once" % CUES[cue]["file"])
    except OSError:
        bad.append("tod_ui.csv unreadable")
    try:
        if not re.search(r'"Filename"\s*:\s*"tod_ui\.csv"', open(at_root(root, SZC_REL), encoding="utf-8").read()):
            bad.append("tod_ui.csv not loaded by the sound zone config")
    except OSError:
        bad.append("szc unreadable")
    try:
        atmo = open(at_root(root, ATMO_REL), encoding="utf-8").read()
        if not re.search(r'^#define TOD_MUSIC_GAMEOVER_ALIAS\s+"tod_music_gameover"', atmo, re.M):
            bad.append("_tod_atmosphere.gsc does not name tod_music_gameover")
        if not re.search(r'^#define TOD_HOUSE_VICTORY_ALIAS\s+"tod_house_victory"', atmo, re.M):
            bad.append("_tod_atmosphere.gsc does not name tod_house_victory")
        if not re.search(r"^\s*level\.sndPlayStateOverride = &snd_play_state_override;", atmo, re.M):
            bad.append("_tod_atmosphere.gsc does not take the stock game_over music state (two game-over cues)")
        if not re.search(r"^\s*gameover_play\(\);", atmo, re.M):
            bad.append("_tod_atmosphere.gsc's music_end_watch does not play the loss cue")
        m = re.search(r"^#define TOD_HOUSE_VICTORY_SECS\s+([\d.]+)", atmo, re.M)
        if not m:
            bad.append("_tod_atmosphere.gsc has no TOD_HOUSE_VICTORY_SECS")
        elif "victory" in man and abs(float(m.group(1)) - man["victory"].get("hold_secs", -1)) > 1e-6:
            bad.append("LOCKSTEP TOD_HOUSE_VICTORY_SECS %s != the shipped cue's hold %.1f" % (m.group(1), man["victory"].get("hold_secs", -1)))
    except OSError:
        bad.append("_tod_atmosphere.gsc unreadable")
    try:
        if "tod_atmosphere::house_victory_start()" not in open(at_root(root, ARENA_REL), encoding="utf-8").read():
            bad.append("_tod_arena.gsc does not start the victory cue")
    except OSError:
        bad.append("_tod_arena.gsc unreadable")
    if bad:
        print("END-OF-RUN MUSIC STALE: " + "; ".join(bad[:8]) + " - run: python tools/sfx/end_of_run_music/make_sounds.py pick")
        sys.exit(1)
    print("END-OF-RUN MUSIC OK: %s" % ", ".join("%s %.1fs %.1f LUFS" % (man[c]["file"], man[c]["secs"], man[c]["lufs"]) for c in ORDER))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="")
    ap.add_argument("--cue", action="append")
    ap.add_argument("--takes", type=int, default=MAX_TAKES)
    ap.add_argument("--out-root", default=REPO)
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--separator", default=os.environ.get("TOD_SEPARATOR", ""))
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
    elif a.cmd == "vocals":
        if not a.separator or not (os.path.exists(a.separator) or shutil.which(a.separator)):
            sys.exit("vocals needs --separator <audio-separator executable> (or TOD_SEPARATOR)")
        vocals(cues, a.separator)
    elif a.cmd == "rescore":
        rescore(cues)
    elif a.cmd == "pick":
        pick(cues, os.path.abspath(a.out_root))
    elif a.cmd == "review":
        review(os.path.abspath(a.out_root))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
