"""Ship the chosen take of every dealer line, and keep the game in step with it.

  python tools/black_market_vo/pick.py            install: copy takes -> sound_assets, alias rows, GSC table, manifests
  python tools/black_market_vo/pick.py --check    build gate: everything still matches the manifest

Which take ships: tools/black_market_vo/picks.json ({"<file>": <take>}) when it
names the file, otherwise take 1. The choice, the text, the model, the seed and
the measured length/loudness of every shipped file are recorded in
art/black_market_vo/manifest.json.

What it keeps in step:
  - sound_assets/tod/sfx/<file>.wav               the shipped wav (48 kHz / 16-bit / stereo, sample 0 = sound)
  - art/sound_kit/manifest.json                   the ten wired lines are ALSO pinned by the docs/194 kit gate:
                                                  their entries are refreshed so `sound_kit/install.py --check` stays green
  - sound/aliases/tod_shop.csv                    one 3D row per line (clone of the shop spark row, voice distances):
                                                  every line plays FROM the dealer's mouth TO one player
  - sound/aliases/tod_ui.csv                      the kit's old 2D voice rows are removed from it
  - scripts/zm/zm_tod2_cybercity/_tod_shop_vo.gsc GENERATED: tod_shop_vo::secs( alias ) = each line's length, the
                                                  shop's one-lane-per-player rule reads it (a line asked for while
                                                  another is still speaking is dropped)
Every file it writes keeps CRLF, like the working copy.
"""
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mask_tone  # noqa: E402  (THE MASK: the slight dark cyber tone laid over every shipped line)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
TAKES = os.path.join(ROOT, "tmp", "black_market_vo", "takes")
SFX = os.path.join(ROOT, "sound_assets", "tod", "sfx")
LINES = os.path.join(HERE, "lines.json")
PICKS = os.path.join(HERE, "picks.json")
MANIFEST = os.path.join(ROOT, "art", "black_market_vo", "manifest.json")
KIT_MANIFEST = os.path.join(ROOT, "art", "sound_kit", "manifest.json")
UI_CSV = os.path.join(ROOT, "sound", "aliases", "tod_ui.csv")
SHOP_CSV = os.path.join(ROOT, "sound", "aliases", "tod_shop.csv")
GSC = os.path.join(ROOT, "scripts", "zm", "zm_tod2_cybercity", "_tod_shop_vo.gsc")
# EVERY line is 3D from the dealer's mouth, played to ONE player (PlaySoundToPlayer): full volume only
# within DIST_MIN (at the counter), falling off by DIST_DRY. 2026-09-30 user: "I can walk away kind of
# far maybe like 7 steps and still almost hear him full volume": 220 / 900 -> 48 / 480. The mutters use the same rows.
VOICE_VOL, DIST_MIN, DIST_DRY, DIST_WET = "94", "48", "480", "560"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def read_text(p):
    return open(p, "rb").read().decode("utf-8")


def write_crlf(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))


def lines():
    return json.load(open(LINES, encoding="utf-8"))["lines"]


def wav_secs(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True).stdout.strip()
    return round(float(out), 3)


def chosen():
    picks = json.load(open(PICKS)) if os.path.exists(PICKS) else {}
    ledger = json.load(open(os.path.join(TAKES, "takes.json")))
    out = {}
    for ln in lines():
        take = int(picks.get(ln["file"], 1))
        name = f"{ln['file']}_{take}"
        if name not in ledger:
            sys.exit(f"no take {take} for {ln['file']} - run generate.py first")
        out[ln["file"]] = dict(ledger[name], take=take, group=ln["group"], hook=ln.get("hook", ""), wired=ln.get("wired", False))
    return out


def csv_rows(path):
    text = read_text(path)
    rows = list(csv.reader(io.StringIO(text.replace("\r\n", "\n"))))
    return rows


def csv_write(path, rows):
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    write_crlf(path, buf.getvalue())


def alias_rows_wanted():
    """(table, alias, row) for EVERY dealer alias: a 3D clone of the shop spark row in tod_shop.csv."""
    shop = csv_rows(SHOP_CSV)
    spark = next(r for r in shop[1:] if r and r[0] == "tod_shop_spark_1")
    scol = {h: i for i, h in enumerate(shop[0])}
    wanted = []
    for ln in lines():
        r = list(spark)
        r[0] = ln["file"]
        r[scol["FileSpec"]] = "tod" + chr(92) + "sfx" + chr(92) + ln["file"] + ".wav"
        r[scol["VolMin"]] = r[scol["VolMax"]] = ln.get("vol", VOICE_VOL)   # a line may carry its own volume (the sign laugh is full)
        r[scol["DistMin"]] = DIST_MIN
        r[scol["DistMaxDry"]] = DIST_DRY
        r[scol["DistMaxWet"]] = DIST_WET
        if ln.get("pan") == "2d":
            r[scol["PanType"]] = "2d"   # a cinematic cue on the player's own client (the first jump's sign reveal)
        wanted.append(("shop", ln["file"], r))
    return wanted


