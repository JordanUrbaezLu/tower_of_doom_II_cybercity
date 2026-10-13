"""HISTORY (rounds 3-7, 2026-09-30 / 10-01): the reveal-line audition desk. The dealer is his own entity since
2026-10-02 (docs/198 round 8): the current desk is build_own_desk.py; this one is kept for the record and its
"Actual" column is empty unless tmp/black_market_vo/reference/reference.json still exists on this machine.

Build the LOCAL Dealer Voice Desk page (never published): the reveal lines in three columns.

  python tools/black_market_vo/build_desk.py --masked V2mask --full V2 --alt B --open
Columns: Masked = <masked> folder (the 100% voice under the mask tone), 100% = <full> folder, with <alt> behind the
A/B toggle, Actual = his reference lines from tmp/black_market_vo/reference (a pick-list per row). Writes
tmp/black_market_vo/review/dealer_voice_desk_local.html with every clip embedded as mp3 data URIs.
"""
import argparse
import base64
import json
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VO = os.path.join(ROOT, "tmp", "black_market_vo")
TEMPLATE = os.path.join(os.path.dirname(__file__), "desk_template.html")
GAMES = {'BOII': 'Black Ops II', 'BOIII': 'Black Ops III', 'BO1': 'Black Ops', 'BO': 'Black Ops', 'WAW': 'World at War'}
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

ACTUAL_CELL = '''  const ac=document.createElement("div"); ac.className="cell";
  const sel=document.createElement("select"); sel.id="actual-"+row.file; sel.style.cssText="max-width:100%;font:inherit;font-size:12.5px;background:var(--panel2);color:var(--text);border:1px solid var(--line);border-radius:6px;padding:5px 8px";
  DATA.actual.forEach(function(s,k){ const o=document.createElement("option"); o.value=k; o.textContent=s.name+" ("+s.game+", "+s.secs+" s)"; sel.appendChild(o); });
  sel.value=String(idx%DATA.actual.length);
  const holder=document.createElement("div"); holder.className="takes"; holder.style.marginTop="8px"; const bar=document.createElement("div"); bar.className="bar"; bar.style.setProperty("--c","var(--actual)"); const i=document.createElement("i"); bar.appendChild(i);
  function mount(){ stopAll(); holder.innerHTML=""; holder.appendChild(makePlay(DATA.actual[+sel.value].src,"play his line","var(--actual)",i)); }
  sel.addEventListener("change",mount); mount();
  ac.appendChild(sel); ac.appendChild(holder); ac.appendChild(bar); grid.appendChild(ac);'''


