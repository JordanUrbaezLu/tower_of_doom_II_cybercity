"""THE PK02 LISTENING DESK: hear the newly-audible sounds at their scripted timing before a build (asset pack PK02).

PK02 ships no new audio - it makes sounds that already ship PLAY (docs/43 B1/B2, the BO6 elites' AudioOneShot@ notes,
the Mangler's footfalls). This renders each moment offline from the REAL shipped wavs at the offsets the staged GSC
fires them, and writes a desk + a timeline sheet:

  python tools/sfx/silent_sounds/make_preview.py [--root DIR] [--out DIR]
      DIR (default the repo) is read for the GSC defines and the alias rows; wavs come from DIR's sound_assets or the
      private tools root's. Output: --out (default tmp/asset_prod/PK02-silent-sounds-wiring/review/):
      <moment>.wav (mono 48 kHz 16-bit), timeline.png, desk.html.

HONEST LIMITS: an alias's VolMin is applied as 20*log10(vol/100) dB (the engine's curve is not documented here), the
first variant of a multi-row alias is used (the engine picks at random), a Secondary plays with its primary, there is
no 3D distance / occlusion / reverb, and the whole moment is scaled down together if it would clip. It previews timing
and relative weight; the level in game is the user's to judge.
"""
import argparse, csv, html, json, math, os, re, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
import check_wiring as cw  # noqa: E402  (read_tables: the zone config's alias tables)

SR = 48000
S = "scripts/zm/zm_tod2_cybercity/"


def defines(root, rel):
    text = open(os.path.join(root, rel), encoding="utf-8").read()
    return {m.group(1): m.group(2) for m in re.finditer(r'^#define\s+(\w+)\s+("?[^\s/"]*"?)', text, re.M)}


def rows_by_name(root):
    out = {}
    for fn_path in cw.read_tables(root)[1]:
        with open(fn_path, newline="", encoding="utf-8-sig", errors="replace") as f:
            for r in csv.DictReader(f):
                if r.get("Name"):
                    out.setdefault(r["Name"].lower(), []).append(r)
    return out


def load_wav(root, filespec):
    p, ch, sr, bits = cw.wav_info(root, filespec)
    if p is None:
        raise SystemExit("missing wav " + filespec)
    with wave.open(p, "rb") as w:
        n, ch, sw, sr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        a = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)), np.arange(len(a)), a)
    return a


class Mixer:
    def __init__(self, root, rows):
        self.root, self.rows, self.events = root, rows, []

    def play(self, alias, t, variant=0, label=None):
        """Place alias (and its Secondary) at t seconds; returns the event record."""
        rs = self.rows[alias.lower()]
        r = rs[variant % len(rs)]
        vol = float(r.get("VolMin") or r.get("VolMax") or 100)
        self.events.append(dict(alias=alias, t=t, file=r["FileSpec"], vol=vol, label=label or alias,
                                pan=(r.get("PanType") or "")))
        sec = (r.get("Secondary") or "").strip()
        if sec:
            srs = self.rows[sec.lower()]
            s2 = srs[variant % len(srs)]
            self.events.append(dict(alias=sec, t=t, file=s2["FileSpec"], label="  + secondary " + sec,
                                    vol=float(s2.get("VolMin") or 100), pan=(s2.get("PanType") or "")))

    def render(self, length=None, restart_alias=None):
        clips = []
        for e in self.events:
            a = load_wav(self.root, e["file"]) * (10 ** (20 * math.log10(max(e["vol"], 1) / 100.0) / 20))
            e["dur"] = len(a) / SR
            clips.append((int(e["t"] * SR), a, e))
        # an EntityLimitCount 1 / oldest alias: a new play cuts the one before it on the same entity
        if restart_alias:
            starts = sorted(s for s, _, e in clips if e["alias"] == restart_alias)
            for i, (s, a, e) in enumerate(clips):
                if e["alias"] == restart_alias:
                    nxt = [x for x in starts if x > s]
                    if nxt:
                        cut = nxt[0] - s
                        clips[i] = (s, a[:cut] * np.concatenate([np.ones(max(cut - 240, 0)), np.linspace(1, 0, min(240, cut))]), e)
                        e["dur"] = cut / SR
        n = max(s + len(a) for s, a, _ in clips)
        if length:
            n = max(n, int(length * SR))
        mix = np.zeros(n, dtype=np.float32)
        for s, a, _ in clips:
            mix[s:s + len(a)] += a
        peak = float(np.max(np.abs(mix)) + 1e-9)
        lim = 10 ** (-1.0 / 20)
        scaled = 1.0
        if peak > lim:
            scaled = lim / peak
            mix *= scaled
        return mix, scaled


