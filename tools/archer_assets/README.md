# Archer source and native art tools

Current state, provenance and limitations: [asset pass](../../docs/169_archer_asset_pass.md).
Editable art: [archer_equipment.blend](../../art/archer_assets/archer_equipment.blend).

## Original Retriever files

The public [HarryBo21 thread](https://zombiemodding.com/index.php?topic=20366.0)
contains a pasted World at War GSC implementation. Its download is unavailable.
The thread snapshot and parsed model/weapon/FX/audio names are retained in
`source_library/archer_equipment/research/retriever_script_dependencies.json`.
The script names the dependencies but does not contain their meshes, textures,
animation data or sound samples. It also relies on WaW utility scripts and native
weapon definitions. Treat it as a reference, not drop-in BO3 code.

Preferred next extraction route: [OpenAssetTools](https://github.com/Laupetin/OpenAssetTools)
reads BO2 fastfiles offline. OAT 0.33.0 is staged privately at
`tmp/archer_assets/oat_0.33.0`; `Unlinker.exe --help` succeeds. Official Windows ZIP:
`https://github.com/Laupetin/OpenAssetTools/releases/download/v0.33.0/oat-windows.zip`
SHA256 `4bf366cec03558a4b0f20bc8f197a51f4b9dad0aa3edc52b0e40fef2dd95a4f5`.
Release metadata is retained under `source_library/archer_equipment/research`.

With BO2 + Mob of the Dead installed, run:

```powershell
python tools/archer_assets/collect_bo2_sources.py --game-root 'D:/Games/Call of Duty Black Ops II' --action list
python tools/archer_assets/collect_bo2_sources.py --game-root 'D:/Games/Call of Duty Black Ops II' --zone zm_prison --action dump
```

Replace the example folder with the actual install. Each run writes a new
timestamped evidence/output folder inside this repo and opens game inputs
read-only. It never launches a game. A dump exports the selected asset types for
the entire zone; the list is the first step. OAT supports BO2 models, animations,
images and sound banks; FX dumping is unsupported and scripts are compiled
binary. Special image encodings can remain unsupported. Extracted T6 animations
still require conversion/retargeting before use in BO3.

The user subsequently loaded BO2 Alcatraz (Steam build 24784239), and extraction
from the installed files succeeded. `collect_bo2_sources.py` now resolves this
Steam depot's `dlczm2.ipak` vs fastfile-requested `dlc2.ipak` through a private
repository copy. It also checks diagnostic error counts because OAT can exit
zero after missing payload errors. No game files are renamed or changed.

For complete audio include `--preload-zone code_post_gfx_zm --preload-zone common_zm`.
Use `--asset-types image` or `--asset-types soundbank` for targeted retries.
`index_retriever.py` gathers the retained successful data/image/audio dumps into
`source_library/archer_equipment/retriever` with source hashes: 84 files and all
22 selected sound alias rows resolved. Patch scripts are extracted separately
with `--zone zm_prison_patch --asset-types script`. Raw and successfully decompiled
references are in `source_library/archer_equipment/retriever_scripts`.
Official GSC Tool 1.5.1 is staged under `tmp/archer_assets/gsc_tool_1.5.1`; its
release metadata/checksum and each decompilation command are retained.

## Greyhound compatibility investigation

The [public BO2 loader](https://github.com/Scobalula/Greyhound/blob/master/src/WraithXCOD/WraithXCOD/GameBlackOps2.cpp)
tries fixed asset-pool/string-table addresses, then two byte-pattern searches.
It validates the first model as `defaultvehicle` and checks a string entry.
Its public file history last changed on 2023-12-31. The latest GitHub binary
release page itself is marked outdated and directs users to the maintainer's
Discord. Therefore GitHub's binary alone does not establish current support.

If offline extraction fails, first reproduce against the exact `t6zm.exe` and
record its hash, Steam build, extractor version and error. A loader fix would
locate and validate the asset pools, sizes and string table for that build;
changed struct layouts would also need updated readers. Do not remove validity
checks or invent replacement offsets. Source inspection establishes feasibility,
not a tested fix. No current-build compatibility failure has been reproduced.

## Existing Apex / BO3 pipeline

`collect_sources.py` uses the existing RSX pipeline against installed Apex.
`mcp_bootstrap.py` / `mcp_call.py` drive the isolated Blender MCP studio.
`stage_scene.py` imports the original hook meshes, binds textures, reconstructs
BC5 normal Z, exports geometry and renders the hook icon. `presentation_scene.py`
adds a stock-axe icon and cable phase preview. `render_preview.py` renders it.
`stage_retriever.py` follows those two MCP scripts, binds original MOTD textures
and replaces the temporary stock-axe HUD silhouette. `install_native.py` converts
hook geometry/textures and all selected sounds and writes the shared GDT;
`install_retriever.py` adds the original three-LOD world model and its materials;
`build_fx.py` makes bounded FX compositions with stock texture art.

Then run the native first-person stages through the same real Blender MCP:
`stage_native_motion.py` (BO2 hand rig + four original clips),
`stage_embers.py` (original source maps -> native animated material), and
`stage_grapple_view.py` (authored wrist housing + three presentation clips).
Run `install_native_weapons.py`, `finish_native_compat.py`, `build_fx.py`, and
`finalize_manifest.py` after those stages. The compatibility step uses BO3's
official export2bin for the flourish, binds the recovered sound with a native
frame-0 `2D Sound` GDT action, and vendors the missing charge-ring texture.
Embedded BO2 sound-note names alone do not execute a sound in BO3.

Arlington's original hands came from `so_zclassic_zm_prison`, with
`code_post_gfx_zm`, `common_zm` AND `zm_prison` preloaded; this completed with
zero extraction errors. Its retained source run is
`20260925_050624_055906_dump`. Native motion uses the original hand hierarchy,
absolute local hand keys and bind-relative weapon keys, in native inches.

After changes: run `verify_retriever.py`, `verify_native.py`,
`node tools/test_archer_equipment.js`, `node tools/test_archer_art.js`, and
`node tools/test_retriever_native.js`, then the guarded full build and
`python tools/verify_archer_deployment.py`. Details: docs/170. The user performs
native gameplay testing; the tools do not launch BO3.
