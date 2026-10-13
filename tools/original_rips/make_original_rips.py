"""THE ORIGINAL RIPS (wave 2 / W2F, 2026-10-05): the Mangler's voice and the Death Perception / PhD Flopper machine
music, from ORIGINALS already on this PC (user: "Pretty sure you can get the originals very easily yourself"). No game is
launched, nothing is downloaded, nothing is written outside --out / tmp/original_rips/. Two read-only sources:

  T7 ASSETS  ~/Downloads/T7 Assets V2.8.rar (a Black Ops III asset dump, 58 GB; read with 7-Zip, only the members below
             are extracted, into tmp/original_rips/src/). Gorod Krovi's Mangler ("raz") - the creature BO6's Mangler is
             built on (BO6's own Mangler clips are ai_zm_dlc3_armored_zombie_* and ai_t9_zm_raz_*). Its 24 vocal takes are
             exactly the files BO3's zm_ai_raz.csv plays as vox_raz_exert_enrage (6) / _melee (10) / _pain (8).
  SAT PERKS  ~/Downloads/SATPerksAssets_extracted (WetEgg's BO6 perk-machine pack: the source of this map's BO6 machines
             and Wisp Tea). BO6's mus_perk_deathperception_jingle / _stinger and mus_perk_phd_jingle / _stinger. The
             pairing is PROVEN, not trusted: the BO6 bank tables this PC's extraction dumped
             (~/Downloads/BO6_Pilot_Export/bo6/sndbanks/json/zm_perkmachine_{deathperception,phd}.all.json) name the same
             payload ids, and the Death Perception rows, hashed in that dump, resolve by FNV-1a 64 (`pairing`).

WHY NOT BO6'S OWN MANGLER VOICE: BO6 voices its Mangler through an AIVox character table (its clips carry AIVox@vox_melee
/ vox_pain / vox_shoot / vox_berserk / vox_mantle / roar notes). None of the 653 bank tables in the BO6 dump holds a
Mangler vox alias: every vox_ai_mangler_* / vox_mangler_* / vox_zm_mangler_* / aivox_mangler_* / vox_ai_raz_* /
evt_ai_mangler_* name (x the 4,877-token alias vocabulary, two tokens deep) was hashed against all 62,083 hashed aliases
with zero hits; its Mangler bank (sndbank_41d51ffb35dcc2f5) holds foley, 42 footstep surfaces, armour, cannon and helmet
radio only (amb_ai_mangler_radio, payload never exported). Loading more needs an elevated Saluki/Cordycep session (UAC).
tmp/wave2/W2F-original-rips/LAND.md records exactly what to pull if that is ever run.

WHAT SHIPS (mono 48 kHz 16-bit under sound_assets/tod/, levelled to the map's own families - measured, not guessed):
  mangler_vox/tod_mangler_roar_N   vox_raz_exert_enrage, as is   -> hb_bo6_vox_ai_mangler_roar     arrival + berserk roar
  mangler_vox/tod_mangler_melee_N  vox_raz_exert_melee, as is    -> hb_bo6_vox_ai_mangler_melee    swing (frame 5)
                                                                 -> hb_bo6_vox_ai_mangler_shoot    cannon (frame 58)
  mangler_vox/tod_mangler_pain_N   vox_raz_exert_pain, as is     -> hb_bo6_vox_ai_mangler_pain     hits, on a gap
  mangler_vox/tod_mangler_death_N  DERIVED: an enrage take at 0.82 speed (varispeed: deeper, longer), its second half
                                   faded, 7 kHz low-pass          -> hb_bo6_vox_ai_mangler_death    the dying roar
  mangler_vox/tod_mangler_growl_N  DERIVED: a melee / pain take at 0.70 speed, 2.4 kHz low-pass (inside the helmet)
                                                                 -> hb_bo6_vox_ai_mangler_ambience the hunting growl
  perk_jingles/mus_perk_*.wav      BO6 originals, (L+R)/2 mono, trailing silence cut, levelled to the stock BO3
                                   perk-jingle family            -> mus_perk_{deathperception,phd}_{jingle,stinger}
The vox families are levelled by their loudest 300 ms K-weighted window to the Doppelghast's matching BO6 vox (the map's
other elite voice, tuned by the user); the music by BS.1770 integrated loudness to the stock BO3 perksacola jingles
(Juggernog, Speed, Revive, Double Tap, Stamin-Up, PhD, Pack-a-Punch: measured from the T7 dump). A look-ahead limiter
(40 ms, never above -1 dBFS) catches the peaks. The two tables are GENERATED here:
  sound/aliases/tod_mangler_vox.csv   the BO6 lane's row shape (hb_bo6_ghoul.csv: UIN_MOD, BUS_FX, vol 95)
  sound/aliases/tod_perk_jingles.csv  stock BO3's own perk-jingle row (mus_perks_jugganog_jingle: 79, 250/1000/1500,
                                      +-50 cents, snp_x3 + zmb_duck_music_3d, streamed), only Name and FileSpec changed

COMMANDS
  python tools/original_rips/make_original_rips.py build [--out ROOT]          extract (cached), render, write wavs + tables
                                                                                 + tools/original_rips/manifest.json
  python tools/original_rips/make_original_rips.py --check [--root ROOT]       the build gate: no sources, no DSP
  python tools/original_rips/make_original_rips.py --verify-sources [--root ROOT]  re-render from the originals and
                                                                                 byte-compare (needs the two sources)
  python tools/original_rips/make_original_rips.py --selftest                  the planted-error controls
ROOT (default the repo) is any tree laid out like the repo (a staged overlay). Never hand-edit an output.
"""
import argparse, copy, csv, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile, wave
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MANIFEST = os.path.join(HERE, 'manifest.json')
WORK = os.path.join(REPO, 'tmp', 'original_rips')
SRC_CACHE = os.path.join(WORK, 'src')
HOME = os.path.expanduser('~')
T7_ARCHIVE = os.path.join(HOME, 'Downloads', 'T7 Assets V2.8.rar')
T7_PREFIX = 'T7 Assets V2.8'
SAT_DIR = os.path.join(HOME, 'Downloads', 'SATPerksAssets_extracted', 'SATPerksAssets', 'sound_assets', '_wetegg', 'sat', 'perks')
BO6_BANKS = os.path.join(HOME, 'Downloads', 'BO6_Pilot_Export', 'bo6', 'sndbanks', 'json')
SEVEN_ZIP = r'C:\Program Files\7-Zip\7z.exe'
SZC = os.path.join('sound', 'zoneconfig', 'zm_tod2_cybercity.szc')
VOX_TABLE = 'tod_mangler_vox.csv'
JINGLE_TABLE = 'tod_perk_jingles.csv'
VOX_DIR = 'tod/mangler_vox'
JINGLE_DIR = 'tod/perk_jingles'
SR = 48000
CEIL_DB = -1.0
FIX = 'run: python tools/original_rips/make_original_rips.py build'

