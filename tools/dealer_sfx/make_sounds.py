"""THE DEALER FIGHT'S SOUNDS + THE ARENA / HOUSE CUES (W2B, asset packs PK10 + PK16, 2026-10-05).

ONE pipeline for three sets of cues, every one MADE for its moment (ElevenLabs), measured, scored, levelled and pinned:

  * THE DEALER (PK10, docs/199): his scythe swings and hits, his attack efforts (in HIS OWN voice through the shipping
    mask, never a borrowed one), the state-two gun bashes and heavy steps, the bamf out / in, his arrival rift, the MASK
    CRACK, his death, and the levitation hum under state one. Written to sound_assets/tod/dealer/ with the alias table
    sound/aliases/tod_dealer.csv REGENERATED whole by this tool (3D rows, BUS_FX, no sound context, variants as repeated
    rows). The note remap in tools/dealer_boss/install.py points his clips' Sound notes at these aliases; the scripted
    beats (spawn, crack, death, hits, the hum) play them from _tod_dealer_finale.gsc.
  * THE BATTLE ARENA (PK16, docs/185): the wave horn, the wave clear, the level fanfare, the gate. They REPLACE the
    synthesised stand-ins of tools/battle_arena/make_sounds.py BY NAME (same files, same alias rows); that generator's
    --check now reads tools/battle_arena/authored_sounds.json (written here) for a cue that is authored, and still
    byte-checks a fresh render for any cue that is not.
  * THE DEALER'S HOUSE (PK16, docs/207): the cursed last roll, the drain drone (exactly 6.5 s), the drain bite. Same lane:
    tools/dealer_house/authored_sounds.json.

THE PIPELINE (the tools/ability_fx/make_sounds.py pattern, docs/206):
  generate  ElevenLabs /v1/sound-generation (eleven_text_to_sound_v2, lossless pcm_48000) - or for a "voice" cue the
            Dealer's own saved TTS voice (tmp/black_market_vo/voice.json) speaking efforts - TAKES per cue into
            tmp/dealer_sfx/takes/<cue>/; every take is MEASURED (onset, peak position, decay, tail, flat-top clipping,
            low / high share, tonality, and for the musical cues the NOTES: stable pitched segments and their direction)
            and SCORED against the cue's profile. "reverse" shaping turns an impact-first take into a rise.
  pick      the best-scored take per variant (or the user's override in tmp/dealer_sfx/picks.json) is trimmed, DC-blocked,
            faded, shaped (a loop is cross-faded seamless; an exact-length cue is fitted), levelled to the cue's BS.1770
            target under a soft limiter at -1.5 dBFS and written mono 48 kHz 16-bit. The manifests record the sha256,
            the source take, the prompt, the measured loudness and length.
  desk      tmp/dealer_sfx/desk.html: every take, its score, the pick - so an ear can overrule the measurement.
  --check   the build gate: no API, no DSP. Every manifest file present with its sha, mono 48 kHz 16-bit, its length in
            the cue's window; tod_dealer.csv exactly as this tool writes it; the authored arena / house manifests match
            their wavs. (The zone config loading tod_dealer.csv is the lander's WIRING; --check reports it.)

  python tools/dealer_sfx/make_sounds.py generate [--cue NAME] [--takes N]
  python tools/dealer_sfx/make_sounds.py rescore  [--cue NAME]
  python tools/dealer_sfx/make_sounds.py pick     [--cue NAME] [--root DIR]
  python tools/dealer_sfx/make_sounds.py desk
  python tools/dealer_sfx/make_sounds.py --check  [--root DIR]

--root DIR writes / checks a tree laid out like the repo (the W2B stage, a scratch mirror); the default is the repo.
The key is ELEVENLABS_API_KEY (tools/black_market_vo/eleven.py: never printed, never stored). Takes stay in tmp/.
"""
import argparse, csv, hashlib, io, json, os, re, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "tools", "black_market_vo"))

SR = 48000
PEAK_DB = -1.5                       # PK10 / PK16: every cue peaks at -1.5 dBFS
WORK = os.path.join(REPO, "tmp", "dealer_sfx")
TAKES_DIR = os.path.join(WORK, "takes")
TAKES_JSON = os.path.join(WORK, "takes.json")
PICKS_JSON = os.path.join(WORK, "picks.json")     # the ear's overrides: {cue: ["take_3", "take_1", ...]}
DESK = os.path.join(WORK, "desk.html")
MODEL = "eleven_text_to_sound_v2"
PROMPT_INFLUENCE = 0.62
DEFAULT_TAKES = 4
FIX = "run: python tools/dealer_sfx/make_sounds.py pick"

# the three sets: where the wavs go, the FileSpec folder, the manifest that pins them
GROUPS = {
    "dealer": dict(wav_dir=("sound_assets", "tod", "dealer"), rel="tod\\dealer\\", manifest=("tools", "dealer_sfx", "sounds_manifest.json")),
    "arena":  dict(wav_dir=("sound_assets", "tod", "arena"),  rel="tod\\arena\\",  manifest=("tools", "battle_arena", "authored_sounds.json")),
    "house":  dict(wav_dir=("sound_assets", "tod", "house"),  rel="tod\\house\\",  manifest=("tools", "dealer_house", "authored_sounds.json")),
}
CSV_REL = ("sound", "aliases", "tod_dealer.csv")
HEADER_FROM = ("sound", "aliases", "tod_ui.csv")
SZC_REL = ("sound", "zoneconfig", "zm_tod2_cybercity.szc")

