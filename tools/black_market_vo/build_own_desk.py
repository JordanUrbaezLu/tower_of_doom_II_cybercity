"""THE DEALER'S OWN VOICE DESK (round 8, 2026-10-02): one LOCAL page, never published.

  python tools/black_market_vo/build_own_desk.py [--open]

Section 1: the nine designed candidates from the design round (tmp/black_market_vo/design6: soft / hollow /
glitch x 3), the shipping default marked; pick another by ear and the re-point is `eleven.save_voice` +
voice.json + `generate.py --force` + `pick.py` (docs/198 round 8).
Section 2: every shipped line as it plays in the game (sound_assets/tod/sfx, i.e. under the mask tone), with its
text, group, class and whether it is one of the MANIC lines; the sign laugh last.
Writes tmp/black_market_vo/review/dealer_own_voice_desk.html with every clip embedded as an mp3 data URI.
"""
import argparse
import base64
import html
import json
import os
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VO = os.path.join(ROOT, "tmp", "black_market_vo")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def mp3(p):
    cmd = ["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "80k", "-f", "mp3", "-"]
    return "data:audio/mpeg;base64," + base64.b64encode(subprocess.run(cmd, capture_output=True, check=True).stdout).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="design6")
    ap.add_argument("--open", action="store_true")
    a = ap.parse_args()
    voice = json.load(open(os.path.join(VO, "voice.json")))
    cands = json.load(open(os.path.join(VO, a.design, "candidates.json")))
    lines = json.load(open(os.path.join(os.path.dirname(__file__), "lines.json"), encoding="utf-8"))["lines"]
    default_gen = voice.get("from", {}).get("generated_voice_id")
    rows = []
    for c in cands["candidates"]:
        src = mp3(os.path.join(VO, a.design, c["file"]))
        tag = ' <span class="tag">SHIPPING DEFAULT</span>' if c["generated_voice_id"] == default_gen else ""
        rows.append(f'<div class="card"><div class="name">{html.escape(c["prompt"])} #{c["n"]}{tag}</div>'
                    f'<audio controls preload="none" src="{src}"></audio>'
                    f'<div class="meta">median pitch {c["median_f0_hz"]} Hz &middot; rasp {c["flatness"]} &middot; {c["duration_s"]} s</div>'
                    f'<div class="desc">{html.escape(cands["prompts"][c["prompt"]])}</div></div>')
    shipped = []
    order = sorted(lines, key=lambda l: (l["group"] == "cinematic", l["group"], l.get("cls", ""), l["file"]))
    for l in order:
        p = os.path.join(ROOT, "sound_assets", "tod", "sfx", l["file"] + ".wav")
        if not os.path.exists(p):
            continue
        mode = ' <span class="tag manic">MANIC</span>' if l.get("mode") == "manic" else ""
        cls = f' <span class="tag cls">{l["cls"].upper()}</span>' if l.get("cls") else ""
        egg = f'<div class="egg">hint: {html.escape(l["egg"])}</div>' if l.get("egg") else ""
        shipped.append(f'<tr><td class="f">{html.escape(l["file"])}<br><small>{html.escape(l["group"])}</small>{cls}{mode}</td>'
                       f'<td class="t">{html.escape(l["text"])}{egg}</td><td><audio controls preload="none" src="{mp3(p)}"></audio></td></tr>')
    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>The Dealer: his own voice</title>
<style>
body{{font-family:Segoe UI,sans-serif;background:#0d0b10;color:#e8e2ea;margin:0;padding:24px 28px;max-width:1280px}}
h1{{font-size:22px;margin:0 0 6px}} h2{{font-size:17px;margin:28px 0 10px;color:#ff6a6a}} p{{color:#b9b0bf;line-height:1.5}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:14px}}
.card{{background:#17131c;border:1px solid #2a2331;border-radius:10px;padding:12px}}
.name{{font-weight:600;margin-bottom:6px}} .meta{{font-size:12px;color:#9a8fa3;margin:6px 0}} .desc{{font-size:12px;color:#8e8597;line-height:1.4}}
audio{{width:100%}} table{{border-collapse:collapse;width:100%}} td{{border-top:1px solid #2a2331;padding:8px 6px;vertical-align:top;font-size:13.5px}}
td.f{{width:230px;color:#c9bfd0}} td.t{{max-width:560px}} .egg{{font-size:11.5px;color:#8e8597;margin-top:4px}}
.tag{{display:inline-block;font-size:10.5px;padding:1px 6px;border-radius:4px;background:#3a2a44;color:#f3e9ff;margin-left:6px;vertical-align:middle}}
.tag.manic{{background:#5a1c1c;color:#ffd0d0}} .tag.cls{{background:#1c3a44;color:#d0f3ff}}
</style></head><body>
<h1>The Dealer: his own voice (round 8, 2026-10-02)</h1>
<p>Soft, scary, dark, slightly cyber, with occasional manic modes. Nothing of any other character. Section 1 is the design round:
nine text-designed candidates, three readings of that sentence; the marked one is what the lines below were generated with.
Section 2 is every line as it ships (under the mask tone), MANIC marks the lines rendered in the manic delivery.
This page is local to this machine and is not published.</p>
<h2>1. The candidates ({voice.get("name", "")} is the default)</h2>
<div class="cards">{"".join(rows)}</div>
<h2>2. The lines as they ship ({len(shipped)})</h2>
<table>{"".join(shipped)}</table>
</body></html>"""
    out = os.path.join(VO, "review", "dealer_own_voice_desk.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    print(out, round(os.path.getsize(out) / 1e6, 2), "MB")
    if a.open and os.path.exists(CHROME):
        subprocess.Popen([CHROME, "file:///" + out.replace("\\", "/")])


if __name__ == "__main__":
    main()
