"""Design candidate voices for the Black Market dealer and measure them.

Runs each prompt in PROMPTS through ElevenLabs voice design, saves every
preview as mp3 under tmp/black_market_vo/design/, measures each preview's
median pitch and rasp (spectral flatness) with ffmpeg + numpy, and writes
candidates.json + gallery.html for the user to audition.

Usage: python tools/black_market_vo/design_voice.py [--only main]
"""
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import eleven  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "tmp", "black_market_vo", os.environ.get("VO_DESIGN_DIR", "design"))

PROMPTS = {
    # ROUND 8 (user 2026-10-02): THE DEALER IS HIS OWN ENTITY - nothing of any known character, no accent, no
    # borrowed mannerisms. "soft scary dark slightly cyber with occasional manic modes". Three readings of that
    # sentence; the user picks by ear on the desk. The MASK (mask_tone.py) adds the shell and the shimmer on top,
    # so the voice itself carries only a hint of the synthetic.
    "soft": (
        "A soft-spoken, low male voice: quiet, intimate and unhurried, spoken in a full voice close to the ear, "
        "never a whisper, never loud. Dark velvet with a dry rasp at its edges and a faint cold synthetic shimmer, "
        "as if filtered through a mask with a cheap speaker in it. Unnervingly calm and patient, amused by things "
        "that should frighten him. Every so often the calm snaps: a sudden short manic burst, a sharp rising cackle, "
        "words tumbling out fast and delighted, then instantly soft and composed again as if nothing happened. "
        "No regional accent, no caricature. Perfect audio quality."
    ),
    "hollow": (
        "A deep, hollow, breathy male voice from inside a dark mask: slow, soft and menacing, each word placed "
        "deliberately, with a low resonant chest tone and a dry scrape on the consonants. A subtle electronic "
        "flutter rides underneath, like a voice carried over a failing cyber speaker. Chillingly gentle, like a "
        "predator making conversation. Now and then he breaks: a jagged, high, unhinged laugh and a rush of manic "
        "glee that cracks the deep calm wide open, then sinks back down into the soft dark voice. "
        "No regional accent. Perfect audio quality."
    ),
    "glitch": (
        "A soft, dark male baritone with a thin digital edge: smooth and quiet on the surface, with a faint "
        "doubled, vocoded quality on sustained vowels and crisp, slightly clipped consonants, as if half his voice "
        "is synthesized. Measured, courteous, sinister; he savours silence between phrases. The composure fails in "
        "sudden bursts of mania: a bright, cracked, manic cackle and quick excited speech, shaking and wild for a "
        "moment, before the soft dark calm returns. No regional accent, never whispering. Perfect audio quality."
    ),
    # ROUND 9 (user 2026-10-02, hearing round 8: "No whispering"): the round-8 picks were breathy (voiced share 0.08-0.18 of
    # the energetic frames; a whisper is unvoiced noise). These three insist on FULL VOICE: every word carried on the
    # vocal cords, quiet but spoken, no breath, no hush. Same dark / cyber / manic character.
    "spoken": (
        "A low male voice speaking in FULL, resonant chest voice at a quiet conversational volume: every word fully "
        "voiced and clearly projected, never breathy, never whispered, never hushed. Dark, calm and unhurried, with a "
        "dry grain on the consonants and a faint cold synthetic ring, as if the voice came through a mask with a small "
        "speaker in it. Patient, amused and menacing. Every so often the composure snaps into a short manic burst: a "
        "sharp rising cackle and quick delighted speech, then the calm, fully voiced tone returns. "
        "No regional accent. Perfect audio quality."
    ),
    "velvet_full": (
        "A smooth, dark male baritone with a full, rich, close-miked tone: warm resonance, clear diction, moderate "
        "volume, completely voiced from the first word to the last, with no breathiness and no whispering at all. "
        "Measured and courteous on the surface, sinister underneath, savouring short pauses between phrases. A thin "
        "digital edge rides the sustained vowels. The composure cracks now and then into a bright, cracked, manic "
        "laugh and fast excited speech before the smooth dark voice settles back. No regional accent. Perfect audio quality."
    ),
    "iron": (
        "A deep, firm male voice with a hard metallic resonance, spoken at normal volume with full vocal weight: "
        "clear, projected, every syllable voiced, no breath, no hush, no whisper. Cold, deliberate, slightly processed "
        "like a voice through a cyber mask. Quietly threatening and amused rather than loud. Occasionally the restraint "
        "breaks into a manic edge: a jagged high laugh and a rush of gleeful words, then the deep firm voice returns. "
        "No regional accent. Perfect audio quality."
    ),
}