# ---- THE CUES --------------------------------------------------------------------------------------------------
# stem: the wav + alias name (variants get _2, _3 ...); profile: the scoring shape; secs: what ElevenLabs is asked for;
# keep: (min, max) seconds of the shipped file (the gate's window); exact: a cue fitted to this length;
# lufs: the BS.1770 target (the arena / house cues keep the measured loudness of the stand-in they replace, so the
# mix does not move); row: the alias row (3d / 2d / loop + vol, dist, pitch cents, probability) - dealer group only;
# prompts: alternated per take. voice = efforts in the Dealer's own saved voice (the shipping mask applied).
CUES = {
    # ---- THE DEALER, state one: the levitating scythe -------------------------------------------------------------
    "scythe_swing": dict(group="dealer", stem="tod_dealer_scythe_swing", variants=4, profile="whoosh", secs=0.7, keep=(0.32, 0.95), lufs=-16.0,
        row=dict(pan="3d", vol=92, dist=(200, 2400), pitch=80),
        prompts=["a huge heavy curved steel scythe blade swung hard through the air, one deep fast whoosh that ends in a thin bright metallic ring, close, dry, no impact, no music, no voice",
                 "a single brutal swing of a giant reaper's scythe cutting the air, a heavy rushing whoosh with a cold blade shimmer, dry cinematic sound effect, no hit, no music",
                 "a long dark scythe blade whipping past the ear, a weighty swoosh with a faint ringing steel tail, dry, no impact, no music, no voice"]),
    "scythe_hit": dict(group="dealer", stem="tod_dealer_scythe_hit", variants=3, profile="impact", secs=0.6, keep=(0.22, 0.75), lufs=-15.0,
        row=dict(pan="3d", vol=94, dist=(200, 2400), pitch=60),
        prompts=["a sharp scythe blade slicing into a body: a fast wet cut with a short metallic scrape, close and punchy, no music, no voice",
                 "a heavy steel blade striking flesh and armor, a quick brutal slash impact with a gritty metal edge, dry, no music, no voice"]),
    "attack_vox": dict(group="dealer", stem="tod_dealer_attack_vox", variants=3, profile="vocal", secs=0.9, keep=(0.3, 1.25), lufs=-16.0, kind="voice",
        row=dict(pan="3d", vol=90, dist=(300, 3500), pitch=40, prob=0.65),
        texts=["[growls] Hhhah!", "[grunts] Hngh!", "[snarls] Rrrah!", "[growls] Hhrrah!", "[grunts] Hah!"]),
    # ---- THE DEALER, state two: the cracked mask on foot with the gun ---------------------------------------------
    "bash": dict(group="dealer", stem="tod_dealer_bash", variants=3, profile="whoosh", secs=0.6, keep=(0.3, 0.85), lufs=-16.0,
        row=dict(pan="3d", vol=90, dist=(200, 2200), pitch=80),
        prompts=["a heavy machine gun swung like a club, a fast blunt whoosh with metal parts and a sling chain rattling, dry, no gunshot, no impact, no music",
                 "a brutal rifle butt swing through the air, a heavy short whoosh with a gun's metal clattering, close, no shot, no music, no voice"]),
    # a state-two blow that LANDS (dealer_hit_cb): the gun's stock is blunt, so it never rings like the scythe's blade
    "bash_hit": dict(group="dealer", stem="tod_dealer_bash_hit", variants=3, profile="impact", secs=0.6, keep=(0.22, 0.75), lufs=-15.0,
        row=dict(pan="3d", vol=94, dist=(200, 2400), pitch=60),
        prompts=["a heavy steel machine gun stock slammed hard into a body: one deep blunt thud with a short rattle of loose metal parts, close and punchy, no gunshot, no blade, no music, no voice",
                 "a brutal rifle butt strike to the chest: a dull heavy body impact with a hard metallic clank, dry, no shot, no slicing, no music, no voice",
                 "a gun used as a club hitting armor: a crunching blunt impact and a gritty metal knock, short and powerful, no gunshot, no music, no voice"]),
    "step": dict(group="dealer", stem="tod_dealer_step", variants=4, profile="step", secs=0.5, keep=(0.12, 0.6), lufs=-22.0,
        row=dict(pan="3d", vol=82, dist=(100, 1400), pitch=60),
        prompts=["one single heavy boot footstep on a metal grating floor, a weighty thud with a short metallic clank, close, dry, no music",
                 "one heavy leather boot stomping on steel, a solid low footstep with a small chain jingle, dry, no music, no voice"]),
    # ---- THE DEALER: the bamf, the rift, the crack, the death, the hum --------------------------------------------
    "bamf_out": dict(group="dealer", stem="tod_dealer_bamf_out", variants=1, profile="fade", secs=1.1, keep=(0.6, 1.4), lufs=-14.0,
        row=dict(pan="3d", vol=94, dist=(300, 4000), pitch=0),
        prompts=["a dark demon vanishing in black smoke: a sharp deep whoomp and an inward rush of air sucked into nothing, with dying embers, no music, no voice",
                 "a supernatural teleport out, a heavy bass whoosh imploding into silence with a crackle of red sparks, dark, no music"]),
    "bamf_in": dict(group="dealer", stem="tod_dealer_bamf_in", variants=1, profile="burst", secs=1.1, keep=(0.6, 1.4), lufs=-14.0,
        row=dict(pan="3d", vol=94, dist=(300, 4000), pitch=0),
        prompts=["a dark demon bursting out of a black smoke rift: a deep whoosh slamming into a heavy bass thump with crackling red embers, no music, no voice",
                 "a sinister figure teleporting in, a sharp bassy boom of displaced air with a hiss of black smoke and sparks, no music"]),
    "spawn": dict(group="dealer", stem="tod_dealer_spawn", variants=1, profile="rift", secs=2.0, keep=(1.3, 2.4), lufs=-12.5,
        row=dict(pan="3d", vol=100, dist=(400, 6500), pitch=0),
        prompts=["a dimensional rift tearing open in reality: a deep ripping tear, a low dark synthetic choir swelling under it, and a heavy sub bass boom, evil, cinematic, no music melody, no words",
                 "a portal to hell ripping open: a rising tearing roar of torn space with a dark electronic choir pad and a deep impact boom at the peak, horror, no words"]),
    "mask_crack": dict(group="dealer", stem="tod_dealer_mask_crack", variants=1, profile="shatter", secs=1.4, keep=(0.8, 1.7), lufs=-11.5,
        row=dict(pan="3d", vol=100, dist=(400, 6500), pitch=0),
        prompts=["a hard ceramic mask cracking apart with one loud sharp crack, then electrical sparks shorting out and a brief distorted inhuman shriek, horror, no music, no words",
                 "a cyborg's face plate splitting with a violent crack and glass shards, a burst of electric arcing and a short glitching robotic scream, no music, no words"]),
    "death": dict(group="dealer", stem="tod_dealer_death", variants=1, profile="collapse", secs=2.8, keep=(1.8, 3.3), lufs=-12.0,
        duck_after=(1.0, -8.0),          # his last words start 1.0 s in (_tod_house on_death): the rumble eases under them
        row=dict(pan="3d", vol=100, dist=(400, 6500), pitch=0),
        prompts=["a demonic machine dying: a short distorted inhuman scream that breaks into digital glitch stutters and collapses into a deep fading rumble, horror, no music, no words",
                 "a cursed cyborg entity collapsing: a glitching electronic shriek stuttering apart, then a heavy implosion and a long low dying rumble, no music, no words",
                 "one short distorted demonic shriek lasting under a second, glitching and stuttering as it breaks apart, then a deep rumble that fades away to complete silence, no music, no words",
                 "an evil cyborg's death: a brief electronic scream cut into digital stutters, a hollow implosion, and a low dying rumble that grows quieter and quieter until silence, no music, no words"]),
    "levitate_lp": dict(group="dealer", stem="tod_dealer_levitate_lp", variants=1, profile="loop", secs=4.0, keep=(2.0, 4.0), lufs=-24.0, loop_secs=3.5, xfade=0.5,
        row=dict(pan="loop", vol=72, dist=(60, 900), pitch=0),
        prompts=["a low dark ominous hovering hum, a deep resonant supernatural drone with a faint cold breath of wind, steady and seamless, no music, no voice",
                 "the steady low hum of a levitating evil entity, a deep throbbing dark energy drone, smooth and continuous, no music, no voice"]),
    # ---- THE BATTLE ARENA (replaces tools/battle_arena/make_sounds.py's stand-ins BY NAME) --------------------------
    "arena_wave": dict(group="arena", stem="tod_arena_wave", variants=1, profile="horn", secs=2.0, keep=(1.5, 2.3), lufs=-16.5,
        # COMPOSED (no single take is a swell INTO a hit: the horns sustain, the booms hit first): the horn take swelling in
        # over 0.4 s with the war-drum boom take landing on its crest
        layers=[dict(take="take_1", fin=0.40, fout=0.25), dict(take="take_2", at=0.45, gain=-1.0, fout=0.3)],
        prompts=["an epic arena battle horn: a low brass horn swelling up for half a second and ending on one huge deep war drum hit, short, cinematic, no melody, no voice",
                 "a gladiator arena call to battle: a deep brass horn blast rising into a massive taiko drum boom, short and powerful, no voice"]),
    "arena_clear": dict(group="arena", stem="tod_arena_clear", variants=1, profile="bell", secs=1.5, keep=(1.0, 1.7), lufs=-16.3,
        # COMPOSED (every take is ONE strike): the bell take struck, then the same bell a fifth higher (x1.5) 170 ms later,
        # louder - the stand-in's E5 -> B5 shape in a real bell
        layers=[dict(take="take_3", gain=-3.0, fout=0.2), dict(take="take_3", at=0.17, rate=1.5, fout=0.2)],
        prompts=["two bright bell chimes, the second one higher in pitch, with a short shimmering sparkle tail, a clean victory notification, no music, no voice",
                 "a short two-note rising glockenspiel chime with a glittering shimmer, a wave cleared reward sound, no voice",
                 "ding then a higher ding: two clear tuned bell notes a fifth apart, the second rings out with a soft sparkle, short and clean, no voice"]),
    "arena_level": dict(group="arena", stem="tod_arena_level", variants=1, profile="fanfare", secs=3.0, keep=(2.3, 3.2), lufs=-15.5,
        prompts=["a short triumphant brass fanfare: three quick rising notes and a final held note, with a deep sub boom under the last note and a crystal shimmer tail, victory, no voice",
                 "a heroic three-note trumpet fanfare ending on a long bright held chord with a timpani hit and a sparkling tail, short level complete sting, no voice"]),
    "arena_gate": dict(group="arena", stem="tod_arena_gate", variants=1, profile="machine", secs=1.8, keep=(1.3, 2.1), lufs=-19.3,
        prompts=["a heavy metal security gate unlocking: a sharp latch clack and a metal ring, a rising electric motor whine, then one heavy metal clank as it opens, industrial sci-fi, no music",
                 "a sci-fi blast door releasing: a mechanical latch snap, an electric servo whine rising in pitch, ending in a deep heavy clunk, no music, no voice"]),
    # ---- THE DEALER'S HOUSE (replaces tools/dealer_house/make_sounds.py's stand-ins BY NAME) -----------------------
    "house_cursed": dict(group="house", stem="tod_house_cursed", variants=1, profile="cursed", secs=1.8, keep=(1.3, 2.0), lufs=-17.3,
        # COMPOSED: the reversed swell sucked into its dead stop (take 4, cut at the stop) and the crack with its falling,
        # dying tone (take 2) landing on the stop
        layers=[dict(take="take_4", seg=(0.0, 0.88), fout=0.01), dict(take="take_2", at=0.82, gain=-1.0, fout=0.25)],
        prompts=["a cursed evil sting: a sour reversed swell sucked into a dead heavy thud, a glass crack, and a low tone falling in pitch, horror, no music melody, no voice",
                 "a bad luck curse stinger: an eerie reverse whoosh into a dull dead impact with a cracking glass and a dark descending drone, no voice"]),
    "house_drain": dict(group="house", stem="tod_house_drain", variants=1, profile="drone", secs=7.0, exact=6.5, keep=(6.49, 6.51), lufs=-17.7,
        # COMPOSED: the drone bed (take 7, its own two thumps ducked out) rising 14 dB over the drain, under a HEARTBEAT that
        # quickens beat by beat (take 7's own thump, 0.85 s apart to 0.30 s, each a little louder) - the stand-in's design
        layers=[dict(take="take_7", ducks=[(1.95, 2.55, -14.0), (4.45, 5.05, -14.0)], ramp=(-14.0, 0.0), gain=-4.0),
                dict(take="take_7", seg=(1.98, 2.48), fout=0.08,
                     at=[0.40, 1.25, 2.02, 2.70, 3.30, 3.84, 4.32, 4.76, 5.16, 5.52, 5.85, 6.15],
                     gains=[-10.0, -9.0, -8.0, -7.0, -6.0, -5.0, -4.0, -3.0, -2.0, -1.5, -1.0, 0.0])],
        prompts=["life being drained out of you: a low dark drone slowly rising in pitch with a heartbeat underneath that keeps getting faster, horror, no music melody, no voice",
                 "a sinister draining drone building slowly, a deep throbbing heartbeat quickening as the tension rises, dark and claustrophobic, no music, no voice",
                 "a continuous low dark drone that starts very quiet and grows steadily louder and higher for the whole length, never fading, with a deep heartbeat thumping underneath that gets faster and faster until the very end, horror, no music, no voice",
                 "an unbroken crescendo of dread: a deep droning hum swelling louder every second, a pounding heartbeat accelerating from slow to frantic, it ends at its loudest, no music, no voice"]),
    "house_cut": dict(group="house", stem="tod_house_cut", variants=1, profile="bite", secs=0.5, keep=(0.25, 0.55), lufs=-15.0,
        # COMPOSED: the dark thump (take 1) with the first 0.2 s of an electric snap over it (take 4) - a bite, not a zap
        layers=[dict(take="take_1", fout=0.06), dict(take="take_4", seg=(0.0, 0.2), gain=-8.0, fout=0.05)],
        prompts=["a short dark electrical bite: a quick zap with a falling pitch and a dull thump, a chunk of health torn away, no music, no voice",
                 "a brief sinister energy snap, an electric crackle that drops in pitch and stops, dark, no music, no voice"]),
}
ORDER = list(CUES.keys())

