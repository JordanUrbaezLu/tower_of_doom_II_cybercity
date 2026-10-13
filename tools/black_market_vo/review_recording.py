"""Stitch the dealer's lines into one recording to audition, with a cue sheet.

  python tools/black_market_vo/review_recording.py            the shipped takes (sound_assets), 0.9 s gaps
  python tools/black_market_vo/review_recording.py --all      every take from tmp/black_market_vo/takes
Writes tmp/black_market_vo/review/dealer_all_lines.wav (+ _cues.txt) or dealer_all_takes.wav.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "tmp", "black_market_vo", "review")
GAP = 0.9


def build(name, picks):
    os.makedirs(OUT, exist_ok=True)
    gap = os.path.join(OUT, "gap.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(GAP),
                    "-c:a", "pcm_s16le", gap], check=True)
    t, cue, lst = 0.0, [], []
    for label, path, secs in picks:
        cue.append(f"{int(t // 60):02d}:{t % 60:05.2f}  {label}")
        lst.append("file '" + os.path.abspath(path).replace("\\", "/") + "'")
        lst.append("file '" + gap.replace("\\", "/") + "'")
        t += secs + GAP
    with open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lst))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(OUT, name + ".txt"),
                    "-c:a", "pcm_s16le", os.path.join(OUT, name + ".wav")], check=True)
    with open(os.path.join(OUT, name + "_cues.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(cue) + "\n")
    print(f"{name}.wav: {t / 60:.1f} min, {len(picks)} clips -> {OUT}")


def main():
    lines = json.load(open(os.path.join(os.path.dirname(__file__), "lines.json"), encoding="utf-8"))["lines"]
    led = json.load(open(os.path.join(ROOT, "tmp", "black_market_vo", "takes", "takes.json")))
    if "--all" in sys.argv:
        picks = [(f"{l['file']}_{k}  {l['text']}", os.path.join(ROOT, "tmp", "black_market_vo", "takes", f"{l['file']}_{k}.wav"),
                  led[f"{l['file']}_{k}"]["seconds"]) for l in lines for k in (1, 2, 3) if f"{l['file']}_{k}" in led]
        build("dealer_all_takes", picks)
    else:
        m = json.load(open(os.path.join(ROOT, "art", "black_market_vo", "manifest.json")))["files"]
        picks = [(f"{l['file']}  [{l['group']}]  {l['text']}", os.path.join(ROOT, "sound_assets", "tod", "sfx", l["file"] + ".wav"),
                  m[l["file"]]["secs"]) for l in lines]
        build("dealer_all_lines", picks)


if __name__ == "__main__":
    main()
