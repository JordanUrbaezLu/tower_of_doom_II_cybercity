"""Download selected official RSX 2.3.0 source files for extraction auditing."""
from pathlib import Path
from urllib.request import urlopen
import json

ROOT = Path(__file__).resolve().parents[2] / "tmp/apex_weapons/upstream"
BASE = "https://raw.githubusercontent.com/r-ex/rsx/2.3.0/"
PATHS = [
    "src/core/filehandling/load.cpp", "src/core/filehandling/mbnk.cpp",
    "src/core/filehandling/rpak.cpp", "src/game/audio/event.cpp",
    "src/game/audio/event.h", "src/game/audio/source.cpp",
    "src/core/utils/utils_general.cpp", "src/core/utils/utils_general.h",
    "src/game/rtech/assets/material.h", "src/game/rtech/assets/texture.h",
    "src/game/rtech/assets/settings.cpp", "src/game/rtech/assets/weapon_definition.h",
    "src/game/rtech/assets/model.cpp", "src/pch.h",
    "src/game/audio/miles.cpp", "src/game/audio/miles.h",
    "src/core/mdl/cast.cpp", "src/core/mdl/cast.h",
    "src/game/rtech/assets/animseq.cpp", "src/game/rtech/assets/animrig.cpp",
    "src/game/rtech/assets/ui_image_atlas.cpp", "src/game/rtech/assets/ui_image.cpp",
    "src/game/rtech/utils/utils.cpp", "src/game/rtech/utils/utils.h",
]

if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    for name in PATHS:
        dest = ROOT / Path(name).name
        if not dest.exists():
            dest.write_bytes(urlopen(BASE + name, timeout=30).read())
        print(name, flush=True)
    (ROOT / "sources.json").write_text(json.dumps([BASE + p for p in PATHS], indent=2))
