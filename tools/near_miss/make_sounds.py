"""THE NEAR MISS + THE HOT STREAK - their eight sounds (docs/201): synthesised, deterministic, GENERATED - never
hand-edit the wavs or the aliases; change this script and re-run it.

  python tools/near_miss/make_sounds.py            write sound_assets/tod/near/tod_*.wav and sound/aliases/tod_near.csv
                                                   (a file whose bytes did not change is left alone), and register
                                                   tod_near.csv in sound/zoneconfig/zm_tod2_cybercity.szc if it is
                                                   missing (a copy of the tod_luck entry, placed right after it)
  python tools/near_miss/make_sounds.py --check    synthesise everything again IN MEMORY and FAIL (exit 1,
                                                   "NEAR MISS SOUNDS STALE: <what> - run python tools/near_miss/make_sounds.py")
                                                   if a wav is missing or differs, the csv is missing or differs, or the
                                                   zone config does not load tod_near.csv; else "NEAR MISS SOUNDS OK: 8 sounds"
  python tools/near_miss/make_sounds.py --out DIR  a preview: the wavs only, into DIR (nothing in the repo is touched)
  python tools/near_miss/make_sounds.py --calibrate
                                                   measure each sound (BS.1770, needs scipy) and print the soft-limiter
                                                   drive / trim that lands it on its target loudness: bake those two
                                                   numbers into SOUNDS after changing a synth or a target

PLACEHOLDERS: every one of these is a synthesised stand-in, made to the right length, shape and loudness so the
timing can be judged in a match. An authored set can replace them BY NAME (same file names, same alias rows).

THE AUTHORED LANE (PK17, 2026-10-05): tools/near_miss/authored.json names a cue's AUTHORED wav by its sha256 and
frame count (written by tools/sfx/w2c_sounds/make_sounds.py: each authored cue keeps the placeholder's musical spine,
rebuilt from the building blocks below, under recorded textures). For a name it lists, --check accepts the file on
disk when its bytes hash to that sha AND it is exactly the placeholder's length in frames (the spin and the card
pull are timed to these lengths); the plain run never overwrites it with the placeholder. A name it does not list
is held to the synthesised bytes, as before. Delete an entry to fall back to the placeholder (re-run to rewrite it).

THE BLACK MARKET (_tod_shop.gsc, docs/201 section 3):
  tod_spin_teeter      2D, 0.50 s   STOPPED SHORT: the needle on the seam of a better tile. A ratchet of 12 clicks
                                    speeding up under a strained tone that climbs a minor third with a fast tremolo,
                                    cut off unresolved (the reel then falls back). A LEGENDARY tease plays the
                                    jackpot heartbeat instead.
  tod_spin_near        2D, 0.80 s   the "so close": two soft glassy notes falling (B5, then F5 bending down a
                                    semitone) over a short breath of air - deflated, never comic
THE CARD PULL (_tod_upgrade_ui.gsc, docs/201 section 4):
  tod_pull_reach       2D, 0.66 s   THE REACH: an air swell rising (a band sweeping 400 Hz -> 3 kHz) under a tone that
                                    climbs a fifth and hovers on a fast tremolo, held at full tension to the end
  tod_pull_reach_fail  2D, 0.45 s   SO CLOSE: the swell let go - a fast glide down (520 -> 170 Hz) with a muffled
                                    whump and a puff of air
  tod_pull_break       2D, 0.90 s   BREAK THROUGH: an impact (a noise crack + a 60 Hz thump) into a bright rising
                                    C-E-G-C bell arpeggio with a shimmer tail
THE HOT STREAK (_tod_luck.gsc, docs/201 section 5):
  tod_heat_up          2D, 0.80 s   WARM / HEATING UP: an ignition whoosh (a band sweeping 300 Hz -> 2.5 kHz) with
                                    sparse fire crackle
  tod_heat_fire        2D, 1.30 s   ON FIRE: a bigger whoosh over a low roar (60-300 Hz) and dense crackle, crowned by
                                    a bright rising two-note stinger
  tod_heat_out         2D, 0.70 s   the streak ends: a steam hiss (3-9 kHz) falling away over a soft tone gliding down

Every file is mono 48 kHz 16-bit, peak -1.5 dBFS, DC-blocked, faded in (3 ms) and out, so it starts and ends on
silence and never clicks. The aliases take tod_ui.csv's header row verbatim and are shaped like its tod_pull_* rows
(Template UIN_MOD, PanType 2d, NONLOOPING, no Bus = the UI bus the card reveal already plays on). No row has a
ContextType / ContextValue (a context makes a sound silent in this map: tools/lint_tod_sound_context.js) and none
randomises pitch. Every generator is seeded, so --check is byte-exact.
"""
import csv, hashlib, io, json, pathlib, re, sys, wave
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
SR = 48000
PEAK_DB = -1.5
WAV_DIR = ROOT / 'sound_assets/tod/near'
CSV_PATH = ROOT / 'sound/aliases/tod_near.csv'
HEADER_FROM = ROOT / 'sound/aliases/tod_ui.csv'
SZC = ROOT / 'sound/zoneconfig/zm_tod2_cybercity.szc'
AUTHORED = ROOT / 'tools/near_miss/authored.json'
FIX = 'run python tools/near_miss/make_sounds.py'