# ---- the sources ---------------------------------------------------------------------------------------------------
RAZ = 'sound_assets/zmb/ai/raz/exerts/'
ENRAGE = ['enrage/vox_plr_1_exert_charge_00', 'enrage/vox_plr_1_exert_charge_01', 'enrage/vox_plr_1_exert_charge_02',
          'enrage/vox_plr_1_exert_charge_03', 'enrage/vox_plr_1_exert_charge_04', 'enrage/vox_plr_1_exert_laugh_05']
MELEE = ['melee/vox_plr_1_exert_melee_00', 'melee/vox_plr_1_exert_melee_01', 'melee/vox_plr_1_exert_melee_02',
         'melee/vox_plr_1_exert_melee_03', 'melee/vox_plr_1_exert_melee_04', 'melee/vox_plr_1_exert_melee_04_alt01',
         'melee/vox_plr_1_exert_melee_04_alt02', 'melee/vox_plr_1_exert_melee_04_alt03',
         'melee/vox_plr_1_exert_melee_04_alt04', 'melee/vox_plr_1_exert_melee_04_alt05']
PAIN = ['pain/vox_plr_1_exert_pain_00', 'pain/vox_plr_1_exert_pain_01', 'pain/vox_plr_1_exert_pain_01_alt01',
        'pain/vox_plr_1_exert_pain_02', 'pain/vox_plr_1_exert_pain_02_alt01', 'pain/vox_plr_1_exert_pain_03',
        'pain/vox_plr_1_exert_pain_03_alt01', 'pain/vox_plr_1_exert_pain_04']

# family -> what it renders. kwin = the loudest-300-ms K-weighted target (dB): the Doppelghast's BO6 vox measured
# 2026-10-05 - roar -9.8, attack -9.2, pain -11.4, death -9.1, ambience (breath) -13.3. The Mangler sits a hair under
# its attack (the cannon is already its loudest sound) and its growl under the ghoul's breath (a pack never walls it).
VOX = [
    dict(fam='roar', src=ENRAGE, mode='as_is', kwin=-9.8),
    dict(fam='melee', src=MELEE, mode='as_is', kwin=-9.6),
    dict(fam='pain', src=PAIN, mode='as_is', kwin=-11.0),
    dict(fam='death', src=ENRAGE[:3], mode='death', kwin=-9.5, rate=0.82, lpf=7000.0, lpf_order=2, fade_from=0.45),
    dict(fam='growl', src=[MELEE[0], MELEE[2], MELEE[5], MELEE[7], PAIN[0], PAIN[5]], mode='growl', kwin=-14.0,
         rate=0.70, lpf=2400.0, lpf_order=4),
]
# alias -> (family files, VolMin/Max, DistMin, DistMaxDry, DistMaxWet, EntityLimitCount). The BO6 lane's row shape;
# vol 95 = the Doppelghast's vox. Reach: the arrival / berserk roar carries like the ghoul's screech, a grunt reaches
# the room, the growl a corner away.
VOX_ROWS = [
    ('hb_bo6_vox_ai_mangler_roar', 'roar', 95, 120, 3200, 3800, 1),
    ('hb_bo6_vox_ai_mangler_melee', 'melee', 95, 100, 2400, 2800, 2),
    ('hb_bo6_vox_ai_mangler_shoot', 'melee', 95, 100, 2600, 3000, 1),
    ('hb_bo6_vox_ai_mangler_pain', 'pain', 95, 100, 2400, 2800, 1),
    ('hb_bo6_vox_ai_mangler_death', 'death', 95, 150, 3000, 3600, 1),
    ('hb_bo6_vox_ai_mangler_ambience', 'growl', 95, 80, 2200, 2600, 1),
]
# the BO6 payloads (SAT pack file stem = the BO6 xsound id) and the bank table that names each
JINGLES = [
    dict(alias='mus_perk_deathperception_jingle', sat='sound_25dfe0056d8a41ee', bank='zm_perkmachine_deathperception.all.json', kind='jingle'),
    dict(alias='mus_perk_deathperception_stinger', sat='sound_2cea6fddcbf1a204', bank='zm_perkmachine_deathperception.all.json', kind='sting'),
    dict(alias='mus_perk_phd_jingle', sat='sound_4bb8feb4a346944e', bank='zm_perkmachine_phd.all.json', kind='jingle'),
    dict(alias='mus_perk_phd_stinger', sat='sound_5c976d1c875b6464', bank='zm_perkmachine_phd.all.json', kind='sting'),
]
# BS.1770 integrated, the stock BO3 mono perksacola family (T7 dump, measured 2026-10-05): jingles jugg -12.4 speed -11.5
# revive -10.7 doubletap -11.6 stamin -11.4 phd -11.1 packapunch -11.0 (mean -11.4); stings -11.3 -12.5 -11.4 -11.8 -11.5
# -11.3 -10.5 (mean -11.5). A machine's music sits half a dB under the family it plays beside.
JINGLE_LUFS = {'jingle': -11.9, 'sting': -12.0}

