# 205 — The war damage pass: the tower after the war

**Status: PHASE 2 BUILT 2026-10-03: FULL BUILD OK 15:01 (tmp/war_damage/full7.log); PLAYED ONCE 15:34-15:45 (no
script errors; every system logged working); its one flaw (every sky flash at one distance) fixed in -GscOnly BUILD OK
15:58 (tmp/war_damage/gsc8.log, .ff 15:58:20) - section 8.** The user judges the look; the distance fix is unplayed.

User, 2026-10-03: *"The tower needs a bit more flavor. The broken off pieces look to clean. The map is
basically the first map but looks like its been fallen and beaten up by wars. Can we add that feel to the
tower"*

## 1. What changed

**THE 24 BREAKS** (the snapped stair flights of tools/broken_tower_layout.js) were clean cuts: a flat-ended
ledge, a tidy catch deck, a stump. Each break is now a wound:

- **The snapped lip is jagged**: concrete slab chunks still hanging off its two ends, rebar bent out over the
  drop, short bars hanging straight down, a torn steel plate.
- **Everything the blast touched is scorched**: soot and blast decals on the ledge, the wall under it, the core
  wall and the catch deck; a blast crater with exposed rebar on the core wall above head height; a spray of
  dark shrapnel holes punched round the crater and across the wall under the lip.
- **The catch deck holds what fell**: a rubble pile, a fallen slab, chunks, scrap metal and glass, kept out of
  the landing spot and the walkway middle.
- **The rest of the stair hangs off the tower**: the old stair's iron beam dangling off the outside, the
  column's rebar cage standing out of the snapped stump, cables hanging loose.
- **It is still burning**: dust trickling off every snapped ledge, embers on the rubble, sparking cables, eight
  rubble fires with real firelight, floating ash, and six tall dark smoke columns that read from the crown,
  the terrace and the jump.

**SCATTERED DAMAGE on the ordinary floors** (the laps without a break, the havens excluded): a scorched
landing corner with debris, a cable off the outside, an iron beam stub past the rail, a blast with rebar on the
core wall. Sparse on purpose: the breaks are the story, the floors between them are the aftermath.

Numbers (generated, `art/war_damage/layout.json`): 34 models (24 breaks + 10 scatter groups of up to five
floors), 611 stock props, 384 decal cards (131 soot / blast, 253 shrapnel holes), 91 effect anchors (24 dust,
16 embers, 8 low smoke, 8 fires, 19 sparks, 10 ash, 6 smoke columns), 51 of them with a looping sound.

**The decals are chosen by measurement.** A scorch must be darker than the dark district panels it sits on.
Blender reads the decal TIFFs' alpha (PIL drops that 4th sample); measured sRGB luminance where the alpha is
solid: `charred_stain_01` 0.10, `blast_01` 0.16, the metal bullet / shrapnel holes 0.01 (kept);
`burn_impact_01` 0.22, `charred_stain_02` 0.23 and the concrete `cracks_01` 0.34 (dropped: the first review
showed them as pale patches and white squiggles on the panels).

## 2. How it is built

Everything is Treyarch's own stock art, placed by script, merged, and drawn by the client:

1. **The kit** (`tools/war_damage/probe_kit.py` -> `art/war_damage/kit.json`): 21 stock props by role
   (rubble pile / scatter / chunks / slabs / rebar straights, grids and a column cage / scrap / an iron gantry
   beam / rubber cables / a damaged light fixture / glass shards), with their LOD files, materials and bounds.
2. **The layout** (`tools/war_damage/layout.js`): composes each break in its own frame (odd laps as written,
   even laps turned 180 degrees, exactly as the generator mirrors the tower), seeded per lap so no two breaks
   match and a re-run gives the same tower. It places props, decal cards (lifted 0.4 off their surface,
   turned only in quarter steps on walls) and effect anchors, and CHECKS every piece against keep-out zones:
   the landing spot (a 60 x 79 column the player falls through), the landing body space, the walkway middle,
   the rail band and the next lap's landing. It writes `art/war_damage/layout.json` and the generated
   `_tod_war_damage_data.csc`.
