# 220 — Moving Tower II development to the new laptop

**2026-10-12.** The user is moving Tower of Doom II: Cybercity to the new laptop (JORDANURBAEZLU,
10.0.0.149), the same way Map One moved on 2026-10-08/09 ("follow that exact same process ... it
was basically a flawless migration"). Map One's plan is its `docs/174_new_laptop_setup.md`; this doc
is the Tower II delta. **Claude on the new laptop: read this first. After the import,
`tools\migrate\check_machine.ps1` says whether the machine is ready.**

Scope (user, 2026-10-12): **only Tower II: Cybercity.** Nothing of the Hellbound map moves (its repo,
its `Downloads\Hellbound_*` sources). The two laptops' Claude sessions may talk and pass data directly.

## The idea

**GitHub carries the repo. One bundle carries everything git can't. One script checks it all.**
Map One's migration already set up everything shared, so this bundle is only Tower II's own data.

| What | How it moves | Size (2026-10-12) |
|---|---|---|
| This repo: scripts, tools, docs, map source, GDTs, `art/`, `model_export/`, sounds — **every file byte-for-byte** | **GitHub** `main` (`*.blend`, `*.fbx` and `tod_boss_music.wav` via Git LFS) | ~7.4 GB git + ~2.9 GB LFS |
| The PRIVATE Mod Tools root `C:\BO3Tools\TOD2Cybercity`: every physical file (stock copies, ported packs, the 17 GB last build), its 123 junctions as (path, target), every folder | **Bundle** `tod2_root\` (sha1 per file) | ~34 GB / 204k files |
| Repo files git does not track: `tmp\` (evidence, restore originals), `source_library\` (raw Apex exports, their only copy), `*.blend1`, `art/sky3d/tod2_sky.blend`, root scratch files | **Bundle** `repo_extras\` | ~56 GB |
| `Downloads\TOD2_*` (Tower II raw sources) | **Bundle** `downloads\` | 0.2 GB |
| `Downloads\T7 Assets V2.8.rar` — **a BUILD input**: `keeper/install_keeper.py --check` and `dealer_boss/install.py --check` re-extract their members from it (with `C:\Program Files\7-Zip\7z.exe`) on every build, `-GscOnly` included | **Bundle** `downloads\` + its SHA1 (the import checks it) | 58.1 GB |
| Claude memory for this project | **Bundle** `claude\memory` | < 1 MB |
| BO3 + Mod Tools + their pack overlay, Git/Python/Node/Blender/FFmpeg, `Documents\BO3_tools`, `test+map` (PyCoD), Blender addons + prefs, BO3 keybinds, Radiant prefs, git identity, Codex config, the Blender MCP venv (`..\tower_of_doom_II_hellbound\tmp\gold_sword_env`) | **Already on the new laptop** (Map One's migration, 2026-10-09) | — |

### Why the private root moves whole (not re-created)
`tools/setup_tod2_workspace.ps1` made the root ONCE (2026-09-22) as a physical copy of that day's
Steam tools root. Re-running it on the new laptop would copy today's Steam root there (stock + Map
One's overlay as of 2026-10-09), not the root Tower II has been building in since: our installers wrote
ported packs, GDTs, sounds and anims into it. So `bundle_tool.py root-export` copies every physical
file (stock copies too: `tod2_workspace.ps1 Resolve-Tod2Root` refuses a root without its private stock
shader binaries and `sw4\textures\tv_lookup.tif`), records the 123 junctions (all point into the
Steam root's `model_export`, `texture_assets`, `_custom`, `art_assets` — the same paths on the new
laptop) and every folder. Left out: the converter cache (`share\assetconvert` except its `shaders`,
`ToolsGfx`, `preshader`), which the first build regenerates. **Never run `setup_tod2_workspace.ps1`
on the new laptop before the import** — it would make a different root.

### How "nothing missed" is proven
- **Repo:** the export refuses to run until every tracked change is committed and pushed, then copies
  every path `git ls-files --others` reports. GitHub + `repo_extras` = this folder.
- **Line endings:** `.gitattributes` is now `* -text` (it was `text=auto eol=lf`): git stores every file
  byte-for-byte, so the 269 CRLF and 69 mixed files the gates pin come back exactly. Same fix as Map
  One's 8be5af0.
- **History:** GitHub held only the initial commit. The three local commits (the 2026-09-20 seed with
  two > 100 MB Blender files GitHub refuses, the path-independence pass, the Skirmisher ladder) were
  never pushed; `main` was rebuilt on GitHub's commit in six size-capped batches (each push < 2 GB)
  and the old commits are kept locally on `backup/local-main-pre-migration`.
- **Private root:** sha1 per file; the import refuses a mismatch; junction targets are checked;
  `check_machine.ps1 -FullHash` re-hashes everything. The export re-stats every source file after the
  copy and re-copies any that changed mid-copy (a build or sync would otherwise tear files).
- **Untracked repo files:** `repo_extras_manifest.json` records every file's size and date; the import
  and `check_machine.ps1` prove each one arrived whole.
- **Reviewed (2026-10-13):** two independent reviewers found 3 blockers + 6 bugs in the first draft
  (an existing root silently kept over Tower II's files, partial untracked copies kept forever, the
  runtime check counting DLLs the private tools cannot load, the marker written first, unrepairable
  same-size corruption, a non-cp1252 file name crashing failure lists, Python 3.11 missing junctions,
  peer builds invisible to the preflight, no free-space check). All fixed; a 34-case round-trip test
  plus a mid-copy-change test pass, and the old tool fails the new cases.

## A. Old laptop (this one)

1. **Visibility:** the GitHub repo stays **public** (user, 2026-10-12, told it publishes the ported
   models, licensed music and the Dealer's voice — same call as Map One).
2. **Commit + push everything** — done 2026-10-12 on `main` (six batches + the migration scripts).
3. **Close BO3, Radiant, the mod launcher, Blender studios and any build.**
4. **Build the bundle** (dry run first):
   ```powershell
   powershell -ExecutionPolicy Bypass -File tools\migrate\export_bundle.ps1 -Dest \\10.0.0.149\tod_transfer\round2 -DryRun
   powershell -ExecutionPolicy Bypass -File tools\migrate\export_bundle.ps1 -Dest \\10.0.0.149\tod_transfer\round2
   ```
   It ends `BUNDLE OK` or FAILs. Options: `-SkipBuildOutput` (leave the last build behind, -17 GB),
   `-IncludeAgentHistory` (this project's Claude transcripts).
   Over Wi-Fi: keep this laptop **plugged in and open** (Modern Standby turns Wi-Fi off on battery).
5. **Keep this laptop untouched** until the new one has passed B4, built and played.

## B. New laptop

1. **Prerequisite: Map One's migration is complete** (its docs/174 B1–B6: same `C:\Users\jorda`
   profile, long paths, Steam BO3 + Mod Tools at `...\Call of Duty Black Ops III 455130`, the usermaps
   junction, Git + LFS, Python 3.14, Node 24, Blender 4.2.23, FFmpeg 8.1.2). Close BO3 and any build.
   **Do not run `setup_tod2_workspace.ps1`** — the import refuses a root it did not make.
   **Runtimes:** Tower II runs cod2map64 / linker / Radiant from `C:\BO3Tools\TOD2Cybercity\bin` (that
   folder is also the working directory), so the VC++ 2012 x64 + DirectX June 2010 DLLs must be in
   System32 or in that private bin — a copy in the Steam tools bin does NOT count. On the new laptop all
   four are in System32 (checked 2026-10-13); if one is not, the import copies it into the private bin.
2. **Import:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File C:\tod_transfer\round2\migrate_scripts\import_bundle.ps1
   ```
   It: refreshes PATH in-process (a stale shell lacks python / node) → checks free space → clones this
   repo (`main`, then a checked `git lfs pull`) → restores the untracked repo files through `.part`
   files and checks every one against `repo_extras_manifest.json` (repairs short copies; keeps only a
   file changed here after the bundle was made) → imports the private root with sha1 checks (refuses a
   root it did not create, never writes through a junction, sets a corrupt bundle file aside as `.bad`
   so the export re-sends it), recreates its folders and 123 junctions, and writes the workspace marker
   LAST with a `.tod2-import.json` stamp → copies a runtime DLL into the private bin only if System32
   lacks it → creates the game's `usermaps\zm_tod2_cybercity` junction (only our own child junction) →
   Downloads (then the T7 pack's SHA1) → Claude memory → pip packages → runs B3. Safe to re-run.
3. **Check:** `powershell -ExecutionPolicy Bypass -File tools\migrate\check_machine.ps1 -FullHash`
   → must end `READY TO BUILD: 0 FAIL`.
4. **Gates, then the first full build** (Claude runs it): `python tools\run_build_gates.py` (check its
   `gates:` count), then `.\tools\build_map.ps1`. It re-converts the assets the map uses, so it takes
   longer than usual. Success = a fresh `.ff` (CLAUDE.md "Builds" / "Verification"). Until it runs, the
   bundle's copy of the last build (2026-10-08 15:20, FF 220,396,416 B) sits in the private root.
5. **Play-test** (the user, `PLAY_NORMAL.bat`). Then confirm Claude sees the memory in the repo.

## Paths that must stay the same

| Path | Why |
|---|---|
| `C:\Users\jorda\Repositories\tower_of_doom_II_cybercity` | `.tod2-workspace.json` names it (the build refuses another); Claude's memory folder name |
| `C:\BO3Tools\TOD2Cybercity` | `tod2_workspace.ps1` hardcodes it; ~80 tools name it |
| `C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130` | the 123 junction targets; the build's stock inputs |
| `C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III\usermaps\zm_tod2_cybercity` | the game reads our build through this child junction |
| `..\tower_of_doom_II_hellbound\tmp\{gold_sword_env,blender_mcp_vendor}` | Blender MCP studio scripts (art sessions only; Map One's import put them there) |
| `..\test+map\tmp\blender-cod`, `%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons` | PyCoD for gates (Map One's import) |

## Not transferred, on purpose

- Nothing of the Hellbound map (user, 2026-10-12). The one BUILD gate that read the Hellbound folder,
  `tools/cyber_elites/verify_assets.py` (7 default-Mangler binaries byte-compared with the donor), now
  checks their sha256s pinned in `art/cyber_elites/mangler_donor.json` (recorded 2026-10-12, each
  byte-identical to the private root's copy) and still compares with the folder wherever it exists;
  proven passing without the folder and failing on a corrupted pin. Authoring-only reads remain:
  `tools/cyber_sword/01_inspect.py` (`Downloads\Hellbound_Gold_Battle_Sword\...`),
  `tools/cyber_elites/01_author.py` / `02_integrate.py` and `tools/prepare_expected_roster.py`
  (`..\tower_of_doom_II_hellbound\...`) — one-off steps whose outputs are already in this repo.
- `SATPerksAssets*` and the other pack archives: only re-extraction tools read them
  (`make_original_rips.py --check`, the build gate, reads no source). The T7 pack is the exception
  above: it is a build input and moves. (The first plan left it out on a wrong "the map builds without
  it" — the 2026-10-12 build-gate audit caught it.)
- The converter cache (`share\assetconvert` minus shaders/ToolsGfx/preshader) — regenerates.
- Credentials: Claude / Codex / git logins, and `ELEVENLABS_API_KEY` (only the voice/SFX generators use
  it — set it as a user environment variable when needed).

## Files

- `tools/migrate/export_bundle.ps1` — old laptop; builds the bundle (`-DryRun` sizes it).
- `tools/migrate/import_bundle.ps1` — new laptop; clone + restore + check.
- `tools/migrate/check_machine.ps1` — read-only readiness check.
- `tools/migrate/bundle_tool.py` — private-root export/import/verify, untracked-file copy (stdlib only).
- `tools/migrate/requirements.txt` — Python packages the tools import, at EXACT versions: many gates
  regenerate PNG / WAV / xmodel_bin in memory and compare bytes. Beyond Map One's five, Tower II's gates
  need `fonttools` (typeface), `resvg_py` (the artgen packs) and `lz4` (PyCoD's xmodel_bin writer —
  never imported by name; without it three gates fail as STALE).

## What else the build reads outside the repo (audit, 2026-10-12)

A read-only audit of all 199 runnable gate lines (+26 post-link) of `build_map.ps1` found, beyond the
above: PyCoD twice (Blender 4.2 addon + `test+map\tmp\blender-cod`, from Map One's migration),
ffmpeg AND ffprobe on PATH, Node 24.18.0 (`gen_kill_feel_art.js --check` compares zlib output),
`tmp\sky_dealer` (its `author.json` holds the absolute repo path), `tmp\wunderstrahl\stage`,
`tmp\partner_assets`, the gitignored `art\dealer_boss\{clips_src,donors}` and
`source_library\fire_bow` — all in `repo_extras`. No gate reads Map One's or ACC's repo; Map One
reaches Tower II only through the shared Steam root behind the 123 junctions (gates hash
`model_export\{hb,black_ops_3,chaos_models,apex}` and `codimages` there), so a Map One edit to those
shared pack folders on the new laptop can turn a Tower II gate red.

## Status

**2026-10-13 00:30:** repo pushed to `main` (six batches + this tools commit). Dry run: ~152.7 GB
(tod2_root 34.14 GB, repo_extras 60.24 GB, T7 pack 58.08 GB, TOD2 Downloads 0.20 GB). Target
`\\10.0.0.149\tod_transfer\round2` (the round-one share, a fresh subfolder; account `todcopy`). The two
sessions coordinate through `OneDrive\Documents\claude-bridge\NNN-from-{old,new}-laptop.md` (Remote
Control messages between them were held by a permission-mode difference and dropped). Export next.
