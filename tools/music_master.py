#!/usr/bin/env python
"""Master the TOD II music from its ORIGINAL sources in ONE pass (2026-10-01, docs: sound_assets/tod/music/README.md).

Chain per track (all float, ffmpeg):
  decode -> soxr 48 k -> trim to the proven loop length -> 10 ms end fade
  -> low shelf (BASS_DB under SHELF_HZ)              the user's "50% less bass"
  -> makeup gain to the track's TARGET LUFS, capped so the limiter never works more than MAX_LIM dB
  -> 4x oversampled true-peak limiter at CEIL_DB   (one limiter, after the EQ: the old two-stage chain
                                                      limited the bass-heavy master first, then EQ'd, then limited again)
  -> soxr 48 k, triangular HP dither, 16-bit PCM.

usage: python tools/music_master.py [--measure] [--band-target -11.0] [--max-lim 3.0] [--out DIR] [names...]
  --measure: print the shelf'd loudness / true peak and the gain + limiter work every target would need, write nothing.
"""
import argparse, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(REPO, 'tmp', 'music_bass', 'src')
DL = os.path.join(os.path.expanduser('~'), 'Downloads')
OUT_DEFAULT = os.path.join(REPO, 'sound_assets', 'tod', 'music')

SHELF_HZ, BASS_DB, CEIL_DB = 200, -6.0, -0.2
BAND = 'band'
# name -> (source file, loop length in s (the shipped masters' proven trims; None = whole file), target LUFS or BAND)
TRACKS = {
    'tod_music_eclipse':   (os.path.join(SRC, '7CodDq8GKpk.webm'), 410.0, BAND),   # "La Clé des Champs" - N'to
    'tod_music_relay':     (os.path.join(SRC, 'az2LslUsw5o.webm'), 208.9, BAND),   # "Meteor Herd" instrumental
    'tod_music_cornfield': (os.path.join(SRC, 'TFEdFXArQz0.webm'), 141.5, BAND),   # "Cornfield Chase"
    'tod_music_city':      (os.path.join(SRC, 'Fod9QOQppKg.webm'), 199.4, BAND),   # "Una Mattina"
    'tod_ambient_music':   (os.path.join(SRC, 'admmPKa6lok.webm'), 455.4, BAND),   # "Reykjavik"
    'tod_music_withyou':   (os.path.join(SRC, 'withyou_instrumental.wav'), 166.3, BAND),  # the separated instrumental (tools/… see README)
    'tod_boss_music':      (os.path.join(DL, '115_Remastered_Extended.wav'), None, -12.2),
    'tod_fall_intro':      (os.path.join(DL, 'Deep Mystery.wav'), None, -12.9),
    'tod_music_ee':        (os.path.join(DL, '01. Falling To Pieces.flac'), None, -5.6),
    # 'tod_music_finale' (the Map One ending's closing song, -7.7 LUFS) retired whole 2026-10-05 (W2E): its master is in
    # archive/map1_carryover/sound_assets/tod/music/, and re-mastering it would put a retired file back in the build tree.
}

def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')

def measure(path):
    r = run(['ffmpeg', '-nostats', '-i', path, '-af', 'ebur128=framelog=quiet:peak=true', '-f', 'null', '-'])
    I = float(re.search(r'^\s+I:\s+(-?[\d.]+) LUFS', r.stderr, re.M).group(1))
    tp = float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', r.stderr).group(1))
    return I, tp

def prep(name, tmpdir):
    src, length, _ = TRACKS[name]
    assert os.path.exists(src), src
    af = ['aresample=48000:resampler=soxr:precision=28']
    if length:
        af.append('atrim=0:%s' % length)
        af.append('afade=t=out:st=%s:d=0.01' % (length - 0.01))
    af.append('lowshelf=f=%d:g=%s:width_type=q:w=0.7' % (SHELF_HZ, BASS_DB))
    out = os.path.join(tmpdir, name + '_shelf.wav')
    r = run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', ','.join(af), '-ar', '48000', '-ac', '2', '-c:a', 'pcm_f32le', out])
    assert r.returncode == 0, r.stderr
    return out

def finish(shelf, gain_db, out):
    af = ('volume=%.2fdB,aresample=192000:resampler=soxr:precision=28,'
          'alimiter=limit=%.4f:attack=5:release=200:level=disabled:latency=1,'
          'aresample=48000:resampler=soxr:precision=28:dither_method=triangular_hp') % (gain_db, 10 ** (CEIL_DB / 20))
    r = run(['ffmpeg', '-v', 'error', '-y', '-i', shelf, '-af', af, '-ar', '48000', '-sample_fmt', 's16', '-ac', '2', out])
    assert r.returncode == 0, r.stderr

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--measure', action='store_true')
    ap.add_argument('--band-target', type=float, default=-11.0)
    ap.add_argument('--max-lim', type=float, default=3.0)
    ap.add_argument('--out', default=OUT_DEFAULT)
    ap.add_argument('--source', action='append', default=[], help='name=path: master this track from another source file')
    ap.add_argument('--length', action='append', default=[], help='name=seconds: a different loop trim for that track')
    ap.add_argument('names', nargs='*')
    a = ap.parse_args()
    for kv in a.source:
        k, v = kv.split('=', 1); TRACKS[k] = (v, TRACKS[k][1], TRACKS[k][2])
    for kv in a.length:
        k, v = kv.split('=', 1); TRACKS[k] = (TRACKS[k][0], float(v), TRACKS[k][2])
    names = a.names or [n for n in TRACKS if os.path.exists(TRACKS[n][0])]
    tmpdir = tempfile.mkdtemp(prefix='tod_music_')
    for n in names:
        shelf = prep(n, tmpdir)
        I, tp = measure(shelf)
        target = a.band_target if TRACKS[n][2] == BAND else TRACKS[n][2]
        want = target - I
        headroom = CEIL_DB - tp
        gain = min(want, headroom + a.max_lim)
        work = max(0.0, gain - headroom)
        if a.measure:
            print('%-20s shelf: I=%.1f LUFS TP=%+.1f | target %.1f needs %+.1f dB -> gain %+.1f, limiter %.1f dB%s' %
                  (n, I, tp, target, want, gain, work, '' if want <= headroom + a.max_lim else '  (CAPPED, lands %.1f)' % (I + gain)))
            continue
        out = os.path.join(a.out, n + '.wav')
        finish(shelf, gain, out)
        I2, tp2 = measure(out)
        # the limiter itself costs loudness (level=disabled): converge on the target in up to two more passes,
        # never past the limiter cap
        for _ in range(2):
            if abs(I2 - target) <= 0.15 or gain >= headroom + a.max_lim - 0.05:
                break
            gain = min(gain + (target - I2), headroom + a.max_lim)
            work = max(0.0, gain - headroom)
            finish(shelf, gain, out)
            I2, tp2 = measure(out)
        print('%-20s -> %s | I=%.1f LUFS TP=%+.1f | gain %+.1f dB, limiter %.1f dB' % (n, os.path.relpath(out, REPO), I2, tp2, gain, work))
        os.remove(shelf)

if __name__ == '__main__':
    main()
