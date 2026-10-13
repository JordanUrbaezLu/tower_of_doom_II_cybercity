# Tower II isolation

Requested by the user on 2026-09-22. This supersedes the inherited shared-root
workflow and the original clone warning in README.

| Resource | Tower II |
|---|---|
| Map / script / sound-zone identity | `zm_tod2_cybercity` |
| Writable tools, database and cache | `C:\BO3Tools\TOD2Cybercity` |
| Build output | `C:\BO3Tools\TOD2Cybercity\usermaps\zm_tod2_cybercity` |
| Game entry | Only `usermaps\zm_tod2_cybercity` links to that output |
| Workshop item | Unpublished; no inherited PublisherID |

Run `tools/setup_tod2_workspace.ps1` once. It copies the compiler, database tools,
GDTs, FX, sounds and animation sources into private directories, starts an empty
database and private conversion cache, and binds the workspace to this repo. Installed model and
texture libraries exceed 84 GB; unmodified stock/donor directories are junctions
used strictly as input. Repo-owned model folders are physical private copies.
The legacy art and third-party `_custom` libraries are input references too;
their 29 GDT files include the perk machines and weapon donors. All 1,101
installed definition files are represented through private-root paths.
Never change a linked donor file. To customize one, copy it into a new private
model directory and point a map-owned GDT at the copy.

Build and sync reject another tools root or a mismatched workspace marker.
Every sync destination must stay within the private root (or this repo for
reverse sync) and must not traverse/contain a reparse point. Build processes
receive private TA_GAME_PATH, TA_TOOLS_PATH and TA_LOCAL_ASSET_CACHE values;
machine/user environment and the shared tools installation remain unchanged.

Do not copy an installed `gdt.db`: `_gdt` records absolute source paths.
The first build creates a new database, and `verify_tod2_database.py` rejects
any definition file outside the private root. Native database-update errors
are fatal. A first migration attempt was stopped before compilation when this
inherited-path problem was found; only Tower II's copied database was parked.
The stricter refresh also exposed seven unsupported `//` lines in the existing
door-material GDT. They were removed and its generator now identifies owned
blocks by asset name; all material fields remain unchanged. Refresh then passed.

The first cold bake revealed another installed dependency: some stock shader
HLSL sources are absent, so Radiant/linker cannot regenerate their binaries.
Setup physically copies `share/assetconvert/ToolsGfx/shaders_modtools`, `shaders`
and `preshader` into the private cache. Model/image caches can start empty.
Missing private shader binaries now fail preflight, and a failed Radiant exit
or missing/stale LED is a hard build failure. Never reuse failed lighting.
The small stock `sw4` texture library is also a physical private copy; the
native `i_generic_lookup` image requires `sw4/textures/tv_lookup.tif`.

Map One's internal ID is `zm_tower_of_doom`, Workshop ID `3788921059`.
Neither is a valid Tower II deployment/publish target. Do not rewrite historical
docs or evidence to pretend older builds used the new identity.

The user tests. Build, preserve diagnostics, and stop; do not launch BO3.

## September 22 verification and concurrent Map One work

PowerShell and Node guards rejected shared-root overrides, Map One repository
writes, path traversal and writes through stock-input junctions. Source checks
confirm the new entry script, zone, sound configuration, vision and launch name.

A separate Map One build started during this migration. Captured processes show
the shared executable linking `-modsource zm_tower_of_doom`, while Tower II's
private Radiant was baking `zm_tod2_cybercity`. Map One's own upgrades script,
patch notes, database and outputs changed. Do not revert that other work or claim
the whole shared installation stayed byte-identical. The unfiltered metadata
audit intentionally records these changes.

The focused separation check found **9,911 shared art-source files unchanged**,
no Tower II map/FX sources in the shared source tree, no Tower II teleporter
model/FX/map identity in Map One's asset ledger, and the unique game child
junction resolving to the private workspace. Rerun after the final package:
`python tools/verify_tod2_separation.py`. Evidence:
`tmp/tod2_isolation/concurrent_build_processes.json`,
`protected_paths_verification.json`, `separation_verification.json`.

September 23 follow-up: the unchanged-source check correctly reports one new
change, `source_data/tod_ui_images/_images/i_tod_spire_win_banner.png`.
Its shared SHA-256 matches Map One's current repo (992e5fff...), while this
repo and its private copy both retain 83c122ef.... Do not restore that other
map's banner or suppress the unfiltered change. The independent follow-up
checks the map/FX boundaries and ledgers, recording all four full hashes in
`tmp/tod2_isolation/separation_followup_20260923.json`.