HEADER = ('Name,Behavior,Storage,FileSpec,FileSpecSustain,FileSpecRelease,Template,Loadspec,Secondary,SustainAlias,'
          'ReleaseAlias,Bus,VolumeGroup,DuckGroup,Duck,ReverbSend,CenterSend,VolMin,VolMax,DistMin,DistMaxDry,DistMaxWet,'
          'DryMinCurve,DryMaxCurve,WetMinCurve,WetMaxCurve,LimitCount,LimitType,EntityLimitCount,EntityLimitType,PitchMin,'
          'PitchMax,PriorityMin,PriorityMax,PriorityThresholdMin,PriorityThresholdMax,AmplitudePriority,PanType,Pan,Futz,'
          'Looping,RandomizeType,Probability,StartDelay,EnvelopMin,EnvelopMax,EnvelopPercent,OcclusionLevel,IsBig,'
          'DistanceLpf,FluxType,FluxTime,Subtitle,Doppler,ContextType,ContextValue,ContextType1,ContextValue1,ContextType2,'
          'ContextValue2,ContextType3,ContextValue3,Timescale,IsMusic,IsCinematic,FadeIn,FadeOut,Pauseable,StopOnEntDeath,'
          'Compression,StopOnPlay,DopplerScale,FutzPatch,VoiceLimit,IgnoreMaxDist,NeverPlayTwice,ContinuousPan,FileSource,'
          'FileSourceSustain,FileSourceRelease,FileTarget,FileTargetSustain,FileTargetRelease,Platform,Language,'
          'OutputDevices,PlatformMask,WiiUMono,StopAlias,DistanceLpfMin,DistanceLpfMax,FacialAnimationName,'
          'RestartContextLoops,SilentInCPZ,ContextFailsafe,GPAD,GPADOnly,MuteVoice,MuteMusic,RowSourceFileName,'
          'RowSourceShortName,RowSourceLineNumber').split(',')
# stock BO3's mus_perks_jugganog_jingle row (t7_zm_sounds.csv in the T7 dump), every set field, verbatim
STOCK_JINGLE_ROW = {
    'Storage': 'streamed', 'Bus': 'BUS_FX', 'VolumeGroup': 'grp_ambience', 'DuckGroup': 'snp_x3', 'Duck': 'zmb_duck_music_3d',
    'ReverbSend': '80', 'CenterSend': '0', 'VolMin': '79', 'VolMax': '79', 'DistMin': '250', 'DistMaxDry': '1000',
    'DistMaxWet': '1500', 'DryMinCurve': 'allon', 'DryMaxCurve': 'default', 'WetMinCurve': 'allon', 'WetMaxCurve': 'default',
    'LimitCount': '6', 'LimitType': 'priority', 'EntityLimitCount': '8', 'EntityLimitType': 'oldest', 'PitchMin': '-50',
    'PitchMax': '50', 'PriorityMin': '40', 'PriorityMax': '75', 'PriorityThresholdMin': '0', 'PriorityThresholdMax': '1',
    'AmplitudePriority': 'no', 'PanType': '3d', 'Pan': 'default', 'Looping': 'nonlooping', 'Probability': '1',
    'StartDelay': '0', 'EnvelopMin': '0', 'EnvelopMax': '0', 'EnvelopPercent': '0', 'OcclusionLevel': '0.65', 'IsBig': 'no',
    'DistanceLpf': 'yes', 'FluxTime': '0', 'Doppler': 'no', 'Timescale': 'yes', 'IsMusic': 'no', 'IsCinematic': 'no',
    'FadeIn': '0', 'FadeOut': '0', 'Pauseable': 'yes', 'StopOnEntDeath': 'no', 'VoiceLimit': 'no', 'IgnoreMaxDist': 'no',
    'NeverPlayTwice': 'no', 'ContinuousPan': 'yes', 'DistanceLpfMin': '800', 'DistanceLpfMax': '3000',
    'RestartContextLoops': 'no', 'SilentInCPZ': 'no', 'ContextFailsafe': 'no', 'GPAD': 'no', 'GPADOnly': 'no',
    'MuteVoice': 'no', 'MuteMusic': 'no'}