def mp3(p, cut=None):
    cmd = ["ffmpeg", "-v", "error", "-i", p] + (["-t", str(cut)] if cut else []) + \
          ["-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "88k", "-f", "mp3", "-"]
    return "data:audio/mpeg;base64," + base64.b64encode(subprocess.run(cmd, capture_output=True, check=True).stdout).decode()


def secs(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True).stdout.strip()
    return round(float(out or 0), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--masked", required=True)
    ap.add_argument("--full", required=True)
    ap.add_argument("--alt", required=True)
    ap.add_argument("--full-label", default="")
    ap.add_argument("--alt-label", default="")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--lines", default="lines_unmasked.json", help="the reveal line table the rows show (lines_reveal_organic.json for the clone / organic sets)")
    a = ap.parse_args()
    here = os.path.dirname(__file__)
    lines = json.load(open(os.path.join(here, a.lines), encoding="utf-8"))["lines"]
    data = {"rows": [], "shop": [], "actual": []}
    for l in lines:
        row = {"file": l["file"], "text": l["text"], "M": [], "A": [], "B": []}
        for key, folder in (("M", a.masked), ("A", a.full), ("B", a.alt)):
            for k in (1, 2):
                p = os.path.join(VO, "unmasked", folder, f"{l['file']}_{k}.wav")
                if os.path.exists(p):
                    row[key].append(mp3(p))
        data["rows"].append(row)
    shop = json.load(open(os.path.join(here, "lines.json"), encoding="utf-8"))["lines"]
    # the strip: six generic lines, then every CLASS line (round 7: the dealer knows who is at his window)
    strip = ["tod_spin_vo_approach_1", "tod_spin_vo_buy_2", "tod_spin_vo_epic_2", "tod_spin_vo_legendary_1",
             "tod_spin_vo_idle_6", "tod_spin_vo_close"] + [x["file"] for x in shop if x.get("cls")]
    for f in strip:
        p = os.path.join(ROOT, "sound_assets", "tod", "sfx", f + ".wav")
        if os.path.exists(p):
            ln = next(x for x in shop if x["file"] == f)
            data["shop"].append({"file": f + (" (" + ln["cls"].upper() + ")" if ln.get("cls") else ""), "text": ln["text"], "src": mp3(p)})
    ref_p = os.path.join(VO, "reference", "reference.json")
    ref = json.load(open(ref_p)) if os.path.exists(ref_p) else {"files": []}
    # ORGANIC ONLY (user 2026-10-01): the BOII Aether-era lines are the "devil Richtofen" register (reverb, zombie-like)
    # and are not what we compare against; the Shadows of Evil ending leads the list
    files = [fn for fn, _ in ref["files"] if not re.search(r'_BOII\.|RichtofensDelight', fn)]   # _BOII. not _BOIII (the Shadows of Evil ending stays)
    files.sort(key=lambda fn: (0 if "ShadowsOfEvil" in fn else 1, fn))
    for fn in files:
        p = os.path.join(VO, "reference", fn)
        m = re.search(r'_(BOII|BOIII|BO1|BO|WAW)\.(ogg|mp3|flac)$', fn)
        label = re.sub(r'\.(ogg|mp3|flac)$', '', fn)
        label = re.sub(r'_(BOII|BOIII|BO1|BO|WAW)$', '', label).replace('_', ' ')
        data["actual"].append({"name": label, "game": GAMES[m.group(1)] if m else "Black Ops", "secs": secs(p), "src": mp3(p, 75)})
    t = open(TEMPLATE, encoding="utf-8").read()
    t = t.replace('>A &middot; maxed 3</button>', '>' + (a.full_label or a.full) + '</button>')
    t = t.replace('>B &middot; maxed older 2</button>', '>' + (a.alt_label or a.alt) + '</button>')
    t = t.replace('<div class="hd actual">Actual</div>', '<div class="hd actual">Actual (his ORGANIC lines only; the Shadows of Evil ending first)</div>')
    t = t.replace('His actual lines load from your own disk and never leave this browser.</p>',
                  "Each row's third cell plays one of his organic lines (the Aether-era demon lines are left out); change the pick-list to any other. "
                  "This copy is local to your machine and is not published.</p>")
    t = t.replace('Masked &middot; the dealer as he ships in the shop', "Masked &middot; the same 100% voice under the mask's slight dark cyber tone")
    s0 = t.index('  const ac=document.createElement("div"); ac.className="cell";')
    marker = '  ac.appendChild(d); ac.appendChild(holder); ac.appendChild(bar); grid.appendChild(ac);'
    s1 = t.index(marker) + len(marker)
    t = t[:s0] + ACTUAL_CELL + t[s1:]
    t = t.replace('<b>Why the third column is a file picker.</b>', '<b>About the third column.</b>')
    t = t.replace('<h2>For context: how he sounds in the shop</h2>', '<h2>How he sounds in the shop, then his lines for each class (archer / breacher / warrior / necro)</h2>')
    filled = t.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    i = filled.index('</style>') + len('</style>')
    page = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + filled[:i] + '</head><body>' + filled[i:] + '</body></html>')
    out = os.path.join(VO, "review", "dealer_voice_desk_local.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    print(out, round(os.path.getsize(out) / 1e6, 2), "MB")
    if a.open:
        subprocess.Popen([CHROME, "file:///" + out.replace("\\", "/")])


if __name__ == "__main__":
    main()