def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def build(root, out):
    os.makedirs(out, exist_ok=True)
    rows = rows_by_name(root)
    A = defines(root, S + "_tod_bo6_audio.gsc")
    MG = defines(root, S + "_tod_mangler.gsc")
    fps = float(A["TOD_BO6_FPS"])
    cannon_rate = float(MG["TOD_MANGLER_CANNON_RATE"])
    moments = []

    def moment(key, title, what, mixer, notes, length=None, restart=None):
        mix, scaled = mixer.render(length, restart)
        write_wav(os.path.join(out, key + ".wav"), mix)
        moments.append(dict(key=key, title=title, what=what, events=mixer.events, len=len(mix) / SR, scaled=scaled,
                            notes=notes))

    m = Mixer(root, rows)
    m.play("zmb_no_purchase", 0.0)
    moment("refusal_single", "Refusal (zmb_no_purchase), one press",
           "25 sites: doors, crates, altars, teleporters, the shop, the arena, the class terminal, the finale",
           m, [("press", 0.0)])
    m = Mixer(root, rows)
    for i, t in enumerate((0.0, 0.32, 0.64)):
        m.play("zmb_no_purchase", t, label="zmb_no_purchase (press %d)" % (i + 1))
    moment("refusal_mashed", "Refusal, USE mashed three times",
           "EntityLimitCount 1 / oldest: each press restarts the buzz instead of stacking it", m,
           [("press", 0.0), ("press", 0.32), ("press", 0.64)], restart="zmb_no_purchase")

    m = Mixer(root, rows)
    m.play("alxs_cwpap_inuse", 0.0); m.play("alxs_cwpap_lever_down", 0.0)
    m.play("cw_mus_perks_packa_sting", 0.05); m.play("alxs_cwpap_lever_up", 1.82)
    moment("pap_pack", "Pack-a-Punch: a pack (in-use + lever + THE STING)",
           "the sting was silent: cw_mus_perks_packa_sting was never defined", m, [("purchase", 0.0)])
    m = Mixer(root, rows)
    m.play("cw_mus_perks_packa_jingle", 0.0)
    moment("pap_jingle", "Pack-a-Punch: the crown machine's idle jingle",
           "every 79-169 s while nothing holds it (alarm siren, intro / teddy music, a world pause, a fresh sting)",
           m, [])

    m = Mixer(root, rows)
    f1, f2 = int(A["TOD_DOPPEL_SWING_FOLEY_F"]), int(A["TOD_DOPPEL_SWING_VOX_F"])
    m.play("hb_bo6_fly_ai_ghoul_melee", f1 / fps); m.play("hb_bo6_vox_ai_ghoul_attack", f2 / fps)
    moment("doppel_swing", "Doppelghast swing (hb_doppelghast_stn_melee_01, 40 frames)",
           "whoosh at frame %d, attack scream at frame %d; the hit lands at frame 18" % (f1, f2), m,
           [("clip start", 0.0), ("hit (f18)", 18 / fps)], length=40 / fps)
    m = Mixer(root, rows)
    fj = int(A["TOD_DOPPEL_JUKE_FOLEY_F"])
    m.play("hb_bo6_fly_ai_ghoul_juke", fj / fps); m.play("hb_bo6_vox_ai_ghoul_juke", 39 / fps)
    moment("doppel_juke", "Doppelghast juke (hb_doppelghast_juke_l_short_01, 40 frames)",
           "push-off whoosh at frame %d, the landing snarl when the juke ends (frame 39 when it runs out)" % fj, m,
           [("clip start", 0.0), ("juke ends", 39 / fps)])

    # a chasing Doppelghast: run steps (the private notes, rate 1.5), the approach roar and the new breath cadence
    rnd = np.random.RandomState(7)
    m = Mixer(root, rows)
    run_frames = [9, 19, 32, 44, 55, 67, 79, 91, 102, 114, 127, 140]
    cycle = 142 / fps / 1.5
    secs = 10.0
    k = 0
    c = 0.0
    while c < secs:
        for f in run_frames:
            t = c + f / fps / 1.5
            if t < secs:
                m.play("hb_bo6_fly_ai_ghoul_step_run_default", t, variant=k, label="step"); k += 1
        c += cycle
    vox = []
    t = 1.0 + rnd.uniform(0, 1)
    while t < secs:
        t += rnd.uniform(2.5, 4.5)
        if t < secs:
            vox.append(("roar", t))
    t = rnd.uniform(0.4, 1.2)
    amin, amax, gap = float(A["TOD_DOPPEL_AMB_MOVE_MIN_S"]), float(A["TOD_DOPPEL_AMB_MOVE_MAX_S"]), float(A["TOD_DOPPEL_AMB_VOX_GAP_MS"]) / 1000
    while t < secs:
        t += rnd.uniform(amin, amax)
        # vox_recent(): skipped only when this ghoul voiced something in the LAST gap seconds (the game cannot see a
        # roar that has not happened yet, and approach_screech does not wait for a growl)
        if t < secs and not any(0 <= t - vt < gap for _, vt in vox):
            vox.append(("amb", t))
    for i, (kind, t) in enumerate(sorted(vox, key=lambda x: x[1])):
        if kind == "roar":
            m.play("hb_bo6_vox_ai_ghoul_roar", t, variant=i, label="roar (approach_screech)")
        else:
            m.play("hb_bo6_vox_ai_ghoul_ambience", t, variant=i, label="breath (NEW ambience_cadence)")
    moment("doppel_chase", "A Doppelghast closing in (10 s)",
           "its run steps (already audible) + the far roar (already audible) + THE NEW BREATH: one growl every "
           "%.1f-%.1f s, never within %.1f s of another of its voices" % (amin, amax, gap), m, [], length=secs)

    m = Mixer(root, rows)
    rate = cannon_rate
    for alias, key in (("hb_bo6_fly_ai_mangler_cannon_preshot", "TOD_MANGLER_PRESHOT_F"),
                       ("hb_bo6_fly_ai_mangler_cannon_pullback", "TOD_MANGLER_PULLBACK_F"),
                       ("hb_bo6_fly_ai_mangler_cannon_charge", "TOD_MANGLER_CHARGE_F")):
        m.play(alias, int(A[key]) / fps / rate)
    shot = 2.04 / rate
    m.play("hb_mangler_fire", shot, label="hb_mangler_fire (already audible)")
    m.play("hb_mangler_pulse", shot, label="hb_mangler_pulse (already audible)")
    m.play("hb_mangler_impact", shot + 1.1, label="hb_mangler_impact (already audible, ~700 u away)")
    moment("mangler_cannon", "Mangler cannon (hb_mangler_cannon at rate %.1f)" % rate,
           "NEW: click f%s, pull-back f%s, charge whine f%s (+ its secondary); then the shot, pulse and impact that "
           "already played" % (A["TOD_MANGLER_PRESHOT_F"], A["TOD_MANGLER_PULLBACK_F"], A["TOD_MANGLER_CHARGE_F"]),
           m, [("windup start", 0.0), ("shot (f61)", shot)])
    m = Mixer(root, rows)
    m.play("hb_mangler_melee", 0.0, label="hb_mangler_melee (already audible)")
    m.play("hb_bo6_fly_ai_mangler_mvmt_melee", int(A["TOD_MANGLER_MELEE_MVMT_F"]) / fps)
    moment("mangler_melee", "Mangler melee", "NEW: the armour lunge at frame %s under the existing swing"
           % A["TOD_MANGLER_MELEE_MVMT_F"], m, [("swing", 0.0), ("hit (f23)", 23 / fps)])
    m = Mixer(root, rows)
    n_run = float(MG["TOD_MANGLER_RUN_FRAMES"])
    k = 0
    for cyc in range(3):
        for f in (9, 20, 32, 43, 54, 64):
            m.play("hb_bo6_fly_ai_mangler_mvmt_heavystep_land", cyc * n_run / 30 + f / 30, variant=k, label="footfall"); k += 1
    moment("mangler_run", "Mangler running (3 cycles of hb_mangler_run at 1x)",
           "NEW: the BO6 heavy step + its armour-rattle secondary on the clip's six 'footstep' notes (it was silent)",
           m, [], length=3 * n_run / 30)

    m = Mixer(root, rows)
    m.play("hb_bo6_vox_ai_ghoul_death", 0.0, label="death scream (now on a carrier)")
    m.play("hb_bo6_evt_ai_ghoul_death_oneshot", 3.0, label="the 3 s burst (now on a carrier)")
    moment("doppel_death", "Doppelghast death", "both went through PlaySoundAtPosition, silent for a custom alias "
           "here; now a script_origin carrier each", m, [("death", 0.0), ("burst", 3.0)])
    m = Mixer(root, rows)
    m.play("hb_bo6_fly_ai_mangler_death_collapse", 0.0, label="collapse (now on a carrier)")
    moment("mangler_death", "Mangler death", "PlaySoundAtPosition -> a script_origin carrier", m, [("death", 0.0)])

    timeline(moments, os.path.join(out, "timeline.png"))
    desk(moments, os.path.join(out, "desk.html"))
    json.dump([{k: v for k, v in mo.items() if k != "events"} | {"events": [
        {k: e[k] for k in ("alias", "t", "file", "vol", "dur")} for e in mo["events"]]} for mo in moments],
        open(os.path.join(out, "preview.json"), "w"), indent=1)
    print("PK02 PREVIEW: %d moments -> %s" % (len(moments), out))


