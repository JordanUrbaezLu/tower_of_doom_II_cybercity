"""THE LISTENING DESK, AS PICTURES (W2B): waveform + spectrogram of every take of every cue (or only the shipped picks),
and for the arena / house cues the shipped stand-in (OLD) beside the authored replacement (NEW), at one shared scale.

  python tools/dealer_sfx/review_sheet.py takes  [--cue NAME ...]  -> art/generated/W2B-dealer-av/takes_<group>.png
  python tools/dealer_sfx/review_sheet.py picks  --root DIR        -> art/generated/W2B-dealer-av/_review_sounds.png

A picture is not an ear: it shows the SHAPE (where the hit lands, whether a drone rises, whether a take clips, whether
a loop seam steps) so a pick can be checked against its brief before anyone listens. The ear decides on the desk.
"""
import argparse, io, json, os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import make_sounds as ms  # noqa: E402

OUT = os.path.join(REPO, "art", "generated", "W2B-dealer-av")


def wav_mono(path):
    with wave.open(path) as w:
        n, ch, sw, sr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        x = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float64) / 32768.0
    if ch == 2:
        x = 0.5 * (x[0::2] + x[1::2])
    return x


def magma(v):
    """0..1 -> an (r, g, b) ramp (black - violet - red - orange - pale yellow), no matplotlib needed"""
    stops = [(0.0, (0, 0, 4)), (0.25, (80, 18, 123)), (0.5, (183, 55, 121)), (0.75, (251, 136, 97)), (1.0, (252, 253, 191))]
    v = min(1.0, max(0.0, v))
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if v <= b:
            k = (v - a) / (b - a)
            return tuple(int(ca[i] + (cb[i] - ca[i]) * k) for i in range(3))
    return stops[-1][1]


LUT = [magma(i / 255.0) for i in range(256)]


def panel(img, draw, x0, y0, w, h, x, label, secs_max, colour):
    """one take: its label, the waveform (min/max per column, the -1.5 dBFS ceiling dotted) and a 0..12 kHz spectrogram"""
    from PIL import Image
    draw.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=(14, 14, 14), outline=(48, 48, 48))
    draw.text((x0 + 4, y0 + 2), label[:72], fill=(225, 225, 225))
    wy, wh = y0 + 16, (h - 20) * 2 // 5
    sy, sh = wy + wh + 2, h - 20 - wh - 4
    n = len(x)
    px = max(1, int(w * min(1.0, (n / ms.SR) / secs_max)))
    mid = wy + wh // 2
    ceil = 10 ** (ms.PEAK_DB / 20)
    for yy in (mid - int(ceil * wh / 2), mid + int(ceil * wh / 2)):
        for xx in range(x0, x0 + w, 4):
            draw.point((xx, yy), fill=(90, 90, 90))
    for c in range(px):
        a, b = int(c * n / px), int((c + 1) * n / px)
        seg = x[a:max(b, a + 1)]
        lo, hi = float(seg.min()), float(seg.max())
        draw.line([(x0 + c, mid - int(hi * wh / 2)), (x0 + c, mid - int(lo * wh / 2))], fill=colour)
    nfft, hop = 1024, 256
    if n > nfft:
        win = np.hanning(nfft)
        cols = [np.abs(np.fft.rfft(x[s:s + nfft] * win)) for s in range(0, n - nfft, hop)]
        S = 20 * np.log10(np.array(cols).T + 1e-9)          # freq x time
        f = np.fft.rfftfreq(nfft, 1.0 / ms.SR)
        S = S[f <= 12000]
        S = np.clip((S + 40) / 80.0, 0, 1)                  # -40..+40 dB re full-scale-ish -> 0..1
        im = Image.fromarray((S[::-1] * 255).astype(np.uint8), "L").resize((px, sh))
        rgb = im.convert("RGB")
        rgb.putdata([LUT[v] for v in im.tobytes()])
        img.paste(rgb, (x0, sy))


def sheet(items, path, cols=3, title=""):
    from PIL import Image, ImageDraw
    pw, ph = 420, 170
    rows = (len(items) + cols - 1) // cols
    img = Image.new("RGB", (cols * pw + 8, rows * ph + 30), (8, 8, 8))
    draw = ImageDraw.Draw(img)
    draw.text((8, 8), title, fill=(240, 240, 240))
    for i, (x, label, colour) in enumerate(items):
        r, c = divmod(i, cols)
        secs_max = max(max(0.6, len(x) / ms.SR), 0.0)
        panel(img, draw, 4 + c * pw, 26 + r * ph, pw - 6, ph - 6, x, label, max(secs_max, 1.0), colour)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("wrote", path, img.size)


def takes(cues):
    data = ms.load_takes()
    by_group = {}
    for cue in cues:
        for r in sorted(data.get(cue, []), key=lambda r: -r["score"]):
            if ms.CUES[cue].get("kind") == "voice" and "seg" not in r:
                continue
            x = ms.shaped(cue, os.path.join(REPO, r["file"]), r.get("seg"))
            x = ms.trim(x)
            x = x / (np.max(np.abs(x)) + 1e-9) * 0.9
            by_group.setdefault(ms.CUES[cue]["group"], []).append((x, "%s %s  %.2f  %.2fs" % (cue, r["name"], r["score"], len(x) / ms.SR), (120, 230, 210)))
    for g, items in by_group.items():
        sheet(items, os.path.join(OUT, "takes_%s.png" % g), cols=4, title="W2B takes: " + g)


def picks(root):
    items = []
    for g in ("dealer", "arena", "house"):
        man = ms.load_manifest(root, g)
        for cue in ms.ORDER:
            if cue not in man:
                continue
            for f in man[cue]["files"]:
                new = os.path.join(ms.root_path(root, ms.GROUPS[g]["wav_dir"]), f["file"])
                if g != "dealer":
                    old = os.path.join(ms.root_path(REPO, ms.GROUPS[g]["wav_dir"]), f["file"])
                    if os.path.exists(old):
                        items.append((wav_mono(old), "OLD %s (synth stand-in)" % f["file"], (140, 140, 140)))
                items.append((wav_mono(new), "NEW %s  %s  %.2fs  %.1f LUFS" % (f["file"], f["take"], f["secs"], f["lufs"]), (255, 110, 100) if g == "dealer" else (100, 200, 255)))
    sheet(items, os.path.join(OUT, "_review_sounds.png"), cols=4, title="W2B: the Dealer fight + arena / house cues (OLD grey = shipping stand-in, NEW = authored)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--cue", action="append")
    ap.add_argument("--root", default=REPO)
    a = ap.parse_args()
    if a.cmd == "takes":
        takes(a.cue or ms.ORDER)
    else:
        picks(os.path.abspath(a.root))