3. **The merge** (`tools/war_damage/build_clusters.py`, PyCoD): one rigid model per cluster with three LODs
   (LOD0 every prop; LOD1 drops chunks, scrap and glass; LOD2 the big shapes at their lowest stock LOD), the
   decal cards built as quads wound the stock way. LOD distances: breaks 900 / 2400, scatter groups 1700 /
   3600. No collision. Writes `model_export/tod_war_damage/`, `source_data/tod_war_damage.gdt`,
   `art/war_damage/clusters.json` (hashes of the layout, the kit, the GDT and every LOD file).
4. **The client** (`scripts/zm/zm_tod2_cybercity/_tod_war_damage.csc`): spawns the 34 models once per local
   client, and runs the effects in a WINDOW round the local player.

**Why client-only:** the damage is decoration. A client model has no collision (nothing to stand on, nothing
the Archer's grapple can anchor to, invisible to every server trace), costs no server entity, and the `.map`
does not change, so there is no re-bake. The navmesh, the drops, the reach model (docs/200) and the recall
are untouched.

## 3. The effect window

Looping effects are played AT a position (`PlayFX`, no host entity) and looping sounds at a position
(`audio::playloopat`, no entity). Every 0.5 s the client stops what left the window and starts what came in:

- an anchor runs within **700 units of height** (about 1.8 floors) and **1,800 sideways** of the local player;
- the six smoke columns are **always on** (they are how the war reads from a distance);
- at most **26 effects** and **3 firelights** run at once per player; a fire over the light budget burns
  without its light.

## 4. Knobs, per symptom

| Symptom | Knob |
|---|---|
| Too much / too little debris at a break | `layout.js` composition (the per-break block), then re-merge |
| Scorch too dark / too strong | decal sizes in `layout.js`; the `DECALS` lists (measure a replacement first: it must be darker than the panels) |
| Too many / too few shrapnel holes | the two `shrapnel` loops in `composeBreak` (6-9 on the core, 2-4 under the lip; their own random stream) |
| A piece in the way | it is decorative (no collision), but move it in `layout.js`: the checks will tell you which zone it hits |
| Smoke too heavy / too light | `SMOKE_COLUMNS` (6) in `layout.js`; `fx_map.smoke_column` |
| Too many fires | `FIRES` (8) in `layout.js` |
| Effects popping in / out as you climb | `TOD_WAR_WINDOW_Z` / `TOD_WAR_WINDOW_XY` in `_tod_war_damage.csc` |
| Frame rate near a break | `TOD_WAR_FX_MAX` / `TOD_WAR_LIGHT_MAX`; the LOD distances in `build_clusters.py` |
| Sounds too loud / quiet | `tools/war_damage/make_sounds.py` (VolMin/VolMax, distances) |

After a layout change: `node tools/war_damage/layout.js`, `python tools/war_damage/build_clusters.py`,
`python tools/war_damage/wire.py` (re-wires the zone's model list), then a build (a GDT change: FULL; the
geometry key reuses the bake because the `.map` does not move).

## 5. Gates and logs

- `tools/war_damage/test_war_damage.js` (every build): the layout and the sounds are fresh, the merged models
  were built from THIS layout, kit and GDT (hashes), every LOD file present with three LODs and no collision,
  every effect a real effect (no `gfx_debug_missing_fx` stub, no `_pcloud`), every decal a PLAIN decal type
  (never an alpha-reveal one) and never zoned bare, the zone / client entry / sound config / sync wired, the
  client effect list and precaches in lockstep with `layout.js`; 9 negative controls.
- `--ledger` (after the link): both scripts, every effect, every decal material and every model with ALL its
  triangles in all three LODs; negative controls at LOD0 and LOD2. The xmodel ledger lists LODs LOWEST DETAIL
  FIRST (our LOD L is column `tris(lodCount-1-L)`). The converter drops zero-area triangles silently ("Degenerate
  triangle (pre-bone)"); the stock rubber cable's lowest LOD carries 4, so `build_clusters.py` drops triangles
  with coincident corners itself and records them (`degenerate_dropped`: 0 / 0 / 44 over the 34 models), keeping
  merged == compiled. The first build caught exactly this (11 LOD2s, 4 short each, all named in the converter
  logs under `share/assetconvert/xmesh/v6/`).
- `tools/war_damage/wire.py --check`: the shared files are wired and the zone's model list is current.
- **Phase 2 (`test_war_damage.js`, 431 checks, 18 negative controls):** `make_fx.py --check`,
  `build_conduit_torn.py --check`, the conductor twins' GDT (no collision, two LODs) and files against
  `conduit_torn.json`, the sky director's effects / aliases, the entry gsc + csc wiring, the sound-flag bits, the
  lamp kind index, the power wave constants against `_tod_fall.gsc` + `tod_crown_data::wave_orgs()`, the power
  clientfield's name on both sides, the sign bearing against `_tod_jump_title.csc`, the tracer speed against
  `make_fx.py`, the scene-hold beats. `layout.js --check` also pins `scorch.json`; `make_scorch.py --check` the
  burned tiles (run by `verify_surfaces.py`'s manifest shas). **`--ledger` is DEPLOYMENT-AWARE:** a peer's build
  syncs the tree before a later edit here lands, so the ledger is held to what the DEPLOYED zone named, and a
  model's triangle count is compared only when the deployed `.xmodel_bin` IS the one the record describes (a stale
  bin is noted, never failed - its own build verified it). The negative controls run on a fresh model when one
  exists and say so when none does.
- Dev logs (zero before a publish): `[TOD_WAR]` (`TOD_WAR_LOG`): `INIT rev=2 local= models=34/34 conductors=27/27
  fx_anchors=142 power=`, `POWER local= initial_snap=`, `CONDUCTORS local= lit= total= wave_z=`, `WINDOW local= z=
  running= lights= capped= wave_z=`; `[TOD_WAR_SKY]` (`TOD_WAR_SKY_LOG`): `READY rev=1`, `FLASH size= at= dist=
  boom_in=`, `BARRAGE`, `EXCHANGE from= to= rounds= reply=`, `WRECK n= ship= model= from= to= secs= k= trail=`,
  `WRECK_BOOM`, `WRECK_END impact= aborted=`, `HOLD` / `RESUME`, `NO_SITE`, `BUDGET`; `[TOD_WAR] POWER why=` from
  the server (dev only).

## 6. Not verified, and why

- **The look in game.** The review renders (`tools/war_damage/preview_break.py`, background Blender) check
  composition only: neutral studio light at -2 stops (the first renders were overexposed and drew every dark
  material near-white), an approximation of the stock materials (the micro-tiled metals' macro colour, the
  decals' alpha kept apart from their colour). The shrapnel holes' crater normal maps catch the preview's strong
  side lights as bright rims; their colour is black. The decals are lit decal materials on a model surface,
  which stock models use too; how they read under this map's lighting is the playtest's call.
- **Lighting.** Client models are lit by the light grid like zombies and props, not by the baked lightmaps.
- **Cost.** About 30k triangles per break at LOD0 (9k at LOD2), 3.5k per scatter group; 34 client entities
  per player. Measured only offline.

## 7. Phase 2: the war is still on (2026-10-03, build A)

User: *"Yes lets go max quality and production"*. Three layers on top of section 1, every one client-side like
the first pass, so the `.map` and the bake are untouched:

**THE BLAST'S WIRING** (every break; some ordinary-floor blasts): beside the crater the LED fixture (stock
`p7_light_fixture_led_ceiling_01_dmg`) was ripped off its mount and dangles by one bracket, tilted away from the
blast; on the crater's other side the power conduit (the tower's own `tod_power_conduit` channel) is TORN OPEN.
`tools/war_damage/build_conduit_torn.py` tears the authored channel mesh: the strip past a hinge curls off the
wall (the angle grows with the distance past the hinge, so it arcs) and twists about its own axis, the free end's
connector block is torn away, and the whole assembly - bed, lips, clips, cables - bends as one armored strip
(variant a stands out of the wall; b curls past vertical and flops back down). A fray cable or two hangs from the
torn mouth. The two cyan CONDUCTORS are a SEPARATE two-state client model (`tod_war_conductor_<a|b>_<off|on>`,
`source_data/tod_war_conductors.gdt`, the stock conduits' own `mtl_tod_conduit_wire_off/on` materials) spawned
at exactly the body's transform (the layout's rotation IS the engine's frame: local +X = forward, +Y = left,
+Z = up; `assertAxes` proves every placement). 27 torn conduits (24 breaks + 3 ordinary floors), 24 fixtures.

**THE POWER**: `_tod_war_damage.gsc` raises a 1-bit world clientfield `tod_war_power` at the power wave's first
floor (`_tod_fall::power_wave`'s `tod_power_wave_z` cue; or 1.5 s after the `power_on` flag if no wave runs).
Every client replays the wave's own schedule - 51 floors from z 19168 down by 384 over 12 s (LOCKSTEP
`TOD_WAR_WAVE_*` in the csc, gated against `_tod_fall.gsc` and `tod_crown_data::wave_orgs()`) - and as the wave
passes a floor: the conductors swap `_off -> _on`, a cyan ARC (`fx_war_arc`) spits at the torn mouth with an
electric buzz, and the fixture's tube starts to FLICKER: three generated looping effects (`fx_war_tube_flicker_a`
a nervous stutter, `_b` a dying buzz, `_c` nearly dead) whose glow sprites and a real dynamic light (the perk
glow's light element, peak 380, radius 220, cold white) follow the SAME stepped curve, looped seamlessly (the
flicker lives in the curve: one element per part, life = the loop), with a 120 Hz tube hum. Powered-only anchors
(flag 16) never run before the wave reaches their height; a late joiner gets the bit in his first snapshot and
sees everything lit. A flickering tube counts against the dynamic-light budget like a firelight
(`TOD_WAR_LIGHT_MAX` 4).

