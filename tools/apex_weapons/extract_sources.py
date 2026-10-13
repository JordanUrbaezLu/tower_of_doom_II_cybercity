"""Collect R-99 / Peacekeeper source assets without changing any game or BO3 inputs.

RSX is copied into this repository's ignored tmp folder because it writes a cache
beside its executable. All native output and logs stay inside this repository.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
APEX = Path("C:/Program Files (x86)/Steam/steamapps/common/Apex Legends")
RSX_SOURCE = Path("C:/Users/jorda/Documents/BO3_tools/RSX_2.3.0")
TOOL = REPO / "tmp/apex_weapons/rsx_2.3.0"
LIBRARY = REPO / "source_library/apex_r99_peacekeeper"
PAKS = APEX / "paks/Win64"
COMMON = [PAKS / n for n in ("common.rpak", "common_early.rpak", "common_mp.rpak")]
UI = [PAKS / n for n in ("ui.rpak", "ui_lobby.rpak", "ui_main_menu.rpak", "ui_ingame_core.rpak", "startup.rpak")]
TYPES = "Ptch,anir,arig,aseq,asqd,dtbl,efct,hcxt,hsys,impa,matl,mdl_,msnp,odla,odlp,refm,rlcd,rson,shdr,shds,stgs,stlt,txan,txls,txtr,ui,uiia,uimg,font,locl,vers,wepn,wrap,rtk"
FILTER = "r99,r97,peacekeeper,energy_shotgun"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def prepare():
    for target in (TOOL, LIBRARY):
        if not target.resolve().is_relative_to(REPO.resolve()):
            raise RuntimeError(f"Output outside the repository: {target}")
        target.mkdir(parents=True, exist_ok=True)
    for name in ("rsx.exe", "rsx_nogui.exe", "rsx_cache_db.bin", "thirdpartylegalnotices.txt"):
        dest = TOOL / name
        if not dest.exists():
            shutil.copy2(RSX_SOURCE / name, dest)
    return TOOL / "rsx.exe"


def run(label, inputs, arguments, audio=False):
    exe = prepare()
    # Each run gets its own cache and working directory. RSX 2.3.0's standalone
    # material exporter hardcodes ./exported_files instead of --exportdir.
    work = TOOL / "runs" / label
    work.mkdir(parents=True, exist_ok=True)
    if not (work / "rsx_cache_db.bin").exists():
        shutil.copy2(TOOL / "rsx_cache_db.bin", work / "rsx_cache_db.bin")
    evidence = LIBRARY / "evidence"
    evidence.mkdir(exist_ok=True)
    argv = [str(exe), "-nogui", "--parsethreads", "2", "--exportthreads", "2",
            "--loadwhitelist", "asrc,aevt" if audio else TYPES]
    argv += arguments + [str(p) for p in inputs if p.exists()]
    if not all(p.exists() for p in inputs):
        raise FileNotFoundError([str(p) for p in inputs if not p.exists()])
    record = dict(argv=argv, cwd=str(work), started=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                  apex_build=(APEX / "build.txt").read_text().strip(),
                  apex_version=(APEX / "gameversion.txt").read_text().strip(),
                  extractor_sha256=digest(exe), inputs=[dict(path=str(p), bytes=p.stat().st_size,
                                                           mtime_ns=p.stat().st_mtime_ns) for p in inputs])
    write_json(evidence / f"{label}.command.json", record)
    print(f"START {label}", flush=True)
    start = time.monotonic()
    with (evidence / f"{label}.log").open("w", encoding="utf-8") as log:
        result = subprocess.run(argv, cwd=work, stdout=log, stderr=subprocess.STDOUT)
    record.update(exit_code=result.returncode, seconds=round(time.monotonic() - start, 2))
    write_json(evidence / f"{label}.result.json", record)
    print(f"DONE {label}: exit={result.returncode}, {record['seconds']}s", flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
    fallback = work / "exported_files"
    if fallback.exists():
        target = LIBRARY / "standalone_materials" / label
        # Validate the absolute resolved endpoints before moving a directory.
        if not all(p.resolve().is_relative_to(REPO.resolve()) for p in (fallback, target)):
            raise RuntimeError("Unsafe fallback output path")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(f"Preserving previous output: {target}")
        fallback.rename(target)
        print(f"Retained RSX fallback output at {target}", flush=True)


def inventory(group):
    inputs = COMMON if group == "common" else UI if group == "ui" else [APEX / "audio/ship/general.mbnk"]
    target = LIBRARY / f"evidence/{group}_assets.csv"
    run(f"inventory_{group}", inputs, ["--list", str(target), "--listformat", "csv",
        "--depfilepath", str(LIBRARY / f"evidence/{group}_dependencies.csv")], group == "audio")
    with target.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    selected = [r for r in rows if any(k in r.get("asset_name", "").lower() for k in FILTER.split(","))]
    write_json(LIBRARY / f"evidence/{group}_weapon_assets.json", selected)
    print(f"Inventory {group}: {len(rows)} total, {len(selected)} matching weapon names", flush=True)


def extract(group, filter_text=None, label=None):
    inputs = COMMON if group in ("models", "motion", "data") else UI if group == "ui" else [APEX / "audio/ship/general.mbnk"]
    types = {"models": "mdl_,matl", "motion": "arig,aseq", "data": "wepn,stgs,stlt,dtbl,rson,wrap,impa,rlcd,txan",
             "ui": "ui,uiia,uimg,txtr,stgs,wrap", "audio": "asrc,aevt"}[group]
    out = LIBRARY / ("audio" if group == "audio" else "assets")
    out.mkdir(parents=True, exist_ok=True)
    args = ["-export", "--exporttypes", types, "--exportfilter", filter_text or FILTER, "--exportdir", str(out),
            "--depfilepath", str(LIBRARY / f"evidence/{label or group}_selected_dependencies.csv")]
    if group in ("models", "motion", "ui"):
        args += ["-matltextures", "-exportdependencies", "-exportrigsequences"]
    if group == "data":
        args += ["-exportfullpaths"]
    run(f"extract_{label or group}", inputs, args, group == "audio")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("inventory", "extract"))
    parser.add_argument("group")
    parser.add_argument("--filter")
    parser.add_argument("--label")
    args = parser.parse_args()
    if args.action == "inventory":
        inventory(args.group)
    else:
        extract(args.group, args.filter, args.label)