# the GSC wiring the gate reads (file -> [(what, regex)])
GSC = 'scripts/zm/zm_tod2_cybercity/'
WIRING = {
    GSC + '_tod_bo6_audio.gsc': [
        ('the arrival roar at attach', r'actor thread timed\( "vox_ai_mangler_roar", TOD_MANGLER_SPAWN_ROAR_F, 1, "spawn_roar" \);'),
        ('the hunting growl cadence at attach', r'actor thread mangler_ambience_cadence\(\);'),
        ('the swing grunt on frame 5', r'actor thread timed\( "vox_ai_mangler_melee", TOD_MANGLER_VOX_MELEE_F, 1, "melee_timed" \);'),
        ('the cannon bellow on frame 58', r'actor thread timed\( "vox_ai_mangler_shoot", TOD_MANGLER_VOX_SHOOT_F, rate, "cannon_timed" \);'),
        ('the pain watch for kind mangler', r'if \( kind == "mangler" \)\s*\{\s*self mangler_pain_watch\(\);'),
        ('the pain grunt', r'emit\( self, "vox_ai_mangler_pain", "damage" \);'),
        ('the berserk roar', r'emit\( self, "vox_ai_mangler_roar", "berserk" \);'),
        ('the hunting growl', r'emit\( self, "vox_ai_mangler_ambience", "ambience_cadence" \);'),
        ('the dying roar at death', r'emit\( actor, "vox_ai_mangler_death", "death_voice" \);'),
        ('the dying roar rides a carrier (the tail list)', r'source_alias == "vox_ai_mangler_death" \)'),
        ('the frame defines', r'#define TOD_MANGLER_VOX_MELEE_F\s+5\b[\s\S]*#define TOD_MANGLER_VOX_SHOOT_F\s+58\b'),
    ],
    GSC + '_tod_perk_electric_cherry.gsc': [
        ('Death Perception jingle', r'use_trigger\.script_sound\s*=\s*"mus_perk_deathperception_jingle";'),
        ('Death Perception stinger', r'use_trigger\.script_label\s*=\s*"mus_perk_deathperception_stinger";'),
    ],
    GSC + '_tod_perk_phd.gsc': [
        ('PhD jingle', r'use_trigger\.script_sound\s*=\s*"mus_perk_phd_jingle";'),
        ('PhD stinger', r'use_trigger\.script_label\s*=\s*"mus_perk_phd_stinger";'),
    ],
}
# shapes that must NOT come back
FORBIDDEN = {
    GSC + '_tod_bo6_audio.gsc': [('the Mangler voice bail-out', r'if \( kind == "mangler" \) return;')],
    GSC + '_tod_perk_phd.gsc': [('PhD on Mule Kick\'s music', r'"mus_perks_mulekick_(jingle|sting)"')],
}


# ---- audio helpers (numpy / scipy: deterministic) --------------------------------------------------------------------
def _np():
    import numpy as np
    return np


def read_mono(path):
    import soundfile as sf
    np = _np()
    y, sr = sf.read(path, always_2d=True, dtype='float64')
    assert sr == SR, (path, sr)
    return y.mean(axis=1)


def encode(x):
    np = _np()
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype('<i2')
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


def kweight(x):
    from scipy.signal import lfilter
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], x)
    return lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y)


def kwin(x, win=0.3):
    """the loudest 300 ms K-weighted window (dB): how loud a grunt FEELS (integrated LUFS under-reads a 0.4 s take)"""
    np = _np()
    y = kweight(x)
    n = int(win * SR)
    if len(y) < n:
        y = np.concatenate([y, np.zeros(n - len(y))])
    c = np.concatenate([[0.0], np.cumsum(y ** 2)])
    return float(-0.691 + 10 * np.log10(((c[n:] - c[:-n]) / n).max() + 1e-20))


def lufs(x):
    """BS.1770-4 integrated loudness (400 ms blocks, 75 % overlap, -70 abs / -10 rel gates)"""
    np = _np()
    y = kweight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    if len(y) < blk:
        y = np.concatenate([y, np.zeros(blk - len(y))])
    c = np.concatenate([[0.0], np.cumsum(y ** 2)])
    starts = np.arange(0, len(y) - blk + 1, hop)
    ms = (c[starts + blk] - c[starts]) / blk
    l = -0.691 + 10 * np.log10(ms + 1e-20)
    ms = ms[l > -70]
    if ms.size == 0:
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(ms)) - 10
    ms = ms[(-0.691 + 10 * np.log10(ms)) > rel]
    return float(-0.691 + 10 * np.log10(np.mean(ms))) if ms.size else -70.0


def peak_db(x):
    np = _np()
    return float(20 * np.log10(np.max(np.abs(x)) + 1e-12))


def envelope_db(x, frame=0.005):
    np = _np()
    n = int(frame * SR)
    k = max(1, len(x) // n)
    e = np.sqrt(np.mean(x[:k * n].reshape(k, n) ** 2, axis=1) + 1e-20)
    return 20 * np.log10(e / (e.max() + 1e-20) + 1e-12), n


def trim(x, head_db=-50.0, tail_db=-55.0, pre=0.005, post=0.06):
    np = _np()
    d, n = envelope_db(x)
    above = np.where(d > head_db)[0]
    if above.size == 0:
        return x
    start = max(0, above[0] * n - int(pre * SR))
    tail = np.where(d > tail_db)[0]
    end = min(len(x), (tail[-1] + 1) * n + int(post * SR))
    return x[start:end]


def dc_block(x):
    np = _np()
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    return np.fft.irfft(np.fft.rfft(x) * (f >= 25), len(x))


def fades(x, fin, fout):
    np = _np()
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if 0 < a < len(x):
        x[:a] *= np.linspace(0, 1, a)
    if 0 < b < len(x):
        x[-b:] *= np.linspace(1, 0, b) ** 2
    return x


def varispeed(x, rate):
    """play at `rate` (0.82 = deeper and 1/0.82 longer, like a slowed tape): band-limited polyphase resampling"""
    from scipy.signal import resample_poly
    f = Fraction(1.0 / rate).limit_denominator(200)
    return resample_poly(x, f.numerator, f.denominator)


def lowpass(x, fc, order):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(order, fc, fs=SR, output='sos'), x)


def tail_fade(x, start_frac):
    np = _np()
    x = x.copy()
    s = int(start_frac * len(x))
    x[s:] *= np.cos(np.linspace(0, np.pi / 2, len(x) - s)) ** 2
    return x