def authored():
    """{name: {"sha256": ..., "frames": ...}} - the cues an authored wav replaces (THE AUTHORED LANE above)"""
    if not AUTHORED.exists():
        return {}
    return json.loads(AUTHORED.read_text(encoding='utf-8'))


def frames_of(data):
    with wave.open(io.BytesIO(data)) as w:
        return w.getnframes(), w.getnchannels(), w.getframerate(), w.getsampwidth()


# ---------------------------------------------------------------------------------------------- building blocks
def timeline(secs):
    n = int(round(secs * SR))
    return n, np.arange(n) / SR


def shaped_noise(n, lo, hi, seed):
    """white noise band-limited to lo..hi Hz in the frequency domain, peak 1"""
    rng = np.random.default_rng(seed)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    gain = ((f >= lo) & (f <= hi)).astype(float)
    x = np.fft.irfft(spec * gain, n)
    return x / (np.max(np.abs(x)) + 1e-12)


def env(t, a, d):
    """0 before t = 0, a linear attack of a s, then an exponential decay with time constant d s"""
    return np.clip(t / max(a, 1e-4), 0, 1) * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def sweep_band(x, fc, q):
    """x through a band-pass whose centre follows fc (one value per sample): a trapezoidal state-variable filter"""
    k = 1.0 / q
    g = np.tan(np.pi * np.clip(fc, 20.0, 0.45 * SR) / SR)
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    xs, A1, A2, A3 = x.tolist(), a1.tolist(), a2.tolist(), a3.tolist()
    out = [0.0] * len(xs)
    ic1 = ic2 = 0.0
    for i in range(len(xs)):
        v3 = xs[i] - ic2
        v1 = A1[i] * ic1 + A2[i] * v3
        v2 = ic2 + A2[i] * ic1 + A3[i] * v3
        ic1 = 2.0 * v1 - ic1
        ic2 = 2.0 * v2 - ic2
        out[i] = k * v1
    return np.array(out)


def glide(t, f0, f1, secs):
    """the phase of a tone gliding from f0 to f1 Hz over secs (exponential in pitch), then holding f1"""
    u = np.clip(t / secs, 0, 1)
    f = f0 * (f1 / f0) ** u
    return 2 * np.pi * np.cumsum(f) / SR


BELL = ((1.0, 1.0, 1.0), (1.0019, 0.3, 0.9), (2.0, 0.18, 0.5), (2.76, 0.22, 0.35), (5.4, 0.07, 0.18))


def strike(n, t0, f0, tau, amp=1.0, partials=BELL, attack=0.004):
    """one struck bell note at t0 s: decaying partials under a raised-cosine attack (no click)"""
    i0 = int(round(t0 * SR))
    L = min(int(7 * tau * SR) + 1, n - i0)
    if L <= 0:
        return np.zeros(n)
    k = np.arange(L) / SR
    y = np.zeros(L)
    for r, a, d in partials:
        if f0 * r < 17000:
            y += a * np.sin(2 * np.pi * f0 * r * k) * np.exp(-k / (tau * d))
    y *= np.where(k < attack, 0.5 - 0.5 * np.cos(np.pi * k / attack), 1.0) * amp
    out = np.zeros(n)
    out[i0:i0 + L] += y
    return out


