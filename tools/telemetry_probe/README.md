# Telemetry probe (2026-10-04) - does the silent storage channel work on OUR build?

**Goal of the wider work:** store per-run play data (class, guns, round reached, run length,
deaths, purchases) so it can be analysed, with the hard rule from the user that **nothing may
ever open outside the game**. The first map's leaderboard lost player trust because launching
its upload helper flashed a console window and threw the player out of fullscreen.

**What is proven elsewhere:** retail BO3's UI Lua can read and write files under the game's
`players\` folder silently. MACHIN[A]'s Trenches save does it (a local file, not a database)
and the first map's board did it for weeks. The only thing that ever opened a window was
launching a program from Lua. This probe re-proves the file channel on THIS map's build and on
the current game patch (Treyarch's 2026-02-19 update removed some UI functions), and records
whether `Engine.OpenUrl` still exists, since a player-pressed "view my run online" button is one
honest way to get data off the machine later.

## Files

| File | Role |
|---|---|
| `tod_telem_probe_chunk.lua` | the inner Lua, compiled to T7 bytecode by `tools/hksc/hksc.exe` (may name `io`/`os`) |
| `tod_telem_probe_outer.tpl.lua` | the menu shell the linker compiles; whitelist-clean; `load(reader)`s the bytecode |
| `build_probe_lui.js` | compile + splice -> `out/tod_telem_probe.lua` (`--check` = gate-style compare) |
| `_tod_telem.gsc` | the GSC side: sets the mode dvar, opens the overlay on the host, polls the trace, logs |
| `land.js` | `--status` / `--apply` / `--remove`: the seven pieces (two files, two zone lines, two entry-script lines, the client LuiLoad) land or retire together |
| `read_probe.ps1` | reads the newest archived console log: every `[TOD_TELEM]` line, the lane census, the verdict, the probe file |

## Run it

1. Nothing may be building and BlackOps3 must be closed.
2. `node tools/telemetry_probe/build_probe_lui.js` then `node tools/telemetry_probe/land.js --apply`
3. `python tools/run_build_gates.py` (every gate green), then `.\tools\build_map.ps1 -GscOnly`
4. The user plays: load the map, wait for the black screen to lift. Two seconds later a teal line
   `[TOD_TELEM] local file storage: GO` (or NO / NO REPORT / CHUNK FAILED) prints on screen.
   To run the page test, end the game (die): at game over the probe calls `Engine.OpenUrl` once.
   Note WHERE the page opened: Steam overlay (stays in game) or desktop browser (tabs out).
5. Evidence: archive `console_mp.log` (`tools/capture_ai_logs.ps1`) and grep `[TOD_TELEM]`;
   read `<game>\players\tod2_telem_probe.txt` (token line, `second`, `trace ...`).
6. `node tools/telemetry_probe/land.js --remove` before the tree goes to anyone else's build or
   a publish. While landed, `#define TOD_TELEM_LOG 1` shows up in the pre-publish grep.

## Rev 1 result (2026-10-04 22:33 run) and what rev 2 changed

Rev 1 came back `NO_REPORT` at boot and wrote no file. With one report lane (a console `set` issued from
Lua) that cannot separate "the menu Lua never ran" from "the lane is dead on the patched game", and with
no file it cannot separate "io is gone" from "the chunk never ran". Rev 2 therefore:
- pushes every report on TWO lanes: `Engine.Exec("set ...")` AND `Engine.SetDvar(name, value)`;
- pushes `outer_open` the instant `createMenu` runs, before any chunk work, and an EARLY trace right after
  the io/os type check, then the full trace; GSC keeps the LAST value seen over a 6 s window;
- records `exec_<type>_setdvar_<type>` so the trace itself says which lanes exist;
- draws the returned trace as a teal text line on the overlay (a witness that needs no lane);
- runs the io probe twice: blackscreen + 2 s and again 40 s later, after the class draft has closed, in
  case the draft's full-screen menu blocked the first open;