**THE WAR IN THE SKY** (`_tod_war_sky.csc`): far over the city's horizon, in every direction but the sign's:
detonations (a hot flash, a warm halo, a smoke knot; three sizes; their BOOM arrives late by the distance - the
speed of sound, 13,500 u/s, with the drawn point standing for something 2.4x further), barrages, EXCHANGES of
tracers (cyan plasma / orange, some landing in a flash, sometimes answered), and now and then a STRICKEN SHIP:
one of the fleet's own haulers or gunships falls out of the sky far away, flown as a scaled stand-in inside the
sealed box exactly like the fleet (`tod_sky_ships::stand_in`, its nozzle flames through the fleet's own
`engines()`), fire and black smoke pouring off it (`fx_war_sky_wreck_s/l`), a secondary explosion on the way
down, and the impact beyond the horizon (`fx_war_sky_impact` + `tod_war_wreck_impact`). The wreck is one client
entity counted in the fleet's budget. THE SIGN'S SKY STAYS CLEAN (nothing within 38 degrees of the sign's bearing
below 30 degrees up; LOCKSTEP with `_tod_jump_title.csc`'s sign yaw) and the whole war HOLDS through a player's
first-jump scene (`tod_jump_title_start` .. `_end` + 3 s; a wreck near the sign at the scene's start is removed
before the camera arrives there).

**SOUNDS** (`make_sounds.py`, seeded synthesis + the user's own large explosion `tod_c4_explode.wav` pitched down,
low-passed and given a rolling tail): `tod_war_tube_lp`, `tod_war_arc_lp`, `tod_war_far_boom_a/b/c`,
`tod_war_far_guns_a/b`, `tod_war_wreck_impact`. **EFFECTS** (`make_fx.py`, from the sky fleet's element
templates like the lucky pass): 13 generated under `share/raw/fx/tod/war/`.

Numbers: 703 props, 142 effect anchors (24 flickering fixtures, 27 arcs, 102 with a sound), 27 conductor twins
(the data file carries `conductor_*`), 61 client models per player with the clusters.

Knobs, per symptom: a tube too bright / dim = `TUBE_LIGHT_PEAK` / `_RADIUS` in `make_fx.py`; a pattern = `PATTERN`
/ `LOOPS`; too much / little war = `TOD_WAR_SKY_GAP_*`, `_WRECK_GAP_*`; the war too near / high = `_R_MIN` /
`_EL_MAX`; a boom too late / early = `TOD_WAR_SKY_FAR_MULT`; the sign's clean cone = `_SIGN_KEEP` / `_SIGN_EL`; a
torn strip's shape = `VARIANTS` in `build_conduit_torn.py` (then re-run it, `layout.js`, `build_clusters.py`,
`wire.py`); the conductors coming alive at the wrong moment = the wave constants (gated).

