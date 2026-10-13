"""A CLEAN SOURCE POOL for the consented clone (user 2026-10-01: "the clone sources are pretty bad since they sound robotic.
Let's choose better ones"): the radios and the Moon logs carry the in-game radio filter, and a clone learns the filter.

Pulls from the Call of Duty wiki (api.php, listening/clone-source only) every audio file on the Black Ops III quote pages
(The Giant, Zetsubou No Shima, Revelations: Primis Richtofen = the Shadows of Evil ending's own voice, clean in-game
lines) plus the Black Ops 6 and Cold War intel recordings, into tmp/black_market_vo/reference/pool/, then MEASURES each
clip for the things that make a clone robotic: bandwidth (the 95 % energy roll-off; a radio filter sits under ~4 kHz),
pitch, flatness, length. gallery.html sorts them clean-first so the user picks by ear.

  python tools/black_market_vo/fetch_pool.py [--pages "Revelations ...;The Giant ..."] [--skip-download]
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from design_voice import measure, decode_mono  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REF = os.path.join(ROOT, "tmp", "black_market_vo", "reference")
POOL = os.path.join(REF, "pool")
API = "https://callofduty.fandom.com/api.php"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) tod2-voice-research/1.0"}
PAGES = ["Revelations - Edward Richtofen's quotes sound files (Black Ops III \"Salvation\" DLC)",
         "The Giant - Edward Richtofen's quotes sound files (Black Ops III \"The Giant\" DLC)",
         "Zetsubou No Shima - Edward Richtofen's quotes sound files (Black Ops III \"Eclipse\" DLC)"]
# loose files from the category worth pooling: the BO6 / Cold War intel (modern studio recordings of the older man)
LOOSE = re.compile(r"(Intel .*BO6|Intel .*BOCW|ShadowsOfEvil BOIII)\.(ogg|mp3|flac)$")
AUDIO = re.compile(r"\.(ogg|mp3|flac|wav)$", re.I)


def api(params):
    params = dict(params, format="json")
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=90))


def page_images(title):
    out, cont = [], None
    while True:
        q = {"action": "query", "prop": "images", "titles": title, "imlimit": "500"}
        if cont:
            q["imcontinue"] = cont
        d = api(q)
        for p in d["query"]["pages"].values():
            out += [im["title"] for im in p.get("images", [])]
        cont = d.get("continue", {}).get("imcontinue")
        if not cont:
            return out


def file_url(title):
    d = api({"action": "query", "prop": "imageinfo", "iiprop": "url|size", "titles": title})
    for p in d["query"]["pages"].values():
        ii = p.get("imageinfo")
        if ii:
            return ii[0]["url"], ii[0].get("size", 0)
    return None, 0


def rolloff(path):
    """The CUTOFF: the highest frequency whose long-term level is still within 45 dB of the voice band (500 Hz - 2 kHz),
    measured at 48 kHz. A radio / telephone filter cuts at 3-4 kHz; a clean studio line keeps air to 12-16 kHz.
    (The first version used a 95 % energy roll-off at 16 kHz: speech energy is all low, so it told us nothing.)"""
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    if len(x) < 24000:
        return None
    win, hop, sr = 4096, 2048, 48000
    acc = np.zeros(win // 2 + 1)
    n = 0
    for i in range(0, len(x) - win, hop):
        fr = x[i:i + win]
        if np.sqrt(np.mean(fr ** 2)) < 0.01:
            continue
        acc += np.abs(np.fft.rfft(fr * np.hanning(win))) ** 2
        n += 1
    if n == 0:
        return None
    f = np.fft.rfftfreq(win, 1.0 / sr)
    db = 10 * np.log10(acc / n + 1e-20)
    ref = np.max(db[(f >= 500) & (f <= 2000)])
    above = np.where(db >= ref - 45)[0]
    return round(float(f[above[-1]]), 0) if above.size else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default=";".join(PAGES))
    ap.add_argument("--skip-download", action="store_true")
    a = ap.parse_args()
    os.makedirs(POOL, exist_ok=True)
    titles = {}
    if not a.skip_download:
        for pg in a.pages.split(";"):
            ims = [t for t in page_images(pg) if AUDIO.search(t)]
            print(f"{pg[:60]}: {len(ims)} audio files", flush=True)
            for t in ims:
                titles[t] = pg
        cat = json.load(open(os.path.join(REF, "category_all.json")))
        for t in cat:
            if LOOSE.search(t):
                titles[t] = "category"
        for i, (t, src) in enumerate(sorted(titles.items()), 1):
            fn = re.sub(r"[^A-Za-z0-9_.\-]+", "_", t.replace("File:", ""))
            dst = os.path.join(POOL, fn)
            if os.path.exists(dst):
                continue
            url, size = file_url(t)
            if not url:
                print("no url:", t)
                continue
            try:
                req = urllib.request.Request(url, headers=UA)
                data = urllib.request.urlopen(req, timeout=120).read()
                open(dst, "wb").write(data)
                print(f"[{i}/{len(titles)}] {fn} {len(data)} B", flush=True)
            except Exception as e:  # noqa: BLE001
                print("failed:", t, e)
            time.sleep(0.4)
    rows = []
    for fn in sorted(os.listdir(POOL)):
        if not AUDIO.search(fn):
            continue
        p = os.path.join(POOL, fn)
        try:
            m = measure(p)
            m["rolloff_hz"] = rolloff(p)
        except Exception as e:  # noqa: BLE001
            print("measure failed:", fn, e)
            continue
        m["file"] = fn
        m["page"] = titles.get("File:" + fn.replace("_", " "), "")
        rows.append(m)
    # clean-first: wide bandwidth, moderate flatness (a hard radio filter also shows as high flatness), then length
    rows.sort(key=lambda r: (-(r["rolloff_hz"] or 0), r["flatness"] or 1))
    json.dump({"note": "wiki audio pool: listening + clone source only (clone_voice.py guards the permissions)", "files": rows},
              open(os.path.join(POOL, "pool.json"), "w", encoding="utf-8"), indent=1)
    total = sum(r["duration_s"] for r in rows)
    trs = "".join("<tr><td>%s</td><td>%ss</td><td>%s Hz</td><td>f0 %s</td><td>%s</td><td><audio controls preload='none' src='%s'></audio></td></tr>"
                  % (r["file"], r["duration_s"], int(r["rolloff_hz"] or 0), r["median_f0_hz"], r["flatness"], r["file"]) for r in rows)
    html = ("<html><head><meta charset='utf-8'></head><body style='font-family:sans-serif;background:#111;color:#eee;padding:20px'>"
            "<h2>Source pool: %d clips, %.0f s, sorted clean-first</h2><p>Roll-off = where 95%% of the energy sits: under ~4000 Hz is the "
            "radio filter (robotic), 8000+ is a clean studio line. Pick by ear; tell me the ones to keep and I build the clone set from them.</p>"
            "<table border=1 cellpadding=5><tr><th>clip</th><th>len</th><th>roll-off</th><th>pitch</th><th>flat</th><th></th></tr>%s</table></body></html>"
            % (len(rows), total, trs))
    open(os.path.join(POOL, "gallery.html"), "w", encoding="utf-8").write(html)
    print(f"pool: {len(rows)} clips, {total:.0f} s; gallery: {os.path.join(POOL, 'gallery.html')}")


if __name__ == "__main__":
    main()