# the dealer alias rows: BUS_FX, no sound context (lint_tod_sound_context.js), UIN_MOD template (the house / arena rows'
# shape), one row per variant under ONE name (the engine picks a variant), PitchMin/Max in cents
def dealer_rows(header, man):
    col = {h: i for i, h in enumerate(header)}
    out = []
    for cue in ORDER:
        spec = CUES[cue]
        if spec["group"] != "dealer" or cue not in man:
            continue
        r0 = spec["row"]
        for f in man[cue]["files"]:
            r = [""] * len(header)
            r[col["Name"]] = spec["stem"]
            r[col["FileSpec"]] = GROUPS["dealer"]["rel"] + f["file"]
            r[col["Template"]] = "UIN_MOD"
            r[col["VolMin"]] = r[col["VolMax"]] = str(r0["vol"])
            r[col["Bus"]] = "BUS_FX"
            r[col["DistMin"]], r[col["DistMaxDry"]], r[col["DistMaxWet"]] = str(r0["dist"][0]), str(r0["dist"][1]), str(int(r0["dist"][1] * 1.15))
            r[col["PitchMin"]], r[col["PitchMax"]] = str(-r0["pitch"]), str(r0["pitch"])
            r[col["PanType"]] = "3d"
            r[col["Looping"]] = "LOOPING" if r0["pan"] == "loop" else "NONLOOPING"
            if r0["pan"] == "loop":
                # the hum dies WITH HIM on every exit path, not only the two the script stops it on (the crack, the death):
                # the shape of this map's other entity loops (tod_jt_jet, tod_jump_wind, hb_caliburn_idle)
                r[col["StopOnEntDeath"]] = "yes"
            if r0.get("prob") is not None:
                r[col["Probability"]] = "%g" % r0["prob"]
            if len(man[cue]["files"]) > 1:
                r[col["RandomizeType"]] = "variant"
            assert not any(c in v for v in r for c in ',"\r\n'), cue + ": a field would need csv quoting"
            out.append(",".join(r))
    return out