Review: `tools/war_damage/preview_wiring.py` (the torn bodies, the conductor twins, the fixture on a wall;
`art/war_damage/review/wiring_*.png`), `preview_break.py` lap 43 with the wiring.

### 7b. Phase 2, build B (the bake): dark breaks and scorched walls

The one part of phase 2 that moves the `.map` (so it re-bakes):

- **THE BREAKS GO DARK.** The stair-pool light of the broken flight is gone with the flight: `gen_tower_map.js`
  skips the `flight1` pool at every drop lap (76 route pools, was 100; `verify_tower_design.js` counts
  `100 - DROP_LAPS.length`). A break is lit by its rubble fires, its sparks, and - once the power is back - the
  dangling fixture's flicker.
- **THE SURFACES ARE SCORCHED.** The map's own faces at each break wear a SCORCHED TWIN of their kit role:
  `tools/war_damage/make_scorch.py` burns the kit's floor / wall / armor tiles (seeded, periodic so the tiles stay
  seamless: several dark soot cores that fade, streaked down a wall / across a floor, a thin grime over the rest,
  charred flecks of blistered coating; the colour darkened to ~12 % in the cores and desaturated, the gloss x0.25
  and the specular x0.3 under the soot, a fine crackle in the normal map, the emissive black) into 15 new maps
  (`i_tod_cc_<floor|wall|armor>_scorch_{c,n,g,s,e}`, `art/war_damage/scorch_manifest.json`, the kit's third
  source library in `install_surfaces.py`; `verify_surfaces.py` wants 45 maps now). Ten `<role>_scorched`
  roles in `crown_materials.json` (the five district decks, the five district walls; same tint, class and size as
  their base, so the geometry lint classes them by itself). WHICH faces: `layout.js` writes
  `art/war_damage/scorch.json` from each break's own stream (the seven broken pieces and the lip landing + its
  two paras whole; of the core quadrant holding the crater only the face the crater is on, by its outward
  normal) and `tower_surfaces.js` applies it per face (1,464 scorched faces across the 24 breaks). The phase-1
  decal cards (the crater, the soot stains, the shrapnel) sit on top.

