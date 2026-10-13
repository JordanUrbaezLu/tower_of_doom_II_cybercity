"""Collect Archer's Apex grapple source assets into an isolated local library.

Uses the same proven RSX 2.3.0 pipeline as the weapon collection. Installed
packages are read-only; extraction, caches and evidence stay in this repo.
"""
from pathlib import Path
import argparse
import csv
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools/apex_weapons"))
import extract_sources as extract
import collect_audio_events as events

extract.LIBRARY = ROOT / "source_library/archer_equipment/apex_grapple"
extract.TOOL = ROOT / "tmp/archer_assets/rsx_2.3.0"
extract.FILTER = "grapple"
events.LIBRARY = extract.LIBRARY


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=("models", "motion", "audio", "data", "ui", "events", "linked_audio"))
    args = parser.parse_args()
    extract.prepare()
    # Reuse the complete inventory taken from this same installed Apex build.
    for group in ("common", "audio", "ui"):
        source = ROOT / f"source_library/apex_r99_peacekeeper/evidence/{group}_assets.csv"
        with source.open(encoding="utf-8-sig", newline="") as file:
            selected = [r for r in csv.DictReader(file) if "grapple" in r.get("asset_name", "").lower()]
        extract.write_json(extract.LIBRARY / f"evidence/{group}_selected_assets.json", selected)
    if args.group == "events":
        events.main(("grapple",))
    elif args.group == "linked_audio":
        import json
        index = json.loads((extract.LIBRARY / "evidence/audio_events.json").read_text())
        missing = index["missing_wavs"]
        for at in range(0, len(missing), 75):
            extract.extract("audio", ",".join(missing[at:at + 75]), f"linked_audio_{at:04d}")
    else:
        extract.extract(args.group)


if __name__ == "__main__":
    main()