- logs whether `OpenLUIMenu` returned a handle.

## Rev 2 result (2026-10-05 17:33 run, three map loads) and what rev 3 changed

Rev 2 opened the menu every time (`OpenLUIMenu handle defined=1`) and still nothing reached GSC: no
`outer_create`, no trace, not even the file's top-level `tod_telem_loaded` marker, and no file on disk.
Archive: `tmp/elite_tracking/runs/20261005_175358_367_fe125096/`. The map's only proven Lua-to-engine
calls pass the controller the engine hands the menu (`Engine.Exec(controller, "map_restart")`, the
Restart button that worked in that same run); rev 2 asked `Engine.GetLocalClientNum()`, which nothing
else in the map uses. Rev 3 is a lane census: every report goes out on five lanes, each to its own dvar
(`tod_telem_l1` engine-given controller, `l2` controller 0, `l3` GetLocalClientNum, `l4`
Engine.SetDvar) plus `Engine.SendMenuResponse` (GSC logs every `menuresponse`). The log line
`LANES L1=. L2=. L3=. L4=. L5=.` names the lane that works; all zero, including L1, means the file never
executes and the loader is the problem, not the lanes.

## Rev 3 result (2026-10-05 20:05 run) and the root cause: no LuiLoad

Every lane came back empty, including L1 (the engine-given controller, the shape the working Restart
button uses), no SendMenuResponse arrived, and the file's top-level marker never fired. The menu's Lua
never executed. A custom LUI menu is FOUR pieces: the Lua, the zone `rawfile` line, the GSC
`#precache( "lui_menu", ... )`, and `LuiLoad( "ui.uieditor.menus.hud.<name>" )` in the client entry
script `zm_tod2_cybercity.csc` (where tod_upgrade and tod_class_select have theirs). Revs 1-3 lacked
the LuiLoad. Rev 4 adds it as land.js piece 7 and is console-only: no IPrintLnBold, no on-screen text.

## Reading the trace

`chunk_io|exec_function_setdvar_function|EG_true|io_table_os_table|wr_true|rd_true_MATCH|ap_true_lines_2|rm_true|rename_function|date_function|clock_function|xuid_function|OpenUrl_function|done`

- `outer_open` alone (verdict MENU RAN, CHUNK SILENT) : the menu file ran but the bytecode chunk reported nothing.
- `exec_nil` / `setdvar_nil` : that lane does not exist on this game build (the other carried the trace).

- `EG_` : `EnableGlobals()` ran (it unlocks io/os on HavokScript).
- `io_table_os_table` : both libraries exist. `nil` here = the patch removed them -> plan B (companion app or share code).
- `wr_true` / `rd_true_MATCH` : write then byte-exact read-back -> **GO** for local records.
- `ap_true_lines_2` : append works (one record per run is the real feature's shape).
- `rm_true` : a temp file could be removed again.
- `*_function` / `*_nil` : existence only; nothing opened. `OpenUrl_nil` = the overlay-link lane is gone.
- `outer_nochunk` / `outer_chunk_error` : the bytecode did not undump / threw -> the toolchain, not the engine.
- `NO_REPORT` : the overlay never reported in 3 s (menu did not open, or the Exec->dvar bridge failed).

## Design rules carried over (do not relax without an in-game test)

- All file work runs synchronously inside `createMenu`. A UITimer-driven io call froze the engine once.
- `load(reader)`, never `load(string)` (throws on retail). Bytecode header must be `1b 4c 75 61 51 0e`.
- Every value pushed through `Engine.Exec` is sanitized to `[A-Za-z0-9_|:.-]`.
- Engine calls always receive a real controller index; a nil controller crashed the old v4 probe to desktop.
- The outer file never names `io` / `os` / `_G` / `getfenv` / `loadstring` (L3akMod's link-time whitelist).
- The probe never launches a process. The url mode is the single deliberate page open, at game over, armed builds only.