# ---- audio helpers ------------------------------------------------------------------------------------------------
def decode(path):
    """a take (.pcm = ElevenLabs pcm_48000, stereo s16le; anything else through ffmpeg) -> mono float64 at SR"""
    if path.endswith(".pcm"):
        x = np.frombuffer(open(path, "rb").read(), dtype="<i2").astype(np.float64) / 32768.0
        meta = path[:-4] + ".json"
        ch = json.load(open(meta)).get("channels", 2) if os.path.exists(meta) else 2
        if ch == 2 and len(x) % 2 == 0:
            x = 0.5 * (x[0::2] + x[1::2])
        return x
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype="<f4").astype(np.float64)


def lufs(x):
    """BS.1770-4 integrated loudness, mono 48 kHz; a cue shorter than a 400 ms block is measured on one zero-padded block"""
    from scipy.signal import lfilter
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], x)
    y = lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    if len(y) < blk:
        return float(-0.691 + 10 * np.log10(np.mean(y ** 2) + 1e-20))   # a short bite: its own mean power
    ms = np.array([np.mean(y[i:i + blk] ** 2) for i in range(0, len(y) - blk + 1, hop)])
    l = -0.691 + 10 * np.log10(ms + 1e-20)
    ms = ms[l > -70]
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
    return 20 * np.log10(np.maximum(v, 1e-9))


def trim(x, head_db=-48.0, tail_db=-54.0, pre=0.004, post=0.06):
    e = envelope(x, 0.005)
    pk = e.max()
    if pk <= 1e-6:
        return x
    above = np.where(db(e / pk) > head_db)[0]
    tail = np.where(db(e / pk) > tail_db)[0]
    n5 = int(0.005 * SR)
    start = max(0, above[0] * n5 - int(pre * SR))
    end = min(len(x), (tail[-1] + 1) * n5 + int(post * SR))
    return x[start:end]


def dc_block(x):
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    return np.fft.irfft(np.fft.rfft(x) * (f >= 24), len(x))


def fades(x, fin, fout):
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if 0 < a < len(x):
        x[:a] *= np.linspace(0, 1, a)
    if 0 < b < len(x):
        x[-b:] *= np.linspace(1, 0, b) ** 2
    return x


def limit(y, ceil):
    """a soft knee that is the IDENTITY below 70 % of the ceiling and bends smoothly into it above (never past it)"""
    k = 0.7 * ceil
    a = np.abs(y)
    over = a > k
    out = y.copy()
    out[over] = np.sign(y[over]) * (k + (ceil - k) * np.tanh((a[over] - k) / (ceil - k)))
    return out


def level_to(x, target, max_squash_db=6.0):
    """gain onto the BS.1770 target under the -1.5 dBFS ceiling: gain, soft-limit, re-measure, correct (a few passes);
    a transient that would need more than max_squash_db of peak reduction to get there stays a little under target"""
    ceil = 10 ** (PEAK_DB / 20)
    g = 10 ** ((target - lufs(x)) / 20)
    y = limit(x * g, ceil)
    for _ in range(4):
        err = target - lufs(y)
        if abs(err) < 0.05:
            break
        g2 = g * 10 ** (err / 20)
        if 20 * np.log10(np.max(np.abs(x)) * g2 / ceil + 1e-12) > max_squash_db:
            g2 = ceil * 10 ** (max_squash_db / 20) / (np.max(np.abs(x)) + 1e-12)
            y = limit(x * g2, ceil)
            break
        g = g2
        y = limit(x * g, ceil)
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