def clicks(n, seed, times, lo, hi, amp=1.0, tau=0.004):
    """short filtered clicks at the given times (s)"""
    rng = np.random.default_rng(seed)
    out = np.zeros(n)
    burst = shaped_noise(int(0.03 * SR), lo, hi, seed + 1)
    k = np.arange(len(burst)) / SR
    shape = burst * np.exp(-k / tau)
    for t0 in times:
        i0 = int(round(t0 * SR))
        if i0 >= n:
            continue
        L = min(len(shape), n - i0)
        out[i0:i0 + L] += shape[:L] * amp * (0.7 + 0.3 * rng.random())
    return out


def crackle(n, seed, count, t_from, t_span, amp):
    rng = np.random.default_rng(seed)
    times = np.sort(t_from + rng.random(count) * t_span)
    return clicks(n, seed + 7, times, 1500, 7000, amp, tau=0.002)


def one_shot(x, fade_out, fade_in=0.003):
    """DC-blocked (the mean of a 16 Hz zero-phase high-pass), faded in and out: starts and ends on silence"""
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    x = np.fft.irfft(np.fft.rfft(x) * (f >= 16), len(x))
    n_in, n_out = int(fade_in * SR), int(fade_out * SR)
    x[:n_in] *= np.linspace(0, 1, n_in)
    x[-n_out:] *= np.linspace(1, 0, n_out) ** 2
    return x


def level(x, drive, gain_db):
    """THE LOUDNESS: peak-normalise, then a soft limiter (tanh(d x) / tanh(d): the identity at d = 0 and continuous
    from there, so a larger `drive` lifts a quiet transient sound toward its target without raising its peak) and a
    trim (`gain_db` <= 0 turns a hot one down). Both numbers are baked into SOUNDS from `--calibrate`, so the build
    path stays plain numpy and byte-exact."""
    x = x / (np.max(np.abs(x)) + 1e-12)
    if drive > 1e-6:
        x = np.tanh(drive * x) / np.tanh(drive)
    return x * 10 ** ((PEAK_DB + gain_db) / 20)


def encode(x):
    """mono 48 kHz 16-bit PCM wav bytes (x already levelled)"""
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype('<i2')
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


# ---------------------------------------------------------------------------------------------- THE BLACK MARKET
def spin_teeter():
    n, t = timeline(0.50)
    # the ratchet: 12 clicks closing in (gaps shrink 55 -> 18 ms)
    gaps = np.linspace(0.055, 0.018, 12)
    times = np.concatenate([[0.0], np.cumsum(gaps)[:-1]])
    ratchet = clicks(n, 101, times, 900, 5000, 0.8)
    # the strain: a tone climbing a minor third (440 -> 523 Hz) with a fast tremolo that tightens
    ph = glide(t, 440.0, 523.25, 0.45)
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * (9 + 14 * t) * t)
    tone = (np.sin(ph) + 0.35 * np.sin(2 * ph)) * trem * smooth(t / 0.12) * 0.35
    x = ratchet + tone
    return one_shot(x, 0.02)


def spin_near():
    n, t = timeline(0.80)
    x = strike(n, 0.0, 987.77, 0.30, 0.75)                     # B5
    # F5, bending down a semitone as it rings (the deflate)
    i0 = int(0.14 * SR)
    k = t[i0:] - t[i0]
    ph = glide(k, 698.46, 659.26, 0.45)
    second = np.zeros(n)
    second[i0:] = (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.18 * np.sin(2.76 * ph)) * np.exp(-k / 0.28) * smooth(k / 0.006)
    air = shaped_noise(n, 600, 4000, 202) * env(t - 0.12, 0.05, 0.16) * 0.12
    return one_shot(x + 0.8 * second + air, 0.12)


