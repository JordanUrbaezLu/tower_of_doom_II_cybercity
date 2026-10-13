"""THE ORGANIC ROUND (user 2026-10-01, after the Shadows of Evil ending vs our 100% voice: "we can do better ...
train on organic content ... a lot of the voice lines you have are like a devil Richtofen where he sounds a bit zombie
like. I don't want those lines in the training, that's not his organic voice").

What "training" means here, and what it never means: NO recording of the character's actor has ever been sent to the
model (not as a clone, not as reference audio); the voice is steered by TEXT only. The devil register came from OUR
text: the design / remix SAMPLE and the reveal lines were all cackles, JACKPOT and "come to Papa", so every preview
was judged - and picked - on mania. This round steers the same way but toward the ORGANIC register of the Shadows of
Evil ending: the description and the preview sample are calm, grounded, measured, with no manic tags at all.

Three candidate sets, 3 previews each, into tmp/black_market_vo/unmasked_organic/:
  remix_B_*    the older-sounding base (B = "maxed_older" 2) remixed toward the organic register
  remix_V2_*   the shipping dealer voice (V2) remixed the same way (keeps what the user already liked in it)
  design_*     a fresh design from the organic description alone (breadth)
Each is measured (pitch / flatness) and laid out in gallery.html next to the organic REFERENCE clips (listening only).
  python tools/black_market_vo/organic_round.py [--only remix_B,remix_V2,design]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import eleven  # noqa: E402
from design_voice import measure  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VO = os.path.join(ROOT, "tmp", "black_market_vo")
OUT = os.path.join(VO, "unmasked_organic")

# the ORGANIC register: his everyday speaking voice, the man and not the demon
ORGANIC = (
    "An older German man's speaking voice, a light, dry, slightly nasal tenor with a clear but natural German accent and "
    "precise, well-formed consonants. Measured, articulate and composed, with the weary gravity and faint melancholy of "
    "a scientist who has seen too much; quietly theatrical in the way he savours certain words, with a thin edge of dry, "
    "knowing amusement, never a cackle, never a growl, never a whisper. Warm in the middle, a little tired at the ends "
    "of sentences, intelligent and unhurried. Natural room tone, no effects, no reverb, perfect audio quality."
)
REMIX = (
    "Make this voice calmer, older and more natural: a grounded, measured, articulate German-accented tenor with the "
    "weary gravity and faint melancholy of an old scientist, dry knowing amusement instead of giggles or cackles, "
    "unhurried pacing, warm and slightly tired, quietly theatrical on the words he savours. Remove every manic, "
    "squealing or demonic quality; no reverb, no growl, no whisper. Keep the accent and the precise consonants."
)
# the preview text: calm, organic, no manic tags; the kind of thing he says when the mask is off and the game is over
SAMPLE = (
    "Do you know how long I have been waiting for this? [pause] Years. Lifetimes, some would say. "
    "I made mistakes, I will not pretend otherwise. Terrible mistakes. [pause] But every one of them taught me something, "
    "and every lesson brought me here, to you. [pause] So. [pause] Shall we finish what I started? "
    "I promise you, this time... [pause] I have read the instructions."
)


def save(resp, prefix):
    out = []
    for i, p in enumerate(resp.get("previews", []), 1):
        path = os.path.join(OUT, f"{prefix}_{i}.mp3")
        eleven.b64_to_file(p["audio_base_64"], path)
        rec = {"base": prefix, "n": i, "file": os.path.basename(path), "generated_voice_id": p.get("generated_voice_id"),
               "api_duration": p.get("duration_secs")}
        rec.update(measure(path))
        out.append(rec)
        print(f"{prefix}_{i}: {rec['duration_s']}s f0 {rec['median_f0_hz']} Hz flat {rec['flatness']}", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="remix_B,remix_V2,design")
    ap.add_argument("--gallery-only", action="store_true", help="rebuild gallery.html from candidates.json, no API")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    cpath = os.path.join(OUT, "candidates.json")
    if a.gallery_only:
        cands = json.load(open(cpath, encoding="utf-8"))["candidates"]
    else:
        voices = json.load(open(os.path.join(VO, "unmasked", "voices.json")))
        want = set(a.only.split(","))
        cands = []
        if "remix_B" in want:
            cands += save(eleven.remix_previews(voices["B"]["voice_id"], REMIX, SAMPLE, seed=4101), "remix_B")
        if "remix_V2" in want:
            cands += save(eleven.remix_previews(voices["V2"]["voice_id"], REMIX, SAMPLE, seed=4102), "remix_V2")
        if "design" in want:
            cands += save(eleven.design_previews(ORGANIC, SAMPLE, seed=4103), "design")
        rec = {"organic_description": ORGANIC, "remix_change": REMIX, "sample": SAMPLE, "candidates": cands,
               "note": "no recording of the actor was used as input; text-steered only; the reference clips in the gallery are listening-only"}
        json.dump(rec, open(cpath, "w", encoding="utf-8"), indent=1)
    # the gallery: the organic reference clips (listening only) on top, then every candidate
    ref = json.load(open(os.path.join(VO, "reference", "reference.json")))
    import re
    organic = [fn for fn, _ in ref["files"] if not re.search(r"_BOII\.|RichtofensDelight", fn)]   # _BOII. not _BOIII: the Shadows of Evil ending stays
    organic.sort(key=lambda fn: (0 if "ShadowsOfEvil" in fn else 1, fn))
    rows = "".join("<tr><td>%s</td><td><audio controls preload='none' src='../reference/%s'></audio></td></tr>" % (fn, fn) for fn in organic)
    crows = "".join("<tr><td><b>%s</b><br><small>%ss &middot; f0 %s Hz &middot; flat %s</small></td><td><audio controls src='%s'></audio></td></tr>"
                    % (c["file"], c["duration_s"], c["median_f0_hz"], c["flatness"], c["file"]) for c in cands)
    html = ("<html><head><meta charset='utf-8'></head><body style='font-family:sans-serif;background:#111;color:#eee;padding:20px'>"
            "<h2>The organic round: his everyday voice, not the demon</h2>"
            "<p>Top: his ORGANIC reference lines (the Shadows of Evil ending first, then Moon, Call of the Dead, Kino, Shi No Numa, the Double Tap song). "
            "Listening only; nothing of his was fed to the model. Below: nine text-steered candidates reading the same calm sample.</p>"
            "<h3>Reference (organic)</h3><table border=1 cellpadding=6>" + rows + "</table>"
            "<h3>Candidates</h3><p><i>" + SAMPLE.replace("[pause]", "...") + "</i></p><table border=1 cellpadding=6>" + crows + "</table></body></html>")
    open(os.path.join(OUT, "gallery.html"), "w", encoding="utf-8").write(html)
    print("gallery:", os.path.join(OUT, "gallery.html"))


if __name__ == "__main__":
    main()
