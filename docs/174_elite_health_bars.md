# 174 — Health bars over every ELITE (2026-09-25)

User: *"the elites on this map will have a health bar above them so players know how
much health they have left ... this applies to only elites ... do something similar to
how we did on Hellbound ... the health bar on that map fits their theme but we need our
own theme, I would prefer if the health bars were white"* — and, same session: *"the bar
does need some kind of nice animation ... when it gets hit, it should tick and then go
down ... a small little pulse, nothing crazy ... it shouldn't be tiny."*

**STATUS: THIRD PASS 2026-10-01 — elites RED, the Necromancer's helpers WHITE (see "Third pass" at the
bottom).** Second pass (bigger bar + edge-only pulse) 2026-09-25 ~21:50; first pass built 20:59, played by
the user. Everything is in place and gated; the look, the heights and the pulse size are the user's to
judge in game. Build record at the bottom.

## What was ported

Hellbound's `_tod_zombie_hp.gsc` (its docs/49 "route A", four playtests deep) is the
mechanism, copied whole and then cut down:

- **Route A** = one server `NewClientHudElem` per elite per player, `SetShader` +
  `SetWaypoint(true)` + `SetTargetEnt(elite)` — the stock entity-head-icon recipe.
  Zero clientfield bits, zero Lua, no world-to-screen needed. Three traps it is shaped
  around (SetShader resets the anchor → re-anchor same frame; two elems at one anchor draw
  as one → frame+track+fill are ONE image; `hud::create*` ignores `SetTargetEnt` → raw
  elems only) are all in the module header.
- **The bar is an image swap**: eleven pre-baked materials per size (0..100 % in tenths),
  so the frame stays put and only the fill moves.
