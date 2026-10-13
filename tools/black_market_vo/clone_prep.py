"""THE CLONE SOURCE (prep only; no model is touched here).

User 2026-10-01: specific written permission from Nolan North and from Activision to clone the voice, custom-map only,
non-commercial. Both documents go in docs/licenses/ (the user adds them); clone_voice.py refuses to run until they are
there. This script only prepares the SOURCE SET from the organic reference clips, the way a clean clone wants it:
  - his ORGANIC lines only (the Shadows of Evil ending, the Moon logs + reel, the Call of the Dead and Shi No Numa
    radios, the Origins player line); the ten BOII Aether-era demon lines and the Double Tap SONG are excluded by rule,
    the Kino loading screen too (a music bed under the speech: flatness 0.014 = tone, not voice)
  - mono 44.1 kHz 16-bit, leading / trailing silence cut, long internal silences shortened, loudness -20 LUFS
  - a manifest with every clip's seconds + the total (an instant clone wants 1-5 minutes; more is not better)
  - a gallery (tmp/black_market_vo/clone_source/gallery.html) so the user can hear each source and strike any clip
    that carries another speaker or a music bed before the clone runs (SKIP in skip.json = {"files": [...]})

  python tools/black_market_vo/clone_prep.py
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from design_voice import measure  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VO = os.path.join(ROOT, "tmp", "black_market_vo")
REF = os.path.join(VO, "reference")
OUT = os.path.join(VO, "clone_source")
EXCLUDE = re.compile(r"_BOII\.|RichtofensDelight|DoubleTap_Song|KinoDerToten_LoadingScreen")

CHAIN = ("highpass=f=70,"
         "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15:"
         "stop_periods=-1:stop_threshold=-45dB:stop_silence=0.6,"
         "loudnorm=I=-20:TP=-2:LRA=11")


def secs(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True).stdout.strip()
    return round(float(out or 0), 2)


def main():
    os.makedirs(OUT, exist_ok=True)
    ref = json.load(open(os.path.join(REF, "reference.json")))
    skip = set(json.load(open(os.path.join(OUT, "skip.json"))).get("files", [])) if os.path.exists(os.path.join(OUT, "skip.json")) else set()
    rows, total = [], 0.0
    for fn, _ in ref["files"]:
        if EXCLUDE.search(fn):
            continue
        src = os.path.join(REF, fn)
        dst = os.path.join(OUT, os.path.splitext(fn)[0] + ".wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", CHAIN, "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", dst], check=True)
        m = measure(dst)
        rec = {"file": os.path.basename(dst), "from": fn, "seconds": secs(dst), "raw_seconds": secs(src),
               "median_f0_hz": m["median_f0_hz"], "flatness": m["flatness"], "skipped": os.path.basename(dst) in skip}
        rows.append(rec)
        if not rec["skipped"]:
            total += rec["seconds"]
        print(f"{rec['file']:45s} {rec['raw_seconds']:6.1f}s -> {rec['seconds']:6.1f}s  f0 {m['median_f0_hz']}  {'SKIP' if rec['skipped'] else ''}")
    man = {"note": "organic reference clips, trimmed + normalised for an instant clone; listening + clone source ONLY once "
                   "docs/licenses/ holds the Nolan North + Activision permissions (clone_voice.py checks)",
           "excluded_by_rule": "the ten BOII Aether-era lines, the Double Tap song, the Kino loading screen (music bed)",
           "total_seconds": round(total, 1), "files": rows}
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8"), indent=1)
    trs = "".join("<tr><td>%s<br><small>from %s</small></td><td>%ss (raw %ss)</td><td>f0 %s</td><td><audio controls preload='none' src='%s'></audio></td><td>%s</td></tr>"
                  % (r["file"], r["from"], r["seconds"], r["raw_seconds"], r["median_f0_hz"], r["file"], "SKIPPED" if r["skipped"] else "") for r in rows)
    html = ("<html><head><meta charset='utf-8'></head><body style='font-family:sans-serif;background:#111;color:#eee;padding:20px'>"
            "<h2>Clone source: his organic lines, trimmed</h2><p>Total %.1f s in the set. Strike any clip that carries another speaker "
            "or a music bed: add its file name to skip.json {\"files\": [...]} and re-run clone_prep.py. Nothing here reaches the model "
            "until docs/licenses/ holds both permissions.</p><table border=1 cellpadding=6>%s</table></body></html>" % (total, trs))
    open(os.path.join(OUT, "gallery.html"), "w", encoding="utf-8").write(html)
    print(f"total {total:.1f} s in the clone set; gallery: {os.path.join(OUT, 'gallery.html')}")


if __name__ == "__main__":
    main()