def gsc_text(rec):
    body = ["// GENERATED by tools/black_market_vo/pick.py from art/black_market_vo/manifest.json - DO NOT EDIT.",
            "// The length of every dealer line, so _tod_shop's vo_say() can keep ONE voice lane per player",
            "// (a line asked for while another is still speaking is dropped: he never talks over himself).",
            "#namespace tod_shop_vo;", "", "function secs( alias )", "{", "    switch ( alias )", "    {"]
    for name in sorted(rec):
        body.append(f'        case "{name}": return {rec[name]["secs"]:.3f};')
    body += ["    }", "    return 2.0;", "}", ""]
    return "\n".join(body)


def install():
    rec = chosen()
    manifest = {"voice": json.load(open(os.path.join(ROOT, "tmp", "black_market_vo", "voice.json"))).get("voice_id"),
                "generator": "tools/black_market_vo (ElevenLabs REST, model per file)", "files": {}}
    for name, r in rec.items():
        src = os.path.join(TAKES, f"{name}_{r['take']}.wav")
        dst = os.path.join(SFX, name + ".wav")
        # THE MASK (user 2026-10-01): the shipped dealer wears a very slight dark cyber tone over the clean take;
        # the raw take stays clean in tmp so the tone can be retuned without credits
        tone_lufs = mask_tone.apply(src, dst)
        secs = wav_secs(dst)
        manifest["files"][name] = dict(sha256=sha(dst), secs=secs, lufs=tone_lufs, true_peak_db=r["true_peak_db"], mask_tone=mask_tone.FILTER,
                                       take=r["take"], seed=r["seed"], model=r["model"], text=r["text"],
                                       group=r["group"], hook=r["hook"], wired=r["wired"], voice_id=r.get("voice_id", manifest["voice"]))
    # the docs/194 kit's own gate pins the ten wired files: refresh those entries
    kit = json.loads(read_text(KIT_MANIFEST))
    for name, m in manifest["files"].items():
        if name in kit["files"]:
            kit["files"][name] = dict(sha256=m["sha256"], secs=m["secs"], lufs=m["lufs"], source_sha256=m["sha256"],
                                      how="ElevenLabs " + m["model"] + " (tools/black_market_vo), take " + str(m["take"]))
    write_crlf(KIT_MANIFEST, json.dumps(kit, indent=2) + "\n")
    # alias rows, idempotent: all in tod_shop.csv; any dealer row still in tod_ui.csv (the kit's old 2D rows) goes
    names = {ln["file"] for ln in lines()}
    ui = [r for r in csv_rows(UI_CSV) if not (r and r[0] in names)]
    shop = csv_rows(SHOP_CSV)
    for table, alias, row in alias_rows_wanted():
        idx = next((i for i, r in enumerate(shop) if r and r[0] == alias), None)
        if idx is None:
            shop.append(row)
        else:
            shop[idx] = row
    csv_write(UI_CSV, ui)
    csv_write(SHOP_CSV, shop)
    write_crlf(GSC, gsc_text(manifest["files"]))
    write_crlf(MANIFEST, json.dumps(manifest, indent=2) + "\n")
    print(f"BLACK MARKET VO INSTALLED: {len(manifest['files'])} files, {len(alias_rows_wanted())} new alias rows, {GSC}")


def check():
    m = json.loads(read_text(MANIFEST))
    bad = [k for k, r in m["files"].items()
           if not os.path.exists(os.path.join(SFX, k + ".wav")) or sha(os.path.join(SFX, k + ".wav")) != r["sha256"]]
    names = {ln["file"] for ln in lines()}
    missing_lines = sorted(names - set(m["files"]))
    ui = csv_rows(UI_CSV)
    shop = csv_rows(SHOP_CSV)
    have = {r[0]: r for r in shop[1:] if r}
    rowbad = [alias for table, alias, row in alias_rows_wanted() if have.get(alias) != row]
    rowbad += [r[0] + " (2D row left in tod_ui.csv)" for r in ui[1:] if r and r[0] in names]
    gsc_bad = read_text(GSC) != gsc_text(m["files"]).replace("\n", "\r\n")
    kit = json.loads(read_text(KIT_MANIFEST))
    kitbad = [k for k in m["files"] if k in kit["files"] and kit["files"][k]["sha256"] != m["files"][k]["sha256"]]
    for k, r in m["files"].items():
        p = os.path.join(SFX, k + ".wav")
        if os.path.exists(p):
            info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=sample_rate,channels,bits_per_sample",
                                   "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip()
            if info != "48000,2,16":
                bad.append(k + " format " + info)
    if bad or missing_lines or rowbad or gsc_bad or kitbad:
        sys.exit("BLACK MARKET VO STALE: files %s  unshipped lines %s  alias rows %s  gsc_table_stale=%s  kit manifest %s"
                 % (bad, missing_lines, rowbad, gsc_bad, kitbad))
    print(f"BLACK MARKET VO OK: {len(m['files'])} files, rows, GSC table, kit manifest")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        install()