def timeline(moments, path):
    W, pad, rowh = 1500, 14, 22
    font = ImageFont.load_default()
    heights = [40 + rowh * len(m["events"]) + 18 for m in moments]
    img = Image.new("RGB", (W, sum(heights) + pad * 2 + 30), (17, 19, 26))
    d = ImageDraw.Draw(img)
    d.text((pad, pad), "PK02 - the silent sounds at their scripted times (bars = each sound's own length; "
           "teal = newly audible, grey = already played; ticks = clip markers)", fill=(200, 220, 235), font=font)
    y = pad + 26
    for m, h in zip(moments, heights):
        span = max(m["len"], 0.5)
        x0, x1 = 420, W - pad
        sx = lambda t: x0 + (x1 - x0) * min(t, span) / span
        d.text((pad, y), m["title"], fill=(240, 240, 240), font=font)
        d.text((pad, y + 13), m["what"][:70], fill=(150, 160, 170), font=font)
        for s in range(0, int(span) + 1):
            d.line([(sx(s), y + 30), (sx(s), y + h - 8)], fill=(40, 44, 54))
            d.text((sx(s) + 2, y + 28), "%ds" % s, fill=(90, 96, 110), font=font)
        for label, t in m["notes"]:
            d.line([(sx(t), y + 36), (sx(t), y + h - 8)], fill=(200, 160, 60), width=2)
            d.text((sx(t) + 3, y + h - 20), label, fill=(200, 160, 60), font=font)
        for i, e in enumerate(m["events"]):
            yy = y + 40 + i * rowh
            new = not ("already" in e["label"] or e["label"] in ("step", "roar (approach_screech)"))
            col = (60, 200, 190) if new else (120, 124, 132)
            d.text((pad + 10, yy + 3), (e["label"] + "  @%.3fs" % e["t"])[:62], fill=col, font=font)
            d.rectangle([sx(e["t"]), yy + 3, max(sx(e["t"] + e.get("dur", 0.1)), sx(e["t"]) + 2), yy + rowh - 5],
                        fill=col)
        y += h
    img.save(path)


