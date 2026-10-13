"""Score the dealer's takes before one ships: does it SAY the line, through the mask, in HIS voice, without dead air?

  python tools/black_market_vo/score_takes.py --takes <dir> [--lines <table.json>] [--ref a.wav,b.wav] [--pick]

For every take in <dir>/takes.json (generate.py's ledger):
  1. THE MASK      the take is run through mask_tone.apply (the exact shipping chain) into <dir>/review/<take>_mask.wav,
                   so every number below is measured on what the player would hear.
  2. THE WORDS     ElevenLabs speech-to-text (scribe, audio events tagged) on the masked take. The words are compared to
                   the line's text with its [tags] removed: word error rate, the transcript, and whether a TAG WAS READ
                   ALOUD ("pause", "laughs", "excited" said as words - the model's classic failure) or an audio event
                   the line asks for ([laughs]) is missing.
  3. THE VOICE     median f0 of the voiced frames (an autocorrelation tracker) against the shipped reference lines
                   (--ref, default the shipped tod_house_vo_fight/crack/down/death): a take whose pitch has drifted far
                   from his is a different voice.
  4. THE PACING    the longest silence inside the line (under -40 dBFS for 60 ms+, between the first and last word):
                   a bark with a 1.5 s dead pause reads as a dropout in a fight.
Writes <dir>/scores.json and prints a table. --pick also writes <dir>/picks_scored.json ({file: take}) with the best take
per line: fewest word errors first (a take that misreads the line never wins), then no tag read aloud, then the
voice nearest his, then the shortest worst gap. The choice is a measured default; a human ear may overrule it in
tools/black_market_vo/picks.json.

The key: ELEVENLABS_API_KEY via eleven.py (never printed). Re-runs reuse cached transcripts (<dir>/review/<take>.stt.json).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import uuid

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eleven  # noqa: E402
import mask_tone  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SR = 16000
TAG_WORDS = {"pause", "laughs", "laugh", "laughing", "excited", "calm", "soft", "pained", "giggles", "sighs", "maniacally",
             "hysterically", "sing", "song", "whispers"}
EVENT_TAGS = {"laughs", "laughs maniacally", "laughs hysterically", "giggles", "sighs"}


def pcm(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def f0_median(x, sr=SR):
    """median f0 (Hz) over voiced 40 ms frames: normalized autocorrelation peak >= 0.5 in 60..400 Hz, frame RMS >= -40 dBFS"""
    n, hop = int(0.04 * sr), int(0.01 * sr)
    lo, hi = int(sr / 400), int(sr / 60)
    f0s = []
    for s in range(0, len(x) - n, hop):
        fr = x[s:s + n] - np.mean(x[s:s + n])
        if np.sqrt(np.mean(fr * fr)) < 0.01:
            continue
        ac = np.correlate(fr, fr, "full")[n - 1:]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] >= 0.5:
            f0s.append(sr / k)
    return (float(np.median(f0s)) if f0s else None), len(f0s)


def longest_gap(x, sr=SR):
    """the longest run under -40 dBFS (10 ms frames) between the first and last loud frame, in seconds"""
    hop = int(0.01 * sr)
    rms = np.array([np.sqrt(np.mean(x[s:s + hop] ** 2)) for s in range(0, len(x) - hop, hop)])
    loud = np.where(rms >= 0.01)[0]
    if loud.size < 2:
        return 0.0
    run = best = 0
    for v in rms[loud[0]:loud[-1] + 1]:
        run = run + 1 if v < 0.01 else 0
        best = max(best, run)
    return round(best * hop / sr, 2)


def words_of(text):
    return re.findall(r"[a-z0-9']+", text.lower().replace("’", "'"))


def wer(ref, hyp):
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r != h))
            prev, d[j] = d[j], cur
    return d[len(hyp)] / max(1, len(ref))


def stt(path):
    """ElevenLabs speech-to-text (multipart): {text, words: [{text, type}]}"""
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in (("model_id", "scribe_v1"), ("tag_audio_events", "true"), ("language_code", "en")):
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, k, v)).encode())
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: audio/wav\r\n\r\n"
                  % (boundary, os.path.basename(path))).encode() + open(path, "rb").read() + b"\r\n")
    parts.append(("--%s--\r\n" % boundary).encode())
    req = urllib.request.Request(eleven.BASE + "/v1/speech-to-text", data=b"".join(parts), method="POST")
    req.add_header("xi-api-key", eleven.key())
    req.add_header("Content-Type", "multipart/form-data; boundary=" + boundary)
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--takes", required=True)
    ap.add_argument("--lines", default=os.path.join(HERE, "lines.json"))
    ap.add_argument("--ref", default=",".join(os.path.join(ROOT, "sound_assets", "tod", "sfx", "tod_house_vo_%s.wav" % n)
                                              for n in ("fight", "crack", "down", "death")))
    ap.add_argument("--pick", action="store_true")
    a = ap.parse_args()
    tdir = os.path.abspath(a.takes)
    review = os.path.join(tdir, "review")
    os.makedirs(review, exist_ok=True)
    ledger = json.load(open(os.path.join(tdir, "takes.json")))
    lines = {ln["file"]: ln for ln in json.load(open(a.lines, encoding="utf-8"))["lines"]}
    refs = [f0_median(pcm(p))[0] for p in a.ref.split(",") if os.path.exists(p)]
    ref_f0 = float(np.median([r for r in refs if r])) if refs else None
    print("reference f0 (shipped lines): %s Hz from %d files" % (ref_f0 and round(ref_f0, 1), len(refs)))
    out = {"reference_f0_hz": ref_f0, "takes": {}}
    for name in sorted(ledger):
        rec = ledger[name]
        ln = lines.get(rec["file"])
        if not ln:
            continue
        src = os.path.join(tdir, name + ".wav")
        masked = os.path.join(review, name + "_mask.wav")
        mask_tone.apply(src, masked)
        cache = os.path.join(review, name + ".stt.json")
        if os.path.exists(cache):
            tr = json.load(open(cache, encoding="utf-8"))
        else:
            tr = stt(masked)
            with open(cache, "w", encoding="utf-8", newline="\n") as f:
                json.dump(tr, f, indent=1)
        spoken = " ".join(w["text"] for w in tr.get("words", []) if w.get("type") == "word")
        events = [w["text"] for w in tr.get("words", []) if w.get("type") == "audio_event"]
        ref_words = words_of(re.sub(r"\[[^\]]*\]", " ", ln["text"]))
        hyp = words_of(spoken)
        tags_read = sorted({w for w in hyp if w in TAG_WORDS and w not in ref_words})
        wants_event = any(t in EVENT_TAGS for t in re.findall(r"\[([^\]]+)\]", ln["text"]))
        x = pcm(masked)
        f0, voiced = f0_median(x)
        rec_out = {
            "file": rec["file"], "take": rec["take"], "secs": rec["seconds"], "text": ln["text"],
            "transcript": spoken, "events": events, "wer": round(wer(ref_words, hyp), 3), "tags_read_aloud": tags_read,
            "event_wanted": wants_event, "event_heard": bool(events),
            "f0_hz": f0 and round(f0, 1), "f0_off_semitones": (round(12 * np.log2(f0 / ref_f0), 2) if f0 and ref_f0 else None),
            "voiced_frames": voiced, "longest_gap_s": longest_gap(x),
        }
        out["takes"][name] = rec_out
        print("%-26s wer %.2f gap %.2fs f0 %s (%+.1f st) %s%s| %s" % (
            name, rec_out["wer"], rec_out["longest_gap_s"], rec_out["f0_hz"], rec_out["f0_off_semitones"] or 0,
            ("TAGS READ %s " % tags_read) if tags_read else "", ("events %s " % events) if events else "", spoken))
    with open(os.path.join(tdir, "scores.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
    if a.pick:
        best = {}
        for name, r in out["takes"].items():
            key = (r["wer"], len(r["tags_read_aloud"]), int(r["event_wanted"] and not r["event_heard"]),
                   abs(r["f0_off_semitones"] or 0), r["longest_gap_s"])
            if r["file"] not in best or key < best[r["file"]][0]:
                best[r["file"]] = (key, r["take"])
        picks = {f: t for f, (k, t) in sorted(best.items())}
        with open(os.path.join(tdir, "picks_scored.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(picks, f, indent=2)
        print("picks:", picks)


if __name__ == "__main__":
    main()