# The audition text: the approach, the loss, the jackpot and the goodbye, so one
# preview shows the soft dark baseline AND one manic crack. 100..1000 characters.
SAMPLE = (
    "Closer. [pause] I don't bite. [pause] The machine does. [pause] Every card you drew, every spin... I was counting. "
    "[pause] Hm. The tower keeps the rest. [pause] Pity. [excited] OH! JACKPOT! [laughs maniacally] "
    "[pause][calm] ...Forgive me. Old habits. [pause] Come back soon. [pause] You will. [pause] They always do."
)


def decode_mono(path, sr=16000):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32), sr


def measure(path):
    """Median pitch (Hz) over voiced frames via autocorrelation, plus spectral flatness (rasp/noise)."""
    x, sr = decode_mono(path)
    win, hop = 1024, 512
    f0s, flats = [], []
    for i in range(0, len(x) - win, hop):
        fr = x[i:i + win] * np.hanning(win)
        if np.sqrt(np.mean(fr ** 2)) < 0.02:
            continue
        ac = np.correlate(fr, fr, "full")[win - 1:]
        lo, hi = sr // 400, sr // 60          # 60..400 Hz
        seg = ac[lo:hi]
        if seg.size == 0 or ac[0] <= 0:
            continue
        k = int(np.argmax(seg)) + lo
        if ac[k] / ac[0] < 0.3:
            continue
        f0s.append(sr / k)
        spec = np.abs(np.fft.rfft(fr)) + 1e-9
        flats.append(float(np.exp(np.mean(np.log(spec))) / np.mean(spec)))
    dur = len(x) / sr
    return {
        "duration_s": round(dur, 2),
        "median_f0_hz": round(float(np.median(f0s)), 1) if f0s else None,
        "flatness": round(float(np.median(flats)), 4) if flats else None,
        "voiced_frames": len(f0s),
    }


def main():
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    os.makedirs(OUT, exist_ok=True)
    cands = []
    for name, desc in PROMPTS.items():
        if only and name not in only:
            continue
        print(f"designing {name} ...", flush=True)
        seed = int(os.environ.get("VO_DESIGN_SEED", "0")) or None
        res = eleven.design_previews(desc, SAMPLE, model_id="eleven_ttv_v3", guidance_scale=6, loudness=0.4, seed=seed,
                                     quality=(float(os.environ["VO_DESIGN_QUALITY"]) if "VO_DESIGN_QUALITY" in os.environ else None))   # ttv_v2 only
        for i, p in enumerate(res.get("previews", [])):
            fn = f"{name}_{i + 1}.mp3"
            path = os.path.join(OUT, fn)
            eleven.b64_to_file(p["audio_base_64"], path)
            m = measure(path)
            cands.append({"prompt": name, "n": i + 1, "file": fn, "generated_voice_id": p["generated_voice_id"],
                          "api_duration": p.get("duration_secs"), **m})
            print(f"  {fn}: f0={m['median_f0_hz']} flat={m['flatness']} dur={m['duration_s']}", flush=True)
    with open(os.path.join(OUT, "candidates.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"sample": SAMPLE, "prompts": PROMPTS, "candidates": cands}, f, indent=2)
    rows = "\n".join(
        f"<tr><td>{c['prompt']} #{c['n']}</td><td><audio controls src='{c['file']}'></audio></td>"
        f"<td>{c['median_f0_hz']}</td><td>{c['flatness']}</td><td>{c['duration_s']}</td></tr>" for c in cands)
    html = ("<html><body style='font-family:sans-serif;background:#111;color:#eee'><h2>The Dealer: candidate voices</h2>"
            f"<p>Sample text: {SAMPLE}</p><table border=1 cellpadding=6><tr><th>candidate</th><th>play</th>"
            f"<th>median pitch Hz (lower = deeper)</th><th>flatness (higher = raspier)</th><th>s</th></tr>{rows}</table>"
            "</body></html>")
    with open(os.path.join(OUT, "gallery.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("gallery:", os.path.join(OUT, "gallery.html"))


if __name__ == "__main__":
    main()
