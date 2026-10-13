"""pick.py for a STAGED voice pack: ship new dealer lines into a stage folder, never into the repo.

Other sessions build this repo live, and pick.py --check is a build gate: a lines.json that names a line before its
wav, alias row and length are all in place fails every build. So a new batch of dealer lines is produced into a
stage tree (tmp/asset_prod/<pack>/stage/<repo-relative paths>) and landed in one step. This tool is pick.py's
install for that stage, built from pick.py's OWN functions (alias_rows_wanted, gsc_text, mask_tone, write_crlf), so
the staged files are byte-for-byte what `pick.py` would write once the takes are in the shipping ledger.

  python tools/black_market_vo/stage_pick.py --stage <dir> --takes <dir> --picks <json>
      the stage must already hold tools/black_market_vo/lines.json (the full new table). For every line in it that the
      repo's manifest does not ship yet: mask the picked take (<takes>/<file>_<take>.wav, generate.py's ledger) into
      <stage>/sound_assets/tod/sfx/<file>.wav, add its manifest entry, its alias row and its length; write
      <stage>/art/black_market_vo/manifest.json, <stage>/sound/aliases/tod_shop.csv,
      <stage>/scripts/zm/zm_tod2_cybercity/_tod_shop_vo.gsc and <stage>/tools/black_market_vo/picks.json, each
      starting from the CURRENT repo file (lines already shipped are left exactly as they are).
  python tools/black_market_vo/stage_pick.py --stage <dir> --check [--mirror <scratch dir>]
      builds a scratch overlay (repo + stage) and runs pick.py's real check() on it: the gate the build will run
      after the landing.

The takes must be merged into tmp/black_market_vo/takes/ (files + takes.json entries) when the pack lands, so a later
full `pick.py` install reproduces the same files (the mask is deterministic: same take in, same sha out).
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mask_tone  # noqa: E402
import pick  # noqa: E402

ROOT = pick.ROOT
REL = {
    "lines": os.path.join("tools", "black_market_vo", "lines.json"),
    "picks": os.path.join("tools", "black_market_vo", "picks.json"),
    "manifest": os.path.join("art", "black_market_vo", "manifest.json"),
    "kit": os.path.join("art", "sound_kit", "manifest.json"),
    "ui": os.path.join("sound", "aliases", "tod_ui.csv"),
    "shop": os.path.join("sound", "aliases", "tod_shop.csv"),
    "gsc": os.path.join("scripts", "zm", "zm_tod2_cybercity", "_tod_shop_vo.gsc"),
    "sfx": os.path.join("sound_assets", "tod", "sfx"),
}


def repo(k):
    return os.path.join(ROOT, REL[k])


def point_pick(base_root, lines_path):
    """aim pick.py's module paths at one tree (the real gate code, other files)"""
    pick.LINES = lines_path
    pick.MANIFEST = os.path.join(base_root, REL["manifest"])
    pick.KIT_MANIFEST = os.path.join(base_root, REL["kit"])
    pick.UI_CSV = os.path.join(base_root, REL["ui"])
    pick.SHOP_CSV = os.path.join(base_root, REL["shop"])
    pick.GSC = os.path.join(base_root, REL["gsc"])
    pick.SFX = os.path.join(base_root, REL["sfx"])


