"""THE MASK: a very slight dark cyber tone laid over the dealer's clean takes when they ship (v6: less cyber, see CYBER).

User 2026-10-01: "The masked version will be the new 100% with a slight dark cyber tone. very slight."
The raw takes stay clean (so the tone can be retuned without credits); pick.py runs this on every
shipped dealer line, the sign laugh included. The chain, all subtle:
  - a short metallic resonance (two tiny early reflections: the inside of a mask)
  - the top shelf eased down and a touch of body added (a mouth behind a grille)
  - a hair of harmonic edge from gentle saturation (a cheap speaker in the mask)
  - loudness re-matched to the clean target so the level does not move

  python tools/black_market_vo/mask_tone.py in.wav out.wav       one file
  python tools/black_market_vo/mask_tone.py --preview             A/B the first shipped line into tmp/black_market_vo/review/
"""
import os
import subprocess
import sys

TARGET_LUFS = -13.0
PEAK_DB = -1.0

# every number is deliberately small; raise them together if "very slight" ever becomes "clearly masked"
FILTER_TEMPLATE = (
    # v5 (user 2026-10-01: "He sounds a bit too much muffled for player pleasure and maybe needs a slight another tweak
    # on cyber dark. Then we should be final"): the DARK and the CYBER no longer come from dulling the top. The top is
    # opened back up (shelf -9.5 -> -3.5 dB, now at 4.6 kHz; low-pass 7.6 -> 11.5 kHz; a presence lift at 3 kHz for the
    # consonants) so every word is clear; the dark comes from the pitch (0.88 -> 0.87) and the low body (+5 dB), the
    # cyber from a stronger electronic shimmer (flanger regen 18 -> 24, depth 0.8) and ringier reflections.
    "rubberband=pitch=%(pitch)s:tempo=1.0,"                 # v5: 0.87 (two and a half semitones down) for a TENOR voice; see pitch_for_voice()
    "aecho=0.8:0.6:1.6|3.1|4.9|7.3:%(echo)s,"               # four close reflections: the inside of a hard shell (v5 0.40|0.29|0.18|0.10)
    "flanger=delay=0.9:depth=%(fl_depth)s:regen=%(fl_regen)s:width=%(fl_width)s:speed=0.22:phase=45,"   # the electronic shimmer (v5 depth 0.8 / regen 24 / width 46)
    "highshelf=f=4600:g=-3.5:width_type=q:width=0.8,"       # only a gentle tilt now: no muffle
    "lowpass=f=11500,"
    "equalizer=f=3000:width_type=q:width=1.4:g=2.0,"        # presence: the consonants cut through the mask
    "equalizer=f=1600:width_type=q:width=2.0:g=4.0,"        # the shell's honk
    "equalizer=f=520:width_type=q:width=1.3:g=-2.5,"
    "lowshelf=f=190:g=5.0:width_type=q:width=0.7,"          # darker body
    "asoftclip=type=tanh:threshold=0.38:output=0.9,"
    "acompressor=threshold=-20dB:ratio=2.6:attack=6:release=90:makeup=3"
)



def pitch_for_voice():
    """ROUND 9 (user 2026-10-02: "No whispering"): v5's 0.87 pitch drop was tuned on a ~205 Hz tenor to make it dark. The
    dealer's own voice (round 8/9) is already a deep baritone (~75-110 Hz median in the design round); dropping it another
    two and a half semitones made mud that read as hush. A voice under 150 Hz keeps its own pitch (1.0); a tenor keeps v5."""
    try:
        import json
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        v = json.load(open(os.path.join(root, "tmp", "black_market_vo", "voice.json")))
        f0 = (v.get("from") or {}).get("median_f0_hz")
        if f0 is not None and f0 < 150:
            return "1.0"
    except Exception:
        pass
    return "0.87"


# v6 (user 2026-10-02, hearing round 9: "Less cyber on the voice"): the CYBER of the mask is the flanger shimmer and the ringing
# reflections; both are cut to a little under half of v5. The dark (the low body, the shell honk, the soft clip) is untouched,
# the words stay as clear as v5 left them. CYBER 1.0 reproduces v5 exactly.
CYBER = 0.45
FILTER = FILTER_TEMPLATE % {
    "pitch": pitch_for_voice(),
    "echo": "|".join("%.2f" % (g * CYBER) for g in (0.40, 0.29, 0.18, 0.10)),
    "fl_depth": "%.2f" % (0.8 * CYBER), "fl_regen": "%d" % round(24 * CYBER), "fl_width": "%d" % round(46 - (46 - 24) * (1 - CYBER)),
}


def lufs(path):
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    il = None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("I:") and "LUFS" in s:
            il = float(s.split()[1])
    return il


def apply(src, dst):
    tmp = dst + ".tone.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", FILTER, "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", tmp], check=True)
    il = lufs(tmp)
    gain = (TARGET_LUFS - il) if il is not None else 0.0
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af",
                    f"volume={gain:.2f}dB,alimiter=limit={10 ** (PEAK_DB / 20):.4f}:attack=3:release=60:level=disabled",
                    "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", dst], check=True)
    os.remove(tmp)
    return lufs(dst)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        src = os.path.join(root, "tmp", "black_market_vo", "takes", "tod_spin_vo_approach_1_1.wav")
        out = os.path.join(root, "tmp", "black_market_vo", "review", "mask_tone_preview.wav")
        print("preview:", out, apply(src, out), "LUFS")
    else:
        print(apply(sys.argv[1], sys.argv[2]), "LUFS")
