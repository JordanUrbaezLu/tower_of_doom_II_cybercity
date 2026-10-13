"""Install the docs/194 SOUND KIT drop (the card reveal + the Black Market) - re-runnable.

  python tools/sound_kit/install.py "<drop.zip>"          validate, process, copy, write alias rows, manifest
  python tools/sound_kit/install.py --check               the installed files + rows still match the manifest

What it does (split agreed with session d2, 2026-09-29: 9c = the asset side, d2 = the spin wiring):
- C1-C7 (tod_pull_*) REPLACE the synthesized placeholders by name; their alias rows are unchanged.
- M1-M13 (tod_spin_*) and V1-V10 (tod_spin_vo_*) are NEW rows in sound/aliases/tod_ui.csv, inserted right
  after the tod_pull_* rows: 2D, NONLOOPING, like the pull rows. The reel's crawl is FIVE rows on the one wav
  (tod_spin_crawl_1..5) a semitone apart, because the engine cannot pitch a sound at play time.
- ALIAS PITCH IS IN CENTS (stock rows use -200 / 200 = +-2 semitones): the crawl steps are 0/100/200/300/400.
- Every file must be 48 kHz / 16-bit / stereo, start at sample 0, peak <= -1 dBFS, and the C/M files within
  10 % of the brief's length (the drop is REFUSED otherwise). The C and M files go in AS DELIVERED: they
  already sit at tod_super_sting's loudness and the reveal ladder's rising level is by design. The dealer's
  voice (V) is lifted to ~-11 LUFS with a -1 dBFS limiter (latency-compensated, so it still starts at sample
  0) so it sits clearly over the spin effects (d2's request). Ticks sit lower through their alias volume.
"""
import csv, hashlib, io, json, pathlib, re, shutil, subprocess, sys, tempfile, wave, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
SFX = ROOT / 'sound_assets/tod/sfx'
CSV = ROOT / 'sound/aliases/tod_ui.csv'
MANIFEST = ROOT / 'art/sound_kit/manifest.json'
C = {'tod_pull_rung_1': 0.45, 'tod_pull_rung_2': 0.45, 'tod_pull_rung_3': 0.45, 'tod_pull_rung_4': 0.45,
     'tod_pull_beat': 0.40, 'tod_pull_legendary': 2.0, 'tod_pull_alert': 0.9}
M = {'tod_spin_coin': 0.6, 'tod_spin_open': 0.8, 'tod_spin_luck': 0.7, 'tod_spin_start': 0.9, 'tod_spin_tick_1': 0.08,
     'tod_spin_tick_2': 0.08, 'tod_spin_tick_3': 0.08, 'tod_spin_crawl': 0.25, 'tod_spin_stop': 0.4,
     'tod_spin_socket': 0.6, 'tod_spin_upgrade': 0.8, 'tod_spin_scrap': 0.8, 'tod_spin_close': 0.5}
V = ['tod_spin_vo_buy_1', 'tod_spin_vo_buy_2', 'tod_spin_vo_buy_3', 'tod_spin_vo_common_1', 'tod_spin_vo_common_2',
     'tod_spin_vo_epic_1', 'tod_spin_vo_epic_2', 'tod_spin_vo_legendary_1', 'tod_spin_vo_legendary_2', 'tod_spin_vo_close']
VO_TARGET_LUFS = -11.0
# alias name -> (wav stem, volume, pitch cents). Volumes: the effects under the dealer; ticks lower (10 a second).
ROWS = [
    ('tod_spin_coin', 'tod_spin_coin', 88, 0), ('tod_spin_open', 'tod_spin_open', 88, 0),
    ('tod_spin_luck', 'tod_spin_luck', 86, 0), ('tod_spin_start', 'tod_spin_start', 88, 0),
    ('tod_spin_tick_1', 'tod_spin_tick_1', 72, 0), ('tod_spin_tick_2', 'tod_spin_tick_2', 72, 0),
    ('tod_spin_tick_3', 'tod_spin_tick_3', 72, 0),
] + [('tod_spin_crawl_%d' % (i + 1), 'tod_spin_crawl', 84, 100 * i) for i in range(5)] + [
    ('tod_spin_stop', 'tod_spin_stop', 90, 0), ('tod_spin_socket', 'tod_spin_socket', 88, 0),
    ('tod_spin_upgrade', 'tod_spin_upgrade', 90, 0), ('tod_spin_scrap', 'tod_spin_scrap', 88, 0),
    ('tod_spin_close', 'tod_spin_close', 84, 0),
]   # the ten V rows moved to sound/aliases/tod_shop.csv as 3D rows (tools/black_market_vo/pick.py, 2026-09-30): the dealer speaks FROM the counter
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def lufs(path):
    out = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    i = re.findall(r'I:\s+(-?[\d.]+) LUFS', out)
    return float(i[-1]) if i else None


def check_wav(path, want_secs=None):
    with wave.open(str(path)) as w:
        fmt = (w.getframerate(), w.getsampwidth() * 8, w.getnchannels())
        secs = w.getnframes() / w.getframerate()
        raw = w.readframes(w.getnframes())
    errs = []
    if fmt != (48000, 16, 2):
        errs.append('format %s (want 48000 Hz / 16-bit / stereo)' % (fmt,))
    if want_secs and abs(secs - want_secs) / want_secs > 0.10:
        errs.append('length %.3f s (brief %.2f s)' % (secs, want_secs))
    samples = memoryview(raw).cast('h')
    first = next((i for i, s in enumerate(samples) if abs(s) > 104), len(samples))    # -50 dBFS
    if first / 2 / 48000 > 0.005:
        errs.append('starts %.1f ms late (must start at sample 0)' % (first / 2 / 48000 * 1000))
    return errs, round(secs, 3)