def install(stage, takes, picks_path):
    stage = os.path.abspath(stage)
    lines_path = os.path.join(stage, REL["lines"])
    if not os.path.exists(lines_path):
        sys.exit("STAGE PICK: no staged lines.json at " + lines_path)
    ledger = json.load(open(os.path.join(takes, "takes.json")))
    chosen = json.load(open(picks_path))
    manifest = json.loads(pick.read_text(repo("manifest")))
    pick.LINES = lines_path
    new = [ln for ln in pick.lines() if ln["file"] not in manifest["files"]]
    if not new:
        sys.exit("STAGE PICK: every staged line is already shipped - nothing to stage")
    sfx = os.path.join(stage, REL["sfx"])
    os.makedirs(sfx, exist_ok=True)
    for ln in new:
        take = int(chosen.get(ln["file"], 1))
        name = "%s_%d" % (ln["file"], take)
        if name not in ledger:
            sys.exit("STAGE PICK: no take %s in %s" % (name, takes))
        r = ledger[name]
        if r["text"] != ln["text"]:
            sys.exit("STAGE PICK: take %s was generated from different text than lines.json now holds" % name)
        dst = os.path.join(sfx, ln["file"] + ".wav")
        tone_lufs = mask_tone.apply(os.path.join(takes, name + ".wav"), dst)
        manifest["files"][ln["file"]] = dict(sha256=pick.sha(dst), secs=pick.wav_secs(dst), lufs=tone_lufs, true_peak_db=r["true_peak_db"],
                                             mask_tone=mask_tone.FILTER, take=take, seed=r["seed"], model=r["model"], text=r["text"],
                                             group=ln["group"], hook=ln.get("hook", ""), wired=ln.get("wired", False),
                                             voice_id=r.get("voice_id", manifest["voice"]))
        print("  %-24s take %d  %.3fs  %s LUFS" % (ln["file"], take, manifest["files"][ln["file"]]["secs"], tone_lufs))
    # the alias rows: pick.alias_rows_wanted() reads the shop table's spark row + the staged lines; applied to the
    # CURRENT repo table exactly as pick.install() does (existing rows replaced in place, new rows appended)
    point_pick(ROOT, lines_path)
    shop = pick.csv_rows(repo("shop"))
    for table, alias, row in pick.alias_rows_wanted():
        idx = next((i for i, r in enumerate(shop) if r and r[0] == alias), None)
        if idx is None:
            shop.append(row)
        else:
            shop[idx] = row
    names = {ln["file"] for ln in pick.lines()}
    if any(r and r[0] in names for r in pick.csv_rows(repo("ui"))[1:]):
        sys.exit("STAGE PICK: tod_ui.csv carries a dealer row - run the real pick.py once the pack lands")
    pick.csv_write(os.path.join(stage, REL["shop"]), shop)
    pick.write_crlf(os.path.join(stage, REL["gsc"]), pick.gsc_text(manifest["files"]))
    pick.write_crlf(os.path.join(stage, REL["manifest"]), json.dumps(manifest, indent=2) + "\n")
    # picks.json (LF, indent 2: the file's own format): the measured take of every new line, named explicitly
    pk = json.load(open(repo("picks")))
    for ln in new:
        pk[ln["file"]] = int(chosen.get(ln["file"], 1))
    os.makedirs(os.path.dirname(os.path.join(stage, REL["picks"])), exist_ok=True)
    with open(os.path.join(stage, REL["picks"]), "wb") as f:
        f.write((json.dumps(pk, indent=2) + "\n").encode("utf-8"))
    print("STAGE PICK: %d new lines staged under %s (manifest %d files)" % (len(new), stage, len(manifest["files"])))


def check(stage, mirror):
    """an overlay of repo + stage holding only what pick.check() reads, then the real check()"""
    stage = os.path.abspath(stage)
    if os.path.exists(mirror):
        shutil.rmtree(mirror)
    for k in ("lines", "manifest", "kit", "ui", "shop", "gsc"):
        src = os.path.join(stage, REL[k]) if os.path.exists(os.path.join(stage, REL[k])) else repo(k)
        dst = os.path.join(mirror, REL[k])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    m = json.loads(pick.read_text(os.path.join(mirror, REL["manifest"])))
    os.makedirs(os.path.join(mirror, REL["sfx"]), exist_ok=True)
    for name in m["files"]:
        s = os.path.join(stage, REL["sfx"], name + ".wav")
        if not os.path.exists(s):
            s = os.path.join(ROOT, REL["sfx"], name + ".wav")
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(mirror, REL["sfx"], name + ".wav"))
    point_pick(mirror, os.path.join(mirror, REL["lines"]))
    pick.check()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--takes", default="")
    ap.add_argument("--picks", default="")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--mirror", default="")
    a = ap.parse_args()
    if a.check:
        check(a.stage, a.mirror or os.path.join(os.path.abspath(a.stage), "..", "check_mirror"))
    else:
        if not a.takes or not a.picks:
            sys.exit("STAGE PICK: --takes and --picks are required to install")
        install(a.stage, os.path.abspath(a.takes), a.picks)


if __name__ == "__main__":
    main()