# ---- measurement ---------------------------------------------------------------------------------------------------
def notes(x):
    """the stable pitched segments of a take: [(t_start, t_end, f0_hz)], a frame's pitch = its strongest spectral peak in
    120..4000 Hz when the frame is tonal (peak >= 8x the band median) and within 24 dB of the loudest frame"""
    n, hop = 4096, 1024
    if len(x) < n:
        return []
    win = np.hanning(n)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    band = (f >= 120) & (f <= 4000)
    frames = []
    for s in range(0, len(x) - n, hop):
        sp = np.abs(np.fft.rfft(x[s:s + n] * win))[band]
        frames.append((s / SR, float(f[band][np.argmax(sp)]), float(sp.max()), float(np.median(sp) + 1e-12)))
    loud = max(fr[2] for fr in frames)
    segs, cur = [], None
    for t, f0, pk, med in frames:
        tonal = pk >= 8 * med and pk >= loud * 10 ** (-24 / 20)
        if tonal and cur and abs(f0 / cur[2] - 1) < 0.04:
            cur[1] = t + hop / SR
        else:
            if cur and cur[1] - cur[0] >= 0.06:
                segs.append(tuple(cur))
            cur = [t, t + hop / SR, f0] if tonal else None
    if cur and cur[1] - cur[0] >= 0.06:
        segs.append(tuple(cur))
    merged = []
    for s in segs:   # one note heard twice with a gap is one note
        if merged and abs(s[2] / merged[-1][2] - 1) < 0.04 and s[0] - merged[-1][1] < 0.08:
            merged[-1] = (merged[-1][0], s[1], merged[-1][2])
        else:
            merged.append(s)
    return merged


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
    s = spec[(f > 60) & (f < 12000)] + 1e-12
    ns = notes(x)
    rising = sum(1 for a, b in zip(ns, ns[1:]) if b[2] > a[2] * 1.03)
    falling = sum(1 for a, b in zip(ns, ns[1:]) if b[2] < a[2] / 1.03)
    # steadiness (a loop / drone): the spread of the 100 ms envelope in its middle 80 %
    e100 = envelope(x, 0.1)
    mid = e100[max(1, len(e100) // 10):max(2, len(e100) - len(e100) // 10)]
    steady = float(np.std(db(mid / (mid.max() + 1e-12)))) if mid.size > 2 else 99.0
    return dict(dur=dur, onset=onset, peak_at=float(t[ip] / max(dur, 1e-6)), decay=decay, tail_db=tail_db, clip=clip,
                low=float(spec[f < 180].sum() / tot), hi=float(spec[f > 4000].sum() / tot),
                flat=float(np.exp(np.mean(np.log(s))) / np.mean(s)), smooth=float(np.mean(np.abs(np.diff(e, 2))) / (pk + 1e-12)),
                notes=len(ns), rising=rising, falling=falling, note_f0=[round(n[2], 1) for n in ns[:8]], steady=steady,
                late_db=float(db(e[int(len(e) * 0.75):].mean() / pk)) if len(e) > 8 else 0.0,
                early_db=float(db(e[:max(1, int(len(e) * 0.25))].mean() / pk)) if len(e) > 8 else 0.0)


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
    lo, hi = spec["keep"]
    s = {}
    s["length"] = closeness(ft["dur"], lo, hi * 1.6 if p in ("loop", "drone") else hi, max(0.15, 0.5 * (hi - lo) + 0.1))
    s["clip"] = 1.0 - min(1.0, ft["clip"] * 50)
    if p not in ("loop", "drone"):
        s["tail"] = closeness(ft["tail_db"], -90, -26, 14)
    if p == "whoosh":
        s["onset"] = closeness(ft["onset"], 0.02, 0.35, 0.3)
        s["peak_at"] = closeness(ft["peak_at"], 0.12, 0.7, 0.3)
        s["smooth"] = closeness(ft["smooth"], 0.0, 0.08, 0.1)
        s["low"] = closeness(ft["low"], 0.0, 0.4, 0.3)
    elif p in ("impact", "step"):
        s["onset"] = closeness(ft["onset"], 0.0, 0.05, 0.12)
        s["decay"] = closeness(ft["decay"], 0.03, 0.45 if p == "step" else 0.6, 0.4)
        s["peak_at"] = closeness(ft["peak_at"], 0.0, 0.3, 0.3)
        if p == "step":
            s["low"] = closeness(ft["low"], 0.08, 1.0, 0.12)
    elif p == "vocal":
        s["onset"] = closeness(ft["onset"], 0.0, 0.2, 0.25)
        s["tonal"] = closeness(ft["flat"], 0.0, 0.45, 0.3)
        # an effort, never a word: a take whose transcript holds a real word (a tag read aloud, "growls") never wins
        s["no_words"] = 0.0 if ft.get("words") else 1.0
    elif p == "burst":
        s["onset"] = closeness(ft["onset"], 0.0, 0.25, 0.3)
        s["decay"] = closeness(ft["decay"], 0.12, 1.1, 0.6)
        s["low"] = closeness(ft["low"], 0.08, 1.0, 0.1)
    elif p == "fade":
        s["onset"] = closeness(ft["onset"], 0.0, 0.2, 0.25)
        s["decay"] = closeness(ft["decay"], 0.25, 1.2, 0.5)
        s["low"] = closeness(ft["low"], 0.06, 1.0, 0.1)
    elif p == "rift":
        s["peak_at"] = closeness(ft["peak_at"], 0.15, 0.75, 0.3)
        s["low"] = closeness(ft["low"], 0.1, 1.0, 0.12)
        s["body"] = closeness(ft["late_db"], -30, -3, 12)          # it keeps tearing: never a single click
    elif p == "shatter":
        s["onset"] = closeness(ft["onset"], 0.0, 0.08, 0.15)
        s["hi"] = closeness(ft["hi"], 0.12, 1.0, 0.12)
        s["peak_at"] = closeness(ft["peak_at"], 0.0, 0.3, 0.3)
        s["decay"] = closeness(ft["decay"], 0.05, 1.0, 0.5)
    elif p == "collapse":
        s["onset"] = closeness(ft["onset"], 0.0, 0.35, 0.3)
        s["peak_at"] = closeness(ft["peak_at"], 0.0, 0.45, 0.3)
        s["tailoff"] = closeness(ft["late_db"], -45, -12, 12)      # a long dying tail, under the last words
    elif p == "loop":
        s["steady"] = closeness(ft["steady"], 0.0, 3.0, 4.0)
        s["low"] = closeness(ft["low"], 0.15, 1.0, 0.15)
    elif p == "drone":
        s["rise"] = closeness(ft["late_db"] - ft["early_db"], 0.0, 30.0, 8.0)   # it builds
        s["low"] = closeness(ft["low"], 0.12, 1.0, 0.15)
    elif p == "horn":
        s["peak_at"] = closeness(ft["peak_at"], 0.15, 0.6, 0.3)    # the swell, then the drum
        s["low"] = closeness(ft["low"], 0.1, 1.0, 0.12)
        s["tonal"] = closeness(ft["flat"], 0.0, 0.45, 0.3)
    elif p == "bell":
        s["notes"] = closeness(ft["notes"], 2, 4, 2)
        s["rising"] = 1.0 if ft["rising"] >= 1 else 0.0
        s["tonal"] = closeness(ft["flat"], 0.0, 0.3, 0.3)
        s["bright"] = closeness(ft["low"], 0.0, 0.3, 0.3)
    elif p == "fanfare":
        s["notes"] = closeness(ft["notes"], 3, 7, 2)
        s["rising"] = closeness(ft["rising"], 1, 4, 1)
        s["tonal"] = closeness(ft["flat"], 0.0, 0.35, 0.3)
    elif p == "machine":
        s["onset"] = closeness(ft["onset"], 0.0, 0.25, 0.3)
        s["hi"] = closeness(ft["hi"], 0.05, 1.0, 0.08)
        s["body"] = closeness(ft["late_db"], -40, -3, 12)          # the clank comes at the end
    elif p == "cursed":
        s["peak_at"] = closeness(ft["peak_at"], 0.2, 0.7, 0.3)     # the swell sucked INTO the thud
        s["low"] = closeness(ft["low"], 0.08, 1.0, 0.1)
    elif p == "bite":
        s["onset"] = closeness(ft["onset"], 0.0, 0.05, 0.1)
        s["decay"] = closeness(ft["decay"], 0.03, 0.35, 0.25)
    return float(sum(s.values()) / len(s)), s


# ---- ElevenLabs ------------------------------------------------------------------------------------------------------
def gen_sfx(prompt, secs, loop=False):
    import eleven
    body = {"text": prompt, "duration_seconds": max(0.5, float(secs)), "prompt_influence": PROMPT_INFLUENCE, "model_id": MODEL}
    if loop:
        body["loop"] = True
    raw = eleven.call("POST", "/v1/sound-generation", body=body, query={"output_format": "pcm_48000"})
    if not isinstance(raw, (bytes, bytearray)):
        sys.exit("sound-generation: unexpected response %r" % (raw,))
    # pcm_48000 from the sound endpoint is interleaved STEREO s16le (measured 2026-10-05: 0.6 s = 115,200 B)
    ch = 2 if abs(len(raw) / 4 / SR - body["duration_seconds"]) <= abs(len(raw) / 2 / SR - body["duration_seconds"]) else 1
    return raw, ch


def gen_voice(text, seed):
    """an effort in the Dealer's own saved voice (round 9, never a borrowed one), manic delivery, raw pcm mono"""
    import eleven
    voice = json.load(open(os.path.join(REPO, "tmp", "black_market_vo", "voice.json")))["voice_id"]
    raw = eleven.tts(voice, text, model_id="eleven_v4", seed=seed, output_format="pcm_48000",
                     stability=0.25, similarity=0.75, style=0.55, speed=1.05)
    return raw, 1, voice


EFFORTS = {"hah", "ha", "hngh", "hng", "ngh", "rah", "rrah", "rrrah", "hrah", "hhrah", "hhrrah", "hhah", "argh", "agh", "grr", "huh", "hm", "hmm"}


def heard(cue, path):
    """ElevenLabs speech-to-text on the MASKED take (score_takes.stt): an effort must come back as an audio event or a bare
    interjection; any other word means the model read a tag aloud or spoke"""
    import score_takes
    x = shaped(cue, path)
    tmpw = path[:-4] + "_stt.wav"
    open(tmpw, "wb").write(encode(x / (np.max(np.abs(x)) + 1e-9) * 0.8))
    r = score_takes.stt(tmpw)
    toks = [w for w in r.get("words", []) if w.get("type") == "word"]
    words = [re.sub(r"[^a-z]", "", w["text"].lower()) for w in toks]
    real = [w for w in words if w and w not in EFFORTS]
    return dict(text=r.get("text", ""), words=real)


def masked(x):
    """the shipping mask (tools/black_market_vo/mask_tone.py FILTER) over a mono take, mono out"""
    import mask_tone
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2").tobytes()
    out = subprocess.run(["ffmpeg", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-",
                          "-af", mask_tone.FILTER, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         input=pcm, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype="<f4").astype(np.float64)


def shaped(cue, path, seg=None):
    """a take as the player will hear it: decoded, masked when it is a voice, reversed when the cue says so; seg = the
    (start, end) seconds of ONE effort inside a voice take"""
    x = decode(path)
    if CUES[cue].get("kind") == "voice":
        x = masked(x)
        if seg is not None:
            a, b = int(seg[0] * SR), int(seg[1] * SR)
            x = fades(x[a:b].copy(), 0.004, 0.05)
    if CUES[cue].get("shape") == "reverse":
        x = np.ascontiguousarray(x[::-1])
    return x


def segments(x, gap_db=-26.0, gap_s=0.12, lo=0.25, hi=1.2):
    """the separate efforts inside one voice take (the model says "[growls] Hhhah!" as two sounds): runs of 10 ms frames
    louder than gap_db under the take's peak, split at quiet runs of gap_s or more, each padded 30 ms; kept when lo..hi s"""
    e = envelope(x, 0.010)
    pk = e.max()
    loud = db(e / (pk + 1e-12)) > gap_db
    segs, start, quiet = [], None, 0
    for i, v in enumerate(loud):
        if v:
            if start is None:
                start = i
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet * 0.010 >= gap_s:
                segs.append((start, i - quiet + 1))
                start, quiet = None, 0
    if start is not None:
        segs.append((start, len(loud) - quiet))
    out = []
    for a, b in segs:
        s0, s1 = max(0.0, a * 0.010 - 0.03), min(len(x) / SR, b * 0.010 + 0.06)
        if lo <= s1 - s0 <= hi:
            out.append((round(s0, 3), round(s1, 3)))
    return out


def load_takes():
    return json.load(open(TAKES_JSON)) if os.path.exists(TAKES_JSON) else {}


def save_takes(data):
    os.makedirs(WORK, exist_ok=True)
    with open(TAKES_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1)


def generate(cues, takes):
    data = load_takes()
    for cue in cues:
        spec = CUES[cue]
        d = os.path.join(TAKES_DIR, cue)
        os.makedirs(d, exist_ok=True)
        rows = data.get(cue, [])
        have = len(rows)
        n = takes if takes else spec.get("takes", spec["variants"] + 3)
        for i in range(have, have + n):
            name = "take_%d" % (i + 1)
            path = os.path.join(d, name + ".pcm")
            meta = {}
            if spec.get("kind") == "voice":
                text = spec["texts"][i % len(spec["texts"])]
                raw, ch, voice = gen_voice(text, 2000 + 11 * i)
                meta = dict(text=text, voice_id=voice, model="eleven_v4", seed=2000 + 11 * i)
            else:
                prompt = spec["prompts"][i % len(spec["prompts"])]
                raw, ch = gen_sfx(prompt, spec["secs"], loop=(spec["profile"] == "loop"))
                meta = dict(prompt=prompt, model=MODEL, secs=spec["secs"], loop=(spec["profile"] == "loop"))
            open(path, "wb").write(raw)
            meta["channels"] = ch
            if spec.get("kind") == "voice":
                meta["heard"] = heard(cue, path)
            json.dump(meta, open(path[:-4] + ".json", "w"), indent=1)
            ft = features(shaped(cue, path))
            if ft is not None and spec.get("kind") == "voice":
                ft["words"] = meta["heard"]["words"]
            sc, parts = score(cue, ft)
            rows.append(dict(name=name, file=os.path.relpath(path, REPO).replace("\\", "/"), features=ft, score=sc, parts=parts, **meta))
            print("%-13s %s score %.3f %s" % (cue, name, sc, "" if ft else "(silent)"), flush=True)
            data[cue] = rows
            save_takes(data)
    return data


def expand_voice(cue, rows):
    """one row per EFFORT: every base take is cut into its separate efforts (segments) and each is scored on its own"""
    base = [r for r in rows if "seg" not in r]
    out = list(base)
    for r in base:
        p = os.path.join(REPO, r["file"])
        if not os.path.exists(p):
            continue
        for k, seg in enumerate(segments(shaped(cue, p))):
            rr = {kk: vv for kk, vv in r.items() if kk not in ("features", "score", "parts")}
            rr.update(name="%s_s%d" % (r["name"], k + 1), seg=list(seg))
            rr["features"] = features(shaped(cue, p, seg))
            if rr["features"] is not None:
                rr["features"]["words"] = (r.get("heard") or {}).get("words", [])
            rr["score"], rr["parts"] = score(cue, rr["features"])
            out.append(rr)
    return out


def rescore(cues):
    data = load_takes()
    for cue in cues:
        if CUES[cue].get("kind") == "voice":
            data[cue] = expand_voice(cue, data.get(cue, []))
            for r in data[cue]:
                if "seg" not in r:
                    r["score"] = -0.5   # a whole two-effort take never ships: its efforts do
            continue
        for r in data.get(cue, []):
            p = os.path.join(REPO, r["file"])
            if os.path.exists(p):
                r["features"] = features(shaped(cue, p))
                if r["features"] is not None and CUES[cue].get("kind") == "voice":
                    r["features"]["words"] = (r.get("heard") or {}).get("words", [])
                r["score"], r["parts"] = score(cue, r["features"])
        rows = data.get(cue, [])
        print("%-13s %s" % (cue, " ".join("%s %.2f" % (r["name"], r["score"]) for r in sorted(rows, key=lambda r: -r["score"]))))
    save_takes(data)


# ---- the render --------------------------------------------------------------------------------------------------------
def make_loop(x, spec):
    """a seamless loop: loop_secs of the take, its head cross-faded (equal power) with what follows the cut"""
    L, F = int(spec["loop_secs"] * SR), int(spec["xfade"] * SR)
    x = trim(x, head_db=-60, tail_db=-70, pre=0, post=0)
    if len(x) < L + F:
        L = len(x) - F
    a = np.sin(np.linspace(0, np.pi / 2, F)) ** 2
    y = x[:L].copy()
    y[:F] = x[:F] * a + x[L:L + F] * (1 - a)
    return y


def fit_exact(x, secs):
    """an exact-length cue (the drain's 6.5 s): cut or pad to the sample, then fade the last 0.35 s to silence"""
    n = int(round(secs * SR))
    y = x[:n] if len(x) >= n else np.concatenate([x, np.zeros(n - len(x))])
    return fades(y, 0.01, 0.35)


def layer_source(cue, ref):
    """a layer's take: "take_3" (this cue) or "other_cue/take_2"; -> (cue, row)"""
    c, name = (ref.split("/", 1) if "/" in ref else (cue, ref))
    row = next((r for r in load_takes().get(c, []) if r["name"] == name), None)
    if row is None:
        sys.exit("%s: layer %s names a take that is not in tmp/dealer_sfx/takes.json - generate it first" % (cue, ref))
    return c, row


def resample(x, rate):
    """play x `rate` times faster (rate 1.5 = up a fifth and two thirds as long), polyphase"""
    if abs(rate - 1.0) < 1e-9:
        return x
    from fractions import Fraction
    from scipy.signal import resample_poly
    fr = Fraction(1.0 / rate).limit_denominator(64)
    return resample_poly(x, fr.numerator, fr.denominator)


def gain_env(n, keys):
    """a gain curve over n samples from [(t_s, dB), ...] keys (linear in dB between keys, flat outside)"""
    t = np.arange(n) / SR
    ts = [k[0] for k in keys]
    ds = [k[1] for k in keys]
    return 10 ** (np.interp(t, ts, ds) / 20)


def compose(cue):
    """-> (signal, [sources]): the cue's LAYERS (authored takes trimmed, cut to a segment, resampled, gain-shaped) summed
    on one timeline. The design the brief asks for, built from real takes where no single take carries it whole (a horn
    INTO a drum, two bell strikes a fifth apart, a swell INTO a crack, a drone UNDER a quickening heartbeat)."""
    spec = CUES[cue]
    parts, srcs, n = [], [], 0
    for L in spec["layers"]:
        c, row = layer_source(cue, L["take"])
        x = trim(shaped(c, os.path.join(REPO, row["file"]), row.get("seg")))
        if L.get("seg"):
            a, b = int(L["seg"][0] * SR), int(L["seg"][1] * SR)
            x = x[a:b].copy()
        x = resample(x, L.get("rate", 1.0))
        if L.get("ducks"):
            keys = [(0.0, 0.0)]
            for t0, t1, d in L["ducks"]:
                keys += [(t0, 0.0), (t0 + 0.06, d), (t1 - 0.06, d), (t1, 0.0)]
            x = x * gain_env(len(x), keys)
        if L.get("ramp"):
            x = x * gain_env(len(x), [(0.0, L["ramp"][0]), (len(x) / SR, L["ramp"][1])])
        x = fades(x, L.get("fin", 0.003), L.get("fout", 0.02)) * 10 ** (L.get("gain", 0.0) / 20)
        for at in (L["at"] if isinstance(L.get("at"), list) else [L.get("at", 0.0)]):
            g = 1.0
            if isinstance(L.get("at"), list) and L.get("gains"):
                g = 10 ** (L["gains"][L["at"].index(at)] / 20)
            parts.append((int(at * SR), x * g))
            n = max(n, int(at * SR) + len(x))
        srcs.append(dict(take=row["file"], name=c + "/" + row["name"], layer={k: v for k, v in L.items() if k != "take"}))
    y = np.zeros(n)
    for i, x in parts:
        y[i:i + len(x)] += x
    return y, srcs


def render(cue, path, seg=None):
    spec = CUES[cue]
    x = compose(cue)[0] if spec.get("layers") else shaped(cue, path, seg)
    if spec["profile"] == "loop":
        y = dc_block(make_loop(x, spec))
        y = level_to(y, spec["lufs"])
        return encode(y), y
    x = dc_block(trim(x))
    if spec.get("duck_after"):                       # the tail eased down under what follows it (the death line)
        t0, d = spec["duck_after"]
        x = x * gain_env(len(x), [(t0, 0.0), (len(x) / SR, d)])
    if spec.get("exact"):
        x = fit_exact(x, spec["exact"])
    else:
        lo, hi = spec["keep"]
        if len(x) > hi * SR:
            x = fades(x[:int(hi * SR)], 0.0, 0.12)   # a take that rings past the window is faded at its edge
        fout = {"impact": 0.03, "step": 0.03, "bite": 0.03, "burst": 0.06}.get(spec["profile"], 0.10)
        x = fades(x, 0.003, fout)
    y = level_to(x, spec["lufs"])
    return encode(y), y


def choose(cue, data, picks):
    spec = CUES[cue]
    rows = [r for r in data.get(cue, []) if r.get("features")]
    out = []
    for name in picks.get(cue, []):
        r = next((r for r in rows if r["name"] == name), None)
        if r:
            out.append(r)
    for r in sorted(rows, key=lambda r: -r["score"]):
        if r not in out:
            out.append(r)
    return out[:spec["variants"]]


def root_path(root, parts):
    return os.path.join(root, *parts)


def pick(cues, root):
    data = load_takes()
    picks = json.load(open(PICKS_JSON)) if os.path.exists(PICKS_JSON) else {}
    mans = {g: load_manifest(root, g) for g in GROUPS}
    for cue in cues:
        spec = CUES[cue]
        g = spec["group"]
        if spec.get("layers"):
            b, y = render(cue, None)
            srcs = compose(cue)[1]
            p = os.path.join(root_path(root, GROUPS[g]["wav_dir"]), spec["stem"] + ".wav")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if not os.path.exists(p) or open(p, "rb").read() != b:
                open(p, "wb").write(b)
            info = dict(file=spec["stem"] + ".wav", sha256=sha256(b), secs=round(len(y) / SR, 4), lufs=round(lufs(y), 2),
                        peak_db=round(float(db(np.max(np.abs(y)) + 1e-12)), 2), take="composed", layers=srcs, score=None)
            mans[g][cue] = dict(stem=spec["stem"], files=[info], profile=spec["profile"], keep=list(spec["keep"]))
            print("%-13s %-30s composed of %d layers  %.2fs  %.1f LUFS  peak %.1f" % (cue, spec["stem"] + ".wav", len(srcs), info["secs"], info["lufs"], info["peak_db"]))
            continue
        rows = choose(cue, data, picks)
        if len(rows) < spec["variants"]:
            print("%-13s only %d take(s) for %d variant(s) - generate more" % (cue, len(rows), spec["variants"]))
            if not rows:
                continue
        files = []
        for i, r in enumerate(rows):
            stem = spec["stem"] + ("" if i == 0 else "_%d" % (i + 1))
            b, y = render(cue, os.path.join(REPO, r["file"]), r.get("seg"))
            p = os.path.join(root_path(root, GROUPS[g]["wav_dir"]), stem + ".wav")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if not os.path.exists(p) or open(p, "rb").read() != b:
                open(p, "wb").write(b)
            info = dict(file=stem + ".wav", sha256=sha256(b), secs=round(len(y) / SR, 4), lufs=round(lufs(y), 2),
                        peak_db=round(float(db(np.max(np.abs(y)) + 1e-12)), 2), source=r["file"], take=r["name"], score=round(r["score"], 3))
            if r.get("seg"):
                info["segment_s"] = r["seg"]
            for k in ("prompt", "text", "model", "voice_id"):
                if r.get(k):
                    info[k] = r[k] if k != "voice_id" else "tmp/black_market_vo/voice.json (the shipping dealer voice)"
            files.append(info)
            print("%-13s %-30s %-8s score %.2f  %.2fs  %.1f LUFS  peak %.1f" % (cue, stem + ".wav", r["name"], r["score"], info["secs"], info["lufs"], info["peak_db"]))
        mans[g][cue] = dict(stem=spec["stem"], files=files, profile=spec["profile"], keep=list(spec["keep"]))
    for g, man in mans.items():
        if man:
            write_manifest(root, g, man)
    write_csv(root, mans["dealer"])
    print("manifests + tod_dealer.csv written under", root)


def load_manifest(root, group):
    p = root_path(root, GROUPS[group]["manifest"])
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding="utf-8")).get("cues", {})


def write_manifest(root, group, man):
    p = root_path(root, GROUPS[group]["manifest"])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    doc = {"about": "GENERATED by tools/dealer_sfx/make_sounds.py (W2B, PK10/PK16) - never hand-edit. Each authored wav's sha256, "
                    "its source take and its measured loudness; the owning generator's --check pins the wav to this sha.",
           "group": group, "cues": {k: man[k] for k in ORDER if k in man}}
    # the flat {wav name: sha} view the arena / house generators read
    doc["files"] = {f["file"][:-4]: dict(sha256=f["sha256"], secs=f["secs"]) for k in ORDER if k in man for f in man[k]["files"]}
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1)
        fh.write("\n")


