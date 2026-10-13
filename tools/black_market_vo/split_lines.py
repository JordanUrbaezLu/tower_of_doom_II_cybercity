"""SPLIT THE QUOTE COMPILATIONS INTO SINGLE LINES and build the clone set from them.

User 2026-10-01: the wiki radios / logs are robotic (the in-game radio filter) and the wiki's category clips include other
speakers. The clean source is John Rizzo's whole-map quote compilations of Primis Richtofen (Black Ops III: Revelations,
Der Eisendrache, Zetsubou No Shima, The Giant: game-extracted lines, one speaker, the Shadows of Evil ending's own voice),
downloaded with yt-dlp into tmp/black_market_vo/reference/yt/<id>.wav. This script:
  1. cuts each compilation on silence (ffmpeg silencedetect) into single lines -> reference/yt_lines/<map>_NNNN.wav
     (mono 44.1 k 16-bit, each line -20 LUFS), measures each (seconds, pitch, flatness, cutoff)
  2. builds the CLONE SET: the cleanest lines of 2.5-9 s, spread across the four maps, up to --target seconds (default 240;
     an instant clone wants a few minutes of varied, clean speech, not an hour), into tmp/black_market_vo/clone_source/
     (the old wiki-radio set is cleared), with manifest.json + gallery.html; skip.json still strikes a clip by name
  3. a browse gallery of EVERY line (reference/yt_lines/gallery.html) so the user can swap any clip in

  python tools/black_market_vo/split_lines.py [--target 240] [--skip-split]
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from design_voice import measure  # noqa: E402
from fetch_pool import rolloff  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VO = os.path.join(ROOT, "tmp", "black_market_vo")
YT = os.path.join(VO, "reference", "yt")
LINES = os.path.join(VO, "reference", "yt_lines")
CLONE = os.path.join(VO, "clone_source")
MAPS = {"mTvID8ZNHOY": "revelations", "3Tsz0Qz_0zU": "eisendrache", "_KnOfoesZVc": "zetsubou", "OxEZvktvqjs": "giant"}
SIL_DB, SIL_SECS = -38, 0.45   # a gap of 0.45 s under -38 dB separates two lines in the compilations


def silences(path):
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", f"silencedetect=n={SIL_DB}dB:d={SIL_SECS}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(m) for m in re.findall(r"silence_start: ([0-9.]+)", out)]
    ends = [float(m) for m in re.findall(r"silence_end: ([0-9.]+)", out)]
    return starts, ends


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True).stdout.strip() or 0)


def cut(src, t0, t1, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", src,
                    "-af", "highpass=f=70,afade=t=in:d=0.01,afade=t=out:st=%.3f:d=0.03,loudnorm=I=-20:TP=-2:LRA=11" % max(0.0, t1 - t0 - 0.03),
                    "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", dst], check=True)


def split_all():
    os.makedirs(LINES, exist_ok=True)
    rows = []
    for vid, name in MAPS.items():
        src = os.path.join(YT, vid + ".wav")
        if not os.path.exists(src):
            print("missing", src)
            continue
        total = duration(src)
        starts, ends = silences(src)
        # speech segments = the gaps between silences
        bounds, pos = [], 0.0
        for s, e in zip(starts, ends):
            if s - pos >= 0.8:
                bounds.append((pos, s))
            pos = e
        if total - pos >= 0.8:
            bounds.append((pos, total))
        print(f"{name}: {total:.0f} s -> {len(bounds)} lines", flush=True)
        for k, (t0, t1) in enumerate(bounds, 1):
            fn = f"{name}_{k:04d}.wav"
            dst = os.path.join(LINES, fn)
            cut(src, max(0.0, t0 - 0.08), min(total, t1 + 0.12), dst)
            m = measure(dst)
            rows.append({"file": fn, "map": name, "t0": round(t0, 2), "seconds": round(min(total, t1 + 0.12) - max(0.0, t0 - 0.08), 2),
                         "median_f0_hz": m["median_f0_hz"], "flatness": m["flatness"], "cutoff_hz": rolloff(dst)})
    json.dump({"files": rows}, open(os.path.join(LINES, "lines.json"), "w", encoding="utf-8"), indent=1)
    return rows


def gallery(path, title, blurb, rows, src_rel=""):
    trs = "".join("<tr><td>%s</td><td>%ss</td><td>f0 %s</td><td>%s</td><td>%s Hz</td><td><audio controls preload='none' src='%s%s'></audio></td></tr>"
                  % (r["file"], r["seconds"], r["median_f0_hz"], r["flatness"], int(r["cutoff_hz"] or 0), src_rel, r["file"]) for r in rows)
    open(path, "w", encoding="utf-8").write(
        "<html><head><meta charset='utf-8'></head><body style='font-family:sans-serif;background:#111;color:#eee;padding:20px'>"
        "<h2>%s</h2><p>%s</p><table border=1 cellpadding=5><tr><th>clip</th><th>len</th><th>pitch</th><th>flat</th><th>cutoff</th><th></th></tr>%s</table></body></html>"
        % (title, blurb, trs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=float, default=240.0)
    ap.add_argument("--skip-split", action="store_true")
    a = ap.parse_args()
    if a.skip_split and os.path.exists(os.path.join(LINES, "lines.json")):
        rows = json.load(open(os.path.join(LINES, "lines.json"), encoding="utf-8"))["files"]
    else:
        rows = split_all()
    gallery(os.path.join(LINES, "gallery.html"), "Every Black Ops III Richtofen line, split from the compilations (%d)" % len(rows),
            "Single speaker, game-extracted. To put one in the clone set: add its file name to clone_source/keep.json {\"files\": [...]} and re-run with --skip-split.", rows)
    # the clone set: clean (wide cutoff, moderate flatness), 2.5-9 s, round-robin across the maps up to the target
    skip = set(json.load(open(os.path.join(CLONE, "skip.json"))).get("files", [])) if os.path.exists(os.path.join(CLONE, "skip.json")) else set()
    keep = json.load(open(os.path.join(CLONE, "keep.json"))).get("files", []) if os.path.exists(os.path.join(CLONE, "keep.json")) else []
    good = [r for r in rows if 2.5 <= r["seconds"] <= 9.0 and (r["cutoff_hz"] or 0) >= 9000 and r["flatness"] is not None and r["flatness"] <= 0.30
            and r["file"] not in skip]
    by_map = {}
    for r in sorted(good, key=lambda r: -r["seconds"]):
        by_map.setdefault(r["map"], []).append(r)
    chosen, total = [], 0.0
    for fn in keep:
        r = next((x for x in rows if x["file"] == fn), None)
        if r:
            chosen.append(r); total += r["seconds"]
    while total < a.target and any(by_map.values()):
        for name in list(by_map):
            if not by_map[name]:
                continue
            r = by_map[name].pop(0)
            if r in chosen:
                continue
            chosen.append(r); total += r["seconds"]
            if total >= a.target:
                break
    os.makedirs(CLONE, exist_ok=True)
    for fn in os.listdir(CLONE):
        if fn.endswith(".wav"):
            os.remove(os.path.join(CLONE, fn))
    for r in chosen:
        subprocess.run(["cmd", "/c", "copy", "/y", os.path.join(LINES, r["file"]).replace("/", "\\"), CLONE.replace("/", "\\")], capture_output=True)
    man = {"note": "clone source = clean single lines split from the Black Ops III quote compilations (Primis Richtofen, Nolan North); "
                   "listening + clone source ONLY once docs/licenses/ holds the Nolan North + Activision permissions (clone_voice.py checks)",
           "source": "John Rizzo's quote compilations (YouTube ids " + ", ".join(MAPS) + "), split on silence",
           "excluded_by_rule": "the wiki radios / Moon logs (radio filter), every BOII Aether line, every clip with another speaker",
           "total_seconds": round(total, 1), "files": [dict(r, skipped=False) for r in chosen]}
    json.dump(man, open(os.path.join(CLONE, "manifest.json"), "w", encoding="utf-8"), indent=1)
    gallery(os.path.join(CLONE, "gallery.html"), "Clone source: %d clean lines, %.0f s" % (len(chosen), total),
            "Strike a clip: add it to skip.json {\"files\": [...]}; force one in: keep.json; then re-run split_lines.py --skip-split. "
            "Nothing here reaches the model until docs/licenses/ holds both permissions.", chosen)
    print(f"clone set: {len(chosen)} lines, {total:.0f} s (from {len(good)} clean candidates of {len(rows)}); gallery: {os.path.join(CLONE, 'gallery.html')}")


if __name__ == "__main__":
    main()
