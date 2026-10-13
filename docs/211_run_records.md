# 211 — RUN RECORDS: storing what players do, without anything ever opening outside the game

STATUS: DESIGN + PROBE STAGED 2026-10-04. The probe (`tools/telemetry_probe/`) is compiled and linted, NOT built,
NOT played. Nothing in this document is in the game yet.

User (2026-10-04): *"store game played information, like preferred guns, games, how long they lasted, anything we
want to get data to improve. We tried to do this with the abandoned cybercity but it would cause a terminal to open
and boot you out ... it loses trust in the players for opening up random apps."* And: *"make sure we are thinking
outside the box ... not get caught in bias of first map and say it's not possible when other maps are doing this."*

## 1. The rule that shapes everything

**Nothing may ever open outside the game.** No console window, no helper program, no page that the player did not
ask for. Trust is the feature; the data is the bonus.

What the first map got right and wrong (docs/40 of that repo, read 2026-10-04): every part of its pipeline worked
except ONE call, `os.execute`, which launched a helper program. Windows gives any program a fullscreen game starts a
console window, and that window yanks exclusive fullscreen. Every "hide it" variant still flashed, and the hidden
background-task route was refused as something an antivirus flags. Pure file reads and writes from the UI Lua were
silent and shipped for weeks. So the old "impossible" is narrow: the game cannot silently phone home on retail BO3.
Storing data is not impossible at all.

What other maps actually do:
- **MACHIN[A]** (`zm_trenches_early`): a LOCAL save file, `players\311210\save_trenches.dat`, written from Lua after
  a one-time permission prompt. No database. Its 2026-10 "match saving" is save-and-resume of a run, with co-op
  state pushed host to clients over the game's own netcode; it overflowed the engine's replicated-string budget
  (`MAX_GAMESTATE_CHARS exceeded`) and is switched off while they fix it.
