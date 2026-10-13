"""THE ORIGINAL RIPS - review sheet (wave 2 / W2F, 2026-10-05). Draws what make_original_rips.py ships beside what the
player hears today and the neighbours it was levelled against, so a reviewer can SEE the voice and the music without a
build: spectrograms of every Mangler voice family next to the Doppelghast's matching BO6 vox (the map's other elite
voice), every take's loudness against that neighbour, and the four machine-music envelopes next to what plays today
(Death Perception: Speed Cola's music, stock's default; PhD: Mule Kick's music) and the stock BO3 Juggernog jingle / the on-map Wisp Tea jingle.

    python tools/original_rips/make_review.py [--root ROOT] [--out PNG]

ROOT (default the W2F stage, else the repo) holds the shipped wavs. Reference wavs: the repo's hb_bo6_ghoul table, the
T7 dump (extracted once into tmp/original_rips/src/t7, read-only) and the SAT pack. Writes one PNG and nothing else.
"""
import argparse, csv, io, os, subprocess, sys
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import make_original_rips as M   # noqa: E402  (the shipping recipe's own meters)

STAGE = os.path.join(REPO, 'tmp', 'wave2', 'W2F-original-rips', 'stage')
OUT = os.path.join(REPO, 'art', 'generated', 'W2F-original-rips', '_review.png')
PRIVATE = r'C:\BO3Tools\TOD2Cybercity'
T7_REVIEW = ['sound_assets/mus/zombie/perksacola/mus_jugganog_jingle.wav', 'sound_assets/mus/zombie/perksacola/mus_jugganog_sting.wav',
             'sound_assets/mus/zombie/perksacola/mus_mulekick_jingle.wav', 'sound_assets/mus/zombie/perksacola/mus_mulekick_sting.wav',
             'sound_assets/mus/zombie/perksacola/mus_speed_jingle.wav', 'sound_assets/mus/zombie/perksacola/mus_speed_sting.wav']
# what each machine plays TODAY: Death Perception's hook never set script_sound / script_label, so it kept the default
# stock's perk_machine_spawn_init stamps on every machine (_zm_perks.gsc:1589-1591, Speed Cola's); PhD borrowed Mule Kick's
OLD_WHO = {'mus_speed_jingle': 'Speed Cola - stock default', 'mus_speed_sting': 'Speed Cola - stock default',
           'mus_mulekick_jingle': 'Mule Kick', 'mus_mulekick_sting': 'Mule Kick'}

FONT = r'C:\Windows\Fonts\consola.ttf'
FONTB = r'C:\Windows\Fonts\consolab.ttf'
BG, PANEL, INK, DIM, ACC, OLDC, REF = (12, 10, 20), (24, 20, 38), (232, 228, 245), (140, 132, 165), (0, 230, 255), (255, 92, 92), (255, 170, 60)


def font(size, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, size)


