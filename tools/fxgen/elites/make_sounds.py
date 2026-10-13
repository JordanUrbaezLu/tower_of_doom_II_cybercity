"""THE ELITES' SOUNDS (PK26, 2026-10-05): the cues the elite effects need that no table defined.

  * tod_elite_doppel_charge - the RISING WHINE under the Doppelghast's death charge (_tod_elite_fx::charge_start plays it
    at the squib; it ends exactly at the blast, where the BO6 death one-shot takes over). Before it the 2.9 s between the
    death and the hurting blast were silent. GENERATED with ElevenLabs sound generation, the house pipeline
    (tools/ability_fx/make_sounds.py, imported READ-ONLY for its measure / trim / level / encode helpers): the model puts
    the loudest moment first, so every take asks for a DISCHARGE that dies away, with a throb that starts fast and slows,
    and is REVERSED - silence, a build, a throb that quickens, full intensity at the very end. Each take is measured and
    scored (a late peak, a slow build, a loud last frame, no clipping, enough length) and the best ships, cut from its
    quiet start to EXACTLY TOD_ELITE_FX_CHARGE_MS (read from _tod_elite_fx.gsc) so the whine and the blast meet.
  * hb_bo6_fly_ai_mangler_death_ground_imp (6 takes) + hb_bo6_dst_ai_mangler_death_impact - the Mangler's BO6 death
    impacts, which Hellbound shipped and nothing ever played; the R5 purge (2026-10-04) retired them as unused to
    archive/map1_carryover/. PK26 plays them (_tod_mangler::corpse_cleanup), so they are RESTORED: the same wavs, byte
    for byte (each sha256 pinned in sounds_manifest.json), back at sound_assets/hb/bo6_enemies/, and the same rows R5
    removed from hb_bo6_mangler.csv (verified identical), now in this package's own table.

The ElevenLabs takes live in tmp/elite_sfx/ (not in git, the ability pipeline's precedent): --check needs only the
manifest; a re-pick after tmp is cleaned needs a fresh `generate`.

  python tools/fxgen/elites/make_sounds.py generate [--takes N]     call ElevenLabs, score, keep the takes (tmp/elite_sfx/)
  python tools/fxgen/elites/make_sounds.py pick [--out-root DIR]    ship the best take + restore the BO6 wavs + write the csv
  python tools/fxgen/elites/make_sounds.py desk [--out-root DIR]   tmp/elite_sfx/desk.html: the shipped mix + every take, playable
  python tools/fxgen/elites/make_sounds.py --check [--out-root DIR] the build gate: wavs + shas + formats, the csv exactly
                                                                    as written here, the csv loaded by the .szc

The key is ELEVENLABS_API_KEY (process or Windows user environment, via tools/black_market_vo/eleven.py: never printed,
never stored). A user override: tmp/elite_sfx/picks.json {"doppel_charge": "take_3"}.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import shutil
import sys
import wave

sys.dont_write_bytecode = True
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
SR = 48000
WORK = ROOT / 'tmp' / 'elite_sfx'
TAKES_DIR = WORK / 'takes'
TAKES_JSON = WORK / 'takes.json'
PICKS_JSON = WORK / 'picks.json'
MANIFEST = HERE / 'sounds_manifest.json'
CSV_REL = 'sound/aliases/tod_elite_fx.csv'
SZC_REL = 'sound/zoneconfig/zm_tod2_cybercity.szc'
MODULE_REL = 'scripts/zm/zm_tod2_cybercity/_tod_elite_fx.gsc'
WAV_REL_DIR = 'sound_assets/tod/elite_fx'
FIX = 'run: python tools/fxgen/elites/make_sounds.py pick'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


A = load(ROOT / 'tools/ability_fx/make_sounds.py', 'abfx_sounds_lib')     # helpers only (read-only)

CHARGE = dict(
    secs=3.6,                     # asked of the model; the shipped cut is TOD_ELITE_FX_CHARGE_MS
    lufs=-17.0,
    vol=86, dist=(150, 2000),
    prompts=[
        'a monster body overloaded with energy discharging and powering down: loud crackling electrical arcs and a deep '
        'throbbing pulse that starts very fast and slows down, the energy draining away to silence over three seconds, '
        'dark sci-fi sound effect, no music, no voice',
        'a powerful unstable energy core shutting down: a sizzling electric hum with a heartbeat-like throb that starts '
        'rapid and slows, crackles and sparks fading out to complete silence, no music, no voice',
    ],
)
# THE RESTORED BO6 ROWS (the R5 purge removed them from hb_bo6_mangler.csv; the rows verbatim)
BO6_WAVS = {
    'sound_77a5b97e3c4bcabc.wav': '',
    'sound_1ed664b5ab4166e9.wav': '', 'sound_372cac844cf777bb.wav': '', 'sound_6178177565c27272.wav': '',
    'sound_67761e9a257d42c6.wav': '', 'sound_6946e88790751157.wav': '', 'sound_7205c12aa734eedc.wav': '',
}
BO6_ARCHIVE = 'archive/map1_carryover/sound_assets/hb/bo6_enemies'
BO6_DIR = 'sound_assets/hb/bo6_enemies'
BO6_ROW = ('{name},,,hb\\bo6_enemies\\{file},,,UIN_MOD,,,,,BUS_FX,,,,,,{vol},{vol},80,1800,2000,,,,,,,3,oldest,,,,,,,,3d,,,'
           'NONLOOPING' + ',' * 61)
BO6_ROWS = [('hb_bo6_dst_ai_mangler_death_impact', 'sound_77a5b97e3c4bcabc.wav', 80)] + [
    ('hb_bo6_fly_ai_mangler_death_ground_imp', f, 72) for f in (
        'sound_1ed664b5ab4166e9.wav', 'sound_372cac844cf777bb.wav', 'sound_6178177565c27272.wav',
        'sound_67761e9a257d42c6.wav', 'sound_6946e88790751157.wav', 'sound_7205c12aa734eedc.wav')]


def charge_ms(out_root):
    for base in (out_root, ROOT):
        p = base / MODULE_REL
        if p.exists():
            m = re.search(r'#define\s+TOD_ELITE_FX_CHARGE_MS\s+(\d+)', p.read_text(encoding='utf-8'))
            if m:
                return int(m.group(1))
    sys.exit('ELITE SOUNDS: TOD_ELITE_FX_CHARGE_MS not found in %s' % MODULE_REL)


def features(x):
    return A.features(x)


def score(ft):
    """the charge's profile: a long slow build, the peak in the last quarter, a LOUD last frame (it stops dead into the
    blast), clean, and long enough to be CUT to the charge (never padded)"""
    if ft is None:
        return -1.0, {'dead': True}
    c = A.closeness
    s = dict(length=c(ft['dur'], 3.0, 8.0, 0.8),
             peak_at=c(ft['peak_at'], 0.75, 1.0, 0.3),
             build=c(ft['onset'] / max(ft['dur'], 1e-6), 0.45, 0.98, 0.3),
             stops=c(ft['tail_db'], -10, 0, 14),
             clip=1.0 - min(1.0, ft['clip'] * 50))
    return float(sum(s.values()) / len(s)), s


def generate(takes):
    sys.path.insert(0, str(ROOT / 'tools' / 'black_market_vo'))
    import eleven
    TAKES_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(TAKES_JSON.read_text()) if TAKES_JSON.exists() else {}
    rows = data.get('doppel_charge', [])
    for i in range(len(rows), len(rows) + takes):
        prompt = CHARGE['prompts'][i % len(CHARGE['prompts'])]
        name = 'take_%d' % (i + 1)
        mp3 = TAKES_DIR / (name + '.mp3')
        raw = eleven.call('POST', '/v1/sound-generation', body={'text': prompt, 'duration_seconds': CHARGE['secs'],
                                                                   'prompt_influence': A.PROMPT_INFLUENCE})
        if not isinstance(raw, (bytes, bytearray)):
            sys.exit('doppel_charge: unexpected response %r' % (raw,))
        mp3.write_bytes(raw)
        x = A.ffmpeg_decode(str(mp3))[::-1].copy()
        ft = features(x)
        sc, parts = score(ft)
        rows.append(dict(name=name, file=str(mp3.relative_to(ROOT)).replace('\\', '/'), prompt=prompt, features=ft, score=sc, parts=parts))
        print('doppel_charge %s score %.3f %s' % (name, sc, ' '.join('%s %.2f' % kv for kv in sorted(parts.items()) if isinstance(kv[1], float))))
    data['doppel_charge'] = rows
    TAKES_JSON.write_text(json.dumps(data, indent=1))


FX = load(HERE / 'make_fx.py', 'elite_fx_lib')       # beats(): the visual heartbeat the thumps lock to
FX_LAG_MS = 50                 # the effect starts one server frame after the cue (_tod_elite_fx::carrier_play's wait)
MIX_DB = dict(bed=0.0, whine=-9.0, thump=-3.0)        # layer levels against each other (each normalised to unit RMS first)


def rms(x):
    return float(np.sqrt(np.mean(x ** 2)) + 1e-12)


def synth_layers(n, beat_ms):
    """THE DESIGNED HALF of the charge (a machine is better than a model at sync): a rising WHINE (180 -> 900 Hz,
    exponential, three harmonics, swelling 18 dB) and a HEARTBEAT THUMP on every beat of the visual (fx beats(): a
    62 -> 44 Hz pitched-down sine with a short noise click, growing with the beat) - so the throb you hear IS the
    flash you see, quickening into a roll at the end. Deterministic (seeded clicks)."""
    t = np.arange(n) / SR
    T = n / SR
    f = 180.0 * (900.0 / 180.0) ** (t / T)
    ph = 2 * np.pi * np.cumsum(f) / SR
    whine = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)) * 10 ** ((-18.0 + 18.0 * (t / T)) / 20)
    thump = np.zeros(n)
    L = int(0.09 * SR)
    tt = np.arange(L) / SR
    body = np.sin(2 * np.pi * np.cumsum(62.0 - 18.0 * tt / 0.09) / SR) * np.minimum(1.0, tt / 0.004) * np.exp(-tt / 0.035)
    for i, b in enumerate(beat_ms):
        k = i / max(1, len(beat_ms) - 1)
        click = np.random.default_rng(4100 + i).standard_normal(L) * np.exp(-tt / 0.006) * 0.25
        s = int(round((b + FX_LAG_MS) * SR / 1000.0))
        if s >= n:
            continue
        e = min(n, s + L)
        thump[s:e] += ((body + click) * (0.35 + 0.65 * k))[:e - s]
    return whine, thump


def render(path, ms):
    """THE MODEL'S HALF: the take reversed (a discharge dying away -> a charge building), trimmed, cut from its quiet
    start to exactly `ms`, DC-blocked, then swelled 12 dB across the charge so it never plateaus. THE DESIGNED HALF:
    synth_layers(). Mixed at MIX_DB, a soft fade in, a 12 ms fade out (it stops dead into the blast, no click), levelled
    to the target under the -1 dBFS limiter."""
    x = A.ffmpeg_decode(str(path))[::-1].copy()
    x = A.trim(x, post=0.0)
    n = int(round(ms * SR / 1000.0))
    if len(x) < n:
        sys.exit('ELITE SOUNDS: take %s is %.2f s, shorter than the %.2f s charge' % (path, len(x) / SR, n / SR))
    bed = A.dc_block(x[len(x) - n:])
    t = np.arange(n) / float(n)
    bed = bed * 10 ** ((-12.0 + 12.0 * t ** 0.8) / 20)
    whine, thump = synth_layers(n, FX.beats(ms))
    mix = sum(layer / rms(layer) * 10 ** (MIX_DB[k] / 20) for k, layer in (('bed', bed), ('whine', whine), ('thump', thump)))
    mix = A.fades(mix, 0.25, 0.012)
    y = A.level_to(mix, CHARGE['lufs'])
    return A.encode(y), dict(dur=round(len(y) / SR, 3), lufs=round(A.lufs(y), 2), peak_db=round(float(A.db(np.max(np.abs(y)) + 1e-12)), 2),
                             mix_db=MIX_DB)


def csv_text(charge_file):
    header = (ROOT / 'sound/aliases/tod_ability.csv').read_text(encoding='utf-8-sig').split('\n')[0].rstrip('\r')
    assert header.startswith('Name,Behavior,Storage,FileSpec,') and header.count(',') == 101, 'the alias header moved'
    lines = [header,
             A.W3D_ROW.format(name='tod_elite_doppel_charge', file='tod\\elite_fx\\' + charge_file, vol=CHARGE['vol'],
                              dmin=CHARGE['dist'][0], dmax=CHARGE['dist'][1], loop='nonlooping')]
    for name, f, vol in BO6_ROWS:
        lines.append(BO6_ROW.format(name=name, file=f, vol=vol))
    for ln in lines[1:]:
        assert ln.count(',') >= 101, ln[:60]
    return '\n'.join(lines) + '\n'


def pick(out_root):
    data = json.loads(TAKES_JSON.read_text()) if TAKES_JSON.exists() else {}
    picks = json.loads(PICKS_JSON.read_text()) if PICKS_JSON.exists() else {}
    rows = sorted([r for r in data.get('doppel_charge', []) if r.get('features')], key=lambda r: -r['score'])
    if picks.get('doppel_charge'):
        rows = [r for r in data.get('doppel_charge', []) if r['name'] == picks['doppel_charge']] + rows
    rows = [r for r in rows if r['features']['dur'] * 1000 >= charge_ms(out_root)]
    if not rows:
        sys.exit('ELITE SOUNDS: no take long enough - run generate')
    best = rows[0]
    ms = charge_ms(out_root)
    b, info = render(ROOT / best['file'], ms)
    wdir = out_root / WAV_REL_DIR
    wdir.mkdir(parents=True, exist_ok=True)
    (wdir / 'tod_elite_doppel_charge.wav').write_bytes(b)
    info.update(file='tod_elite_doppel_charge.wav', sha256=hashlib.sha256(b).hexdigest(), take=best['name'], score=round(best['score'], 3),
                prompt=best['prompt'], charge_ms=ms)
    # the restored BO6 wavs, byte for byte from the archive
    bdir = out_root / BO6_DIR
    bdir.mkdir(parents=True, exist_ok=True)
    bo6 = {}
    for f in BO6_WAVS:
        src = ROOT / BO6_ARCHIVE / f
        if not src.exists():
            src = ROOT / BO6_DIR / f
        raw = src.read_bytes()
        (bdir / f).write_bytes(raw)
        bo6[f] = hashlib.sha256(raw).hexdigest()
    man = dict(charge=info, bo6=bo6)
    MANIFEST.write_text(json.dumps(man, indent=1, sort_keys=True) + '\n')
    p = out_root / CSV_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(csv_text(info['file']).encode('utf-8'))
    print('shipped %s from %s (score %.3f): %.3f s, %.1f LUFS, peak %.1f dB' % (info['file'], best['name'], best['score'], info['dur'], info['lufs'], info['peak_db']))
    print('restored %d BO6 wavs; wrote %s' % (len(bo6), p))


def desk(out_root):
    data = json.loads(TAKES_JSON.read_text()) if TAKES_JSON.exists() else {}
    man = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    h = ['<!doctype html><meta charset=utf-8><title>Elite sounds desk</title>',
         '<style>body{font:14px system-ui;background:#111;color:#ddd;margin:24px}td{padding:4px 10px;border-bottom:1px solid #333}'
         '.pick{color:#6f6;font-weight:bold}</style><h1>The Doppelghast charge</h1>']
    WORK.mkdir(parents=True, exist_ok=True)
    shipped_wav = out_root / WAV_REL_DIR / 'tod_elite_doppel_charge.wav'
    if shipped_wav.exists():
        shutil.copyfile(shipped_wav, WORK / 'shipped_tod_elite_doppel_charge.wav')
        h.append("<p class=pick>SHIPPED (the reversed take + the whine + the heartbeat thumps, %s ms): "
                 "<audio controls src='shipped_tod_elite_doppel_charge.wav'></audio></p>" % man.get('charge', {}).get('charge_ms', '?'))
    for name, f, _ in BO6_ROWS:
        src = out_root / BO6_DIR / f
        if src.exists():
            shutil.copyfile(src, WORK / f)
            h.append("<p>%s: <audio controls src='%s'></audio></p>" % (name, f))
    h.append('<h2>Every take, as generated (the shipped cut plays it REVERSED)</h2><table>')
    shipped = man.get('charge', {}).get('take')
    for r in data.get('doppel_charge', []):
        parts = ' '.join('%s %.2f' % (k, v) for k, v in sorted((r.get('parts') or {}).items()) if isinstance(v, float))
        h.append("<tr><td class='%s'>%s</td><td>%.3f</td><td><small>%s</small></td><td><audio controls src='takes/%s.mp3'></audio></td></tr>"
                 % ('pick' if r['name'] == shipped else '', r['name'], r['score'], parts, r['name']))
    h.append('</table>')
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / 'desk.html').write_text('\n'.join(h), encoding='utf-8')
    print('desk:', WORK / 'desk.html')


def check(out_root):
    bad = []
    if not MANIFEST.exists():
        print('ELITE SOUNDS STALE: no manifest - ' + FIX)
        return 1
    man = json.loads(MANIFEST.read_text())
    ch = man.get('charge', {})
    p = out_root / WAV_REL_DIR / ch.get('file', '?')
    if not p.exists():
        bad.append('missing ' + str(p.relative_to(out_root)))
    else:
        b = p.read_bytes()
        if hashlib.sha256(b).hexdigest() != ch.get('sha256'):
            bad.append('changed ' + ch['file'])
        with wave.open(io.BytesIO(b)) as w:
            if w.getnchannels() != 1 or w.getframerate() != SR or w.getsampwidth() != 2:
                bad.append(ch['file'] + ' is not mono 48 kHz 16-bit')
            ms = w.getnframes() * 1000.0 / SR
        want = charge_ms(out_root)
        if abs(ms - want) > 1.0 or ch.get('charge_ms') != want:
            bad.append('the charge whine is %.0f ms, the charge %d ms (TOD_ELITE_FX_CHARGE_MS moved: re-pick)' % (ms, want))
    for f, sha in man.get('bo6', {}).items():
        q = out_root / BO6_DIR / f
        if not q.exists():
            bad.append('missing restored ' + f)
        elif hashlib.sha256(q.read_bytes()).hexdigest() != sha:
            bad.append('changed restored ' + f)
    if set(man.get('bo6', {})) != set(BO6_WAVS):
        bad.append('the restored BO6 set is not the seven death wavs')
    c = out_root / CSV_REL
    if not c.exists() or c.read_bytes() != csv_text(ch.get('file', '')).encode('utf-8'):
        bad.append(CSV_REL + ' differs from the generated table')
    try:
        szc = json.loads((out_root / SZC_REL).read_text(encoding='utf-8-sig'))
        if not any(s.get('Type') == 'ALIAS' and s.get('Filename') == 'tod_elite_fx.csv' for s in szc.get('Sources', [])):
            bad.append('tod_elite_fx.csv is not loaded by the sound zone config')
    except (OSError, ValueError) as e:
        bad.append('szc unreadable: %s' % e)
    if bad:
        print('ELITE SOUNDS STALE: ' + '; '.join(bad) + ' - ' + FIX)
        return 1
    print('ELITE SOUNDS OK: the charge whine (%d ms, %s) + %d restored BO6 death wavs, %d alias rows'
          % (charge_ms(out_root), ch.get('take'), len(man['bo6']), 1 + len(BO6_ROWS)))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', nargs='?', default='')
    ap.add_argument('--takes', type=int, default=4)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--out-root', default=str(ROOT))
    a = ap.parse_args(argv)
    out_root = pathlib.Path(a.out_root).resolve()
    if a.check or a.cmd == 'check':
        return check(out_root)
    if a.cmd == 'generate':
        generate(a.takes)
    elif a.cmd == 'pick':
        pick(out_root)
    elif a.cmd == 'desk':
        desk(out_root)
    else:
        ap.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