- **Ultimate Experience Mod**: posts every round to a Cloudflare Worker + Supabase from the player's PC. Its transport
  is not public; the old research inferred the same program-launch trick. Read its fastfile before copying any
  assumption (the old repo's `tools/ff_grep.js`).

## 2. The three tiers

| Tier | What | Leaves the machine? | Trust cost |
|---|---|---|---|
| **1. Local run records** | every run appended to a file under `players\`; a RECORDS screen in game | no | none, after one consent card |
| **2. Player-pressed share** | SUBMIT RUN / VIEW ONLINE button at game over: `Engine.OpenUrl` to our page with the run in the link; share code fallback | yes, on the player's press | none, the player asked |
| **3. Opt-in companion** | a visible desktop app the player downloads knowingly; uploads the local file, writes a file the map reads at boot (live boards, messages) | yes, for those who install | none, informed install |
| never | a process launched from the game, however disguised | | the whole problem |

Tier 1 delivers the player-facing value and produces the file every later tier carries. Tier 2 is how data reaches
us from everyone who cares, with zero install. Tier 3 is for the hardcore and for live in-game boards.

## 3. What Tier 1 proves first: the probe

`tools/telemetry_probe/README.md`. One armed dev build, one three-minute run. It answers, on OUR build and on the
game's current patch (Treyarch's 2026-02-19 update removed some UI functions): can the UI Lua write, read back,
append and remove files under `players\` (GO / NO), and does `Engine.OpenUrl` still exist and where does its page
open (Steam overlay = stays in game; desktop browser = tabs out). The verdict decides Tier 2's shape; Tier 1 needs
only the file half.

## 4. Tier 1 design — local run records

### 4.1 Where the data comes from (zero new network cost)

Each machine records ITS OWN player from what its HUD Lua already sees. That sidesteps the replicated-string budget
MACHIN[A] hit and the full client UI-model pool (61/61 bits):

| Field | Client-side source already in the HUD |
|---|---|
| class | `tod_upg_class` eventstring (sent at the draft and at the crown terminal) |
| current weapon, per-second sample | the loadout widget's weapon-name model (`Engine.GetModelValue( weaponNameModel )`) |
| floor, highest floor | `tod_floor` eventstring (the gauge) |
| round | `gameScore.roundsPlayed` model |
| score, kills, downs, revives, headshots | `PlayerList.<i>` models + `Engine.GetScoreboardColumnForClient` (the scoreboard's own path) |
| run start / end, duration | `os.time()` at blackscreen and at `end_game` |
| party size | `PlayerList` count |

The HOST additionally writes one MATCH row with what only the server knows, pushed through the proven host-local
dvar + menu-open channel (a `SetDvar` blob read by the Lua chunk at `end_game`; it never replicates, which is fine
because it is read on the host): arena level reached, Dealer fight outcome, havens purified, doors bought, cards
drawn, companions received, deaths by cause, power-on round, ambush counts. Dev or god runs record NOTHING.

### 4.2 Files

Flat files directly under `players\` (no folder creation, which is the one step that needs a launched command):

- `players\tod2_runs.jsonl` — one JSON object per run per player, appended. Compact keys. Capped: when the file passes
  2 MB the oldest half is dropped by rewrite (write to `tod2_runs.tmp`, then `os.rename` over the original if the probe
  shows `rename_function`; otherwise rewrite in place).
- `players\tod2_profile.json` — consent flag, schema version, totals (runs, time, best round, best floor, time per
  class, time per weapon), the last 10 runs for the RECORDS screen.
- Identity: `Engine.GetXUID` hashed (never the gamertag, never the raw id) — one profile per Steam user on a shared PC.

Every file call is pcall-guarded, every write is followed by a read-back, and a corrupt file is renamed aside and
recreated, never trusted. Values pushed through `Engine.Exec` are sanitized.

### 4.3 Consent, in our UI language

First time the map loads on a machine: a `TodPromptCard`-family full-screen card under the HUD veil, before the class
draft, in simple words: *"TOWER OF DOOM keeps your run history on this PC so you can see your records. Nothing is sent
anywhere. Allow?"* YES / NOT NOW. The answer is stored in the profile; NOT NOW asks again after 10 runs, never
every run. No consent = no file at all (MACHIN[A]'s precedent, kept).

### 4.4 The RECORDS screen

Pause-menu row and a crown terminal (the GRID TERMINAL's neighbour, same art family): best round, best floor, total
runs, time played, favourite class, top three weapons by time, last 10 runs. Everything the file holds is visible
here, so a player can see exactly what is recorded. That visibility is what makes the consent honest.

### 4.5 Build recipe (proven on this toolchain)

Inner Lua naming `io`/`os` is compiled by `tools/hksc/hksc.exe` to T7 HavokScript bytecode and spliced as a `\ddd`
string into an outer menu file the linker compiles; the outer file loads it with `load(reader)` inside `createMenu`,
synchronously. Generator + `--check` gate: `tools/telemetry_probe/build_probe_lui.js` is the template.

## 5. Tier 2 design — getting data to us, on the player's press

At game over the decision menu grows one entry, **SUBMIT RUN**: `Engine.OpenUrl` to our Cloudflare Worker (the first
map's Worker + D1 is the template, `backend/leaderboard/` there) with the run encoded in the link, signed with a key
baked into the bytecode so forged links are dropped. The page stores the row and shows the run and the boards. If the
probe says the page opens in the desktop browser, the entry's text says so ("opens your browser"). If `OpenUrl` is
gone, the fallback is a 12-character **share code** on the game-over screen that a Discord bot decodes. Tier 2 never
fires on its own, and the game-over screen already waits for the player's choice (`_tod_gameover.gsc`), so there is a
natural place for it.

## 6. Diagnostics

Feature tag `[TOD_RECORDS]`, console-only, gated on `( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) )` per
docs/210: consent read, file open/append results with byte counts, rewrite/trim events, every refusal with its reason,
the host match-row size. The probe keeps its own tag `[TOD_TELEM]`. `tools/capture_ai_logs.ps1` already extracts
every `[TOD_*]` tag into `diagnostics.txt`.

## 7. Risks

- A future game patch strips `io`/`os` from the UI Lua: the feature degrades to "no records", never to an error box
  (every call is guarded). The probe is the canary; keep it runnable.
- Disk full / read-only folder: write fails, read-back fails, the run is dropped and logged. Nothing else changes.
- Co-op: each machine writes only its own player, so there is no cross-client payload to overflow.
- Privacy: hashed id, no gamertags on disk, consent before the first byte, the RECORDS screen shows everything stored.