Knobs: how burnt = `make_scorch.py` (`soot_field`: the thresholds and the streak length; `render`: the colour /
gloss / specular factors) then `python tools/war_damage/make_scorch.py` + `install_surfaces.py` + a FULL build;
which pieces = the list in `layout.js` (then `layout.js`, `gen_tower_map.js`, a FULL build).

## 8. Build record

- **Build 1** (tmp/war_damage/full1.log, .ff 05:46:29): linked, then FAILED its own post-link ledger check. Two
  causes, both fixed: 11 LOD2s compiled 4 triangles short (the stock cable's zero-area triangles, section 5) and
  the check compared our LOD0 to the ledger's coarsest column. The fix was proven against this build's own ledger
  (`--ledger` passed on it with the regenerated clusters.json) before rebuilding.
- **Build 2 = FULL BUILD OK 06:03** (tmp/war_damage/full2.log; synced 05:51; geom_key REUSED the Battle Arena
  session's 05:18 BSP / LED / navmesh because the .map is unchanged): .ff 06:01:44, FF 229,314,304 B. WAR DAMAGE OK
  (372) and WAR DAMAGE LEDGER OK ran inside it. Verified by hand: the ledger carries scriptparsetree
  `_tod_war_damage.csc` + `_tod_war_damage_data.csc`, 34 `xmodel,tod_war_*`, all 8 effects and the 5 decal
  materials (`mc/...`); `amb\fire\small\small.wav` and `chr\robot\sparking_lp.wav` are in the fresh loaded bank
  (06:00:57); `model_export/tod_war_damage`, `source_data/tod_war_damage.gdt` and `sound/aliases/tod_war.csv`
  deployed = repo; scripts / zone_source / ui repo == deployed, nothing synced after the .ff, no repo source edited
  after the build start; the 8 known-waived linker lines only. UNPLAYED.
- **Phase 2, build 3** (tmp/war_damage/full3.log, started 13:22:44): died before cod2map at the teleporter gate,
  `tools/teleporter/test_states.js` - `ReferenceError: pad_lock_reason_at is not defined`. That harness evaluates
  the shipping `refresh()` with callee stubs, and session -a4's guarded-haven landing (docs/202 v3) had just given
  the pad a new callee; -a4 added the stub (TELEPORTER STATES PASS on the repo). Nothing of the war pass failed.
- **Phase 2, build 4** (tmp/war_damage/full4.log, started 13:43:39): every gate up to the Retriever's passed
  (teleporter states, ability fx 448, ability sounds, battle arena 66, the haven gates), then
  `tools/test_retriever_native.js` died at 13:51 - `TypeError: abfx.axe_hit is not a function`: session -09's
  docs/206 landing had added `tod_ability_fx::axe_hit()` to the Retriever and its harness stub still carried only
  `ring_at`; -09 added the stub at 13:53 (NATIVE RETRIEVER passed on the repo). The war gate sits after the
  Retriever gate in the build order, so it had not yet run. Lesson, both builds: a harness that stubs a module's
  callees fails the moment a peer adds a call; before a FULL build, run the gate list on the repo (ten minutes)
  rather than paying for it inside the build.
- **Phase 2, build 5** (tmp/war_damage/full5.log, started 13:55:25): NATIVE RETRIEVER passed, WAR DAMAGE OK (431
  checks: 34 client models, 142 effect anchors, 24 flickering fixtures, 27 live arcs, 27 conductor twins) ran
  inside a real build for the first time, then at 14:02:52 `tools/dealer_presence/verify.py --check` died:
  `Reviewed native material source changed: source_data/tod_surface.gdt` - the floor-20 Dealer display's review
  pins the bytes of the kit's material GDT, and build B's ten scorched twins changed it (CLAUDE.md haven v2 rule
  3: a change near that display needs `inventory.js` + a preview re-render + a re-review entry). Session -09's
  sweep of all 84 gate lines on the repo found exactly that one failure. Nothing linked (the deployed .ff stayed
  13:18:01). The re-review: `layout.js` + `inventory.js` regenerated geometry.json / context.json BYTE-IDENTICAL
  to the pinned ones (the map edit moved nothing near the panel; the seventeen kit images were unchanged too),
  the seven previews were re-rendered through the Dealer studio (port 9897, `mcp_call.py preview.py`) and the
  re-review entry recorded in `art/dealer_presence/review_acceptance.json`.
- **Phase 2, build 6** (tmp/war_damage/full6.log, started 14:13:08; carried -7a's arena v2.2, landed 14:04 at my
  LAND NOW so one bake served both): every gate passed (WAR DAMAGE OK 431, DEALER_PRESENCE_SOURCE_OK, ARENA BADGE HUD
  OK, the Lua harness list...), geom_key saw 41 changed inputs and REBUILT: fresh BSP 14:26:33, NAVMESH GATE OK (25
  tower sections joined by the 24 one-way drops, the crown island, the arena whole, 8 transit pads), a fresh bake
  (LED 239,400,329 B), and then the LINKER died at 14:41: `_tod_haven.gsc (963,35) in "cleanse_dome()" : syntax
  error, unexpected TOKEN_CONDITIONAL` - session -a4's v3 haven script, never compiled before (builds 3-5 died
  earlier), wrote `SetModel( ( i % 2 == 0 ) ? a : b )`; the compiler needs the whole ternary in its own parens.
  The haven gate's interpreter accepts that shape, and no other gate compiles GSC. -a4 fixed it at 14:44. Because
  the linker stops at the FIRST script error and 27 scripts had never been compiled, I wrote
  `tools/lint_tod_gsc_strict.js` (unwrapped ternary, `( expr ).field`, a late `#using`, a keyword-less function, a
  never-assigned local, brackets; a self-test of planted errors every run; zero hits on the 108 scripts that had
  compiled at 13:18) and wired it FIRST in build_map.ps1's GSC step: the 27 were clean (session -09's independent
  scan agreed). geom_key records the bake BEFORE the link, so its non-mutating check said REUSE for build 7.