def limit(x, ceil_db=CEIL_DB, radius_ms=40.0, report=False):
    """look-ahead brickwall: each sample's gain is the mean of a min-filter whose reach covers the averaging window, so
    it never exceeds what that sample needs (the ceiling holds exactly) and moves over ~radius_ms (no clicks)"""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    np = _np()
    c = 10 ** (ceil_db / 20)
    need = np.minimum(1.0, c / np.maximum(np.abs(x), 1e-12))
    if need.min() >= 1.0:
        return (x.copy(), 0.0) if report else x.copy()
    r = max(1, int(radius_ms * SR / 1000))
    g = np.minimum(uniform_filter1d(minimum_filter1d(need, size=2 * r + 1, mode='nearest'), size=r, mode='nearest'), need)
    return (x * g, float(20 * np.log10(g.min()))) if report else x * g


def compress(x, ratio=2.5, below_peak_db=12.0, knee_db=6.0, win_ms=10.0, smooth_ms=30.0):
    """a soft-knee vox compressor (10 ms RMS sense, 30 ms gain glide): the BO3 exerts are far more dynamic than BO6's
    mastered vox, so a short grunt cannot sit beside them on gain alone without a limiter crushing its attack"""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    np = _np()
    w = max(1, int(win_ms * SR / 1000))
    edb = 10 * np.log10(np.maximum(uniform_filter1d(x * x, size=w, mode='nearest'), 0.0) + 1e-20)   # the running mean can dip a hair under 0
    over = edb - (edb.max() - below_peak_db)
    gr = np.where(over <= -knee_db / 2, 0.0, np.where(over >= knee_db / 2, over * (1 - 1 / ratio),
                                                      (1 - 1 / ratio) * (over + knee_db / 2) ** 2 / (2 * knee_db)))
    r = max(1, int(smooth_ms * SR / 1000))
    g = uniform_filter1d(minimum_filter1d(10 ** (-gr / 20), size=2 * r + 1, mode='nearest'), size=r, mode='nearest')
    return x * g


def level_kwin(x, target, ceil_db=-0.3, max_limit_db=3.0):
    """gain onto the kwin target, but never more than max_limit_db of limiting: a take that cannot get there clean stops
    short (its reached level is in the manifest) instead of being crushed"""
    np = _np()
    k0 = kwin(x)
    for t in np.arange(target, target - 9.0, -0.25):
        y, gr = limit(x * 10 ** ((t - k0) / 20), ceil_db=ceil_db, radius_ms=25.0, report=True)
        if gr >= -max_limit_db:
            return y
    return limit(x * 10 ** ((target - 9.0 - k0) / 20), ceil_db=ceil_db, radius_ms=25.0)


def level_lufs(x, target):
    y = x * 10 ** ((target - lufs(x)) / 20)
    for _ in range(4):
        y = limit(y)
        d = target - lufs(y)
        if abs(d) < 0.05:
            break
        y = y * 10 ** (d / 20)
    return limit(y)


# ---- rendering -------------------------------------------------------------------------------------------------------
def render_vox(spec, src_path):
    x = read_mono(src_path)
    if spec['mode'] == 'as_is':
        y = compress(fades(dc_block(trim(x)), 0.003, 0.04))
    elif spec['mode'] == 'death':
        y = trim(x)
        y = lowpass(varispeed(dc_block(y), spec['rate']), spec['lpf'], spec['lpf_order'])
        y = fades(tail_fade(compress(y), spec['fade_from']), 0.003, 0.02)   # compress BEFORE the fade, or it undoes it
    elif spec['mode'] == 'growl':
        y = trim(x)
        y = lowpass(varispeed(dc_block(y), spec['rate']), spec['lpf'], spec['lpf_order'])
        y = fades(trim(y, tail_db=-50.0, post=0.04), 0.03, 0.12)
    else:
        raise ValueError(spec['mode'])
    return level_kwin(y, spec['kwin'])


def render_jingle(spec, src_path):
    x = read_mono(src_path)                              # (L+R)/2: a machine is a point in the world
    x = trim(x, head_db=-60.0, tail_db=-60.0, pre=0.0, post=0.35)
    x = fades(dc_block(x), 0.002, 0.30)
    return level_lufs(x, JINGLE_LUFS[spec['kind']])


def outputs():
    """[(rel path under sound_assets, kind, spec, source key)] in a fixed order"""
    out = []
    for spec in VOX:
        for i, s in enumerate(spec['src']):
            out.append(('%s/tod_mangler_%s_%d.wav' % (VOX_DIR, spec['fam'], i + 1), 'vox', spec, 't7:' + RAZ + s + '.wav'))
    for spec in JINGLES:
        out.append(('%s/%s.wav' % (JINGLE_DIR, spec['alias']), 'jingle', spec, 'sat:' + spec['sat'] + '.wav'))
    return out


def source_path(key):
    kind, rel = key.split(':', 1)
    if kind == 't7':
        return os.path.join(SRC_CACHE, 't7', rel)
    return os.path.join(SAT_DIR, rel)


def extract_t7():
    members = sorted({k.split(':', 1)[1] for _, _, _, k in outputs() if k.startswith('t7:')})
    todo = [m for m in members if not os.path.exists(os.path.join(SRC_CACHE, 't7', m))]
    if not todo:
        return
    if not os.path.exists(T7_ARCHIVE):
        sys.exit('T7 Assets archive not found: %s' % T7_ARCHIVE)
    tmp = os.path.join(SRC_CACHE, '_x')
    os.makedirs(tmp, exist_ok=True)
    args = [SEVEN_ZIP, 'x', '-y', '-o' + tmp, T7_ARCHIVE] + [T7_PREFIX + '\\' + m.replace('/', '\\') for m in todo]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('7-Zip failed (%d): %s' % (r.returncode, r.stdout[-400:] + r.stderr[-400:]))
    for m in todo:
        got = os.path.join(tmp, T7_PREFIX, m)
        if not os.path.exists(got):
            sys.exit('7-Zip did not produce %s' % m)
        dst = os.path.join(SRC_CACHE, 't7', m)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(got, dst)
    shutil.rmtree(tmp, ignore_errors=True)