def csv_text(root, man):
    header_line = open(root_path(REPO if not os.path.exists(root_path(root, HEADER_FROM)) else root, HEADER_FROM),
                       encoding="utf-8-sig").read().splitlines()[0]
    header = next(csv.reader([header_line]))
    return "\r\n".join([header_line] + dealer_rows(header, man)) + "\r\n"


def write_csv(root, man):
    if not man:
        return
    p = root_path(root, CSV_REL)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    b = csv_text(root, man).encode("utf-8")
    if not os.path.exists(p) or open(p, "rb").read() != b:
        open(p, "wb").write(b)


# ---- the desk ------------------------------------------------------------------------------------------------------------
def desk():
    data = load_takes()
    man = {g: load_manifest(REPO if not os.path.isdir(os.path.join(REPO, "tmp", "wave2", "W2B-dealer-av", "stage")) else
                            os.path.join(REPO, "tmp", "wave2", "W2B-dealer-av", "stage"), g) for g in GROUPS}
    h = ["<!doctype html><meta charset=utf-8><title>Dealer sounds desk</title>",
         "<style>body{font:14px system-ui;background:#111;color:#ddd;margin:24px}h2{margin:26px 0 6px;color:#f88}"
         "td{padding:4px 10px;border-bottom:1px solid #333;vertical-align:top}.pick{color:#6f6;font-weight:bold}code{color:#fc8}</style>",
         "<h1>The Dealer fight + arena / house cues: every take, the pick</h1>",
         "<p>Overrule a pick: <code>tmp/dealer_sfx/picks.json</code> = <code>{\"scythe_swing\": [\"take_3\", \"take_1\"]}</code>, then "
         "<code>python tools/dealer_sfx/make_sounds.py pick --cue scythe_swing --root tmp/wave2/W2B-dealer-av/stage</code>.</p>"]
    for cue in ORDER:
        spec = CUES[cue]
        shipped = {f["take"] for f in man[spec["group"]].get(cue, {}).get("files", [])}
        h.append("<h2>%s <small>(%s, %d variant%s, %s)</small></h2><table>" % (cue, spec["profile"], spec["variants"], "s" if spec["variants"] > 1 else "", spec["stem"]))
        for r in sorted(data.get(cue, []), key=lambda r: -r["score"]):
            what = r.get("prompt") or r.get("text") or ""
            parts = " ".join("%s %.2f" % (k, v) for k, v in sorted((r.get("parts") or {}).items()) if isinstance(v, float))
            h.append("<tr><td class='%s'>%s%s</td><td>%.3f</td><td><small>%s<br>%s</small></td><td><audio controls src='../../%s'></audio></td></tr>" % (
                "pick" if r["name"] in shipped else "", r["name"], " SHIPPED" if r["name"] in shipped else "", r["score"], parts, what,
                r["file"].replace(".pcm", ".wav")))
        h.append("</table>")
    # browsers do not play raw pcm: a wav beside every take for the desk
    for cue in ORDER:
        for r in data.get(cue, []):
            p = os.path.join(REPO, r["file"])
            w = p[:-4] + ".wav"
            if os.path.exists(p) and not os.path.exists(w):
                open(w, "wb").write(encode(np.clip(shaped(cue, p), -1, 1)))
    open(DESK, "w", encoding="utf-8").write("\n".join(h))
    print("desk:", DESK)