- **Phase 2, build 7 = FULL BUILD OK 15:01** (tmp/war_damage/full7.log, started ~14:51; geom_key REUSED build 6's
  BSP / LED / navmesh): .ff 15:01:16, FF 229,403,200 B, the 8 known-waived linker lines only. Inside it: GSC STRICT
  LINT OK (135 scripts), WAR DAMAGE OK 431, DEALER_PRESENCE_SOURCE_OK, NAVMESH GATE OK on the reused mesh, then WAR
  DAMAGE LEDGER OK (110 LOD files with every triangle, 905,900 merged at LOD0) and the haven / sky fleet / jump
  title / lucky ledgers. Verified by hand: the 15:01:16 ledger carries scriptparsetree `_tod_war_damage.gsc` +
  `.csc` + `_data.csc` + `_tod_war_sky.csc`, 38 `xmodel,tod_war_*` (34 clusters + 4 conductor twins), 13 `fx,tod/war`,
  the 10 scorched materials and 15 scorch images; all 8 war stems are in the fresh loaded bank (all.sabl 15:00:18,
  160.5 MB); deployed = repo for scripts / zone_source / ui, `tod_war.csv`, both GDTs, `model_export/tod_war_damage`,
  `sound_assets/tod/war` and the .map (76 route pools); nothing synced after the .ff; no repo source edited after the
  build start. It also carries session -7a's arena v2.1 + v2.2, -a4's haven v3 (its first compile) and -09's docs/206,
  each owner's rows found in the same ledger and bank. UNPLAYED.