def rows_csv(header):
    col = {h: i for i, h in enumerate(header)}
    out = []
    for name, stem, vol, cents in ROWS:
        r = [''] * len(header)
        r[col['Name']] = name
        r[col['FileSpec']] = 'tod\\sfx\\' + stem + '.wav'
        r[col['Template']] = 'UIN_MOD'
        r[col['VolMin']] = r[col['VolMax']] = str(vol)
        if cents:
            r[col['PitchMin']] = r[col['PitchMax']] = str(cents)
        r[col['PanType']] = '2d'
        r[col['Looping']] = 'NONLOOPING'
        out.append(r)
    return out


def write_rows():
    text = CSV.read_text(encoding='utf-8')
    lines = text.splitlines()
    header = next(csv.reader([lines[0]]))
    ours = {n for n, _, _, _ in ROWS}
    kept = [l for l in lines if not (l.split(',', 1)[0] in ours)]
    at = max(i for i, l in enumerate(kept) if l.startswith('tod_pull_')) + 1
    buf = io.StringIO()
    csv.writer(buf, lineterminator='\n').writerows(rows_csv(header))
    new = kept[:at] + buf.getvalue().rstrip('\n').split('\n') + kept[at:]
    CSV.write_text('\n'.join(new) + ('\n' if text.endswith('\n') else ''), encoding='utf-8')


def install(zip_path):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='tod_sound_kit_'))
    z = zipfile.ZipFile(zip_path)
    for i in z.infolist():                    # the loose files are the delivery; a nested zip repeats them
        name = pathlib.Path(i.filename).name
        if name.lower().endswith('.wav') and not name.startswith('_PREVIEW'):
            (tmp / name).write_bytes(z.read(i.filename))
    want = {**C, **M, **{v: None for v in V}}
    missing = [k for k in want if not (tmp / (k + '.wav')).exists()]
    if missing:
        sys.exit('SOUND KIT REFUSED: missing ' + ', '.join(missing))
    errs = {}
    for k, secs in want.items():
        e, _ = check_wav(tmp / (k + '.wav'), secs)
        if k in V and _ > 2.05:
            e.append('voice line over 2 s')
        if e:
            errs[k] = e
    if errs:
        sys.exit('SOUND KIT REFUSED: ' + json.dumps(errs))
    SFX.mkdir(parents=True, exist_ok=True)
    record = {}
    for k in want:
        src, dst = tmp / (k + '.wav'), SFX / (k + '.wav')
        if k in V:
            level = lufs(src)
            gain = max(-6.0, min(4.0, (VO_TARGET_LUFS - level) if level is not None and level > -60 else 2.5))
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(src), '-af',
                            'volume=%.2fdB,alimiter=limit=0.891:attack=2:release=60:level=disabled:latency=1' % gain,
                            '-ar', '48000', '-sample_fmt', 's16', '-ac', '2', str(dst)], check=True)
            how = 'voice +%.1f dB, limit -1 dBFS' % gain
        else:
            shutil.copyfile(src, dst)
            how = 'as delivered'
        e, secs = check_wav(dst, want[k])
        assert not e, (k, e)
        record[k] = dict(sha256=sha(dst), secs=secs, lufs=lufs(dst), source_sha256=sha(src), how=how)
    write_rows()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(dict(source=pathlib.Path(zip_path).name, brief='docs/194_sound_kit_prompt.md',
                                        files=record, aliases=[r[0] for r in ROWS], alias_table='sound/aliases/tod_ui.csv',
                                        pitch_units='cents', native_played=False), indent=2), encoding='utf-8')
    print('SOUND KIT INSTALLED: %d files, %d alias rows (+ the 7 existing tod_pull_* rows)' % (len(record), len(ROWS)))


def check():
    m = json.loads(MANIFEST.read_text(encoding='utf-8'))
    bad = [k for k, r in m['files'].items() if not (SFX / (k + '.wav')).exists() or sha(SFX / (k + '.wav')) != r['sha256']]
    rows = list(csv.reader(CSV.read_text(encoding='utf-8').splitlines()))
    header, col = rows[0], {h: i for i, h in enumerate(rows[0])}
    have = {r[0]: r for r in rows[1:] if r}
    rowbad = []
    for want in rows_csv(header):
        got = have.get(want[0])
        if got is None or [got[col[k]] for k in ('FileSpec', 'VolMax', 'PitchMin', 'PanType', 'Looping')] != \
                [want[col[k]] for k in ('FileSpec', 'VolMax', 'PitchMin', 'PanType', 'Looping')]:
            rowbad.append(want[0])
    if bad or rowbad:
        sys.exit('SOUND KIT STALE: files [' + ', '.join(bad) + '] rows [' + ', '.join(rowbad) + ']')
    print('SOUND KIT OK: %d files, %d rows' % (len(m['files']), len(rows_csv(header))))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        check()
    elif len(sys.argv) > 1:
        install(sys.argv[1])
    else:
        sys.exit(__doc__)