# ---- the gate ------------------------------------------------------------------------------------------------------------------
def check(root):
    bad, n = [], 0
    for g in GROUPS:
        man = load_manifest(root, g)
        mp = root_path(root, GROUPS[g]["manifest"])
        want = [c for c in ORDER if CUES[c]["group"] == g]
        if g == "dealer":
            missing = [c for c in want if c not in man]
            if missing:
                bad.append("dealer cues not shipped: %s" % ", ".join(missing))
        for cue, ent in man.items():
            if cue not in CUES:
                bad.append("%s: unknown cue %s" % (os.path.basename(mp), cue))
                continue
            lo, hi = CUES[cue]["keep"]
            for f in ent["files"]:
                p = os.path.join(root_path(root, GROUPS[g]["wav_dir"]), f["file"])
                n += 1
                if not os.path.exists(p):
                    bad.append("missing " + f["file"])
                    continue
                b = open(p, "rb").read()
                if sha256(b) != f["sha256"]:
                    bad.append("changed " + f["file"])
                try:
                    with wave.open(io.BytesIO(b)) as w:
                        if (w.getnchannels(), w.getframerate(), w.getsampwidth()) != (1, SR, 2):
                            bad.append(f["file"] + " is not mono 48 kHz 16-bit")
                        secs = w.getnframes() / float(SR)
                        if not (lo - 0.005 <= secs <= hi + 0.005):
                            bad.append("%s length %.3fs outside %.2f..%.2f" % (f["file"], secs, lo, hi))
                except wave.Error as e:
                    bad.append("%s unreadable: %s" % (f["file"], e))
    dman = load_manifest(root, "dealer")
    cp = root_path(root, CSV_REL)
    if not os.path.exists(cp):
        bad.append("sound/aliases/tod_dealer.csv missing")
    elif dman and open(cp, "rb").read() != csv_text(root, dman).encode("utf-8"):
        bad.append("tod_dealer.csv differs from the generated table")
    szc = root_path(root, SZC_REL)
    loaded = os.path.exists(szc) and '"tod_dealer.csv"' in open(szc, encoding="utf-8-sig").read()
    if bad:
        print("DEALER SOUNDS STALE: " + "; ".join(bad[:10]) + " - " + FIX)
        sys.exit(1)
    print("DEALER SOUNDS OK: %d files (%d dealer cues + %d authored arena / house cues), tod_dealer.csv %d rows%s" % (
        n, len(dman), len(load_manifest(root, "arena")) + len(load_manifest(root, "house")),
        len(dealer_rows(next(csv.reader([open(root_path(root, HEADER_FROM) if os.path.exists(root_path(root, HEADER_FROM)) else root_path(REPO, HEADER_FROM), encoding="utf-8-sig").read().splitlines()[0]])), dman)),
        "" if loaded else "  (NOTE: the zone config does not load tod_dealer.csv yet - WIRING)"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="")
    ap.add_argument("--cue", action="append")
    ap.add_argument("--group")
    ap.add_argument("--takes", type=int, default=0, help="takes per cue (default: the cue's variants + 3)")
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cues = a.cue or [c for c in ORDER if not a.group or CUES[c]["group"] == a.group]
    for c in cues:
        if c not in CUES:
            sys.exit("unknown cue %s" % c)
    root = os.path.abspath(a.root)
    if a.check or a.cmd == "check":
        check(root)
    elif a.cmd == "generate":
        generate(cues, a.takes)
    elif a.cmd == "rescore":
        rescore(cues)
    elif a.cmd == "pick":
        pick(cues, root)
    elif a.cmd == "desk":
        desk()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