def fnv1a64(s):
    h = 0xCBF29CE484222325
    for b in s.encode():
        h = ((h ^ b) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def pairing():
    """prove every jingle's BO6 payload id against the dumped bank table that names it"""
    out = {}
    for spec in JINGLES:
        rows = json.load(open(os.path.join(BO6_BANKS, spec['bank']), encoding='utf-8'))
        want = format(fnv1a64(spec['alias']), 'x')
        hits = [r for r in rows if r['snd'] == spec['sat'] and r['alias'] in (spec['alias'], want)]
        if len(hits) != 1:
            sys.exit('BO6 pairing failed for %s (%s in %s): %r' % (spec['alias'], spec['sat'], spec['bank'], hits))
        out[spec['alias']] = dict(payload=spec['sat'], bank=spec['bank'], bank_alias=hits[0]['alias'],
                                  by=('name' if hits[0]['alias'] == spec['alias'] else 'fnv1a64'))
    return out


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def render_all():
    """-> {rel: (bytes, info)} rendered from the sources"""
    np = _np()
    res = {}
    for rel, kind, spec, key in outputs():
        p = source_path(key)
        if not os.path.exists(p):
            sys.exit('missing source %s (%s)' % (p, key))
        y = render_vox(spec, p) if kind == 'vox' else render_jingle(spec, p)
        b = encode(y)
        info = dict(path=rel, sha256=sha256(b), bytes=len(b), secs=round(len(y) / SR, 3), kind=kind,
                    source=key.split(':', 1)[1] if key.startswith('t7:') else 'SATPerksAssets/_wetegg/sat/perks/' + key.split(':', 1)[1],
                    source_from=('T7 Assets V2.8.rar' if key.startswith('t7:') else 'SATPerksAssets (BO6 payload)'),
                    source_sha256=sha256(open(p, 'rb').read()),
                    peak_db=round(peak_db(y), 2), kwin=round(kwin(y), 2), lufs=round(lufs(y), 2),
                    process=(spec['mode'] if kind == 'vox' else 'jingle:' + spec['kind']))
        res[rel] = (b, info)
    return res


# ---- the tables --------------------------------------------------------------------------------------------------------
def files_of(fam):
    spec = next(s for s in VOX if s['fam'] == fam)
    return ['%s/tod_mangler_%s_%d.wav' % (VOX_DIR, fam, i + 1) for i in range(len(spec['src']))]


def row(fields):
    return ','.join(fields.get(h, '') for h in HEADER)


def vox_csv_text():
    lines = [','.join(HEADER)]
    for name, fam, vol, dmin, ddry, dwet, ent in VOX_ROWS:
        for rel in files_of(fam):
            lines.append(row(dict(Name=name, FileSpec=rel.replace('/', '\\'), Template='UIN_MOD', Bus='BUS_FX',
                                  VolMin=str(vol), VolMax=str(vol), DistMin=str(dmin), DistMaxDry=str(ddry),
                                  DistMaxWet=str(dwet), EntityLimitCount=str(ent), EntityLimitType='oldest',
                                  PanType='3d', Looping='NONLOOPING')))
    return '\n'.join(lines) + '\n'


def jingle_csv_text():
    lines = [','.join(HEADER)]
    for spec in JINGLES:
        f = dict(STOCK_JINGLE_ROW)
        f.update(Name=spec['alias'], FileSpec=('%s/%s.wav' % (JINGLE_DIR, spec['alias'])).replace('/', '\\'))
        lines.append(row(f))
    return '\n'.join(lines) + '\n'


TABLES = {VOX_TABLE: vox_csv_text, JINGLE_TABLE: jingle_csv_text}


# ---- build -----------------------------------------------------------------------------------------------------------
def build(out_root):
    extract_t7()
    pair = pairing()
    res = render_all()
    for rel, (b, info) in res.items():
        p = os.path.join(out_root, 'sound_assets', rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not os.path.exists(p) or open(p, 'rb').read() != b:
            open(p, 'wb').write(b)
        print('%-52s %5.2fs kwin %6.2f lufs %6.2f peak %5.2f  <- %s' % (rel, info['secs'], info['kwin'], info['lufs'],
                                                                         info['peak_db'], info['source'][-46:]))
    # no stray wav in the two folders this tool owns
    for d in (VOX_DIR, JINGLE_DIR):
        full = os.path.join(out_root, 'sound_assets', d)
        for f in sorted(os.listdir(full)):
            if d + '/' + f not in res:
                os.remove(os.path.join(full, f))
                print('removed stray', d + '/' + f)
    tables = {}
    for name, fn in TABLES.items():
        text = fn()
        p = os.path.join(out_root, 'sound', 'aliases', name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not os.path.exists(p) or open(p, encoding='utf-8', newline='').read() != text:
            open(p, 'w', encoding='utf-8', newline='').write(text)
        tables[name] = sha256(text.encode())
    man = dict(tool='tools/original_rips/make_original_rips.py', files=[info for _, info in res.values()],
               tables=tables, bo6_pairing=pair,
               sources=dict(t7=T7_ARCHIVE.replace(HOME, '~'), sat=SAT_DIR.replace(HOME, '~'), bo6_banks=BO6_BANKS.replace(HOME, '~')))
    open(MANIFEST, 'w', encoding='utf-8', newline='\n').write(json.dumps(man, indent=1) + '\n')
    print('manifest: %d files, 2 tables -> %s' % (len(res), os.path.relpath(MANIFEST, REPO)))


# ---- the gate ----------------------------------------------------------------------------------------------------------
def check(root, man=None):
    bad = []
    if man is None:
        if not os.path.exists(MANIFEST):
            return ['no manifest (%s)' % os.path.relpath(MANIFEST, REPO)]
        man = json.load(open(MANIFEST, encoding='utf-8'))
    want = {rel for rel, _, _, _ in outputs()}
    have = {f['path'] for f in man['files']}
    if want != have:
        bad.append('the manifest lists %d files, the tool renders %d (stale manifest)' % (len(have), len(want)))
    for f in man['files']:
        p = os.path.join(root, 'sound_assets', f['path'])
        if not os.path.exists(p):
            bad.append('missing sound_assets/%s' % f['path'])
            continue
        b = open(p, 'rb').read()
        if sha256(b) != f['sha256']:
            bad.append('changed sound_assets/%s' % f['path'])
        try:
            with wave.open(io.BytesIO(b)) as w:
                if (w.getnchannels(), w.getframerate(), w.getsampwidth()) != (1, SR, 2):
                    bad.append('%s is not mono 48 kHz 16-bit' % f['path'])
                secs = w.getnframes() / float(SR)
                lo, hi = (0.2, 3.0) if f['kind'] == 'vox' else (4.0, 120.0)
                if not lo <= secs <= hi:
                    bad.append('%s is %.2f s (want %.1f-%.1f)' % (f['path'], secs, lo, hi))
        except wave.Error as e:
            bad.append('%s unreadable: %s' % (f['path'], e))
    for d in (VOX_DIR, JINGLE_DIR):
        full = os.path.join(root, 'sound_assets', d)
        if os.path.isdir(full):
            for fn in sorted(os.listdir(full)):
                if d + '/' + fn not in have:
                    bad.append('stray sound_assets/%s/%s (no manifest row: dead weight in the bank or a hand edit)' % (d, fn))
    for name, fn in TABLES.items():
        p = os.path.join(root, 'sound', 'aliases', name)
        if not os.path.exists(p):
            bad.append('sound/aliases/%s missing' % name)
            continue
        text = open(p, encoding='utf-8', newline='').read()
        if text != fn():
            bad.append('sound/aliases/%s differs from the generated table' % name)
        rows = list(csv.DictReader(io.StringIO(text)))
        for r in rows:
            for col in ('ContextType', 'ContextValue', 'ContextType1', 'ContextValue1'):
                if (r.get(col) or '').strip():
                    bad.append('%s row %s carries %s (this map sets no sound context: silent)' % (name, r['Name'], col))
            if (r.get('PanType') or '').lower() != '3d' or (r.get('Looping') or '').lower() != 'nonlooping':
                bad.append('%s row %s must be 3d NONLOOPING' % (name, r['Name']))
            if r['FileSpec'].replace('\\', '/') not in have:
                bad.append('%s row %s points at %s, which this tool does not ship' % (name, r['Name'], r['FileSpec']))
    try:
        szc = json.load(open(os.path.join(root, SZC), encoding='utf-8-sig'))
        for name in TABLES:
            n = sum(1 for s in szc.get('Sources', []) if s.get('Type') == 'ALIAS' and s.get('Filename') == name)
            if n != 1:
                bad.append('the sound zone config loads %s %d times (want 1: one {"Type": "ALIAS", "Name": "%s", '
                           '"Filename": "%s", "Specs": []} in %s)' % (name, n, name[:-4], name, SZC.replace('\\', '/')))
    except (OSError, ValueError) as e:
        bad.append('szc unreadable: %s' % e)
    for rel, needles in WIRING.items():
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            bad.append('%s missing' % rel)
            continue
        text = open(p, encoding='utf-8', errors='replace').read()
        code = re.sub(r'//[^\n]*', '', text)
        for what, pat in needles:
            if not re.search(pat, code):
                bad.append('%s: %s is not wired' % (os.path.basename(rel), what))
        for what, pat in FORBIDDEN.get(rel, []):
            if re.search(pat, code):
                bad.append('%s: %s is back' % (os.path.basename(rel), what))
    # every BO6 source name the lane emits for the Mangler has its row (check_wiring rule 2 sees the same from the tree)
    lane = os.path.join(root, GSC + '_tod_bo6_audio.gsc')
    if os.path.exists(lane):
        names = set(re.findall(r'"(vox_ai_mangler_[a-z0-9_]+)"', open(lane, encoding='utf-8').read()))
        rows = {r[0] for r in VOX_ROWS}
        for n in sorted(names):
            if 'hb_bo6_' + n not in rows:
                bad.append('the BO6 lane emits %s but %s has no hb_bo6_%s row' % (n, VOX_TABLE, n))
        for r in sorted(rows):
            if r[len('hb_bo6_'):] not in names:
                bad.append('%s ships %s but the BO6 lane never emits it (dead row)' % (VOX_TABLE, r))
    return bad


def verify_sources(root):
    extract_t7()
    pairing()
    res = render_all()
    bad = []
    for rel, (b, info) in res.items():
        p = os.path.join(root, 'sound_assets', rel)
        if not os.path.exists(p) or open(p, 'rb').read() != b:
            bad.append('sound_assets/%s does not re-render byte-for-byte from its original' % rel)
    return bad


# ---- the planted-error controls ---------------------------------------------------------------------------------------
def selftest():
    man = json.load(open(MANIFEST, encoding='utf-8'))
    stage = os.path.join(REPO, 'tmp', 'wave2', 'W2F-original-rips', 'stage')
    src_root = stage if os.path.exists(os.path.join(stage, 'sound_assets', VOX_DIR)) else REPO
    cases = [
        ('clean', None, None),
        ('a wav changed', lambda d: open(os.path.join(d, 'sound_assets', VOX_DIR, 'tod_mangler_pain_1.wav'), 'r+b').write(b'RIFX'), 'changed'),
        ('a wav missing', lambda d: os.remove(os.path.join(d, 'sound_assets', JINGLE_DIR, 'mus_perk_phd_stinger.wav')), 'missing'),
        ('a stray wav', lambda d: shutil.copy(os.path.join(d, 'sound_assets', VOX_DIR, 'tod_mangler_roar_1.wav'),
                                             os.path.join(d, 'sound_assets', VOX_DIR, 'tod_mangler_roar_9.wav')), 'stray'),
        ('a hand-edited row', lambda d: _sed(os.path.join(d, 'sound', 'aliases', VOX_TABLE), ',95,95,', ',99,99,', 1), 'differs'),
        ('a table not loaded', lambda d: _sed(os.path.join(d, SZC), '"tod_perk_jingles.csv"', '"tod_perk_jingles_x.csv"', 1), 'loads tod_perk_jingles.csv 0'),
        ('PhD back on Mule Kick', lambda d: _sed(os.path.join(d, GSC + '_tod_perk_phd.gsc'), '"mus_perk_phd_jingle"', '"mus_perks_mulekick_jingle"', 1), 'Mule Kick'),
        ('Death Perception back on the stock Speed Cola default', lambda d: _sed(os.path.join(d, GSC + '_tod_perk_electric_cherry.gsc'),
                                                   'use_trigger.script_label  = "mus_perk_deathperception_stinger";', '', 1), 'Death Perception stinger'),
        ('the Mangler bail-out back', lambda d: _sed(os.path.join(d, GSC + '_tod_bo6_audio.gsc'), 'if ( kind == "mangler" )\n    {\n        self mangler_pain_watch();',
                                                     'if ( kind == "mangler" ) return;\n    {\n        self mangler_pain_watch();', 1), 'bail-out'),
        ('a dead vox row', lambda d: _sed(os.path.join(d, GSC + '_tod_bo6_audio.gsc'), '"vox_ai_mangler_shoot", TOD_MANGLER_VOX_SHOOT_F', '"vox_ai_mangler_shout", TOD_MANGLER_VOX_SHOOT_F', 1), 'vox_ai_mangler_shout'),
    ]
    fails = 0
    for label, plant, expect in cases:
        with tempfile.TemporaryDirectory() as d:
            for sub in ('sound_assets/' + VOX_DIR, 'sound_assets/' + JINGLE_DIR):
                shutil.copytree(os.path.join(src_root, sub), os.path.join(d, sub))
            for name in TABLES:
                os.makedirs(os.path.join(d, 'sound', 'aliases'), exist_ok=True)
                open(os.path.join(d, 'sound', 'aliases', name), 'w', encoding='utf-8', newline='').write(TABLES[name]())
            os.makedirs(os.path.join(d, 'sound', 'zoneconfig'), exist_ok=True)
            szc = json.load(open(os.path.join(REPO, SZC), encoding='utf-8-sig'))
            for name in TABLES:
                if not any(s.get('Filename') == name for s in szc['Sources']):
                    szc['Sources'].append(dict(Type='ALIAS', Name=name[:-4], Filename=name, Specs=[]))
            json.dump(szc, open(os.path.join(d, SZC), 'w'), indent=4)
            for rel in WIRING:
                os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
                s = os.path.join(stage, rel) if os.path.exists(os.path.join(stage, rel)) else os.path.join(REPO, rel)
                shutil.copy(s, os.path.join(d, rel))
            if plant:
                plant(d)
            bad = check(d, man)
            ok = (not bad) if expect is None else any(expect in b for b in bad)
            if not ok:
                fails += 1
                print('  SELFTEST FAIL [%s]: expected %s, got %s' % (label, expect or 'a pass', bad[:4]))
    print('ORIGINAL RIPS SELFTEST %s: %d cases' % ('OK' if not fails else 'FAILED', len(cases)))
    return fails == 0


def _sed(path, old, new, count):
    text = open(path, encoding='utf-8', newline='').read()
    if old not in text:
        raise AssertionError('selftest plant: %r not in %s' % (old[:60], path))
    open(path, 'w', encoding='utf-8', newline='').write(text.replace(old, new, count))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cmd', nargs='?', default='')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--verify-sources', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--root', default=REPO)
    ap.add_argument('--out', default=REPO)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.check or a.cmd == 'check':
        bad = check(os.path.abspath(a.root))
        if bad:
            for b in bad[:12]:
                print('  FAIL ' + b)
            print('ORIGINAL RIPS STALE (%d) - %s' % (len(bad), FIX))
            sys.exit(1)
        man = json.load(open(MANIFEST, encoding='utf-8'))
        print('ORIGINAL RIPS OK: %d files (%d Mangler voice, %d machine music), 2 tables, wiring in 3 scripts, root=%s'
              % (len(man['files']), sum(f['kind'] == 'vox' for f in man['files']),
                 sum(f['kind'] == 'jingle' for f in man['files']), os.path.abspath(a.root)))
        return
    if a.verify_sources:
        bad = verify_sources(os.path.abspath(a.root))
        for b in bad:
            print('  FAIL ' + b)
        print('ORIGINAL RIPS SOURCES %s' % ('OK: every file re-renders byte-for-byte' if not bad else 'DIFFER (%d)' % len(bad)))
        sys.exit(1 if bad else 0)
    if a.cmd == 'build':
        build(os.path.abspath(a.out))
        return
    ap.print_help()


if __name__ == '__main__':
    main()