# ------------------------------------------------------------------------------------------------- THE CARD PULL
def pull_reach():
    n, t = timeline(0.66)
    # the air swell: noise through a band climbing 400 Hz -> 3 kHz, growing louder to the end
    fc = 400.0 * (3000.0 / 400.0) ** smooth(t / 0.66)
    air = sweep_band(shaped_noise(n, 150, 9000, 303), fc, 2.2) * (0.15 + 0.85 * smooth(t / 0.6)) * 0.9
    # the tone: up a fifth (330 -> 494 Hz) over 0.35 s, then hovering on a 14 Hz tremolo
    ph = glide(t, 329.63, 493.88, 0.35)
    trem = np.where(t < 0.35, 1.0, 0.65 + 0.35 * np.sin(2 * np.pi * 14 * (t - 0.35)))
    tone = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)) * trem * smooth(t / 0.05) * 0.5
    return one_shot(air + tone, 0.03)


def pull_reach_fail():
    n, t = timeline(0.45)
    ph = glide(t, 520.0, 170.0, 0.3)
    tone = (np.sin(ph) + 0.3 * np.sin(2 * ph)) * env(t, 0.004, 0.16) * 0.7
    whump = np.sin(2 * np.pi * 70 * t) * env(t, 0.006, 0.09) * 0.8
    puff = shaped_noise(n, 300, 2500, 404) * env(t, 0.01, 0.07) * 0.25
    return one_shot(tone + whump + puff, 0.1)


def pull_break():
    n, t = timeline(0.90)
    crack = shaped_noise(n, 800, 12000, 505) * env(t, 0.001, 0.035) * 1.0
    thump = np.sin(2 * np.pi * 60 * t) * env(t, 0.003, 0.12) * 1.1
    bells = np.zeros(n)
    for i, f in enumerate((1046.50, 1318.51, 1567.98, 2093.0)):   # C6 E6 G6 C7, 55 ms apart
        bells += strike(n, 0.04 + 0.055 * i, f, 0.32, 0.55)
    shimmer = shaped_noise(n, 5000, 11000, 506) * env(t - 0.2, 0.08, 0.25) * 0.08
    return one_shot(crack + thump + bells + shimmer, 0.18)


# ---------------------------------------------------------------------------------------------- THE HOT STREAK
def heat_up():
    n, t = timeline(0.80)
    fc = 300.0 * (2500.0 / 300.0) ** smooth(t / 0.35)
    whoosh = sweep_band(shaped_noise(n, 100, 9000, 606), fc, 1.4) * env(t, 0.22, 0.25) * 1.0
    body = shaped_noise(n, 80, 600, 607) * env(t, 0.18, 0.22) * 0.35
    return one_shot(whoosh + body + crackle(n, 608, 14, 0.12, 0.55, 0.5), 0.12)


def heat_fire():
    n, t = timeline(1.30)
    fc = 250.0 * (3200.0 / 250.0) ** smooth(t / 0.45)
    whoosh = sweep_band(shaped_noise(n, 100, 10000, 707), fc, 1.2) * env(t, 0.3, 0.4) * 1.0
    roar = shaped_noise(n, 60, 300, 708) * env(t, 0.25, 0.45) * 0.7
    stinger = strike(n, 0.30, 784.0, 0.35, 0.5) + strike(n, 0.42, 1174.66, 0.45, 0.6)   # G5 then D6
    return one_shot(whoosh + roar + stinger + crackle(n, 709, 40, 0.1, 1.0, 0.55), 0.2)


def heat_out():
    n, t = timeline(0.70)
    hiss = shaped_noise(n, 3000, 9000, 808) * env(t, 0.015, 0.22) * 0.8
    ph = glide(t, 600.0, 200.0, 0.5)
    tone = np.sin(ph) * env(t, 0.01, 0.2) * 0.25
    return one_shot(hiss + tone, 0.15)


