"""Resolve weapon icon names to RPak GUIDs, then export native UI PNGs.

SPDX-License-Identifier: AGPL-3.0-or-later
Hash arithmetic follows RTech::StringToGuid in RSX 2.3.0:
https://github.com/r-ex/rsx/blob/2.3.0/src/game/rtech/utils/utils.cpp
"""
import csv
import json
import re
from extract_sources import LIBRARY, UI, run, write_json


def guid(name):
    raw = bytes(c & 0xDF for c in name.replace("\\", "/").encode("ascii"))
    mask = (1 << 64) - 1
    state = 0
    for at in range(0, len(raw) + 1, 4):
        word = int.from_bytes(raw[at:at + 4].ljust(4, b"\0"), "little")
        product = (0x633D5F1 * state) & mask
        term = ((0xFB8C4D96501 * word) & mask) >> 24
        total = (product + term) & mask
        if at + 4 > len(raw):
            return (total - 0xAE502812AA7333 * len(raw)) & mask
        state = total ^ (total >> 61)


if __name__ == "__main__":
    inventory = list(csv.DictReader((LIBRARY / "evidence/ui_assets.csv").open(encoding="utf-8-sig")))
    by_guid = {int(row["guid"], 16): row for row in inventory}
    # Verify arithmetic against known named assets before trusting hashed icons.
    checked = [r for r in inventory if r["type"] == "ui" and not r["asset_name"].startswith("ui\\0x")]
    assert checked and all(guid(r["asset_name"]) == int(r["guid"], 16) for r in checked[:20])
    names = set()
    for path in (LIBRARY / "assets/weapon").glob("*.txt"):
        names.update(re.findall(r'"(?:menu_icon|hud_icon[^\"]*)"\s+"([^\"]+)"', path.read_text()))
    # Skin/loot settings also carry UI paths (including cosmetic thumbnails).
    for path in (LIBRARY / "assets/settings").rglob("*.json"):
        names.update(re.findall(r'"(rui/[^\"]+)"', path.read_text()))
    mapping = []
    for name in sorted(names):
        hits = [by_guid[guid(n)] for n in ("ui_image/" + name + ".rpak", name, name + ".rpak")
                if guid(n) in by_guid]
        mapping.append(dict(name=name, assets=hits))
    write_json(LIBRARY / "evidence/icon_names.json", mapping)
    assets = {a["asset_name"]: a for r in mapping for a in r["assets"]}
    print(f"Resolved {len(assets)} icon assets from {len(names)} names", flush=True)
    if assets:
        run("extract_icons", UI, ["-export", "--exporttypes", "uiia,uimg,txtr",
            "--exportfilter", ",".join(assets), "--exportdir", str(LIBRARY / "assets")])
