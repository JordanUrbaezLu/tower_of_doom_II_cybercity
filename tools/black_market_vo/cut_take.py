"""Cut a stretch out of an existing take into a NEW take number, for picks.json.

  python tools/black_market_vo/cut_take.py --file tod_spin_vo_sign_laugh --from-take 2 --start 12.0 --end 14.0 --as 7
Both edges snap to the quietest point within +-0.25 s, a 15 ms fade-in and 120 ms fade-out are applied, the cut is
re-normalized to the current TARGET_LUFS, and the ledger gets an entry so pick.py can ship it.
"""
import argparse, json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import generate as G

ap = argparse.ArgumentParser()
ap.add_argument("--file", required=True); ap.add_argument("--from-take", type=int, required=True)
ap.add_argument("--start", type=float, required=True); ap.add_argument("--end", type=float, required=True)
ap.add_argument("--as", dest="as_take", type=int, required=True); ap.add_argument("--snap", type=float, default=0.25)
a = ap.parse_args()
src = os.path.join(G.TAKES, f"{a.file}_{a.from_take}.wav")
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(G.SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
x = G.pcm_to_np(raw)
env = np.convolve(np.abs(x), np.ones(int(0.02 * G.SR)) / int(0.02 * G.SR), "same")
def snap(t):
    lo, hi = max(0, int((t - a.snap) * G.SR)), min(len(x) - 1, int((t + a.snap) * G.SR))
    return lo + int(np.argmin(env[lo:hi]))
s, e = snap(a.start), snap(a.end)
y = x[s:e].copy()
fi, fo = int(0.015 * G.SR), int(0.12 * G.SR)
y[:fi] *= np.linspace(0, 1, fi, dtype=np.float32); y[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)
name = f"{a.file}_{a.as_take}"
path = os.path.join(G.TAKES, name + ".wav")
il, tp = G.write_wav(y, path)
lp = os.path.join(G.TAKES, "takes.json"); led = json.load(open(lp))
base = led[f"{a.file}_{a.from_take}"]
led[name] = dict(base, take=a.as_take, seconds=round(len(y) / G.SR, 3), lufs=il, true_peak_db=tp,
                 cut_of={"take": a.from_take, "start_s": round(s / G.SR, 3), "end_s": round(e / G.SR, 3)})
json.dump(led, open(lp, "w", encoding="utf-8", newline="\n"), indent=2)
print(f"{name}: cut of take {a.from_take} {s / G.SR:.3f}-{e / G.SR:.3f} s -> {len(y) / G.SR:.2f}s  {il} LUFS  peak {tp}")