def desk(moments, path):
    out = ["<!doctype html><meta charset=utf-8><title>PK02 silent sounds</title>",
           "<style>body{font:14px system-ui;background:#111;color:#ddd;margin:24px;max-width:1100px}"
           "h2{color:#9ef;margin:26px 0 4px}td{padding:3px 10px;border-bottom:1px solid #333}"
           "audio{height:30px;width:420px}.dim{color:#888}</style>",
           "<h1>PK02: the sounds that were silent, at their scripted timing</h1>",
           "<p class=dim>Rendered offline from the shipped wavs by tools/sfx/silent_sounds/make_preview.py. Alias volume "
           "approximated as 20&middot;log10(vol/100) dB, first variant of each alias, no 3D distance. Timing and "
           "relative weight only &mdash; the level in game is the user's to judge.</p>",
           "<p><img src='timeline.png' style='max-width:100%'></p>"]
    for m in moments:
        out.append("<h2>%s</h2><p>%s</p><p><audio controls src='%s.wav'></audio>%s</p><table>" % (
            html.escape(m["title"]), html.escape(m["what"]), m["key"],
            (" <span class=dim>(scaled %.2f to stay under -1 dBFS)</span>" % m["scaled"]) if m["scaled"] < 1 else ""))
        for e in m["events"]:
            out.append("<tr><td>%.3f s</td><td>%s</td><td class=dim>%s</td><td class=dim>vol %g</td></tr>" % (
                e["t"], html.escape(e["label"]), html.escape(e["file"]), e["vol"]))
        out.append("</table>")
    open(path, "w", encoding="utf-8").write("\n".join(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--out", default=os.path.join(REPO, "tmp", "asset_prod", "PK02-silent-sounds-wiring", "review"))
    a = ap.parse_args()
    build(os.path.abspath(a.root), os.path.abspath(a.out))


if __name__ == "__main__":
    main()