- **The pulse** (the user's "tick"): first pass punched the WHOLE bar; the second pass pulses
  only the fill's leading edge via baked hit frames (see "Second pass").

## What is different here

| | Hellbound | TOD II |
|---|---|---|
| Who gets a bar | every zombie (hit-linger 3 s) + persistent boss bars | **ELITES ONLY, persistent** from spawn-in to death |
| Palette | charred track, brass frame, ember / blood fill | **WHITE** fill, smoked-glass track, cool-grey frame, faint cyan lip (Fallen/Blackout) |
| Module | `_tod_zombie_hp.gsc` | `scripts/zm/zm_tod2_cybercity/_tod_elite_hp.gsc`, namespace `tod_elite_hp` |
| Materials | `hb_hpbar_h_NN` / `hb_hpbar_b_NN` | `tod_hpbar_e_NN` (elite, 192×24 → 48×6 units) / `tod_hpbar_b_NN` (Panzer + King, 384×32 → 96×8) |
| GDT / images | `source_data/hb_hud_bars.gdt` | `source_data/tod_hud_bars.gdt` + `source_data/tod_hud_bars/_images/` |
| Generator | `tools/gen_hpbar_art.js` → a staging folder | `tools/gen_hpbar_art.js` → **straight into the build inputs** (+ `docs/174_elite_hpbar_art/` previews + zone_lines.txt) |
| Gate | none | `tools/test_elite_hp.js` in `build_map.ps1` (precache = GDT = zone = PNGs; every stamped `tod_boss_kind` has a height row; one init thread) |

**"Elite" (`is_elite`)** = `tod_king` OR a `tod_boss_kind` OR `tod_is_sprinter` OR
`is_boss`. That is the Panzer + Warden King, Rogue Protector, Apothicon Fury ("reaver"),
hellhound, Doppelghast, Mangler and the armored sprinter. Every family stamps its marks on
the spawn frame (each spawner's own TRAP 3 note), so the scan can never see an elite as a
zombie first, and an ordinary zombie never gets a bar: the scan skips it and the damage
callback returns before creating anything.

**Spawn-in grace** (new): a bar is not dealt until the actor is in — Doppelghast and
Mangler are `Ghost()`ed for a 1.2 s tell (grace 1.7 s), the hound bolts in (3.0 s), the
Fury bamfs (2.0 s), everything else 1.5 s. A real hit ends the grace early.

## Heights (first pass — one `#define` each, `-GscOnly`)

| kind | zoff | grounding |
|---|---|---|
| panzer (+ King) | 104 | 72-unit box, tall model |
| protector | 84 | Hellbound's row |
| reaver (Fury) | 48 | hunched |
| hellhound | 30 | a dog |
| doppelghast | 74 | 72-unit box |
| mangler | 76 | 72-unit box + helmet |
| sprinter | 66 | zombie + pack |
| fallback | 90 | an elite with no row |

The dev log prints `kind=` and `zoff=` on every bar (`[TOD_HPBAR] BAR ...`), so "the
Mangler's is too high" names the exact line.

## Knobs, per symptom (all in `_tod_elite_hp.gsc`, `-GscOnly` unless noted)

- bar too big / small on screen → the generator's `ELITE` / `BOSS` spec (w, h, pad), re-run, then `TOD_HPBAR_W/H` / `_BOSS_W/H` = canvas / 4 (the gate checks it), **FULL build**
- pulse too big / small → the generator's `HIT` table (baked), **FULL build**; too long / short → `TOD_HPBAR_HIT_FRAMES` / `_PEAK` (`-GscOnly`)
- bar shows before the elite is visible → `TOD_HPBAR_GRACE_*`
- wrong height → the `TOD_HPBAR_Z_*` row for that kind
- want it to shrink with distance → `SetWaypoint( false )` in `apply()`
- the look itself → `tools/gen_hpbar_art.js` palette/spec, re-run, **FULL build**
- turn it off → `TOD_HPBAR_ENABLED 0`

## Dev logs

`[TOD_HPBAR] INIT / DEAL / DENY / BAR / END / POOL_FULL / SUMMARY` (SUMMARY every 30 s
carries the hudelem high-water mark `hi=`, the pool question). Gated on `level.tod_dev`.

## Verify list (in game)

1. A bar over every elite kind, none over an ordinary zombie.
2. Heights per kind (read `BAR kind= zoff=`).
3. The pulse on every hit: visible, not a white box.
4. No bar over a ghosted Doppelghast/Mangler during the tell.
5. `hi=` at 4 players stays sane; no leftover elems after a seal reclaim or `end_game`.

## Art

Generated white art ships now (`docs/174_elite_hpbar_art/preview_screen.png`). If the
user wants a hand-authored version, **docs/175 is the request brief** and
`~/Downloads/tod_elite_hpbar_art_pack.zip` is the pack; a drop replaces the 22 PNGs under
the same names → `node tools/test_elite_hp.js` → FULL build.

## Build record

See CHANGELOG `2026-09-25 - Elite health bars` and the top of CLAUDE.md.

## Second pass (user, after the first play)

- **Bigger:** bar body 76x10 units elite (was 48x6), 128x12 boss (was 96x8). The drawn size is
  the CANVAS, which includes a 16 px transparent margin for the pulse: 84x18 / 136x20 units
  from 336x72 / 544x80 PNGs. `test_elite_hp.js` fails if draw size != PNG size / 4.
- **Only the edge pulses:** a waypoint element can only be scaled whole, so the whole-bar punch
  is gone. Each fill step 01..10 has two baked hit frames, `_h1` (small) and `_h2` (peak), where
  only the fill's leading edge swells past the frame and glows. A drop shows `_h2` x3 frames,
  `_h1` x3, then rest (`TOD_HPBAR_HIT_FRAMES/PEAK/TICK`). 62 materials total.
- **Red art:** the user is making the final set red from the rewritten docs/175 pack. Install by
  name over `source_data/tod_hud_bars/_images/`, run the gate, full build; do not re-run the
  generator after a drop.

## Third pass: RED for enemies, WHITE for the Necromancer's helpers (2026-10-01)

User: *"the elites on this map have a white bar above them that needs to be changed to red. And then
the necromancers summoners need to have the white bar. So you can tell the difference and you can see
how much health they have left."*

- **Elites and bosses are RED** (sets `e` / `b`, same names, same sizes, same pulse shape). The user's
  own red set (docs/175) never came back; `tools/gen_hpbar_art.js` now draws the red itself. Fill
  `#E61E2B` lit from the top, a red-pink lip and bleed, and a **pink-white** edge pulse so the hit pops
  off the red. Frame and track unchanged.
- **The Necromancer's helpers are WHITE** — a NEW set `s`, `tod_hpbar_s_NN[_h1|_h2]` (31 more
  materials, 93 total): the old white look on a smaller bar, body 64x8 units (192x24 px @1080p, ~84%
  of the elite's), canvas 288x64 -> `TOD_HPBAR_SUMMON_W/H` 72x16. Every player sees them, so a black
  helper Mangler can never be mistaken for the enemy Mangler.
- **What a helper's bar measures.** Nothing on the horde's side hurts a helper, so its "health" is
  what is LEFT of it: `_tod_necro_summon::helper_life` publishes `tod_hpbar_frac` (0..1) every 0.25 s —
  the life clock (paused with the world), and for a thrall also its kills against stock Turned's
  limit, whichever runs out first. The bar draws the smaller of that and real health, steps down in
  tenths, and **pulses its edge on every step** (the same baked pulse as a hit), so the last seconds
  are visible.
- **Discovery.** Helpers are on team `"allies"`, so `scan_loop` also walks `GetAITeamArray( "allies" )`
  and deals only to `is_summon()` (= `tod_necro_helper`, stamped in `helper_register`). Partners and
  any other ally never get one. `is_elite()` now returns false for a helper whatever it carries.
- **Their own budget.** `TOD_HPBAR_SUMMON_BUDGET` 64 hudelems (module total 96 + 64 = 160), so a screen
  of helpers can never take a bar from an elite. Up to 6 helpers per Necromancer: solo 6 bars; four
  Necromancers in 4p could field 24 against a cap of 16 — the rest are dealt as others end (DENY log).
- **Heights.** `TOD_HPBAR_Z_THRALL` 66 (the sprinter's row: the same charcoal body), `_SOULHOUND` 30
  (the hellhound's), `_HELPER_MANGLER` 76 (the Mangler's). Grace 600 ms (`TOD_HPBAR_GRACE_SUMMON_MS`).
- **Gate.** `tools/test_elite_hp.js` now DECODES the full rest frame of each set and fails unless `e` /
  `b` are red and `s` is white; it also checks the helper rows and the helper wiring (stamp, frac
  published + read, the allies scan). 11 negative controls, incl. "elites back to white" and "helpers
  drawn red". `tools/lint_tod_assets.js` exempts `i_tod_hpbar_[ebs]_*` (gated here).
- **Logs.** `[TOD_HPBAR]` DEAL / BAR / END carry `set=e|b|s`; BAR on a helper carries `owner=` and
  `frac=`; SUMMARY adds `summon_live=` and `summon_cap=`. `[TOD_NECRO_SUMMON] HELPER_END` carries
  `bar_frac=`.
- **Build.** BUILT in the Dealer session's FULL BUILD OK 12:22:31 (tmp/dealer_boss/full5.log, exit 0; the map compile + bake reused): FF 228,267,968 B at 12:20:46; test_elite_hp ran INSIDE it (colours e/b RED, s WHITE); the ledger carries all 93 `image,i_tod_hpbar_*` + 93 `material,tod_hpbar_*` (31 per set, e / b / s), and all 93 .iwi were re-converted after the 11:54:33 landing; deployed = repo for both scripts, the zone, tod_hud_bars.gdt and the 93 PNGs; nothing synced after the .ff; the 8 known-waived linker lines only. (A peer's `_tod_shop.gsc` saved 12:19:38 is NOT in this .ff.) UNPLAYED.
- **Preview.** `docs/174_elite_hpbar_art/preview_context.png`: a boss and an elite (red) beside two
  helpers (white) at 1080p on the night sky, the dark ground and a magenta neon wash.

Knobs: the red / white themselves = `FILLS` in the generator (re-run, FULL build); the helper bar's size
= the generator's `SUMMON` spec + `TOD_HPBAR_SUMMON_W/H` together; a helper's bar height = its
`TOD_HPBAR_Z_*` row (`-GscOnly`); the step pulse = the `summon && q < last_q` line in `manage()`.