# ------------------------------------------------------------------------------------------------------ the aliases
# name, synth, VolMin/VolMax (the card reveal's rows sit at 86..95), target loudness (LUFS, BS.1770 gated - the
# shipped reveal sounds measure -8 .. -13: rung 1 -11.5, beat -13.0, super sting -8.6, spin stop -13.7), and the
# (drive, gain_db) that --calibrate found for that target - baked so the build path never measures anything.
SOUNDS = [
    ('tod_spin_teeter', spin_teeter, 84, -13.0, (0.622, 0.0)),
    ('tod_spin_near', spin_near, 88, -12.5, (1.029, 0.0)),
    ('tod_pull_reach', pull_reach, 88, -11.5, (0.0, -1.71)),
    ('tod_pull_reach_fail', pull_reach_fail, 86, -12.5, (2.002, 0.0)),
    ('tod_pull_break', pull_break, 92, -10.0, (2.081, 0.0)),
    ('tod_heat_up', heat_up, 88, -11.5, (1.475, 0.0)),
    ('tod_heat_fire', heat_fire, 92, -10.0, (2.153, 0.0)),
    ('tod_heat_out', heat_out, 82, -14.0, (2.003, 0.0)),
]


def render():
    """name -> wav bytes, all eight synthesised and levelled in memory"""
    return {name: encode(level(synth(), *lv)) for name, synth, _, _, lv in SOUNDS}


def lufs(x):
    """BS.1770-4 integrated loudness of a mono 48 kHz signal (K-weighting, 400 ms blocks at 75 % overlap, the
    -70 LUFS absolute and -10 LU relative gates). --calibrate only (it imports scipy; the build path never does)."""
    from scipy.signal import lfilter
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], x)
    y = lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    ms = np.array([np.mean(y[i:i + blk] ** 2) for i in range(0, max(1, len(y) - blk + 1), hop)])
    l = -0.691 + 10 * np.log10(ms + 1e-20)
    ms = ms[l > -70]
    if ms.size == 0:
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(ms)) - 10
    ms = ms[(-0.691 + 10 * np.log10(ms)) > rel]
    return float(-0.691 + 10 * np.log10(np.mean(ms)))


def calibrate():
    """print the (drive, gain_db) that brings each sound to its target loudness: drive first (a louder sound for the
    same peak), and a negative trim only when the plain normalised sound is already hotter than the target"""
    for name, synth, _, target, _ in SOUNDS:
        x = synth()
        base = lufs(level(x, 0.0, 0.0))
        if base >= target:
            drive, gain = 0.0, round(target - base, 2)
        else:
            lo, hi = 0.0, 12.0
            for _ in range(40):
                mid = (lo + hi) / 2
                if lufs(level(x, mid, 0.0)) < target:
                    lo = mid
                else:
                    hi = mid
            drive, gain = round(hi, 3), 0.0
        got = lufs(level(x, drive, gain))
        print('%-20s target %6.1f  plain %6.1f  ->  drive %6.3f  gain %6.2f dB  =  %6.2f LUFS' % (name, target, base, drive, gain, got))


def alias_csv():
    """sound/aliases/tod_near.csv as bytes: tod_ui.csv's header row verbatim, one 2D row per sound, CRLF"""
    header_line = HEADER_FROM.read_text(encoding='utf-8-sig').splitlines()[0]
    header = next(csv.reader([header_line]))
    col = {h: i for i, h in enumerate(header)}
    lines = [header_line]
    for name, _, vol, _, _ in SOUNDS:
        r = [''] * len(header)
        r[col['Name']] = name
        r[col['FileSpec']] = 'tod\\near\\' + name + '.wav'
        r[col['Template']] = 'UIN_MOD'
        r[col['VolMin']] = r[col['VolMax']] = str(vol)
        r[col['PanType']] = '2d'
        r[col['Looping']] = 'NONLOOPING'
        assert not any(c in v for v in r for c in ',"\r\n'), name + ': a field would need csv quoting'
        lines.append(','.join(r))
    return ('\r\n'.join(lines) + '\r\n').encode('utf-8')


def szc_loads_near(text):
    """does the sound zone config load tod_near.csv as an ALIAS source?"""
    try:
        data = json.loads(text)
    except ValueError:
        return False
    return any(isinstance(s, dict) and s.get('Type') == 'ALIAS' and str(s.get('Filename', '')).lower() == 'tod_near.csv'
               for s in data.get('Sources', []))