def t7_review_sources():
    todo = [m for m in T7_REVIEW if not os.path.exists(os.path.join(M.SRC_CACHE, 't7', m))]
    if todo:
        tmp = os.path.join(M.SRC_CACHE, '_x')
        os.makedirs(tmp, exist_ok=True)
        r = subprocess.run([M.SEVEN_ZIP, 'x', '-y', '-o' + tmp, M.T7_ARCHIVE] + [M.T7_PREFIX + '\\' + m.replace('/', '\\') for m in todo],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit('7-Zip failed: ' + r.stdout[-300:] + r.stderr[-300:])
        for m in todo:
            dst = os.path.join(M.SRC_CACHE, 't7', m)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.replace(os.path.join(tmp, M.T7_PREFIX, m), dst)
    return {os.path.basename(m)[:-4]: os.path.join(M.SRC_CACHE, 't7', m) for m in T7_REVIEW}


def load(p):
    y, sr = sf.read(p, always_2d=True, dtype='float64')
    x = y.mean(axis=1)
    if sr != M.SR:
        from scipy.signal import resample_poly
        x = resample_poly(x, M.SR, sr)
    return x


def colormap(v):
    """v in 0..1 -> a dark-violet / magenta / amber / white ramp (array of RGB)"""
    stops = np.array([[0.0, 8, 6, 16], [0.25, 60, 14, 90], [0.5, 190, 40, 120], [0.75, 255, 150, 50], [1.0, 255, 250, 220]])
    out = np.zeros(v.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(v, stops[:, 0], stops[:, c + 1])
    return out.astype(np.uint8)


def spectrogram(x, w, h, secs, fmax=8000.0):
    """log-magnitude STFT, 0..fmax, time axis fixed to `secs` so takes compare at one scale"""
    n, hop = 1024, 256
    need = int(secs * M.SR)
    x = np.concatenate([x[:need], np.zeros(max(0, need - len(x)))])
    frames = 1 + (len(x) - n) // hop
    win = np.hanning(n)
    S = np.abs(np.stack([np.fft.rfft(x[i * hop:i * hop + n] * win) for i in range(frames)], axis=1))
    f = np.fft.rfftfreq(n, 1.0 / M.SR)
    S = S[f <= fmax]
    db = 20 * np.log10(S + 1e-9)
    db = np.clip((db - (db.max() - 70)) / 70, 0, 1)
    img = Image.fromarray(colormap(db[::-1]), 'RGB').resize((w, h), Image.BILINEAR)
    return img


def envelope(draw, x, box, secs, colour):
    x0, y0, x1, y1 = box
    w = x1 - x0
    n = int(secs * M.SR)
    x = np.concatenate([x[:n], np.zeros(max(0, n - len(x)))])
    k = max(1, len(x) // w)
    seg = np.abs(x[:k * w]).reshape(w, k).max(axis=1)
    mid = (y0 + y1) / 2
    half = (y1 - y0) / 2
    for i, v in enumerate(seg):
        draw.line([(x0 + i, mid - v * half), (x0 + i, mid + v * half)], fill=colour)


def ghoul_refs(repo):
    rows = list(csv.DictReader(open(os.path.join(repo, 'sound', 'aliases', 'hb_bo6_ghoul.csv'), encoding='utf-8')))
    out = {}
    for r in rows:
        out.setdefault(r['Name'], []).append(os.path.join(repo, 'sound_assets', r['FileSpec'].replace('\\', '/')))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=STAGE if os.path.isdir(os.path.join(STAGE, 'sound_assets', M.VOX_DIR)) else REPO)
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    refs = ghoul_refs(REPO)
    t7 = t7_review_sources()
    W = 1900
    vox_rows = [  # family, alias, moment, neighbour alias
        ('roar', 'hb_bo6_vox_ai_mangler_roar', 'arrival (0.33 s after it appears) + the berserk roar at half health', 'hb_bo6_vox_ai_ghoul_roar'),
        ('melee', 'hb_bo6_vox_ai_mangler_melee', 'the swing grunt, clip frame 5 (the hit is 0.77 s)', 'hb_bo6_vox_ai_ghoul_attack'),
        ('melee', 'hb_bo6_vox_ai_mangler_shoot', 'the cannon bellow, clip frame 58 (the shot is frame 61)', 'hb_bo6_vox_ai_ghoul_attack'),
        ('pain', 'hb_bo6_vox_ai_mangler_pain', 'pain grunts, one per 1.6-2.6 s at most, never mid-attack', 'hb_bo6_vox_ai_ghoul_pain'),
        ('death', 'hb_bo6_vox_ai_mangler_death', 'the dying roar (derived: enrage take at 0.82 speed, faded)', 'hb_bo6_vox_ai_ghoul_death'),
        ('growl', 'hb_bo6_vox_ai_mangler_ambience', 'the hunting growl every 4-7 s (derived: 0.70 speed, helmet LPF)', 'hb_bo6_vox_ai_ghoul_ambience'),
    ]
    RH = 170
    jingles = [
        ('mus_perk_deathperception_jingle', 'DEATH PERCEPTION jingle', 'mus_speed_jingle', 'mus_jugganog_jingle'),
        ('mus_perk_deathperception_stinger', 'DEATH PERCEPTION purchase sting', 'mus_speed_sting', 'mus_jugganog_sting'),
        ('mus_perk_phd_jingle', 'PhD FLOPPER jingle', 'mus_mulekick_jingle', 'mus_jugganog_jingle'),
        ('mus_perk_phd_stinger', 'PhD FLOPPER purchase sting', 'mus_mulekick_sting', 'mus_jugganog_sting'),
    ]
    JH = 150
    H = 150 + 40 + len(vox_rows) * RH + 70 + len(jingles) * JH + 120
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((30, 22), 'THE ORIGINAL RIPS  -  W2F review (2026-10-05)', font=font(34, True), fill=ACC)
    d.text((30, 70), 'Mangler voice: Black Ops III Gorod Krovi Mangler (vox_raz_exert_*, 24 takes) + 2 cues derived from them.  '
           'Machine music: BO6 originals (SATPerks payloads, paired to the BO6 bank tables).', font=font(17), fill=INK)
    d.text((30, 96), 'OLD = what the player hears today.  NEW = what ships.  REF = the neighbour it was levelled against '
           '(loudest 300 ms K-weighted window for the voice, BS.1770 integrated for the music).', font=font(17), fill=DIM)
    y = 150
    d.text((30, y), 'THE MANGLER\'S VOICE   (OLD: silent - it had no voice at all)', font=font(24, True), fill=INK)
    y += 40
    for fam, alias, moment, nb in vox_rows:
        files = M.files_of(fam)
        d.rectangle([20, y, W - 20, y + RH - 12], fill=PANEL)
        d.text((34, y + 10), alias, font=font(19, True), fill=ACC)
        d.text((34, y + 36), moment, font=font(15), fill=INK)
        d.text((34, y + 58), '%d takes  (%s)' % (len(files), ', '.join(os.path.basename(f)[:-4].replace('tod_mangler_', '') for f in files[:6]) + (' ...' if len(files) > 6 else '')),
               font=font(14), fill=DIM)
        d.text((34, y + 80), 'OLD: silent', font=font(16, True), fill=OLDC)
        new = load(os.path.join(root, 'sound_assets', files[0]))
        ref = load(refs[nb][0])
        secs = 2.0
        sx = 640
        img.paste(spectrogram(new, 420, RH - 40, secs), (sx, y + 24))
        d.text((sx, y + 4), 'NEW take 1  0-8 kHz  2.0 s', font=font(13), fill=ACC)
        img.paste(spectrogram(ref, 420, RH - 40, secs), (sx + 440, y + 24))
        d.text((sx + 440, y + 4), 'REF ' + nb.replace('hb_bo6_', '') + ' take 1', font=font(13), fill=REF)
        # loudness: every take's kwin against the neighbour family's
        bx0, bx1 = sx + 880, W - 40
        d.text((bx0, y + 4), 'loudest-300ms LUFS per take (cyan) vs REF family (amber)', font=font(13), fill=DIM)
        kn = [M.kwin(load(os.path.join(root, 'sound_assets', f))) for f in files]
        kr = [M.kwin(load(p)) for p in refs[nb]]
        lo, hi = -20.0, -6.0
        def X(v):
            return bx0 + (min(max(v, lo), hi) - lo) / (hi - lo) * (bx1 - bx0)
        base = y + 30
        d.line([(bx0, base + 96), (bx1, base + 96)], fill=DIM)
        for t in range(int(lo), int(hi) + 1, 2):
            d.line([(X(t), base + 96), (X(t), base + 100)], fill=DIM)
            d.text((X(t) - 10, base + 102), str(t), font=font(11), fill=DIM)
        for i, v in enumerate(kn):
            yy = base + 6 + (i % 12) * 6
            d.ellipse([X(v) - 3, yy - 3, X(v) + 3, yy + 3], fill=ACC)
        for i, v in enumerate(kr):
            yy = base + 80 + (i % 3) * 5
            d.ellipse([X(v) - 3, yy - 3, X(v) + 3, yy + 3], fill=REF)
        d.text((bx0, base + 112), 'NEW mean %.1f  (%.1f..%.1f)   REF mean %.1f' % (np.mean(kn), min(kn), max(kn), np.mean(kr)), font=font(13), fill=INK)
        y += RH
    y += 20
    d.text((30, y), 'THE MACHINE MUSIC   (stock perk timer: a jingle at random every 30-60 s, the sting on every purchase)', font=font(24, True), fill=INK)
    y += 50
    sat_wisp = os.path.join(PRIVATE, 'sound_assets', '_wetegg', 'sat', 'perks', 'sound_3670ddce89016ad8.wav')
    if not os.path.exists(sat_wisp):
        sat_wisp = os.path.join(REPO, 'sound_assets', '_wetegg', 'sat', 'perks', 'sound_3670ddce89016ad8.wav')
    wisp_l = M.lufs(load(sat_wisp)) if os.path.exists(sat_wisp) else float('nan')
    for alias, label, old, ref in jingles:
        d.rectangle([20, y, W - 20, y + JH - 12], fill=PANEL)
        new = load(os.path.join(root, 'sound_assets', M.JINGLE_DIR, alias + '.wav'))
        refx = load(t7[ref])
        secs = max(len(new), len(refx), len(load(t7[old])) if old else 0) / M.SR
        d.text((34, y + 10), label, font=font(19, True), fill=ACC)
        d.text((34, y + 36), alias, font=font(14), fill=INK)
        d.text((34, y + 58), 'NEW %.1f s  %.1f LUFS' % (len(new) / M.SR, M.lufs(new)), font=font(14), fill=ACC)
        d.text((34, y + 78), 'REF stock %s  %.1f LUFS' % (ref.replace('mus_', ''), M.lufs(refx)), font=font(14), fill=REF)
        if old:
            ox = load(t7[old])
            d.text((34, y + 98), 'OLD %s (%s)  %.1f LUFS' % (old.replace('mus_', ''), OLD_WHO[old], M.lufs(ox)), font=font(14), fill=OLDC)
        else:
            d.text((34, y + 98), 'OLD silent (no script_sound / script_label)', font=font(14), fill=OLDC)
        if 'jingle' in alias:
            d.text((34, y + 116), 'on-map BO6 neighbour Wisp Tea jingle %.1f LUFS (vol 81.5)' % wisp_l, font=font(12), fill=DIM)
        ex0, ex1 = 640, W - 40
        lane = (JH - 30) // 3
        d.text((ex0, y + 2), 'envelopes on one time scale (%.0f s)' % secs, font=font(12), fill=DIM)
        envelope(d, new, (ex0, y + 16, ex1, y + 16 + lane - 4), secs, ACC)
        envelope(d, refx, (ex0, y + 16 + lane, ex1, y + 16 + 2 * lane - 4), secs, REF)
        if old:
            envelope(d, load(t7[old]), (ex0, y + 16 + 2 * lane, ex1, y + 16 + 3 * lane - 4), secs, OLDC)
        else:
            d.text((ex0 + 6, y + 16 + 2 * lane + 6), 'OLD: silent', font=font(14, True), fill=OLDC)
        y += JH
    d.text((30, y + 10), 'Not proven here: the in-game mix, 3D falloff and occlusion - the user\'s playtest judges those. '
           'tools/original_rips/make_original_rips.py --check is the build gate; --verify-sources re-renders every wav byte-for-byte.',
           font=font(15), fill=DIM)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    img.save(a.out, optimize=True)
    print('review sheet -> %s (%dx%d)' % (os.path.relpath(a.out, REPO), W, H))


if __name__ == '__main__':
    main()