- **The first play** (15:34-15:45 on the jump-pad session's FULL build, .ff 15:32:18, which carries this pass; log
  archived at `tmp/elite_tracking/runs/20261003_154548_488_a1bee5db`): `[TOD_WAR] INIT rev=2 ... models=34/34
  conductors=27/27 fx_anchors=142`; the power wave lit the conductors in order, 1/27 -> 27/27 as it swept z 18,915 ->
  414 in 11.3 s; the effect window stayed inside budget from the crown (z 19,952) to the ground floor (at most 17
  effects and 3 lights at once, never capped); the sky war ran 14 flashes, 7 tracer exchanges, 3 barrages and 2
  stricken ships (both impacts, none aborted), HELD through the first-jump scene and resumed; one `NO_SITE` (an exchange
  target near the crown, skipped as designed); zero script errors. ONE FLAW: every site sat at 11,252 and every boom
  came exactly 2.0 s late - `site()` clamped its radius only by the sealed box, and the box reaches past R_MAX almost
  everywhere. FIXED: the radius is picked in R_MIN..R_MAX, then clamped (6,790..11,252 out, booms 1.2..2.0 s late),
  with a gate check and a negative control (432 checks).
- **Build 8 = -GscOnly BUILD OK 15:58** (tmp/war_damage/gsc8.log, on the 15:32 bake): .ff 15:58:20, FF 229,559,168 B,
  the 8 known-waived lines only; GSC STRICT LINT OK, WAR DAMAGE OK 432 and WAR DAMAGE LEDGER OK inside it; the
  ledger carries `_tod_war_sky.csc` and the deployed copy = repo (it carries the pick); nothing synced after the .ff.
  The fix is UNPLAYED.

## 9. Files

`tools/war_damage/` (probe_kit.py, layout.js, build_clusters.py, build_conduit_torn.py, make_fx.py, make_sounds.py,
make_scorch.py, preview_inventory.js, preview_break.py, preview_wiring.py, test_war_damage.js, wire.py),
`art/war_damage/` (kit.json, kit_war.json, conduit_torn.json, layout.json, clusters.json, scorch.json,
scorch_manifest.json, fx_tables.json, review/), `model_export/tod_war_damage/` (the merged clusters, the conductor
twins, `kit/` the torn bodies), `model_export/tod_surface/_images/i_tod_cc_*_scorch_*.png`,
`source_data/tod_war_damage.gdt` + `tod_war_conductors.gdt` (+ the scorched roles in `tod_surface.gdt`),
`share/raw/fx/tod/war/` (13 effects), `sound/aliases/tod_war.csv` + `sound_assets/tod/war/` (8 wavs),
`scripts/zm/zm_tod2_cybercity/_tod_war_damage.gsc` / `.csc` / `_tod_war_damage_data.csc` (generated) /
`_tod_war_sky.csc`; the scorched kit roles in `tools/art_cohesion/crown_materials.json`, `tower_surfaces.js`
(reads scorch.json), `install_surfaces.py` / `verify_surfaces.py` (the third source library),
`verify_tower_design.js` (76 pools), `tools/gen_tower_map.js` (the broken flights' pools skipped).
