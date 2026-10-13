"""Generate the Black Market dealer's lines with ElevenLabs and prepare them for the bank.

For every line in lines.json: N takes at slightly different seeds through the
saved dealer voice (tmp/black_market_vo/voice.json), each returned as raw
48 kHz PCM, then: leading silence trimmed to sample 0 (the game times these to
the frame), tail trimmed to a short fade, loudness measured, converted to the
bank format (48 kHz / 16-bit / stereo), and written to
tmp/black_market_vo/takes/<file>_<take>.wav with a takes.json ledger and a
gallery.html. Nothing is copied into sound_assets by this script; `pick.py`
does that from the ledger so a human choice (or the measured default) is
recorded per file.

Usage:
  python tools/black_market_vo/generate.py [--group buy,epic] [--file tod_spin_vo_buy_1] [--takes 3] [--model eleven_v4]
Re-runs skip takes that already exist unless --force.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import eleven  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TMP = os.path.join(ROOT, "tmp", "black_market_vo")
TAKES = os.path.join(TMP, "takes")
LINES = os.path.join(os.path.dirname(__file__), "lines.json")
TARGET_LUFS = -13.0     # 2026-09-30 user: "a little bit too loud ... 15 to 20% lower": -2 dB from the kit's -11 LUFS
PEAK_DB = -1.0
SR = 48000
LEAD_THRESH = 0.004     # -48 dBFS: the first sample above this is sample 0
TAIL_THRESH = 0.002
TAIL_PAD = 0.12         # seconds kept after the last audible sample
FADE = 0.06             # seconds of fade on the trimmed tail

# ROUND 8 (user 2026-10-02: "soft scary dark slightly cyber with occasional manic modes"): the baseline is soft, even and
# unhurried; a line marked "mode": "manic" in lines.json is rendered wild (low stability, high style, a touch faster) so
# the crack in the calm is a different DELIVERY, not just a tag in the text.
VS = {"stability": 0.45, "similarity": 0.8, "style": 0.08, "speed": 0.97}
VS_MANIC = {"stability": 0.22, "similarity": 0.75, "style": 0.55, "speed": 1.06}


def pcm_to_np(raw):
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def trim(x):
    a = np.abs(x)
    idx = np.where(a > LEAD_THRESH)[0]
    if idx.size == 0:
        return x
    start = int(idx[0])
    idx2 = np.where(a > TAIL_THRESH)[0]
    end = min(len(x), int(idx2[-1]) + int(TAIL_PAD * SR))
    y = x[start:end].copy()
    n = min(len(y), int(FADE * SR))
    if n > 0:
        y[-n:] *= np.linspace(1.0, 0.0, n, dtype=np.float32)
    return y


def lufs(path):
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    il, tp = None, None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("I:") and "LUFS" in s:
            il = float(s.split()[1])
        if s.startswith("Peak:") and "dBFS" in s:
            tp = float(s.split()[1])
    return il, tp


def write_wav(x, path):
    """Mono float -> 48k/16-bit/stereo, loudness-matched with a true-peak ceiling."""
    tmp_raw = path + ".f32"
    x.astype(np.float32).tofile(tmp_raw)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", tmp_raw,
                    "-ac", "2", "-ar", str(SR), "-c:a", "pcm_s16le", path], check=True)
    os.remove(tmp_raw)
    il, tp = lufs(path)
    if il is None:
        return il, tp
    gain = TARGET_LUFS - il
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-af",
                    f"volume={gain:.2f}dB,alimiter=limit={10 ** (PEAK_DB / 20):.4f}:attack=3:release=60:level=disabled",
                    "-ac", "2", "-ar", str(SR), "-c:a", "pcm_s16le", path + ".tmp.wav"], check=True)
    os.replace(path + ".tmp.wav", path)
    return lufs(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="")
    ap.add_argument("--skip-group", default="", help="comma list of groups to leave alone (e.g. cinematic: the sign laugh the user chose by ear)")
    ap.add_argument("--file", default="")
    ap.add_argument("--takes", type=int, default=3)
    ap.add_argument("--model", default="eleven_v4")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--lines", default="", help="a different line table (lines_unmasked.json)")
    ap.add_argument("--voice", default="", help="a different saved voice id (never the shipping dealer by accident)")
    ap.add_argument("--out", default="", help="a different takes folder (keeps the shipping ledger untouched)")
    ap.add_argument("--renorm", action="store_true", help="re-trim + re-normalize every existing take to the current targets, no API")
    a = ap.parse_args()
    voice = a.voice or json.load(open(os.path.join(TMP, "voice.json")))["voice_id"]
    lines = json.load(open(a.lines or LINES, encoding="utf-8"))["lines"]
    global TAKES
    if a.out:
        TAKES = os.path.abspath(a.out)
    groups = set(a.group.split(",")) if a.group else None
    skip = set(a.skip_group.split(",")) if a.skip_group else set()
    os.makedirs(TAKES, exist_ok=True)
    ledger_path = os.path.join(TAKES, "takes.json")
    ledger = json.load(open(ledger_path)) if os.path.exists(ledger_path) else {}
    for ln in lines:
        if groups and ln["group"] not in groups:
            continue
        if ln["group"] in skip:
            continue
        if a.file and ln["file"] != a.file:
            continue
        for t in range(1, a.takes + 1):
            name = f"{ln['file']}_{t}"
            path = os.path.join(TAKES, name + ".wav")
            if a.renorm and name in ledger and os.path.exists(path):
                raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                                     capture_output=True, check=True).stdout
                x = trim(pcm_to_np(raw))
                il, tp = write_wav(x, path)
                ledger[name].update({"seconds": round(len(x) / SR, 3), "lufs": il, "true_peak_db": tp, "renorm_target_lufs": TARGET_LUFS})
                print(f"{name}: renorm {len(x) / SR:.2f}s  {il} LUFS  peak {tp}", flush=True)
                with open(ledger_path, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(ledger, f, indent=2)
                continue
            if os.path.exists(path) and not a.force:
                continue
            seed = 1000 + 7 * t
            vs = dict(VS_MANIC if ln.get("mode") == "manic" else VS, **ln.get("settings", {}))   # a line may carry its own delivery (the villain laugh is wilder than the counter)
            raw = eleven.tts(voice, ln["text"], model_id=a.model, seed=seed, output_format="pcm_48000", **vs)
            x = trim(pcm_to_np(raw))
            il, tp = write_wav(x, path)
            ledger[name] = {"file": ln["file"], "take": t, "text": ln["text"], "model": a.model, "seed": seed, "voice_id": voice,
                            "voice_settings": vs, "seconds": round(len(x) / SR, 3), "lufs": il, "true_peak_db": tp}
            print(f"{name}: {len(x) / SR:.2f}s  {il} LUFS  peak {tp}", flush=True)
            with open(ledger_path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(ledger, f, indent=2)
    # the gallery: one row per line, every take side by side
    by_file = {}
    for name, rec in ledger.items():
        by_file.setdefault(rec["file"], []).append((rec["take"], name, rec))
    rows = []
    for ln in lines:
        takes = sorted(by_file.get(ln["file"], []))
        if not takes:
            continue
        cells = "".join(f"<td><audio controls src='{n}.wav'></audio><br><small>{r['seconds']}s {r['lufs']} LUFS</small></td>"
                        for _, n, r in takes)
        rows.append(f"<tr><td><b>{ln['file']}</b><br><small>{ln['group']}</small></td><td style='max-width:360px'>{ln['text']}</td>{cells}</tr>")
    html = ("<html><body style='font-family:sans-serif;background:#111;color:#eee'><h2>The Dealer: takes</h2>"
            "<table border=1 cellpadding=6>" + "".join(rows) + "</table></body></html>")
    with open(os.path.join(TAKES, "gallery.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("gallery:", os.path.join(TAKES, "gallery.html"))


if __name__ == "__main__":
    main()