def szc_register():
    """add the tod_near ALIAS source if it is missing: a text copy of the tod_luck entry (so the file keeps its own
    style), placed right after it. True if added."""
    raw = SZC.read_bytes()
    bom = b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
    text = raw[len(bom):].decode('utf-8')
    if szc_loads_near(text):
        return False
    tpl = re.search(r'([ \t]*)(\{[^{}]*"Filename"\s*:\s*"tod_luck\.csv"[^{}]*\})', text)
    if not tpl:
        raise SystemExit('NEAR MISS SOUNDS: no tod_luck entry in %s to copy - add the tod_near ALIAS source by hand' % SZC)
    nl = '\r\n' if '\r\n' in text else '\n'
    clone = tpl.group(2).replace('"tod_luck.csv"', '"tod_near.csv"').replace('"tod_luck"', '"tod_near"')
    new = text[:tpl.end()] + ',' + nl + tpl.group(1) + clone + text[tpl.end():]
    if not szc_loads_near(new):
        raise SystemExit('NEAR MISS SOUNDS: %s would not parse with tod_near added - left untouched' % SZC)
    SZC.write_bytes(bom + new.encode('utf-8'))
    return True


def describe(data):
    with wave.open(io.BytesIO(data)) as w:
        return '%.3f s, %d ch, %d Hz' % (w.getnframes() / w.getframerate(), w.getnchannels(), w.getframerate())


def main():
    args = sys.argv[1:]
    if '--calibrate' in args:
        calibrate()
        return
    wavs = render()
    if '--out' in args:
        out_dir = pathlib.Path(args[args.index('--out') + 1])
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, data in wavs.items():
            (out_dir / (name + '.wav')).write_bytes(data)
            print('NEAR MISS SOUND PREVIEW', out_dir / (name + '.wav'), describe(data))
        return
    csv_bytes = alias_csv()
    lane = authored()
    if '--check' in args:
        bad = []
        for name, data in wavs.items():
            p = WAV_DIR / (name + '.wav')
            if not p.exists():
                bad.append(name + '.wav missing')
            elif name in lane:
                got = p.read_bytes()
                if hashlib.sha256(got).hexdigest() != lane[name].get('sha256'):
                    bad.append(name + '.wav is not the authored file authored.json names')
                elif frames_of(got) != frames_of(data):
                    bad.append(name + '.wav (authored) is %d frames / %d ch / %d Hz / %d B, the timing wants %d / %d / %d / %d'
                               % (frames_of(got) + frames_of(data)))
            elif p.read_bytes() != data:
                bad.append(name + '.wav differs')
        for name in lane:
            if name not in wavs:
                bad.append('authored.json names %s, which is not one of the eight' % name)
        norm = lambda b: b.replace(b'\r\n', b'\n')
        if not CSV_PATH.exists():
            bad.append('sound/aliases/tod_near.csv missing')
        elif norm(CSV_PATH.read_bytes()) != norm(csv_bytes):
            bad.append('sound/aliases/tod_near.csv differs')
        if not SZC.exists() or not szc_loads_near(SZC.read_bytes().decode('utf-8-sig')):
            bad.append('sound/zoneconfig/zm_tod2_cybercity.szc does not load tod_near.csv')
        if bad:
            print('NEAR MISS SOUNDS STALE: ' + '; '.join(bad) + ' - ' + FIX)
            sys.exit(1)
        print('NEAR MISS SOUNDS OK: %d sounds (%d authored, %d placeholder)' % (len(wavs), len(lane), len(wavs) - len(lane)))
        return
    WAV_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in wavs.items():
        p = WAV_DIR / (name + '.wav')
        if name in lane:
            print('NEAR MISS SOUND', p.name, '(authored - kept; authored.json)')
            continue
        same = p.exists() and p.read_bytes() == data
        if not same:
            p.write_bytes(data)
        print('NEAR MISS SOUND', p.name, describe(data), '(unchanged)' if same else '(written)')
    if not (CSV_PATH.exists() and CSV_PATH.read_bytes() == csv_bytes):
        CSV_PATH.write_bytes(csv_bytes)
    print('NEAR MISS ALIASES sound/aliases/tod_near.csv', [s[0] for s in SOUNDS])
    if szc_register():
        print('NEAR MISS SOUNDS: registered tod_near.csv in sound/zoneconfig/zm_tod2_cybercity.szc')


if __name__ == '__main__':
    main()
